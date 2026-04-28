import traceback
from ollama import chat
from typing import List, Dict, Any, Generator, AsyncGenerator
import asyncio
from queue import Queue


class LLMService:
    def __init__(self, model_name: str = "deepseek-r1:7b", base_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.base_url = base_url

    def generate(self, messages: List[Dict[str, Any]]) -> str:
        """非流式生成 - 同步方法"""
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

    async def async_stream_generate(self, messages: List[Dict[str, Any]]) -> AsyncGenerator[str, None]:
        """异步流式生成 - 使用队列实现实时流式"""
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

        loop = asyncio.get_event_loop()
        producer_task = loop.run_in_executor(None, sync_producer)

        try:
            while True:
                item = await loop.run_in_executor(None, queue.get)

                if item is sentinel:
                    break

                if isinstance(item, tuple) and item[0] == 'error':
                    raise Exception(item[1])

                yield item
        finally:
            await producer_task
