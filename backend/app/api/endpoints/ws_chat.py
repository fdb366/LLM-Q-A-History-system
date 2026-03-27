# backend/app/api/endpoints/ws_chat.py
import asyncio
import json
import uuid
import time
import traceback
from fastapi import WebSocket, WebSocketDisconnect
from jose import jwt, JWTError
from app.core.config import settings
from app.core.sync_database import SessionLocal
from app.models.sql.user import User
from app.models.sql.conversation import Conversation
from app.models.sql.message import Message
from app.services.llm_service import LLMService

MODEL_NAME = "deepseek-r1:7b"
llm_service = LLMService(model_name=MODEL_NAME)

# 延迟加载 RetrievalService（避免 import 时加载大模型导致启动缓慢）
_retrieval_service = None

def get_retrieval_service():
    global _retrieval_service
    if _retrieval_service is None:
        from app.services.retrieval_service import RetrievalService
        _retrieval_service = RetrievalService()
    return _retrieval_service


async def websocket_chat(websocket: WebSocket):
    print("WebSocket received connection, accepting...")
    await websocket.accept()
    print("WebSocket accepted")
    try:
        # 等待认证消息（必须是第一条消息）
        data = await websocket.receive_text()
        print(f"WebSocket received auth message (len={len(data)})")
        auth_data = json.loads(data)
        if auth_data.get("type") != "auth":
            await websocket.send_json({"type": "auth_failed", "reason": "Authentication required"})
            await websocket.close(code=1008)
            return

        token = auth_data.get("token")
        if not token:
            print("WebSocket auth failed: missing token")
            await websocket.send_json({"type": "auth_failed", "reason": "Missing token"})
            await websocket.close(code=1008)
            return

        # 验证 JWT token
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            sub = payload.get("sub")
            print(f"WebSocket JWT decoded, sub={sub}")
            user_id = int(sub)
            db = SessionLocal()
            user = db.query(User).filter(User.id == user_id).first()
            db.close()
            if not user:
                print(f"WebSocket auth failed: user {user_id} not found")
                await websocket.send_json({"type": "auth_failed", "reason": "Invalid user"})
                await websocket.close(code=1008)
                return
            print(f"WebSocket auth success: user={user.username}")
        except JWTError as e:
            print(f"WebSocket JWT error: {e}")
            await websocket.send_json({"type": "auth_failed", "reason": f"Invalid token: {str(e)}"})
            await websocket.close(code=1008)
            return
        except Exception as e:
            print(f"WebSocket auth error: {e}")
            traceback.print_exc()
            await websocket.send_json({"type": "auth_failed", "reason": str(e)})
            await websocket.close(code=1008)
            return

        # 认证成功
        await websocket.send_json({"type": "auth_success"})
        print("WebSocket auth_success sent, entering message loop")

        # 进入正常消息循环
        while True:
            data = await websocket.receive_text()
            request_data = json.loads(data)
            question = request_data.get("question", "")
            use_context = request_data.get("use_context", True)
            conversation_id = request_data.get("conversation_id")

            if not question.strip():
                continue

            start_time = time.time()

            # 处理会话：有则用，无则创建
            db = SessionLocal()
            try:
                conv = None
                if conversation_id:
                    conv = db.query(Conversation).filter(
                        Conversation.id == conversation_id,
                        Conversation.user_id == user_id
                    ).first()

                if not conv:
                    conv = Conversation(
                        user_id=user_id,
                        title=question[:30] + "...",
                        session_id=str(uuid.uuid4())
                    )
                    db.add(conv)
                    db.commit()
                    db.refresh(conv)

                # 将 conversation_id 发给前端
                await websocket.send_json({"type": "conversation_id", "conversation_id": conv.id})

                # 检索 RAG 上下文（同步操作放到线程池）
                context = ""
                sources = []
                if use_context:
                    try:
                        retrieval_svc = get_retrieval_service()
                        retrieved = await asyncio.to_thread(
                            retrieval_svc.retrieve, question, 3
                        )
                        if retrieved:
                            context = "\n\n".join([doc["content"] for doc in retrieved])
                            sources = [
                                {"content": doc["content"], "metadata": doc["metadata"], "score": doc["score"]}
                                for doc in retrieved
                            ]
                    except Exception as e:
                        print(f"RAG retrieval error: {e}")

                # 构造消息列表
                messages = []
                if context:
                    prompt = f"""请根据以下历史资料回答问题，并按照以下格式输出：

资料：
{context}

问题：{question}

请先生成思考过程（用<think>标签包裹），然后给出最终回答。

格式示例：
<think>
首先，我需要分析用户的问题...
然后，我需要结合提供的资料...
最后，我需要总结答案...
</think>

最终回答：...

现在请回答："""
                else:
                    prompt = f"""请回答问题，并按照以下格式输出：

问题：{question}

请先生成思考过程（用<think>标签包裹），然后给出最终回答。

格式示例：
<think>
首先，我需要分析用户的问题...
然后，我需要思考相关知识...
最后，我需要总结答案...
</think>

最终回答：...

现在请回答："""
                messages.append({"role": "user", "content": prompt})

                # 流式请求 Ollama
                full_answer = ""
                stream_success = False
                
                try:
                    # 使用LLM服务的流式生成方法
                    for chunk in llm_service.stream_generate(messages):
                        if chunk:
                            full_answer += chunk
                            await websocket.send_json({"chunk": chunk, "done": False})
                            stream_success = True
                except Exception as e:
                    print(f"Ollama流式请求失败: {e}")
                    # 如果流式失败，尝试非流式请求作为降级方案
                    try:
                        content = llm_service.generate(messages)
                        full_answer = content
                        # 一次性发送完整内容
                        await websocket.send_json({"chunk": content, "done": False})
                        stream_success = True
                    except Exception as fallback_error:
                        print(f"Ollama非流式请求也失败: {fallback_error}")
                        await websocket.send_json({"error": "大模型服务暂时不可用，请稍后重试"})
                        return

                elapsed = time.time() - start_time

                # 保存消息到数据库
                user_msg = Message(
                    conversation_id=conv.id,
                    role="user",
                    content=question
                )
                db.add(user_msg)

                assistant_msg = Message(
                    conversation_id=conv.id,
                    role="assistant",
                    content=full_answer,
                    processing_time=elapsed,
                    source_documents=sources if sources else None
                )
                db.add(assistant_msg)

                conv.last_message = full_answer[:100] if full_answer else question[:100]
                conv.message_count += 2
                db.commit()

                await websocket.send_json({"done": True, "sources": sources, "processing_time": elapsed})

            except Exception as e:
                db.rollback()
                print(f"Error processing question: {e}")
                traceback.print_exc()
                await websocket.send_json({"done": True, "error": str(e)})
            finally:
                db.close()

    except WebSocketDisconnect:
        print("WebSocket disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
        try:
            await websocket.send_json({"error": str(e)})
        except:
            pass
