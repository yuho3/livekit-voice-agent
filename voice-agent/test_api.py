import asyncio
import uuid
from datetime import datetime
from api import save_conversation

async def test_save():
    conversation_data = {
        "conversation_id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(),
        "end_time": datetime.now().isoformat(),
        "action_types": ["テスト"],
        "summary": "テスト会話データ",
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
