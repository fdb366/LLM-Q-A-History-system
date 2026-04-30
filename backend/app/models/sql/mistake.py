# backend/app/models/sql/mistake.py
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Mistake(Base):
    """错题本表"""
    __tablename__ = "mistakes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    question = Column(Text, nullable=False)  # 问题内容
    correct_answer = Column(Text, nullable=True)  # 正确答案
    user_answer = Column(Text, nullable=True)  # 用户答案（如果有）
    knowledge_tag = Column(String(100), nullable=True)  # 知识点标签
    is_weak_point = Column(Boolean, default=False)  # 是否标记为薄弱点
    review_count = Column(Integer, default=0)  # 复习次数
    last_review_at = Column(DateTime, nullable=True)  # 上次复习时间
    next_review_at = Column(DateTime, nullable=True)  # 下次复习时间
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship("User", backref="mistakes")


class KnowledgeTag(Base):
    """知识点标签表"""
    __tablename__ = "knowledge_tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)  # 标签名称
    category = Column(String(50), nullable=True)  # 分类（如"古代史"、"近代史"）
    description = Column(Text, nullable=True)  # 描述
    created_at = Column(DateTime, server_default=func.now())


class ReviewSchedule(Base):
    """复习计划表"""
    __tablename__ = "review_schedules"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    mistake_id = Column(Integer, ForeignKey("mistakes.id", ondelete="CASCADE"), nullable=False)
    scheduled_date = Column(DateTime, nullable=False)  # 计划复习日期
    is_completed = Column(Boolean, default=False)  # 是否已完成
    completed_at = Column(DateTime, nullable=True)  # 完成时间
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", backref="review_schedules")
    mistake = relationship("Mistake", backref="review_schedules")
