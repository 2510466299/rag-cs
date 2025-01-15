from fastapi import FastAPI
import uvicorn
import logging
from api.documents import router as document_router

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)

# 创建FastAPI应用
app = FastAPI(
    title="文档检索系统",
    description="基于CLIP模型的智能文档检索系统",
    version="1.0.0"
)

# 注册路由
app.include_router(document_router, prefix="/api/v1", tags=["documents"])

if __name__ == "__main__":
    # 确保日志目录存在
    import os
    os.makedirs("logs", exist_ok=True)
    
    # 启动服务器
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 