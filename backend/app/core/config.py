# app/core/config.py
import os
from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

# 指定 .env 文件路径为项目根目录下的 .env
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

class Settings(BaseSettings):
    # 应用配置
    APP_NAME: str = "历史问答系统"
    DEBUG: bool = True
    
    # 数据库配置
    DATABASE_URL: str = "mysql+pymysql://history_user:History%402023@localhost:3306/history_qa"
    
    # 向量数据库配置
    CHROMA_PATH: str = "./data/chroma_db"
    
    # 大模型API配置
    BAIDU_API_KEY: Optional[str] = None
    BAIDU_SECRET_KEY: Optional[str] = None
    ALI_API_KEY: Optional[str] = None
    
    # Embedding配置
    EMBEDDING_MODEL: str = "text-embedding-v1"  # 百度文心
    EMBEDDING_SIZE: int = 384
    
    # JWT配置
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24小时
    
    class Config:
        env_file = ".env"

settings = Settings()