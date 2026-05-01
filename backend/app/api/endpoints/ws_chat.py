# backend/app/api/endpoints/ws_chat.py
import asyncio
import json
import uuid
import time
import traceback
import base64
from fastapi import WebSocket, WebSocketDisconnect
from jose import jwt, JWTError
from app.core.config import settings
from app.core.sync_database import SessionLocal
from app.models.sql.user import User
from app.models.sql.conversation import Conversation
from app.models.sql.message import Message
from app.models.sql.file import File
from app.services.llm_service import LLMService
from app.services.web_search_service import WebSearchService
from app.services.guidance_service import GuidanceService

MODEL_NAME = "deepseek-r1:7b"
llm_service = LLMService(model_name=MODEL_NAME)

# 延迟加载 RAGService（避免 import 时加载大模型导致启动缓慢）
_rag_service = None

def get_rag_service():
    global _rag_service
    if _rag_service is None:
        from app.services.rag_service import RAGService
        _rag_service = RAGService()
    return _rag_service


# 延迟加载 WebSearchService
_web_search_service = None

def get_web_search_service():
    global _web_search_service
    if _web_search_service is None:
        _web_search_service = WebSearchService(api_key=settings.TAVILY_API_KEY)
    return _web_search_service


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
            top_k = request_data.get("top_k", 3)
            conversation_id = request_data.get("conversation_id")
            file_data = request_data.get("file")  # 获取文件数据
            use_web_search = request_data.get("use_web_search", False)  # 网络搜索开关

            if not question.strip() and not file_data:
                continue

            print("=" * 80)
            print("[步骤1] 接收用户问题")
            print(f"  - 问题内容: {question[:100]}..." if len(question) > 100 else f"  - 问题内容: {question}")
            print(f"  - 使用RAG上下文: {use_context}")
            print(f"  - 使用网络搜索: {use_web_search}")
            print(f"  - Top-K: {top_k}")
            print(f"  - 会话ID: {conversation_id}")
            print(f"  - 是否有文件: {'是' if file_data else '否'}")
            if file_data:
                print(f"  - 文件名: {file_data.get('filename', 'unknown')}")
                print(f"  - 文件类型: {file_data.get('type', 'unknown')}")
            print("=" * 80)

            # 检查是否需要主动引导
            # if not file_data:
            #     guidance = GuidanceService.get_guidance(question)
            #     if guidance:
            #         print("[引导] 检测到宽泛问题，需要澄清")
            #         print(f"  - 主题: {guidance['topic']}")
            #         print(f"  - 引导问题: {guidance['guidance_question']}")

            #         # 发送引导消息
            #         await websocket.send_json({
            #             "type": "guidance",
            #             "needs_clarification": True,
            #             "guidance_question": guidance["guidance_question"],
            #             "categories": guidance["categories"],
            #             "topic": guidance["topic"]
            #         })

            #         # 保存引导消息到数据库
            #         db = SessionLocal()
            #         try:
            #             conv = None
            #             if conversation_id:
            #                 conv = db.query(Conversation).filter(
            #                     Conversation.id == conversation_id,
            #                     Conversation.user_id == user_id
            #                 ).first()

            #             if not conv:
            #                 conv = Conversation(
            #                     user_id=user_id,
            #                     title=question[:30] + "..." if question else "新对话",
            #                     session_id=str(uuid.uuid4())
            #                 )
            #                 db.add(conv)
            #                 db.commit()
            #                 db.refresh(conv)

            #             await websocket.send_json({"type": "conversation_id", "conversation_id": conv.id})

            #             # 保存用户问题
            #             user_msg = Message(
            #                 conversation_id=conv.id,
            #                 role="user",
            #                 content=question
            #             )
            #             db.add(user_msg)

            #             # 保存引导回复
            #             guidance_answer = guidance["guidance_question"]
            #             assistant_msg = Message(
            #                 conversation_id=conv.id,
            #                 role="assistant",
            #                 content=guidance_answer,
            #                 processing_time=0
            #             )
            #             db.add(assistant_msg)

            #             conv.last_message = guidance_answer[:100]
            #             conv.message_count += 2
            #             db.commit()

            #             print("[引导] 引导消息已保存到数据库")
            #         except Exception as e:
            #             db.rollback()
            #             print(f"[引导] 保存引导消息失败: {e}")
            #         finally:
            #             db.close()

            #         continue  # 跳过正常处理流程

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
                        title=question[:30] + "..." if question else "文件分析",
                        session_id=str(uuid.uuid4())
                    )
                    db.add(conv)
                    db.commit()
                    db.refresh(conv)

                # 将 conversation_id 发给前端
                await websocket.send_json({"type": "conversation_id", "conversation_id": conv.id})

                print("=" * 80)
                print("[步骤2] RAG 检索上下文")
                print(f"  - 是否启用RAG: {use_context}")
                
                # 检索 RAG 上下文（同步操作放到线程池）
                context = ""
                sources = []
                if use_context:
                    try:
                        print("  - 正在初始化检索服务...")
                        rag_svc = get_rag_service()
                        print(f"  - 正在检索问题: {question[:50]}...")
                        rag_start = time.time()
                        retrieved = await asyncio.to_thread(
                            rag_svc.retrieve, question, top_k
                        )
                        rag_elapsed = time.time() - rag_start
                        print(f"  - 检索耗时: {rag_elapsed:.2f}秒")
                        print(f"  - 检索结果数量: {len(retrieved) if retrieved else 0}")
                        
                        if retrieved:
                            context = "\n\n".join([doc["content"] for doc in retrieved])
                            print(f"  - 上下文总长度: {len(context)} 字符")
                            sources = []
                            for i, doc in enumerate(retrieved):
                                metadata = doc["metadata"] or {}
                                file_id = metadata.get("file_id")
                                page_number = metadata.get("page_number", "未知")
                                chunk_index = metadata.get("chunk_index", "未知")
                                content = doc["content"]
                                content_preview = content[:100] + "..." if len(content) > 100 else content
                                
                                # 从数据库查询文件名
                                if file_id:
                                    db_file = db.query(File).filter(File.id == file_id).first()
                                    if db_file:
                                        metadata["filename"] = db_file.original_filename
                                
                                filename = metadata.get('filename', '未知')
                                print(f"  - 结果{i+1}:")
                                print(f"      文件: {filename}")
                                print(f"      页码: 第 {page_number} 页")
                                print(f"      切片索引: {chunk_index}")
                                print(f"      相似度: {doc['score']:.4f}")
                                print(f"      内容长度: {len(content)} 字符")
                                print(f"      内容预览: {content_preview}")
                                print(f"      【完整内容】: {content}")
                                
                                sources.append({
                                    "content": doc["content"],
                                    "metadata": metadata,
                                    "score": doc["score"],
                                    "type": "knowledge"
                                })
                        else:
                            print("  - 未检索到相关内容")
                    except Exception as e:
                        print(f"  - RAG检索错误: {e}")
                        traceback.print_exc()
                else:
                    print("  - RAG已禁用，跳过检索")
                print("=" * 80)

                # ========== 网络搜索（新增） ==========
                web_context = ""
                web_sources = []

                if use_web_search and question.strip():
                    try:
                        print("=" * 80)
                        print("[步骤2b] 网络搜索")
                        print(f"  - 查询: {question[:50]}...")

                        web_svc = get_web_search_service()
                        web_start = time.time()
                        web_results = await asyncio.to_thread(
                            web_svc.search,
                            question,
                            max_results=settings.WEB_SEARCH_MAX_RESULTS,
                            search_depth=settings.WEB_SEARCH_DEPTH
                        )
                        web_elapsed = time.time() - web_start

                        if web_results:
                            web_context = web_svc.format_results_for_context(web_results)
                            web_sources = web_svc.convert_to_dict_list(web_results)
                            print(f"  - 搜索耗时: {web_elapsed:.2f}秒")
                            print(f"  - 结果数量: {len(web_results)}")
                            print(f"  - 上下文长度: {len(web_context)} 字符")
                        else:
                            print("  - 未找到相关结果")

                    except Exception as e:
                        print(f"  - 网络搜索错误: {e}")
                        traceback.print_exc()
                elif not use_web_search:
                    print("  - 网络搜索已禁用，跳过")
                print("=" * 80)

                # 处理文件数据
                file_content_for_prompt = ""
                images_for_ollama = []
                
                if file_data:
                    file_type = file_data.get("type", "")
                    file_content_base64 = file_data.get("content", "")
                    file_name = file_data.get("filename", "unknown")
                    
                    # 如果是图片类型，提取 base64 数据用于 Ollama 多模态
                    if file_type.startswith("image/"):
                        # 从 data:image/png;base64,xxx 中提取纯 base64
                        if "," in file_content_base64:
                            base64_data = file_content_base64.split(",")[1]
                            images_for_ollama.append(base64_data)
                            print(f"[WS] Image file detected for Ollama: {file_name}")
                    else:
                        # 文本文件，提取内容用于提示词
                        try:
                            # 从 base64 解码文本内容
                            if "," in file_content_base64:
                                base64_data = file_content_base64.split(",")[1]
                                decoded_content = base64.b64decode(base64_data).decode("utf-8")
                                file_content_for_prompt = decoded_content
                                print(f"[WS] Text file content extracted: {file_name}, length: {len(decoded_content)}")
                        except Exception as e:
                            print(f"[WS] Failed to decode file content: {e}")
                            file_content_for_prompt = f"[无法解析文件内容: {file_name}]"

                # 构造消息列表
                print("=" * 80)
                print("[步骤3] 构造消息")
                
                messages = []
                
                # 构造用户消息 - 支持多源上下文
                user_content = ""

                # 判断可用的上下文来源
                has_rag_context = bool(context and context.strip())
                has_web_context = bool(web_context and web_context.strip())

                if file_content_for_prompt:
                    print("  - 消息类型: 文件分析")
                    user_content = (
                        f"请根据以下文件内容回答问题：\n\n"
                        f"文件内容：\n{file_content_for_prompt[:5000]}\n\n"
                        f"问题：{question}\n\n"
                        f"请先生成思考过程，然后给出最终回答。"
                    )
                    print(f"  - 文件内容长度: {len(file_content_for_prompt[:5000])} 字符")

                elif has_rag_context and has_web_context:
                    print("  - 消息类型: 混合检索（RAG + 网络搜索）")
                    user_content = (
                        f"请根据以下多种来源的信息综合回答问题：\n\n"
                        f"【本地历史资料库】\n{context}\n\n"
                        f"【网络搜索结果】\n{web_context}\n\n"
                        f"【用户问题】\n{question}\n\n"
                        f"要求：\n"
                        f"1. 优先使用本地历史资料\n"
                        f"2. 参考网络搜索中的相关内容，忽略无关信息\n"
                        f"3. 明确标注信息来源（本地资料/网络搜索）\n\n"
                        f"请先生成思考过程，然后给出最终回答。"
                    )
                    print(f"  - 本地上下文长度: {len(context)} 字符")
                    print(f"  - 网络上下文长度: {len(web_context)} 字符")

                elif has_rag_context:
                    print("  - 消息类型: RAG上下文问答")
                    user_content = (
                        f"请根据以下历史资料回答问题：\n\n"
                        f"资料：\n{context}\n\n"
                        f"问题：{question}\n\n"
                        f"请先生成思考过程，然后给出最终回答。"
                    )
                    print(f"  - 上下文长度: {len(context)} 字符")

                elif has_web_context:
                    print("  - 消息类型: 网络搜索问答")
                    user_content = (
                        f"请根据以下网络搜索结果回答问题：\n\n"
                        f"【网络搜索结果】\n{web_context}\n\n"
                        f"【用户问题】\n{question}\n\n"
                        f"要求：\n"
                        f"1. 综合搜索结果给出回答\n"
                        f"2. 只使用与问题相关的内容，忽略无关信息\n"
                        f"3. 注明信息来源\n\n"
                        f"请先生成思考过程，然后给出最终回答。"
                    )
                    print(f"  - 网络上下文长度: {len(web_context)} 字符")

                else:
                    print("  - 消息类型: 普通问答")
                    user_content = (
                        f"请回答问题：\n\n"
                        f"问题：{question}\n\n"
                        f"请先生成思考过程，然后给出最终回答。"
                    )

                # 构造 Ollama 消息格式
                ollama_message = {"role": "user", "content": user_content}
                
                # 如果有图片，添加到消息中（Ollama 多模态格式）
                if images_for_ollama:
                    ollama_message["images"] = images_for_ollama
                    print(f"  - 包含图片数量: {len(images_for_ollama)}")
                
                messages.append(ollama_message)
                print(f"  - 消息总长度: {len(user_content)} 字符")
                print("=" * 80)

                # 流式请求 Ollama
                print("=" * 80)
                print("[步骤4] 调用 LLM 服务")
                print(f"  - 模型: {MODEL_NAME}")
                print(f"  - 流式模式: True")
                
                full_answer = ""
                stream_success = False
                chunk_count = 0
                
                try:
                    llm_start = time.time()
                    # 使用LLM服务的流式生成方法
                    for chunk in llm_service.stream_generate(messages):
                        if chunk:
                            full_answer += chunk
                            chunk_count += 1
                            await websocket.send_json({"chunk": chunk, "done": False})
                            stream_success = True
                            # 每100个chunk打印一次进度
                            if chunk_count % 100 == 0:
                                print(f"  - 已发送 {chunk_count} 个chunk, 累计长度: {len(full_answer)}")
                    
                    llm_elapsed = time.time() - llm_start
                    print(f"  - LLM响应完成:")
                    print(f"    - 总chunk数: {chunk_count}")
                    print(f"    - 总字符数: {len(full_answer)}")
                    print(f"    - 耗时: {llm_elapsed:.2f}秒")
                    print(f"    - 速度: {len(full_answer)/llm_elapsed:.1f} 字符/秒")
                except Exception as e:
                    print(f"  - LLM流式请求失败: {e}")
                    # 如果流式失败，尝试非流式请求作为降级方案
                    try:
                        print("  - 尝试非流式请求作为降级方案...")
                        content = llm_service.generate(messages)
                        full_answer = content
                        # 一次性发送完整内容
                        await websocket.send_json({"chunk": content, "done": False})
                        stream_success = True
                        print(f"  - 非流式请求成功，内容长度: {len(content)}")
                    except Exception as fallback_error:
                        print(f"  - 非流式请求也失败: {fallback_error}")
                        await websocket.send_json({"error": "大模型服务暂时不可用，请稍后重试"})
                        return
                print("=" * 80)

                elapsed = time.time() - start_time

                # 合并所有来源（RAG + 网络搜索）- 必须在保存之前
                all_sources = []
                if sources:
                    all_sources.extend(sources)
                if web_sources:
                    all_sources.extend(web_sources)

                # 保存消息到数据库
                print("=" * 80)
                print("[步骤5] 保存消息到数据库")

                display_content = question
                if file_data:
                    display_content = f"{question}\n\n[附件: {file_data.get('filename', 'unknown')}]"

                user_msg = Message(
                    conversation_id=conv.id,
                    role="user",
                    content=display_content
                )
                db.add(user_msg)

                assistant_msg = Message(
                    conversation_id=conv.id,
                    role="assistant",
                    content=full_answer,
                    processing_time=elapsed,
                    source_documents=all_sources if all_sources else None  # 修复：保存所有来源（RAG + 网络搜索）
                )
                db.add(assistant_msg)

                conv.last_message = full_answer[:100] if full_answer else question[:100]
                conv.message_count += 2
                db.commit()

                print(f"  - 用户消息已保存")
                print(f"  - 助手消息已保存 (长度: {len(full_answer)})")
                print(f"  - 来源数量: {len(all_sources) if all_sources else 0}")
                print(f"  - 会话消息数: {conv.message_count}")
                print(f"  - 总耗时: {elapsed:.2f}秒")
                print("=" * 80)

                await websocket.send_json({"done": True, "sources": all_sources, "processing_time": elapsed})

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
