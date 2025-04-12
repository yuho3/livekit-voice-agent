from livekit.agents import llm
from livekit.agents.pipeline import AgentCallContext
import logging
import random
import datetime

logger = logging.getLogger("voice-agent")

class AssistantFnc(llm.FunctionContext):
    """
    音声アシスタントが実行できるLLM関数のセットを定義する。
    """

    def __init__(self):
        super().__init__()
        # 注文データを保持するディクショナリ
        self.orders = {}
        
    @llm.ai_callable(
        description="user_idとorder_idを引数に取り、注文のステータスを返します。user_idはともに5桁の数字です。",
    )
    async def check_order_details(
        self,
        user_id: int,
        order_id: int
    ):
        """注文のステータスを確認する"""

        # Function Calling実行中の場合、ユーザーに対して時間がかかることを通知するためのオプションがいくつかある
        # オプション1: Function Callingをトリガーした直後に.sayでフィラーメッセージを使用する
        # オプション2: Function Calling中に、エージェントにテキスト応答を返すように指示する
        agent = AgentCallContext.get_current().agent

        if (
            not agent.chat_ctx.messages
            or agent.chat_ctx.messages[-1].role != "assistant"
        ):
            # エージェントがすでに発話中の場合はスキップ
            filler_message =" ユーザーID{user_id},  注文ID{order_id}の注文のステータスを確認中です"
            message = filler_message.format(user_id=user_id, order_id=order_id)
            logger.info(f"フィラーメッセージを発話: {message}")

            # NOTE: add_to_chat_ctx=True は、Function Callingのチャットコンテキストの末尾にメッセージを追加する
            speech_handle = await agent.say(message, add_to_chat_ctx=True)  # noqa: F841

        logger.info(f"注文ステータスを確認: {user_id}, {order_id}")
        
        # 注文が存在するか確認
        order_key = f"{user_id}_{order_id}"
        if order_key not in self.orders:
            # 注文が存在しない場合は新しく作成
            order_status = random.choice(["準備中", "配送中"])
            order_items = self.generate_random_order_items()
            total_price = sum(item["price"] * item["quantity"] for item in order_items)
            
            # 注文情報を保存
            self.orders[order_key] = {
                "user_id": user_id,
                "order_id": order_id,
                "status": order_status,
                "items": order_items,
                "total_price": total_price,
                "created_at": datetime.datetime.now().isoformat()
            }
        
        # 注文情報を返す
        return self.orders[order_key]

    @llm.ai_callable(
        description="ユーザーの注文をキャンセルする"
    )
    async def cancel_order(
        self,
        user_id: int,
        order_id: int
    ):
        """ユーザーの注文をキャンセルする"""
        
        # Function Calling実行中の状態通知
        agent = AgentCallContext.get_current().agent
        
        if (
            not agent.chat_ctx.messages
            or agent.chat_ctx.messages[-1].role != "assistant"
        ):
            # フィラーメッセージを発話
            filler_message = "ユーザーID{user_id}の注文ID{order_id}のキャンセル処理を実行中です"
            message = filler_message.format(user_id=user_id, order_id=order_id)
            logger.info(f"フィラーメッセージを発話: {message}")
            
            # チャットコンテキストに追加
            speech_handle = await agent.say(message, add_to_chat_ctx=True)  # noqa: F841
        
        logger.info(f"注文キャンセルを実行: {user_id}, {order_id}")
        
        # 注文が存在するか確認
        order_key = f"{user_id}_{order_id}"
        if order_key not in self.orders:
            return {
                "order_id": order_id,
                "user_id": user_id,
                "cancelled": False,
                "message": "注文が見つかりません"
            }
        
        # 注文のステータスに基づいてキャンセル可能かを判断
        order = self.orders[order_key]
        if order["status"] == "準備中":
            # 準備中ならキャンセル可能
            order["status"] = "キャンセル済み"
            return {
                "order_id": order_id,
                "user_id": user_id,
                "cancelled": True,
                "message": "注文が正常にキャンセルされました。返金は3-5営業日以内に処理されます"
            }
        elif order["status"] == "配送中":
            # 配送中はキャンセル不可
            return {
                "order_id": order_id,
                "user_id": user_id,
                "cancelled": False,
                "message": "この注文はすでに配送中のためキャンセルできません"
            }
        elif order["status"] == "配達完了":
            # 配達完了はキャンセル不可
            return {
                "order_id": order_id,
                "user_id": user_id,
                "cancelled": False,
                "message": "この注文はすでに配達済みのためキャンセルできません"
            }
        elif order["status"] == "キャンセル済み":
            # すでにキャンセル済み
            return {
                "order_id": order_id,
                "user_id": user_id,
                "cancelled": False,
                "message": "この注文はすでにキャンセル済みです"
            }
    
    @llm.ai_callable(
        description="ユーザーの注文内容（商品の数量）を変更する.一つずつしか変更ができないので注意"
    )
    async def update_order_quantity(
        self,
        user_id: int,
        order_id: int,
        product_name: str,
        new_quantity: int
    ):
        """注文内容の商品数量を変更する"""
        
        # Function Calling実行中の状態通知
        agent = AgentCallContext.get_current().agent
        
        if (
            not agent.chat_ctx.messages
            or agent.chat_ctx.messages[-1].role != "assistant"
        ):
            # フィラーメッセージを発話
            filler_message = "ユーザーID{user_id}の注文ID{order_id}の商品「{product_name}」の数量を{new_quantity}個に変更しています"
            message = filler_message.format(user_id=user_id, order_id=order_id, product_name=product_name, new_quantity=new_quantity)
            logger.info(f"フィラーメッセージを発話: {message}")
            
            # チャットコンテキストに追加
            speech_handle = await agent.say(message, add_to_chat_ctx=True)  # noqa: F841
        
        logger.info(f"注文内容変更を実行: {user_id}, {order_id}, {product_name}, {new_quantity}")
        
        # 注文が存在するか確認
        order_key = f"{user_id}_{order_id}"
        if order_key not in self.orders:
            return {
                "order_id": order_id,
                "user_id": user_id,
                "updated": False,
                "message": "注文が見つかりません"
            }
        
        # 注文のステータスに基づいて変更可能かを判断
        order = self.orders[order_key]
        
        if order["status"] in ["配送中", "配達完了", "キャンセル済み"]:
            return {
                "order_id": order_id,
                "user_id": user_id,
                "updated": False,
                "message": f"注文は現在「{order['status']}」状態のため変更できません"
            }
        
        # 指定された商品が注文に存在するか確認
        product_found = False
        old_quantity = 0
        old_total = order["total_price"]
        
        for item in order["items"]:
            if item["name"] == product_name:
                product_found = True
                old_quantity = item["quantity"]
                
                # 合計金額の更新（古い数量分を引いて新しい数量分を足す）
                price_diff = (new_quantity - old_quantity) * item["price"]
                order["total_price"] += price_diff
                
                # 数量の更新
                item["quantity"] = new_quantity
                break
        
        if not product_found:
            return {
                "order_id": order_id,
                "user_id": user_id,
                "updated": False,
                "message": f"注文に商品「{product_name}」が見つかりません"
            }
        
        # 注文の更新日時を記録
        order["updated_at"] = datetime.datetime.now().isoformat()
        
        # 商品の数量が0になった場合は注文から削除
        if new_quantity == 0:
            order["items"] = [item for item in order["items"] if item["name"] != product_name]
            return {
                "order_id": order_id,
                "user_id": user_id,
                "updated": True,
                "message": f"商品「{product_name}」を注文から削除しました",
                "old_quantity": old_quantity,
                "new_quantity": new_quantity,
                "old_total": old_total,
                "new_total": order["total_price"]
            }
        
        return {
            "order_id": order_id,
            "user_id": user_id,
            "updated": True,
            "message": f"商品「{product_name}」の数量を{old_quantity}個から{new_quantity}個に変更しました",
            "old_quantity": old_quantity,
            "new_quantity": new_quantity,
            "old_total": old_total,
            "new_total": order["total_price"]
        }

    def generate_random_order_items(self, min_items=1, max_items=3):
        """
        ランダムなEC商品と個数のリストを生成する関数
        """
        # ECサイトの商品リスト（商品名と固定金額）
        products = [
            {"name": "ワイヤレスイヤホン", "price": 12800},
            {"name": "スマートウォッチ", "price": 24500},
            {"name": "ポータブル充電器", "price": 3980}
        ]
        
        # ランダムに選ぶ商品数を決定
        num_items = random.randint(min_items, max_items)
        
        # 重複なしで商品をランダムに選択
        num_items = min(num_items, len(products))
        selected_products = random.sample(products, num_items)
        
        # 各商品について数量を決定
        order_items = []
        for product in selected_products:
            quantity = random.randint(1, 3)  # 1〜3個をランダムに選択
            
            order_items.append({
                "name": product["name"],
                "quantity": quantity,
                "price": product["price"]
            })
        
        return order_items



