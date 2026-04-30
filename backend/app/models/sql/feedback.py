# backend/app/models/sql/feedback.py
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Feedback(Base):
    """用户反馈表"""
    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    rating = Column(Integer, default=0)  # 1-5 星评分，0 表示未评分
    feedback_type = Column(String(50), nullable=True)  # 'inaccurate', 'too_brief', 'other'
    comment = Column(Text, nullable=True)  # 用户评论
    created_at = Column(DateTime, server_default=func.now())

    message = relationship("Message", backref="feedbacks")
    user = relationship("User", backref="feedbacks")


class FeedbackStats(Base):
    """反馈统计表（用于教师后台查看）"""
    __tablename__ = "feedback_stats"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id", ondelete="CASCADE"), nullable=False)
    avg_rating = Column(Integer, default=0)
    total_feedbacks = Column(Integer, default=0)
    low_score_count = Column(Integer, default=0)  # 评分 <= 2 的数量
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
