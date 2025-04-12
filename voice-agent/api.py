import os
import json
import uuid
import asyncio
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from flask import Flask, request, jsonify
from flask_cors import CORS
from sqlalchemy import Column, String, DateTime, Text, create_engine, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session

# データベース設定
DATABASE_URL = "sqlite:///conversations.db"
Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# アプリケーション設定
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# モデル定義
class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime, default=datetime.now)
    end_time = Column(DateTime, nullable=True)
    summary = Column(Text, nullable=True)
    history = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    executed_functions = relationship("ExecutedFunction", back_populates="conversation", cascade="all, delete-orphan")
    
class ActionType(Base):
    __tablename__ = "action_types"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String, ForeignKey("conversations.id"))
    action_type = Column(String, nullable=False)
    conversation = relationship("Conversation")

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String, ForeignKey("conversations.id"))
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.now)
    conversation = relationship("Conversation", back_populates="history")

class ExecutedFunction(Base):
    __tablename__ = "executed_functions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String, ForeignKey("conversations.id"))
    function_name = Column(String, nullable=False)
    arguments = Column(Text, nullable=False)  # JSON形式
    timestamp = Column(DateTime, nullable=False)
    conversation = relationship("Conversation", back_populates="executed_functions")

# データベース初期化
Base.metadata.create_all(bind=engine)

# データベース操作関数
def get_db():
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()

# APIルート
@app.route("/api/conversations", methods=["GET"])
def get_conversations():
    db = get_db()
    conversations = db.query(Conversation).order_by(Conversation.timestamp.desc()).all()
    
    result = []
    for conv in conversations:
        # アクションタイプを取得
        action_types = db.query(ActionType).filter(ActionType.conversation_id == conv.id).all()
        action_type_list = [at.action_type for at in action_types]
        
        result.append({
            "id": conv.id,
            "timestamp": conv.timestamp.isoformat(),
            "end_time": conv.end_time.isoformat() if conv.end_time else None,
            "action_types": action_type_list,
            "summary": conv.summary
        })
    
    return jsonify(result)

@app.route("/api/conversations/<conversation_id>", methods=["GET"])
def get_conversation_detail(conversation_id: str):
    db = get_db()
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    
    if not conversation:
        return jsonify({"error": "Conversation not found"}), 404
    
    # アクションタイプを取得
    action_types = db.query(ActionType).filter(ActionType.conversation_id == conversation_id).all()
    action_type_list = [at.action_type for at in action_types]
    
    # メッセージを取得
    messages = db.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.timestamp).all()
    message_list = [{"role": msg.role, "content": msg.content, "timestamp": msg.timestamp.isoformat()} for msg in messages]
    
    # 実行された関数を取得
    functions = db.query(ExecutedFunction).filter(ExecutedFunction.conversation_id == conversation_id).order_by(ExecutedFunction.timestamp).all()
    function_list = [
        {
            "function": func.function_name, 
            "arguments": json.loads(func.arguments), 
            "timestamp": func.timestamp.isoformat()
        } 
        for func in functions
    ]
    
    result = {
        "id": conversation.id,
        "timestamp": conversation.timestamp.isoformat(),
        "end_time": conversation.end_time.isoformat() if conversation.end_time else None,
        "action_types": action_type_list,
        "summary": conversation.summary,
        "conversation_history": message_list,
        "executed_functions": function_list
    }
    
    return jsonify(result)

# 会話データを保存する非同期関数
async def save_conversation(data: Dict[str, Any]):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _save_conversation_sync, data)

def _save_conversation_sync(data: Dict[str, Any]):
    db = get_db()
    
    try:
        # 会話の作成
        conv = Conversation(
            id=data["conversation_id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            end_time=datetime.fromisoformat(data["end_time"]) if data["end_time"] else None,
            summary=data["summary"]
        )
        db.add(conv)
        
        # アクションタイプの保存
        for action_type in data["action_types"]:
            at = ActionType(
                conversation_id=data["conversation_id"],
                action_type=action_type
            )
            db.add(at)
        
        # 会話履歴の保存
        for msg in data["conversation_history"]:
            message = Message(
                conversation_id=data["conversation_id"],
                role=msg["role"],
                content=msg["content"]
            )
            db.add(message)
        
        # 実行された関数の保存
        for func in data["executed_functions"]:
            executed_function = ExecutedFunction(
                conversation_id=data["conversation_id"],
                function_name=func["function"],
                arguments=json.dumps(func["args"]),
                timestamp=datetime.fromisoformat(func["timestamp"])
            )
            db.add(executed_function)
        
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"データベース保存エラー: {str(e)}")
    finally:
        db.close()

# サーバー起動関数
def run_api_server():
    app.run(host="0.0.0.0", port=5001, debug=True)

if __name__ == "__main__":
    print("APIサーバーを起動しています（ポート5001）...")
    run_api_server() 