# scripts/data_collector.py
import os
from pathlib import Path
from typing import List, Dict
import hashlib
# 文件路径保存为绝对路径或相对项目根目录的路径？这里保存为绝对路径，后续处理时直接使用。如果想保持可移植性，可改为相对路径，但在脚本中需基于项目根目录拼接。
class HistoryDataCollector:
    def __init__(self, raw_dir: str = "./data/raw_pdfs"):
        self.raw_dir = Path(raw_dir)
        # 注意：不在这里创建目录，因为已存在

    def scan_all_pdfs(self) -> List[Dict]:
        """递归扫描 raw_pdfs 下所有子目录中的 PDF 文件"""
        pdf_files = []
        # 使用 rglob 递归查找所有 .pdf 文件
        for file_path in self.raw_dir.rglob("*.pdf"):
            if not file_path.is_file():
                continue
            stat = file_path.stat()
            # 从相对路径中提取年级信息（例如 grade_7）
            relative_path = file_path.relative_to(self.raw_dir)
            grade = relative_path.parts[0] if len(relative_path.parts) > 0 else "unknown"

            file_info = {
                "name": file_path.stem,                     # 文件名（不含扩展名）
                "file_path": str(file_path),                # 绝对或相对路径？建议存相对项目根目录的路径
                "file_size": stat.st_size,
                "modified_time": stat.st_mtime,
                "content_hash": self._compute_hash(file_path),
                "grade": grade                               # 从子目录名获取
            }
            pdf_files.append(file_info)
        return pdf_files

    def _compute_hash(self, file_path: Path) -> str:
        """计算文件哈希用于去重"""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def collect_data(self):
        """主流程：扫描并保存元数据到JSON"""
        local_pdfs = self.scan_all_pdfs()
        print(f"找到 {len(local_pdfs)} 个PDF文件")
        # 可选：将元数据保存到JSON文件
        import json
        json_path = Path("./data/raw_pdfs/metadata.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(local_pdfs, f, indent=2, ensure_ascii=False)
        print(f"元数据已保存到 {json_path}")
        return local_pdfs

if __name__ == "__main__":
    collector = HistoryDataCollector()
    collector.collect_data()
    