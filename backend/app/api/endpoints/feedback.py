# backend/app/api/endpoints/feedback.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from app.core.database import SessionLocal
from app.models.sql.feedback import Feedback, FeedbackStats
from app.models.sql.message import Message
from app.models.sql.conversation import Conversation
from app.models.sql.user import User
from app.models.sql.notification import Notification, FeedbackReview
from app.api.dependencies.auth import get_current_user, require_roles

router = APIRouter()


class FeedbackCreate(BaseModel):
    message_id: int
    rating: int  # 1-5
    feedback_type: Optional[str] = None  # 'inaccurate', 'too_brief', 'other'
    comment: Optional[str] = None


class FeedbackResponse(BaseModel):
    id: int
    message_id: int
    user_id: int
    rating: int
    feedback_type: Optional[str]
    comment: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


class FeedbackDetailResponse(BaseModel):
    id: int
    message_id: int
    user_id: int
    username: str
    user_role: str
    question: str
    answer: str
    model_name: str
    knowledge_sources: List[dict]
    web_sources: List[dict]
    processing_time: float
    rating: int
    feedback_type: Optional[str]
    comment: Optional[str]
    created_at: str
    conversation_title: str

    class Config:
        from_attributes = True


class FeedbackStatsResponse(BaseModel):
    message_id: int
    question: str
    answer: str
    avg_rating: float
    total_feedbacks: int
    low_score_count: int


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/feedbacks")
def create_feedback(
    feedback: FeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """提交反馈"""
    if not current_user.is_approved:
        raise HTTPException(status_code=403, detail="Account not approved")

    message_id = int(feedback.message_id)

    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    existing = db.query(Feedback).filter(
        Feedback.message_id == message_id,
        Feedback.user_id == current_user.id
    ).first()

    if existing:
        existing.rating = int(feedback.rating)
        existing.feedback_type = feedback.feedback_type
        existing.comment = feedback.comment
        db.commit()
        db.refresh(existing)
        return {
            "id": existing.id,
            "message_id": existing.message_id,
            "user_id": existing.user_id,
            "rating": existing.rating,
            "feedback_type": existing.feedback_type,
            "comment": existing.comment,
            "created_at": str(existing.created_at) if existing.created_at else "",
        }

    db_feedback = Feedback(
        message_id=message_id,
        user_id=current_user.id,
        rating=int(feedback.rating),
        feedback_type=feedback.feedback_type,
        comment=feedback.comment
    )
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)

    _update_feedback_stats(db, message_id)

    # 创建推送通知给审核员
    _create_feedback_notifications(db, db_feedback)

    return {
        "id": db_feedback.id,
        "message_id": db_feedback.message_id,
        "user_id": db_feedback.user_id,
        "rating": db_feedback.rating,
        "feedback_type": db_feedback.feedback_type,
        "comment": db_feedback.comment,
        "created_at": str(db_feedback.created_at) if db_feedback.created_at else "",
    }


@router.get("/feedbacks/my", response_model=List[FeedbackResponse])
def get_my_feedbacks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户的所有反馈"""
    if not current_user.is_approved:
        raise HTTPException(status_code=403, detail="Account not approved")

    feedbacks = db.query(Feedback).filter(Feedback.user_id == current_user.id).all()
    return feedbacks


@router.get("/feedbacks/stats", response_model=List[FeedbackStatsResponse])
def get_feedback_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取反馈统计（教师/管理员专用）"""
    if current_user.role not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="Admin or Teacher only")

    stats = db.query(FeedbackStats).all()
    result = []
    for stat in stats:
        message = db.query(Message).filter(Message.id == stat.message_id).first()
        if message:
            result.append({
                "message_id": stat.message_id,
                "question": message.content[:100] + "..." if len(message.content) > 100 else message.content,
                "answer": message.content[:100] + "..." if len(message.content) > 100 else message.content,
                "avg_rating": stat.avg_rating,
                "total_feedbacks": stat.total_feedbacks,
                "low_score_count": stat.low_score_count
            })
    return result


@router.get("/feedbacks/low-score")
def get_low_score_feedbacks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取低分反馈（评分 <= 2）"""
    if current_user.role not in ["teacher", "admin"]:
        raise HTTPException(status_code=403, detail="Admin or Teacher only")

    low_score_feedbacks = db.query(Feedback).filter(Feedback.rating <= 2).all()
    result = []
    for feedback in low_score_feedbacks:
        message = db.query(Message).filter(Message.id == feedback.message_id).first()
        if message:
            result.append({
                "feedback_id": feedback.id,
                "message_id": feedback.message_id,
                "rating": feedback.rating,
                "feedback_type": feedback.feedback_type,
                "comment": feedback.comment,
                "created_at": feedback.created_at,
                "question": message.content[:200] + "..." if len(message.content) > 200 else message.content
            })
    return result


@router.get("/feedbacks/manage")
def get_all_feedbacks_for_management(
    rating_filter: Optional[int] = None,
    current_user: User = Depends(require_roles(["admin", "teacher"])),
    db: Session = Depends(get_db)
):
    """教师/管理员获取所有反馈详情（含消息上下文）"""
    query = db.query(Feedback).order_by(Feedback.created_at.desc())

    if rating_filter is not None:
        query = query.filter(Feedback.rating == rating_filter)

    feedbacks = query.all()
    result = []

    for fb in feedbacks:
        user = db.query(User).filter(User.id == fb.user_id).first()
        message = db.query(Message).filter(Message.id == fb.message_id).first()

        if not message or not user:
            continue

        conv = None
        if message.conversation_id:
            conv = db.query(Conversation).filter(Conversation.id == message.conversation_id).first()

        user_question = ""
        if conv and message.conversation_id:
            prev_msg = (
                db.query(Message)
                .filter(
                    Message.conversation_id == message.conversation_id,
                    Message.role == "user",
                    Message.id < message.id,
                )
                .order_by(Message.id.desc())
                .first()
            )
            if prev_msg:
                user_question = prev_msg.content

        knowledge_sources = []
        web_sources = []

        try:
            if message.source_documents and isinstance(message.source_documents, list):
                for src in message.source_documents:
                    if isinstance(src, dict):
                        meta = src.get("metadata", {}) or {}
                        # 优先使用 src.type 判断，兼容旧数据检查 metadata.source_type
                        is_web_search = src.get("type") == "web_search" or meta.get("source_type") == "web_search"
                        if is_web_search:
                            web_sources.append({
                                "title": meta.get("title", ""),
                                "url": meta.get("url", ""),
                                "content": str(src.get("content", ""))[:500],
                            })
                        else:
                            knowledge_sources.append({
                                "filename": meta.get("filename", "未知"),
                                "page_number": str(meta.get("page_number", "-")),
                                "content": str(src.get("content", ""))[:500],
                                "score": round(float(src.get("score", 0)), 4),
                            })
        except Exception as e:
            print(f"Error parsing source_documents: {e}")

        result.append({
            "id": fb.id,
            "message_id": fb.message_id,
            "user_id": fb.user_id,
            "username": user.username or "",
            "user_role": user.role or "",
            "question": user_question,
            "answer": message.content or "",
            "model_name": "deepseek-r1:7b",
            "knowledge_sources": knowledge_sources,
            "web_sources": web_sources,
            "processing_time": float(message.processing_time or 0),
            "rating": fb.rating,
            "feedback_type": fb.feedback_type,
            "comment": fb.comment,
            "created_at": str(fb.created_at) if fb.created_at else "",
            "conversation_title": conv.title if conv else "",
        })

    return result


@router.get("/feedbacks/manage/{feedback_id}", response_model=FeedbackDetailResponse)
def get_feedback_detail(
    feedback_id: int,
    current_user: User = Depends(require_roles(["admin", "teacher"])),
    db: Session = Depends(get_db)
):
    """查看单条反馈的完整详情"""
    fb = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    if not fb:
        raise HTTPException(status_code=404, detail="Feedback not found")

    user = db.query(User).filter(User.id == fb.user_id).first()
    message = db.query(Message).filter(Message.id == fb.message_id).first()
    conv = None
    if message and message.conversation_id:
        conv = db.query(Conversation).filter(Conversation.id == message.conversation_id).first()

    user_question = ""
    if message and message.conversation_id:
        prev_msg = (
            db.query(Message)
            .filter(
                Message.conversation_id == message.conversation_id,
                Message.role == "user",
                Message.id < message.id,
            )
            .order_by(Message.id.desc())
            .first()
        )
        if prev_msg:
            user_question = prev_msg.content

    knowledge_sources = []
    web_sources = []

    try:
        if message and message.source_documents and isinstance(message.source_documents, list):
            for src in message.source_documents:
                if isinstance(src, dict):
                    meta = src.get("metadata", {}) or {}
                    # 优先使用 src.type 判断，兼容旧数据检查 metadata.source_type
                    is_web_search = src.get("type") == "web_search" or meta.get("source_type") == "web_search"
                    if is_web_search:
                        web_sources.append({
                            "title": meta.get("title", ""),
                            "url": meta.get("url", ""),
                            "content": str(src.get("content", "")),
                        })
                    else:
                        knowledge_sources.append({
                            "filename": meta.get("filename", "未知"),
                            "page_number": str(meta.get("page_number", "-")),
                            "content": str(src.get("content", "")),
                            "score": round(float(src.get("score", 0)), 4),
                        })
    except Exception as e:
        print(f"Error parsing source_documents: {e}")

    return {
        "id": fb.id,
        "message_id": fb.message_id,
        "user_id": fb.user_id,
        "username": user.username if user else "",
        "user_role": user.role if user else "",
        "question": user_question,
        "answer": message.content if message else "",
        "model_name": "deepseek-r1:7b",
        "knowledge_sources": knowledge_sources,
        "web_sources": web_sources,
        "processing_time": float(message.processing_time) if message and message.processing_time else 0,
        "rating": fb.rating,
        "feedback_type": fb.feedback_type,
        "comment": fb.comment,
        "created_at": str(fb.created_at) if fb.created_at else "",
        "conversation_title": conv.title if conv else "",
    }


@router.delete("/feedbacks/{feedback_id}")
def delete_feedback(
    feedback_id: int,
    current_user: User = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db)
):
    """管理员删除反馈"""
    fb = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    if not fb:
        raise HTTPException(status_code=404, detail="Feedback not found")

    db.delete(fb)
    db.commit()
    return {"msg": "Feedback deleted"}


def _update_feedback_stats(db: Session, message_id: int):
    """更新反馈统计"""
    feedbacks = db.query(Feedback).filter(Feedback.message_id == message_id).all()

    if not feedbacks:
        return

    total = len(feedbacks)
    avg_rating = sum(f.rating for f in feedbacks) / total
    low_score_count = sum(1 for f in feedbacks if f.rating <= 2)

    stat = db.query(FeedbackStats).filter(FeedbackStats.message_id == message_id).first()
    if stat:
        stat.avg_rating = avg_rating
        stat.total_feedbacks = total
        stat.low_score_count = low_score_count
    else:
        stat = FeedbackStats(
            message_id=message_id,
            avg_rating=avg_rating,
            total_feedbacks=total,
            low_score_count=low_score_count
        )
        db.add(stat)

    db.commit()


def _create_feedback_notifications(db: Session, feedback: Feedback):
    """创建反馈推送通知"""
    # 获取所有审核员
    reviewers = db.query(User).filter(User.role == "reviewer", User.is_active == True).all()
    
    # 获取消息和用户信息
    message = db.query(Message).filter(Message.id == feedback.message_id).first()
    user = db.query(User).filter(User.id == feedback.user_id).first()
    
    if not message or not user:
        return
    
    # 创建审核记录
    review = FeedbackReview(
        feedback_id=feedback.id,
        reviewer_id=None,  # 待分配
        status="pending"
    )
    db.add(review)
    db.commit()
    
    # 为每个审核员创建通知
    for reviewer in reviewers:
        notification = Notification(
            user_id=reviewer.id,
            feedback_id=feedback.id,
            title=f"新反馈待审核 - {user.username}",
            content=f"用户 {user.username} 提交了新的反馈，评分：{feedback.rating}星，请及时处理。",
            type="feedback_submit",
            is_urgent=feedback.rating <= 2  # 低分反馈设为紧急
        )
        db.add(notification)
    
    db.commit()


# 新增审核相关 API
@router.post("/feedbacks/{feedback_id}/review")
def review_feedback(
    feedback_id: int,
    review_data: dict,
    current_user: User = Depends(require_roles(["reviewer"])),
    db: Session = Depends(get_db)
):
    """审核员处理反馈"""
    feedback = db.query(Feedback).filter(Feedback.id == feedback_id).first()
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    
    # 查找或创建审核记录
    review = db.query(FeedbackReview).filter(
        FeedbackReview.feedback_id == feedback_id,
        FeedbackReview.reviewer_id == None
    ).first()
    
    if not review:
        review = FeedbackReview(
            feedback_id=feedback_id,
            reviewer_id=current_user.id,
            status="in_review"
        )
        db.add(review)
    else:
        review.reviewer_id = current_user.id
        review.status = "in_review"
    
    # 更新审核信息
    review.review_comment = review_data.get("comment")
    review.action_taken = review_data.get("action")
    review.escalated_to = review_data.get("escalated_to")
    review.reviewed_at = db.func.now()
    
    if review_data.get("status") == "resolved":
        review.status = "resolved"
        review.resolved_at = db.func.now()
    elif review_data.get("status") == "escalated":
        review.status = "escalated"
    
    db.commit()
    
    # 创建结果通知
    _create_review_result_notifications(db, feedback, review)
    
    return {"msg": "审核完成"}


def _create_review_result_notifications(db: Session, feedback: Feedback, review: FeedbackReview):
    """创建审核结果通知"""
    user = db.query(User).filter(User.id == feedback.user_id).first()
    
    if review.status == "resolved":
        # 通知提交用户
        notification = Notification(
            user_id=feedback.user_id,
            feedback_id=feedback.id,
            title="反馈已处理完成",
            content=f"您的反馈已被审核员处理，处理措施：{review.action_taken}",
            type="feedback_resolved"
        )
        db.add(notification)
    
    elif review.status == "escalated":
        # 通知教师或管理员
        target_roles = ["teacher", "admin"] if review.escalated_to == "teacher" else ["admin"]
        
        targets = db.query(User).filter(
            User.role.in_(target_roles),
            User.is_active == True
        ).all()
        
        for target in targets:
            notification = Notification(
                user_id=target.id,
                feedback_id=feedback.id,
                title="反馈需要升级处理",
                content=f"审核员已将用户 {user.username} 的反馈升级处理，请及时处理。",
                type="feedback_review",
                is_urgent=True
            )
            db.add(notification)
    
    db.commit()
