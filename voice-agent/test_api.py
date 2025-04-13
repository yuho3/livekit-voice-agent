import asyncio
import uuid
from datetime import datetime
from api import save_conversation

async def test_save():
    conversation_data = {
        "conversation_id": str(uuid.uuid4()),
        "action_types": ["テスト"],
        "order_id": "12345",
        "user_id": "67890",
        "conversation_history": [
            {"role": "assistant", "content": "こんにちは"},
            {"role": "user", "content": "テスト"}
        ],
        "executed_functions": []
    }
    
    print(f"テストデータを保存します: {conversation_data['conversation_id']}")
    await save_conversation(conversation_data)
    print("保存完了")

if __name__ == "__main__":
    asyncio.run(test_save())
