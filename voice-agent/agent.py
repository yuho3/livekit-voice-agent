import logging
import uuid

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
logger = logging.getLogger("voice-agent")


def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()


async def entrypoint(ctx: JobContext):
    initial_ctx = llm.ChatContext().append(
        role="system",
        text=(
            "あなたはLiveKit によって作成された音声エージェントです。ユーザーとのインターフェースは音声になります。文字起こしされた音声があなたに届けられるため、誤字脱字が発生している可能性があります。必要に応じて文意を推測しながら答えてください。"
            "あなたは、短い簡潔な応答を使用し、発音できない句読点の使用は避けるべきです。"
            "あなたは注文確認のコールセンターのエージェントです。注文の確認・変更・キャンセルを司ります。それ以外のことはできません"
            "特に、注文番号・ユーザー番号はともに5桁の数字になります。それぞれのfunctionを使用する前に、ユーザーから聞いた数字があっているかは必ず確認してください。聞こえたものが5桁でなかった場合は、聞き取れなかった旨を謝罪しつつ、もう一度ゆっくり発話してもらうことを促しながら聞いてください"
        ),
    )

    logger.info(f"connecting to room {ctx.room.name}")
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # Wait for the first participant to connect
    participant = await ctx.wait_for_participant()
    logger.info(f"starting voice assistant for participant {participant.identity}")

    # 会話IDの生成
    conversation_id = str(uuid.uuid4())
    logger.info(f"新しい会話ID: {conversation_id}")

    # AssistantFncのインスタンスを作成
    fnc_ctx = AssistantFnc()

    # This project is configured to use Deepgram STT, OpenAI LLM and Cartesia TTS plugins
    # Other great providers exist like Cerebras, ElevenLabs, Groq, Play.ht, Rime, and more
    # Learn more and pick the best one for your app:
    # https://docs.livekit.io/agents/plugins
    agent = VoicePipelineAgent(
        vad=ctx.proc.userdata["vad"],
        stt=openai.STT(model="gpt-4o-transcribe", language="ja"),
        llm=openai.LLM(model="gpt-4o-mini"),
        tts=openai.TTS(
            model="gpt-4o-mini-tts",
            instructions="あなたは注文確認のコールセンターのエージェントです。注文の確認・変更・キャンセルを司ります。注文番号・ユーザー番号はともに5桁の数字になります。それらの数字は一文字ずつ読み上げてください。例：01135 -> ぜろ いち いち さん ご 注文番号は、必ず5桁全てを読み上げてください",
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

    # 会話終了時に実行される処理
    @agent.on("conversation_ended")
    async def on_conversation_ended():
        logger.info("会話が終了しました")
        
        # 会話履歴を取得
        conversation_history = []
        for message in agent.chat_ctx.messages:
            if message.role in ["user", "assistant"]:
                conversation_history.append({
                    "role": message.role,
                    "content": message.text
                })
        
        # 実行された関数からアクションの種類を判断
        action_types = []
        for func in fnc_ctx.executed_functions:
            if func["function"] == "check_order_details":
                if "確認" not in action_types:
                    action_types.append("確認")
            elif func["function"] == "cancel_order":
                if "キャンセル" not in action_types:
                    action_types.append("キャンセル")
            elif func["function"] == "update_order_quantity":
                if "変更" not in action_types:
                    action_types.append("変更")
        
        # 要約生成用のプロンプト
        summary_prompt = llm.ChatContext().append(
            role="system",
            text="あなたは会話の内容を簡潔に要約するアシスタントです。以下の会話履歴から、何が行われたかを50文字以内で要約してください。"
        )
        
        # 会話履歴を追加
        for msg in conversation_history:
            summary_prompt.append(role=msg["role"], text=msg["content"])
        
        # 要約を生成するためのLLMリクエスト
        summary_response = await agent.llm.chat_completion(summary_prompt)
        summary = summary_response.message.text
        
        # アクション要約がない場合のデフォルトメッセージ
        if not action_types:
            action_types = ["不明"]
        
        # データベースに保存するデータ
        conversation_data = {
            "conversation_id": conversation_id,
            "timestamp": agent.start_time.isoformat(),
            "end_time": agent.end_time.isoformat() if agent.end_time else None,
            "action_types": action_types,
            "summary": summary,
            "conversation_history": conversation_history,
            "executed_functions": fnc_ctx.executed_functions
        }
        
        # ここでAPI経由でデータベースに保存
        from api import save_conversation
        await save_conversation(conversation_data)
        
        logger.info(f"会話データを保存しました: {conversation_id}")

    agent.start(ctx.room, participant)

    # The agent should be polite and greet the user when it joins :)
    await agent.say("こんにちは, こちらは楽々ECのコールセンターです。どんなご用件ですか？", allow_interruptions=True)


if __name__ == "__main__":
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            prewarm_fnc=prewarm,
        ),
    )
