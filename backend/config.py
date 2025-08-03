# 配置管理
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 数据库配置
    DATABASE_URL: str = "mysql+pymysql://root:password@localhost:3306/real_estate_db"
    
    # JWT配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7天
    
    # 大模型API配置
    DOUBAO_API_KEY: str = ""
    DOUBAO_API_URL: str = ""
    ARK_API_KEY: str = ""  # 豆包API密钥
    OPENAI_API_KEY: str = ""  # OpenAI API密钥
    
    # 文件上传配置
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: str = "jpg,jpeg,png"
    
    class Config:
        env_file = ".env"

settings = Settings()