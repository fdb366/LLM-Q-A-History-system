# backend/app/api/endpoints/chat.py
import uuid
from datetime import datetime
from typing import List, Optional
from app.models.sql.message import Message
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.sync_database import get_db
from app.models.sql.user import User
from app.models.sql.conversation import Conversation
from app.api.dependencies.auth import get_current_user
from pydantic import BaseModel

router = APIRouter(prefix="/conversations", tags=["会话"])

# ---------- 请求/响应模型 ----------
class ConversationOut(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True  # 兼容 SQLAlchemy 模型（Pydantic v2）

class ConversationCreate(BaseModel):
    title: str = "新对话"

class MessageOut(BaseModel):
    id: int
    role: str          # 'user' 或 'assistant'
    content: str
    created_at: datetime

    class Config:
        from_attributes = True

# ---------- 接口实现 ----------
@router.post("", response_model=ConversationOut)
def create_conversation(
    conv_in: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建新会话"""
    conv = Conversation(
        user_id=current_user.id,
        title=conv_in.title,
        session_id=str(uuid.uuid4())
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv

@router.get("", response_model=List[ConversationOut])
def get_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户的所有会话，按更新时间倒序"""
    convs = db.query(Conversation).filter(
        Conversation.user_id == current_user.id
    ).order_by(Conversation.updated_at.desc()).all()
    return convs

@router.delete("/{conv_id}")
def delete_conversation(
    conv_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除会话（同时删除关联的消息，因为有级联）"""
    conv = db.query(Conversation).filter(
        Conversation.id == conv_id,
        Conversation.user_id == current_user.id
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail="会话不存在")
    db.delete(conv)
    db.commit()
    return {"msg": "删除成功"}

@router.get("/{conv_id}/messages", response_model=List[MessageOut])
def get_messages(
    conv_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取指定会话的所有消息（按时间正序）"""
    # 首先确认会话属于当前用户
    conv = db.query(Conversation).filter(
        Conversation.id == conv_id,
        Conversation.user_id == current_user.id
    ).first()
    if not conv:
        raise HTTPException(status_code=404, detail="会话不存在")

    messages = db.query(Message).filter(
        Message.conversation_id == conv_id
    ).order_by(Message.created_at.asc()).all()
    return messages