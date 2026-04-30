# backend/app/models/sql/file.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)  # 唯一文件名
    original_filename = Column(String(255), nullable=False)  # 原始文件名
    file_path = Column(String(500), nullable=False)  # 文件存储路径
    file_size = Column(Integer, nullable=False)  # 文件大小（字节）
    file_type = Column(String(100), nullable=True)  # 文件类型（MIME）
    uploader_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # 上传者 ID
    is_knowledge_base = Column(Boolean, default=False)  # 是否属于知识库
    is_processed = Column(Boolean, default=False)  # 向量索引是否已处理
    created_at = Column(DateTime, server_default=func.now())
    
    uploader = relationship("User", back_populates="files")
