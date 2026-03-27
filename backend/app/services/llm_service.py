import traceback
from ollama import chat
from typing import List, Dict, Any, AsyncGenerator

class LLMService:
    def __init__(self, model_name: str = "deepseek-r1:7b", base_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.base_url = base_url

    async def generate(self, messages: List[Dict[str, Any]]) -> str:
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

    async def stream_generate(self, messages: List[Dict[str, Any]]) -> AsyncGenerator[str, None]:
        """流式生成"""
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