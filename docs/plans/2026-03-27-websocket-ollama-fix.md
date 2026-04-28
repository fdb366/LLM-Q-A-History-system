# WebSocket Ollama 流式调用修复实现计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 修复 WebSocket 连接问题，使 Ollama 流式调用不阻塞 FastAPI 事件循环

**Architecture:** 将同步的 ollama.chat() 调用放到线程池中执行，使用 asyncio.to_thread 包装同步生成器，确保 WebSocket 连接不会被阻塞

**Tech Stack:** FastAPI, WebSocket, Ollama Python SDK, asyncio

---

## 问题分析

### 当前问题

1. **llm_service.py**: `stream_generate` 是 async 函数，但内部调用的是同步的 `ollama.chat()`，会阻塞事件循环
2. **ws_chat.py**: 使用普通 `for` 循环迭代 async 生成器，语法错误
3. **阻塞影响**: 当 Ollama 处理请求时，整个 FastAPI 事件循环被阻塞，导致 WebSocket 无法处理其他消息

### 解决方案

将同步的 Ollama 调用放到线程池中执行，使用 `asyncio.to_thread` 或 `run_in_executor` 包装。

---

## Task 1: 修复 LLMService 流式生成方法

**Files:**
- Modify: `d:\桌面\LLM_project\backend\app\services\llm_service.py`

**Step 1: 重写 stream_generate 方法为同步生成器**

将 async 生成器改为普通生成器，因为 ollama.chat() 本身是同步的：

```python
import traceback
from ollama import chat
from typing import List, Dict, Any, Generator

class LLMService:
    def __init__(self, model_name: str = "deepseek-r1:7b", base_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.base_url = base_url

    def generate(self, messages: List[Dict[str, Any]]) -> str:
        """非流式生成"""
        try:
            response = chat(
                model=self.model_name,
                messages=messages,
                stream=False
            )
            return response['message']['content']
        except Exception as e:
            print("Ollama 调用失败:")
            traceback.print_exc()
            raise

    def stream_generate(self, messages: List[Dict[str, Any]]) -> Generator[str, None, None]:
        """流式生成 - 同步生成器"""
        try:
            for chunk in chat(
                model=self.model_name,
                messages=messages,
                stream=True
            ):
                if 'message' in chunk and 'content' in chunk['message']:
                    yield chunk['message']['content']
        except Exception as e:
            print("Ollama 流式调用失败:")
            traceback.print_exc()
            raise
```

**Step 2: 验证文件语法正确**

运行: `python -m py_compile backend/app/services/llm_service.py`
预期: 无错误输出

---

## Task 2: 修复 WebSocket 处理中的流式调用

**Files:**
- Modify: `d:\桌面\LLM_project\backend\app\api\endpoints\ws_chat.py`

**Step 1: 修改流式调用部分，使用 asyncio.to_thread 包装同步生成器**

找到第 177-200 行的流式调用代码，修改为：

```python
                # 流式请求 Ollama
                full_answer = ""
                stream_success = False
                
                try:
                    # 定义同步生成器消费函数
                    def consume_stream():
                        chunks = []
                        for chunk in llm_service.stream_generate(messages):
                            if chunk:
                                chunks.append(chunk)
                        return chunks
                    
                    # 在线程池中运行同步生成器
                    chunks = await asyncio.to_thread(consume_stream)
                    
                    # 逐个发送 chunks
                    for chunk in chunks:
                        full_answer += chunk
                        await websocket.send_json({"chunk": chunk, "done": False})
                        stream_success = True
                        
                except Exception as e:
                    print(f"Ollama流式请求失败: {e}")
                    # 如果流式失败，尝试非流式请求作为降级方案
                    try:
                        content = await asyncio.to_thread(llm_service.generate, messages)
                        full_answer = content
                        # 一次性发送完整内容
                        await websocket.send_json({"chunk": content, "done": False})
                        stream_success = True
                    except Exception as fallback_error:
                        print(f"Ollama非流式请求也失败: {fallback_error}")
                        await websocket.send_json({"error": "大模型服务暂时不可用，请稍后重试"})
                        return
```

**Step 2: 验证文件语法正确**

运行: `python -m py_compile backend/app/api/endpoints/ws_chat.py`
预期: 无错误输出

---

## Task 3: 实现真正的实时流式传输（可选优化）

**Files:**
- Modify: `d:\桌面\LLM_project\backend\app\services\llm_service.py`
- Modify: `d:\桌面\LLM_project\backend\app\api\endpoints\ws_chat.py`

**Step 1: 创建异步流式生成器包装器**

在 llm_service.py 中添加：

```python
    async def async_stream_generate(self, messages: List[Dict[str, Any]]) -> AsyncGenerator[str, None]:
        """异步流式生成 - 使用队列实现实时流式"""
        import asyncio
        from queue import Queue
        
        queue: Queue = Queue()
        sentinel = object()
        
        def sync_producer():
            try:
                for chunk in chat(
                    model=self.model_name,
                    messages=messages,
                    stream=True
                ):
                    if 'message' in chunk and 'content' in chunk['message']:
                        queue.put(chunk['message']['content'])
            except Exception as e:
                queue.put(('error', str(e)))
            finally:
                queue.put(sentinel)
        
        # 在线程池中启动生产者
        loop = asyncio.get_event_loop()
        producer_task = loop.run_in_executor(None, sync_producer)
        
        try:
            while True:
                # 使用 run_in_executor 从队列获取数据
                item = await loop.run_in_executor(None, queue.get)
                
                if item is sentinel:
                    break
                    
                if isinstance(item, tuple) and item[0] == 'error':
                    raise Exception(item[1])
                    
                yield item
        finally:
            # 确保生产者任务完成
            await producer_task
```

**Step 2: 在 ws_chat.py 中使用异步流式生成器**

修改流式调用部分：

```python
                # 流式请求 Ollama - 实时流式
                full_answer = ""
                stream_success = False
                
                try:
                    async for chunk in llm_service.async_stream_generate(messages):
                        if chunk:
                            full_answer += chunk
                            await websocket.send_json({"chunk": chunk, "done": False})
                            stream_success = True
                            
                except Exception as e:
                    print(f"Ollama流式请求失败: {e}")
                    try:
                        content = await asyncio.to_thread(llm_service.generate, messages)
                        full_answer = content
                        await websocket.send_json({"chunk": content, "done": False})
                        stream_success = True
                    except Exception as fallback_error:
                        print(f"Ollama非流式请求也失败: {fallback_error}")
                        await websocket.send_json({"error": "大模型服务暂时不可用，请稍后重试"})
                        return
```

---

## Task 4: 测试验证

**Step 1: 启动后端服务**

运行: `cd backend && python -m app.main`
预期: 服务正常启动，监听 8000 端口

**Step 2: 启动前端服务**

运行: `cd frontend && npm run dev`
预期: 前端服务正常启动

**Step 3: 测试 WebSocket 连接**

1. 打开浏览器开发者工具
2. 登录系统
3. 发送一条消息
4. 观察控制台输出：
   - "WebSocket connected, sending auth..."
   - "WebSocket authenticated"
   - 流式消息正常显示

**Step 4: 验证流式输出**

- 消息应该逐字/逐块显示
- 不应该出现长时间阻塞
- WebSocket 连接状态应该保持稳定

---

## Task 5: 提交代码

**Step 1: 检查修改的文件**

运行: `git status`
预期: 显示修改的文件列表

**Step 2: 提交更改**

```bash
git add backend/app/services/llm_service.py backend/app/api/endpoints/ws_chat.py
git commit -m "fix: 修复 WebSocket 流式调用阻塞事件循环问题

- 将同步的 ollama.chat() 调用放到线程池中执行
- 使用 asyncio.to_thread 包装同步生成器
- 实现基于队列的异步流式传输
- 确保 WebSocket 连接不会被 Ollama 调用阻塞"
```

---

## 实施清单

1. 修改 `llm_service.py` 中的 `stream_generate` 方法为同步生成器
2. 修改 `ws_chat.py` 中的流式调用，使用 `asyncio.to_thread` 包装
3. （可选）实现基于队列的异步流式生成器 `async_stream_generate`
4. 启动后端服务验证
5. 启动前端服务验证
6. 测试 WebSocket 连接和流式输出
7. 提交代码
