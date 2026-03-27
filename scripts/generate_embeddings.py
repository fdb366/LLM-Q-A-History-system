# scripts/generate_embeddings.py
# 运行该脚本前，请先确保：
# 1. 数据库已初始化并包含所有文档
# 2. 已运行 process_all_pdfs.py 进行分块
# 3. 已安装所有依赖（requirements.txt）
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import requests
import json
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
from backend.app.core.sync_database import SessionLocal
from backend.app.models.sql.knowledge import KnowledgeChunk

# 配置
CHROMA_PATH = "./data/chroma_db"
COLLECTION_NAME = "history_knowledge"
BATCH_SIZE = 100  # 每批处理的文本块数
# MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"  # 多语言模型，适合中文

def get_embeddings(texts, model):
    """使用 sentence-transformers 模型生成向量"""
    return model.encode(texts, show_progress_bar=False).tolist()
    
def main():
    print("初始化向量模型...")
    model = SentenceTransformer('./models/all-MiniLM-L6-v2')
    print("模型加载完成，向量维度:", model.get_sentence_embedding_dimension())

    # 连接 ChromaDB
    print("连接 ChromaDB...")
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    # 如果集合已存在，先删除（可选，根据需求决定）
    try:
        client.delete_collection(COLLECTION_NAME)
        print(f"已删除旧集合 {COLLECTION_NAME}")
    except:
        pass
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"description": "中小学历史知识向量库", "dimension": 384}
    )

    # 从数据库读取所有已完成分块的文档
    print("从数据库读取文本块...")
    db = SessionLocal()
    chunks = db.query(KnowledgeChunk).all()
    db.close()
    print(f"共读取 {len(chunks)} 个文本块")

    if not chunks:
        print("没有文本块，请先运行 process_all_pdfs.py")
        return

    # 准备数据
    texts = [chunk.content for chunk in chunks]
    metadatas = [{
        "document_id": chunk.document_id,
        "chunk_index": chunk.chunk_index,
        "source": chunk.meta_data.get("source", "") if chunk.meta_data else "",
        "char_count": chunk.content_length
    } for chunk in chunks]
    ids = [f"chunk_{chunk.id}" for chunk in chunks]

    # 分批生成向量并存入 ChromaDB
    print("开始生成向量并存入 ChromaDB...")
    for i in tqdm(range(0, len(texts), BATCH_SIZE), desc="处理批次"):
        batch_texts = texts[i:i+BATCH_SIZE]
        batch_metadatas = metadatas[i:i+BATCH_SIZE]
        batch_ids = ids[i:i+BATCH_SIZE]

        # 生成向量
        embeddings = get_embeddings(batch_texts, model)

        # 存入 ChromaDB
        collection.add(
            embeddings=embeddings,
            documents=batch_texts,
            metadatas=batch_metadatas,
            ids=batch_ids
        )

    print(f"向量化完成！共存入 {collection.count()} 个向量到集合 '{COLLECTION_NAME}'")
    print(f"ChromaDB 数据保存在: {CHROMA_PATH}")

if __name__ == "__main__":
    main()