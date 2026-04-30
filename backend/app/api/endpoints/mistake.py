# backend/app/api/endpoints/mistake.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
from app.core.database import SessionLocal
from app.models.sql.mistake import Mistake, KnowledgeTag, ReviewSchedule
from app.api.dependencies.auth import get_current_user
from app.models.sql.user import User

router = APIRouter()


class MistakeCreate(BaseModel):
    question: str
    correct_answer: Optional[str] = None
    user_answer: Optional[str] = None
    knowledge_tag: Optional[str] = None


class MistakeResponse(BaseModel):
    id: int
    question: str
    correct_answer: Optional[str]
    user_answer: Optional[str]
    knowledge_tag: Optional[str]
    is_weak_point: bool
    review_count: int
    last_review_at: Optional[str]
    next_review_at: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/mistakes", response_model=MistakeResponse)
def create_mistake(
    mistake: MistakeCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """记录错题"""
    if not current_user.is_approved:
        raise HTTPException(status_code=403, detail="Account not approved")

    db_mistake = Mistake(
        user_id=current_user.id,
        question=mistake.question,
        correct_answer=mistake.correct_answer,
        user_answer=mistake.user_answer,
        knowledge_tag=mistake.knowledge_tag,
        next_review_at=datetime.now() + timedelta(days=1)  # 1天后复习
    )
    db.add(db_mistake)
    db.commit()
    db.refresh(db_mistake)

    # 创建复习计划
    schedule = ReviewSchedule(
        user_id=current_user.id,
        mistake_id=db_mistake.id,
        scheduled_date=datetime.now() + timedelta(days=1)
    )
    db.add(schedule)
    db.commit()

    return db_mistake


@router.get("/mistakes", response_model=List[MistakeResponse])
def get_mistakes(
    knowledge_tag: Optional[str] = None,
    is_weak_point: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取错题列表"""
    if not current_user.is_approved:
        raise HTTPException(status_code=403, detail="Account not approved")

    query = db.query(Mistake).filter(Mistake.user_id == current_user.id)

    if knowledge_tag:
        query = query.filter(Mistake.knowledge_tag == knowledge_tag)
    if is_weak_point is not None:
        query = query.filter(Mistake.is_weak_point == is_weak_point)

    mistakes = query.order_by(Mistake.created_at.desc()).all()
    return mistakes


@router.get("/mistakes/weak-points")
def get_weak_points(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取薄弱点分析"""
    if not current_user.is_approved:
        raise HTTPException(status_code=403, detail="Account not approved")

    # 按知识点标签统计错题数量
    weak_points = db.query(
        Mistake.knowledge_tag,
        func.count(Mistake.id).label("mistake_count")
    ).filter(
        Mistake.user_id == current_user.id,
        Mistake.is_weak_point == True
    ).group_by(Mistake.knowledge_tag).all()

    result = []
    for wp in weak_points:
        result.append({
            "knowledge_tag": wp.knowledge_tag or "未分类",
            "mistake_count": wp.mistake_count
        })

    return result


@router.get("/mistakes/review")
def get_review_list(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取今日复习列表"""
    if not current_user.is_approved:
        raise HTTPException(status_code=403, detail="Account not approved")

    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)

    schedules = db.query(ReviewSchedule).filter(
        ReviewSchedule.user_id == current_user.id,
        ReviewSchedule.scheduled_date >= today,
        ReviewSchedule.scheduled_date < tomorrow,
        ReviewSchedule.is_completed == False
    ).all()

    result = []
    for schedule in schedules:
        mistake = db.query(Mistake).filter(Mistake.id == schedule.mistake_id).first()
        if mistake:
            result.append({
                "schedule_id": schedule.id,
                "mistake_id": mistake.id,
                "question": mistake.question,
                "correct_answer": mistake.correct_answer,
                "knowledge_tag": mistake.knowledge_tag,
                "review_count": mistake.review_count
            })

    return result


@router.post("/mistakes/{mistake_id}/review")
def review_mistake(
    mistake_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """完成复习"""
    if not current_user.is_approved:
        raise HTTPException(status_code=403, detail="Account not approved")

    mistake = db.query(Mistake).filter(
        Mistake.id == mistake_id,
        Mistake.user_id == current_user.id
    ).first()

    if not mistake:
        raise HTTPException(status_code=404, detail="Mistake not found")

    # 更新复习次数和时间
    mistake.review_count += 1
    mistake.last_review_at = datetime.now()

    # 根据复习次数设置下次复习时间（间隔重复算法）
    intervals = [1, 3, 7, 14, 30]  # 1天、3天、7天、14天、30天
    next_interval = intervals[min(mistake.review_count - 1, len(intervals) - 1)]
    mistake.next_review_at = datetime.now() + timedelta(days=next_interval)

    # 标记当前复习计划为完成
    schedule = db.query(ReviewSchedule).filter(
        ReviewSchedule.mistake_id == mistake_id,
        ReviewSchedule.user_id == current_user.id,
        ReviewSchedule.is_completed == False
    ).first()

    if schedule:
        schedule.is_completed = True
        schedule.completed_at = datetime.now()

    # 创建新的复习计划
    new_schedule = ReviewSchedule(
        user_id=current_user.id,
        mistake_id=mistake_id,
        scheduled_date=mistake.next_review_at
    )
    db.add(new_schedule)

    db.commit()

    return {"msg": "Review completed", "next_review": mistake.next_review_at}


@router.put("/mistakes/{mistake_id}/weak-point")
def toggle_weak_point(
    mistake_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """切换薄弱点标记"""
    if not current_user.is_approved:
        raise HTTPException(status_code=403, detail="Account not approved")

    mistake = db.query(Mistake).filter(
        Mistake.id == mistake_id,
        Mistake.user_id == current_user.id
    ).first()

    if not mistake:
        raise HTTPException(status_code=404, detail="Mistake not found")

    mistake.is_weak_point = not mistake.is_weak_point
    db.commit()

    return {"is_weak_point": mistake.is_weak_point}


@router.delete("/mistakes/{mistake_id}")
def delete_mistake(
    mistake_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除错题"""
    if not current_user.is_approved:
        raise HTTPException(status_code=403, detail="Account not approved")

    mistake = db.query(Mistake).filter(
        Mistake.id == mistake_id,
        Mistake.user_id == current_user.id
    ).first()

    if not mistake:
        raise HTTPException(status_code=404, detail="Mistake not found")

    db.delete(mistake)
    db.commit()

    return {"msg": "Mistake deleted"}
