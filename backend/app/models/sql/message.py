# backend/app/models/sql/message.py
from sqlalchemy import Column, Integer, String, DateTime, Text, Enum, JSON, Float, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    role = Column(Enum("user", "assistant", "system"), nullable=False)
    content = Column(Text, nullable=False)
    tokens_used = Column(Integer, default=0)
    processing_time = Column(Float, default=0)
    source_documents = Column(JSON, nullable=True)  # 存储检索到的来源
    meta_data = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    conversation = relationship("Conversation", back_populates="messages")