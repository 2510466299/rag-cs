from pydantic_settings import BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    """应用程序配置类，管理所有配置项"""
    
    # API相关配置
    API_V1_STR: str = "/api/v1"          # API版本前缀
    PROJECT_NAME: str = "客服辅助文档检索系统"  # 项目名称
    
    # CLIP模型配置
    CLIP_MODEL_NAME: str = "openai/clip-vit-base-patch32"  # 使用较小的模型
    CLIP_USE_GPU: bool = False  # 明确指定使用CPU
    CLIP_BATCH_SIZE: int = 8    # 减小批处理大小
    CLIP_MAX_LENGTH: int = 77   # 限制文本长度
    
    # 数据库配置
    CHROMA_PERSIST_DIRECTORY: str = "./data/chroma"  # ChromaDB数据存储目录
    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")  # Neo4j连接URI
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")               # Neo4j用户名
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "yunjipassword")    # Neo4j密码
    
    # 向量搜索配置
    VECTOR_DIMENSION: int = 512  # 向量维度
    TOP_K_RESULTS: int = 5      # 默认返回的最大结果数
    
    # 安全配置
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")  # 密钥
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # 访问令牌过期时间（分钟）
    
    class Config:
        # 配置类设置
        case_sensitive = True  # 配置键名大小写敏感

# 创建全局配置实例
settings = Settings() 