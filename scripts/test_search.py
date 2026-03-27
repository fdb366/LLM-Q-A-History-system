# scripts/test_search.py
import chromadb
from sentence_transformers import SentenceTransformer

CHROMA_PATH = "./data/chroma_db"
COLLECTION_NAME = "history_knowledge"
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"

client = chromadb.PersistentClient(path=CHROMA_PATH)
collection = client.get_collection(COLLECTION_NAME)
model = SentenceTransformer(MODEL_NAME)

def search(query, top_k=3):
    query_emb = model.encode([query]).tolist()
    results = collection.query(query_embeddings=query_emb, n_results=top_k)
    for i, (doc, meta, dist) in enumerate(zip(results['documents'][0], results['metadatas'][0], results['distances'][0])):
        print(f"\n结果 {i+1} (相似度: {1-dist:.3f}):")
        print(f"来源文档ID: {meta['document_id']}")
        print(f"内容: {doc[:150]}...")

if __name__ == "__main__":
    while True:
        q = input("\n请输入查询（输入 exit 退出）: ")
        if q.lower() == 'exit':
            break
        search(q)