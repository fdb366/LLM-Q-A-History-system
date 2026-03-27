# scripts/process_all_pdfs.py
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import json
import pdfplumber
import re
from langchain.text_splitter import RecursiveCharacterTextSplitter
from backend.app.core.sync_database import SessionLocal
from backend.app.models.sql.knowledge import KnowledgeDocument, KnowledgeChunk

class PDFTextProcessor:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.text = ""

    def extract_text(self) -> str:
        """使用 pdfplumber 提取文本"""
        with pdfplumber.open(self.pdf_path) as pdf:
            pages_text = []
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pages_text.append(text)
        self.text = "\n".join(pages_text)
        return self.text

    def clean_text(self) -> str:
        """清洗文本"""
        # 去除页码（常见的“第X页”）
        self.text = re.sub(r'第\s*[0-9一二三四五六七八九十]+\s*页', '', self.text)
        # 去除多余空白
        self.text = re.sub(r'\s+', ' ', self.text)
        # 去除特殊符号（保留中文、英文、数字、常用标点）
        self.text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9，。！？；：、（）《》【】"\'“”]', '', self.text)
        return self.text

    def chunk_text(self, chunk_size=500, overlap=50) -> list:
        """分块"""
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap,
            separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""]
        )
        chunks = splitter.split_text(self.text)
        return chunks

    def process(self) -> list:
        """完整处理流程"""
        self.extract_text()
        self.clean_text()
        chunks = self.chunk_text()
        chunks_meta = []
        for idx, chunk in enumerate(chunks):
            chunks_meta.append({
                "chunk_index": idx,
                "text": chunk,
                "metadata": {
                    "source": Path(self.pdf_path).stem,
                    "file_path": self.pdf_path,
                    "char_count": len(chunk)
                }
            })
        return chunks_meta

def process_all_pdfs():
    db = SessionLocal()
    # 查询所有状态为 pending 的文档
    docs = db.query(KnowledgeDocument).filter(KnowledgeDocument.status == "pending").all()
    if not docs:
        print("没有待处理的 PDF 文档。")
        return

    for doc in docs:
        print(f"处理文档: {doc.title} (ID: {doc.id})")
        try:
            doc.status = "processing"
            db.commit()

            processor = PDFTextProcessor(doc.file_path)
            chunks = processor.process()

            for chunk in chunks:
                db_chunk = KnowledgeChunk(
                    document_id=doc.id,
                    chunk_index=chunk["chunk_index"],
                    content=chunk["text"],
                    content_length=chunk["metadata"]["char_count"],
                    meta_data=chunk["metadata"]   # 注意字段名改为 meta_data
                )
                db.add(db_chunk)

            doc.status = "completed"
            doc.chunk_count = len(chunks)
            db.commit()
            print(f"✅ 完成: {doc.title}, 分块数: {len(chunks)}")

            # 可选：保存 JSON 备份
            output_dir = Path("./data/processed_texts")
            output_dir.mkdir(parents=True, exist_ok=True)
            output_file = output_dir / f"{doc.title}_chunks.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(chunks, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"❌ 处理失败 {doc.title}: {e}")
            doc.status = "failed"
            db.commit()

    db.close()
    print("所有文档处理完成。")

if __name__ == "__main__":
    process_all_pdfs()