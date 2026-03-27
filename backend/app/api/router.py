# backend/app/api/router.py
from fastapi import APIRouter
from app.api.endpoints import qa, auth, admin, chat

router = APIRouter()

router.include_router(qa.router, prefix="/v1", tags=["问答"])
router.include_router(auth.router, prefix="/auth", tags=["认证"])
router.include_router(admin.router, prefix="/admin", tags=["管理员"])
router.include_router(chat.router, prefix="/chat", tags=["对话"])