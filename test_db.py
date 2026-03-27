from backend.app.core.sync_database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
db.execute(text('SELECT 1'))
print('连接成功')