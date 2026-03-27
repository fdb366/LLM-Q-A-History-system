# backend/app/api/endpoints/admin.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.sync_database import SessionLocal
from app.models.sql.user import User
from app.api.dependencies.auth import require_roles

router = APIRouter()

@router.get("/users")
def list_users(
    current_user: User = Depends(require_roles(["admin"]))  # 仅管理员可访问
):
    """获取所有用户列表（管理员专用）"""
    db = SessionLocal()
    users = db.query(User).all()
    db.close()
    # 避免返回密码哈希等敏感字段，可自定义返回模型
    return users