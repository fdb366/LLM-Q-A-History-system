# backend/app/api/endpoints/qa.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Any
import time

from app.models.sql.conversation import Conversation
from app.models.sql.message import Message
from app.core.sync_database import SessionLocal
import json
import uuid
from app.services.llm_service import LLMService
from app.services.retrieval_service import RetrievalService
from app.api.dependencies.auth import get_current_user
from app.models.sql.user import User

router = APIRouter()

class QuestionRequest(BaseModel):
    question: str
    use_context: bool = False
    user_id: Optional[str] = None   # 不再需要前端传，从 token 获取
    conversation_id: Optional[int] = None  # 如果提供，则添加到该对话；否则新建对话

class QuestionResponse(BaseModel):
    answer: str
    sources: List[Any] = []
    processing_time: float
    conversation_id: Optional[int] = None

llm_service = LLMService()
retrieval_service = RetrievalService()

@router.post("/ask", response_model=QuestionResponse)
async def ask_question(
    request: QuestionRequest,
    current_user: User = Depends(get_current_user)
):
    print(f"用户 {current_user.username} 提问: {request.question}")
    start = time.time()
    db = SessionLocal()  # 创建数据库会话
    try:
        # 处理对话ID
        conv = None
        if request.conversation_id:
            conv = db.query(Conversation).filter(
                Conversation.id == request.conversation_id,
                Conversation.user_id == current_user.id
            ).first()
            if not conv:
                raise HTTPException(status_code=404, detail="对话不存在")
        else:
            # 创建新对话
            session_id = str(uuid.uuid4())
            conv = Conversation(
                user_id=current_user.id,
                title=request.question[:30] + "...",  # 用问题前30字作为标题
                session_id=session_id
            )
            db.add(conv)
            db.commit()
            db.refresh(conv)

        # 检索上下文（如果有）
        context = ""
        sources = []
        if request.use_context:
            retrieved = retrieval_service.retrieve(request.question, top_k=3)
            if retrieved:
                context = "\n\n".join([doc["content"] for doc in retrieved])
                sources = retrieved  # 注意：retrieved 中可能包含不可 JSON 序列化的对象，需要处理

        # 构造提示词
        messages = []
        if context:
            prompt = f"""请根据以下历史资料回答问题。
资料：
{context}

问题：{request.question}

回答："""
        else:
            prompt = request.question
        messages.append({"role": "user", "content": prompt})

        # 调用 LLM
        answer = await llm_service.generate(messages)
        elapsed = time.time() - start

        # 保存用户消息
        user_msg = Message(
            conversation_id=conv.id,
            role="user",
            content=request.question
        )
        db.add(user_msg)

        # 保存助手消息（包含来源）
        assistant_msg = Message(
            conversation_id=conv.id,
            role="assistant",
            content=answer,
            processing_time=elapsed,
            source_documents=sources  # 注意：需要确保 sources 可 JSON 序列化
        )
        db.add(assistant_msg)

        # 更新对话的 last_message 和 message_count
        conv.last_message = answer[:100]  # 截取前100字符
        conv.message_count += 2  # 用户+助手两条
        db.commit()

        return QuestionResponse(answer=answer, sources=sources, processing_time=elapsed, conversation_id=conv.id)
    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"服务内部错误: {str(e)}")
    finally:
        db.close()