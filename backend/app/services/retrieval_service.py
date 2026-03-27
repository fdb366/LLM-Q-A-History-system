# backend/app/services/retrieval_service.py
import chromadb
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any

CHROMA_PATH = "../data/chroma_db"
COLLECTION_NAME = "history_knowledge"
EMBEDDING_MODEL_PATH = "../models/all-MiniLM-L6-v2"  # 你的本地模型路径

class RetrievalService:
    def __init__(self):
        # 初始化 embedding 模型（与向量化时使用相同的模型）
        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL_PATH)
        # 连接 ChromaDB
        self.client = chromadb.PersistentClient(path=CHROMA_PATH)
        self.collection = self.client.get_collection(COLLECTION_NAME)

    def retrieve(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        根据查询检索最相关的 top_k 个文本块
        返回格式：[{"content": "...", "metadata": {...}, "score": ...}]
        """
        # 生成查询向量
        query_emb = self.embedding_model.encode([query]).tolist()
        # 在 ChromaDB 中检索
        results = self.collection.query(
            query_embeddings=query_emb,
            n_results=top_k
        )
        # 整理结果
        retrieved = []
        if results['documents'] and results['documents'][0]:
            for i in range(len(results['documents'][0])):
                retrieved.append({
                    "content": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "score": 1 - results['distances'][0][i]  # 将距离转换为相似度
                })
        return retrieved