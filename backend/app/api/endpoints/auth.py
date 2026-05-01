# backend/app/api/endpoints/auth.py
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Optional
from app.core.sync_database import SessionLocal, get_db
from app.models.sql.user import User
from app.core.security import get_password_hash, verify_password, create_access_token
from app.core.config import settings
from app.api.dependencies.auth import get_current_user  # 稍后实现

router = APIRouter()

# 请求/响应模型
class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UserOut(BaseModel):
    id: int
    username: str
    email: str
    role: str
    avatar_url: Optional[str] = None
    is_approved: bool = True
    permissions: list = []

@router.post("/register", response_model=dict)
def register(user_data: UserRegister):
    """用户注册"""
    db = SessionLocal()
    # 检查用户名/邮箱是否已存在
    if db.query(User).filter(User.username == user_data.username).first():
        db.close()
        raise HTTPException(status_code=400, detail="Username already registered")
    if db.query(User).filter(User.email == user_data.email).first():
        db.close()
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed = get_password_hash(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hashed
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    db.close()
    return {"msg": "User created successfully"}

@router.post("/login", response_model=Token)
def login(user_data: UserLogin):
    """用户登录，返回 JWT token"""
    db = SessionLocal()
    user = db.query(User).filter(User.username == user_data.username).first()
    if not user or not verify_password(user_data.password, user.password_hash):
        db.close()
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    db.close()
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserOut)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """获取当前登录用户信息"""
    return current_user


@router.post("/upload-avatar")
def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """上传用户头像"""
    # 这里需要实现文件上传逻辑
    # 暂时返回成功消息
    return {"msg": "头像上传成功"}


@router.post("/change-password")
def change_password(
    password_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """修改密码"""
    old_password = password_data.get("old_password")
    new_password = password_data.get("new_password")
    
    if not verify_password(old_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="原密码错误")
    
    current_user.password_hash = get_password_hash(new_password)
    db.commit()
    
    return {"msg": "密码修改成功"}


@router.get("/user-detail", response_model=UserOut)
def get_user_detail(current_user: User = Depends(get_current_user)):
    """获取用户详细信息"""
    return current_user