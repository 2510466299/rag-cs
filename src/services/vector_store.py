import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import numpy as np
from typing import List, Dict, Any, Optional
from config.config import settings
from loguru import logger

class VectorStore:
    """向量数据库服务，用于存储和检索文档向量"""
    
    def __init__(self):
        """初始化ChromaDB客户端和文档集合"""
        try:
            # 创建ChromaDB客户端实例
            self.client = chromadb.Client(Settings(
                persist_directory=settings.CHROMA_PERSIST_DIRECTORY,  # 持久化存储目录
                anonymized_telemetry=False                           # 禁用遥测数据收集
            ))
            
            # 创建或获取文档集合
            self.collection = self.client.get_or_create_collection(
                name="documents",                                    # 集合名称
                metadata={"description": "Document embeddings collection"}  # 集合描述
            )
            logger.info("ChromaDB initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing ChromaDB: {str(e)}")
            raise

    async def add_document(
        self,
        document_id: str,
        embedding: List[float],
        metadata: Dict[str, Any]
    ) -> None:
        """
        添加文档到向量数据库
        
        Args:
            document_id: 文档唯一标识符
            embedding: 文档的向量表示
            metadata: 文档的元数据（标题、类型等）
        """
        try:
            # 向集合中添加文档
            self.collection.add(
                embeddings=[embedding],                    # 文档向量
                documents=[metadata.get("content", "")],   # 文档内容
                metadatas=[metadata],                     # 文档元数据
                ids=[document_id]                         # 文档ID
            )
            logger.info(f"Document {document_id} added to vector store")
        except Exception as e:
            logger.error(f"Error adding document to vector store: {str(e)}")
            raise

    async def search_similar(
        self,
        query_embedding: List[float],
        n_results: int = settings.TOP_K_RESULTS,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        搜索相似文档
        
        Args:
            query_embedding: 查询向量
            n_results: 返回结果的数量
            filter_metadata: 元数据过滤条件
            
        Returns:
            相似文档列表，每个文档包含ID、内容、元数据和相似度距离
        """
        try:
            # 执行向量相似度搜索
            results = self.collection.query(
                query_embeddings=[query_embedding],    # 查询向量
                n_results=n_results,                   # 返回结果数量
                where=filter_metadata                  # 过滤条件
            )
            
            # 格式化搜索结果
            formatted_results = []
            for i in range(len(results["ids"][0])):
                formatted_results.append({
                    "id": results["ids"][0][i],                  # 文档ID
                    "document": results["documents"][0][i],      # 文档内容
                    "metadata": results["metadatas"][0][i],      # 文档元数据
                    "distance": results["distances"][0][i] if "distances" in results else None  # 相似度距离
                })
            
            return formatted_results
        except Exception as e:
            logger.error(f"Error searching similar documents: {str(e)}")
            raise

    async def delete_document(self, document_id: str) -> None:
        """
        从向量数据库中删除文档
        
        Args:
            document_id: 要删除的文档ID
        """
        try:
            # 从集合中删除指定ID的文档
            self.collection.delete(ids=[document_id])
            logger.info(f"Document {document_id} deleted from vector store")
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            raise

    async def update_document(
        self,
        document_id: str,
        embedding: List[float],
        metadata: Dict[str, Any]
    ) -> None:
        """
        更新向量数据库中的文档
        
        Args:
            document_id: 文档ID
            embedding: 新的文档向量
            metadata: 新的文档元数据
        """
        try:
            # ChromaDB不支持直接更新，所以先删除再添加
            await self.delete_document(document_id)
            await self.add_document(document_id, embedding, metadata)
            logger.info(f"Document {document_id} updated in vector store")
        except Exception as e:
            logger.error(f"Error updating document: {str(e)}")
            raise 