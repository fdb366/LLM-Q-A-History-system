# backend/app/core/sync_database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .config import settings

# 将异步 URL 转换为同步 URL（将 asyncmy 替换为 pymysql）
print("原始 settings.DATABASE_URL:", settings.DATABASE_URL)
sync_url = settings.DATABASE_URL.replace("+asyncmy", "").replace("+aiomysql", "")
print("替换后的 sync_url:", sync_url)
if "pymysql" not in sync_url and sync_url.startswith("mysql://"):
    sync_url = sync_url.replace("mysql://", "mysql+pymysql://")
print("最终 sync_url:", sync_url)
if "pymysql" not in sync_url and sync_url.startswith("mysql://"):
    sync_url = sync_url.replace("mysql://", "mysql+pymysql://")

engine = create_engine(
    sync_url,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
def get_db():
    """同步数据库会话依赖"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()