# backend/app/api/router.py
# 导入所有模型以确保 SQLAlchemy 关系正确解析
from app.models.sql import User, Conversation, Message, File, KnowledgeDocument, KnowledgeChunk, CloudFile

from fastapi import APIRouter
from app.api.endpoints import qa, auth, admin, chat, files, cloud_files, feedback, mistake

router = APIRouter()

router.include_router(qa.router, prefix="/v1", tags=["问答"])
router.include_router(auth.router, prefix="/auth", tags=["认证"])
router.include_router(admin.router, prefix="/admin", tags=["管理员"])
router.include_router(chat.router, prefix="/chat", tags=["对话"])
router.include_router(files.router, prefix="/files", tags=["文件"])
router.include_router(cloud_files.router, prefix="/cloud-files", tags=["云盘"])
router.include_router(feedback.router, prefix="/feedbacks", tags=["反馈"])
router.include_router(mistake.router, prefix="/mistakes", tags=["错题本"])