import logging
import os
import uuid
from logging.handlers import RotatingFileHandler

from dotenv import load_dotenv
from livekit.agents import (
    AutoSubscribe,
    JobContext,
    JobProcess,
    WorkerOptions,
    cli,
    llm,
    metrics,
)
from livekit.agents.pipeline import VoicePipelineAgent
from livekit.plugins import (
    cartesia,
    openai,
    deepgram,
    noise_cancellation,
    silero,
    turn_detector,
)

from tools import AssistantFnc


load_dotenv(dotenv_path=".env.local")

# ログディレクトリの設定
log_dir = os.environ.get("LOG_DIR", "KMS/logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "voice-agent.log")

# ロガーの設定
logger = logging.getLogger("voice-agent")
logger.setLevel(logging.INFO)  # ログレベルの設定

# ファイルハンドラーの追加
file_handler = RotatingFileHandler(log_file, maxBytes=10485760, backupCount=5)  # 10MB、最大5ファイル
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# コンソールハンドラーも残しておく（必要に応じて）
console_handler = logging.StreamHandler()
console_formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)

# これにより既存のロガー設定をリセットする（オプション）
logger.propagate = False


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    initial_ctx = llm.ChatContext().append(
        role="system",
        text=(
            "あなたはLiveKit によって作成された音声エージェントです。ユーザーとのインターフェースは音声になります。文字起こしされた音声があなたに届けられるため、誤字脱字が発生している可能性があります。特に漢字を間違えます。必要に応じて文意を推測しながら答えてください。\n"
            "あなたは、短い簡潔な応答を使用し、発音できない句読点の使用は避けるべきです。\n"
            "あなたは注文確認のコールセンターのエージェントです。注文の確認・変更・キャンセルを司ります。それ以外のことはできません。\n"
            "確認: 注文内容の確認、配送状況と注文商品が確認できるので、必ずユーザーにどちらもお伝えします、"
            "変更: 注文内容の変更、注文商品の数量変更を承ります。ただし、すでに配送・発送が完了している注文は変更できません。"
            "キャンセル: 注文内容のキャンセルを承ります。ただし、すでに配送・発送が完了している注文はキャンセルできません。"
            "特に、注文番号(order_id)とユーザー番号(user_id)はともに5桁の数字になります。これらの番号は会話の中で非常に重要な要素です。\n"
            "初めてfunctionを使用する前に、ユーザーから聞いた数字があっているかは必ず確認してください。聞こえたものが5桁でなかった場合は、聞き取れなかった旨を謝罪しつつ、もう一度ゆっくり発話してもらうことを促しながら聞いてください。一度確認が取れたら、以後基本的にそのユーザーIDと注文IDを使い回してください。\n"
            "会話の中で注文番号とユーザー番号が特定できたらそれをしっかり記録してください。"
        ),
    )

    logger.info(f"connecting to room {ctx.room.name}")
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # Wait for the first participant to connect
    participant = await ctx.wait_for_participant()
    logger.info(f"starting voice assistant for participant {participant.identity}")

    # AssistantFncのインスタンスを作成
    fnc_ctx = AssistantFnc()

    # This project is configured to use Deepgram STT, OpenAI LLM and Cartesia TTS plugins
    # Other great providers exist like Cerebras, ElevenLabs, Groq, Play.ht, Rime, and more
    # Learn more and pick the best one for your app:
    # https://docs.livekit.io/agents/plugins
    agent = VoicePipelineAgent(
        vad=ctx.proc.userdata["vad"],
        stt=openai.STT(model="gpt-4o-transcribe", 
                       language="ja",
                       prompt = "あなたは注文確認のコールセンターのエージェントです。注文の確認・変更・キャンセルを司ります。注文番号(order_id)とユーザー番号(user_id)はともに5桁の数字になります。それらの数字は半角で書き出してください"
                       ),
        llm=openai.LLM(model="gpt-4o"),
        tts=openai.TTS(
            model="gpt-4o-mini-tts",
            instructions="あなたは注文確認のコールセンターのエージェントです。注文の確認・変更・キャンセルを司ります。注文番号(order_id)とユーザー番号(user_id)はともに5桁の数字になります。それらの数字は一文字ずつ読み上げてください。例：01135 -> ぜろ いち いち さん ご。注文番号とユーザー番号は、必ず5桁全てを読み上げてください。これらの番号は会話において非常に重要なため、特に明瞭に発音してください。",
            ),
        # use LiveKit's transformer-based turn detector
        turn_detector=turn_detector.EOUModel(),
        # minimum delay for endpointing, used when turn detector believes the user is done with their turn
        min_endpointing_delay=0.5,
        # maximum delay for endpointing, used when turn detector does not believe the user is done with their turn
        max_endpointing_delay=5.0,
        # enable background voice & noise cancellation, powered by Krisp
        # included at no additional cost with LiveKit Cloud
        noise_cancellation=noise_cancellation.BVC(),
        chat_ctx=initial_ctx,
        fnc_ctx=fnc_ctx,
    )

    usage_collector = metrics.UsageCollector()

    @agent.on("metrics_collected")
    def on_metrics_collected(agent_metrics: metrics.AgentMetrics):
        metrics.log_metrics(agent_metrics)
        usage_collector.collect(agent_metrics)

    agent.start(ctx.room, participant)

    # The agent should be polite and greet the user when it joins :)
    await agent.say("こんにちは, こちらは楽々ECのコールセンターです。どんなご用件ですか？", allow_interruptions=True, add_to_chat_ctx=True)


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
        ),
    )
