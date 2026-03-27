"""
数据库验证脚本
"""
import asyncio
import mysql.connector
from mysql.connector import Error
import chromadb
from app.core.config import settings

async def verify_mysql():
    """验证MySQL连接"""
    print("验证MySQL数据库连接...")
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='history_user',
            password='History@2023',
            database='history_qa'
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute("SELECT DATABASE();")
            db_name = cursor.fetchone()[0]
            print(f"✓ MySQL连接成功！当前数据库: {db_name}")
            
            # 检查表是否存在
            cursor.execute("SHOW TABLES;")
            tables = cursor.fetchall()
            print(f"✓ 数据库表数量: {len(tables)}")
            
            for table in tables:
                print(f"  - {table[0]}")
            
            cursor.close()
            connection.close()
            return True
            
    except Error as e:
        print(f"✗ MySQL连接失败: {e}")
        return False

def verify_chromadb():
    """验证ChromaDB连接"""
    print("\n验证ChromaDB连接...")
    try:
        client = chromadb.PersistentClient(path=settings.CHROMA_PATH)
        collections = client.list_collections()
        print(f"✓ ChromaDB连接成功！")
        print(f"  数据库路径: {settings.CHROMA_PATH}")
        print(f"  集合数量: {len(collections)}")
        
        if len(collections) > 0:
            for collection in collections:
                count = collection.count()
                print(f"  - {collection.name}: {count} 条记录")
        
        return True
    except Exception as e:
        print(f"✗ ChromaDB连接失败: {e}")
        return False

async def main():
    """主验证函数"""
    print("=" * 50)
    print("数据库环境验证")
    print("=" * 50)
    
    mysql_ok = await verify_mysql()
    chroma_ok = verify_chromadb()
    
    print("\n" + "=" * 50)
    if mysql_ok and chroma_ok:
        print("✓ 所有数据库连接验证通过！")
        return True
    else:
        print("✗ 数据库连接存在问题，请检查配置。")
        return False

if __name__ == "__main__":
    asyncio.run(main())