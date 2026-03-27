"""
ChromaDB向量库配置
"""
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings

class ChromaConfig:
    """ChromaDB配置类"""
    
    # 向量库名称
    COLLECTION_NAME = "history_knowledge"
    
    # 向量维度（根据嵌入模型调整）
    EMBEDDING_DIMENSION = 384  # 百度文心embedding-v1的维度
    
    # 距离度量方法
    DISTANCE_METRIC = "cosine"  # 可选: "l2", "ip", "cosine"
    
    # 元数据字段定义
    METADATA_FIELDS = {
        "document_id": str,      # 文档ID
        "chunk_index": int,      # 分块索引
        "source_type": str,      # 来源类型: textbook, reference_book等
        "source_name": str,      # 来源名称
        "grade_level": str,      # 年级层次
        "subject_area": str,     # 学科领域
        "title": str,            # 文档标题
        "page_number": int,      # 页码（如果适用）
        "keywords": List[str],   # 关键词
        "timestamp": str,        # 时间戳
    }
    
    @classmethod
    def get_chroma_settings(cls, persist_directory: str = "./chroma_db") -> Settings:
        """获取ChromaDB设置"""
        return Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory=persist_directory,
            anonymized_telemetry=False  # 禁用遥测
        )
    
    @classmethod
    def get_collection_config(cls) -> Dict[str, Any]:
        """获取集合配置"""
        return {
            "name": cls.COLLECTION_NAME,
            "metadata": {
                "hnsw:space": cls.DISTANCE_METRIC,
                "description": "中小学历史知识向量库"
            }
        }

# 嵌入模型配置
class EmbeddingConfig:
    """嵌入模型配置"""
    
    # 本地嵌入模型（备选）
    LOCAL_MODELS = {
        "paraphrase-multilingual-MiniLM-L12-v2": {
            "dimension": 384,
            "language": "multilingual",
            "description": "多语言句子嵌入模型"
        },
        "text2vec-base-chinese": {
            "dimension": 768,
            "language": "chinese",
            "description": "中文文本嵌入模型"
        }
    }
    
    # 云端嵌入模型
    CLOUD_MODELS = {
        "baidu": {
            "model_name": "embedding-v1",
            "dimension": 384,
            "max_tokens": 384,
            "endpoint": "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/embeddings/embedding-v1"
        },
        "ali": {
            "model_name": "text-embedding-v1",
            "dimension": 1536,
            "max_tokens": 2048,
            "endpoint": "https://dashscope.aliyuncs.com/api/v1/services/embeddings/text-embedding/text-embedding"
        }
    }