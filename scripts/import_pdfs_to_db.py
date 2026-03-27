# scripts/import_pdfs_to_db.py
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from backend.app.core.sync_database import SessionLocal
from backend.app.models.sql.knowledge import KnowledgeDocument
from scripts.data_collector import HistoryDataCollector

def import_pdfs():
    db = SessionLocal()
    collector = HistoryDataCollector()
    pdfs = collector.scan_all_pdfs()

    for pdf in pdfs:
        existing = db.query(KnowledgeDocument).filter(
            KnowledgeDocument.content_hash == pdf["content_hash"]
        ).first()
        if existing:
            print(f"跳过已存在的文件: {pdf['name']}")
            continue

        doc = KnowledgeDocument(
            title=pdf["name"],
            source_type="textbook",
            source_name="本地教材",
            grade_level=pdf["grade"],
            file_path=pdf["file_path"],
            file_size=pdf["file_size"],
            content_hash=pdf["content_hash"],
            status="pending"
        )
        db.add(doc)
        print(f"新增文档: {pdf['name']} (年级: {pdf['grade']})")

    db.commit()
    db.close()
    print("导入完成")

if __name__ == "__main__":
    import_pdfs()