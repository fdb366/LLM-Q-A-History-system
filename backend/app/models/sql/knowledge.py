# backend/app/models/sql/knowledge.py
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, BigInteger, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    source_type = Column(Enum("textbook", "reference_book", "website", "paper"), default="textbook")
    source_name = Column(String(200))
    grade_level = Column(String(50))
    file_path = Column(String(500))
    file_size = Column(BigInteger, default=0)
    content_hash = Column(String(64), unique=True)
    chunk_count = Column(Integer, default=0)
    status = Column(Enum("pending", "processing", "completed", "failed"), default="pending")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    chunks = relationship("KnowledgeChunk", back_populates="document", cascade="all, delete-orphan")

class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("knowledge_documents.id", ondelete="CASCADE"))
    chunk_index = Column(Integer)
    content = Column(Text)
    content_length = Column(Integer)
    # 将 metadata 改为 meta_data（或其他非保留名）
    meta_data = Column(JSON)   # 原 metadata = Column(JSON)

    document = relationship("KnowledgeDocument", back_populates="chunks")