import logging
from contextlib import asynccontextmanager

from app.api.endpoints.ws_chat import websocket_chat

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.api.router import router
from app.core.config import settings
# 配置日志（临时替代 setup_logger）
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 如果你未来需要同步创建数据库表，可以在此导入同步引擎
# from app.core.sync_database import engine
# from app.models.sql.knowledge import Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("Starting up...")

    # 如果需要自动创建表（使用同步引擎），可以在这里执行
    # 但当前表已存在，可以注释掉
    # Base.metadata.create_all(bind=engine)

    yield
    logger.info("Shutting down...")

# 创建 FastAPI 应用
app = FastAPI(
    title="中小学历史知识智能问答系统",
    description="基于大模型的RAG问答系统",
    version="1.0.0",
    lifespan=lifespan,
    redirect_slashes=False  # 禁用尾部斜杠重定向，避免 CORS 问题
)

# CORS 配置（允许前端本地开发）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_api_websocket_route("/ws/chat", websocket_chat)
# 注册路由
app.include_router(router, prefix="/api")

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)