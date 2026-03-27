from typing import List, Dict, Any

class RAGService:
    """检索增强生成服务（预留，当前未实现）"""
    
    async def retrieve(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        根据查询检索相关文档片段
        返回值示例：[{"content": "...", "score": 0.95, "metadata": {...}}]
        """
        # TODO: 将来接入 ChromaDB 或其他向量库
        return []