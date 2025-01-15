from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import UUID

from models.document import Document
from services.embedding import EmbeddingService
from services.vector_store import VectorStore
from services.graph_store import GraphStore
from loguru import logger

class DocumentService:
    """
    文档服务类，整合向量嵌入、向量存储和图数据库服务，
    提供完整的文档管理功能
    """
    
    def __init__(self):
        """初始化文档服务，创建所需的服务实例"""
        # 创建向量嵌入服务实例，用于生成文档的向量表示
        self.embedding_service = EmbeddingService()
        # 创建向量存储服务实例，用于存储和检索文档向量
        self.vector_store = VectorStore()
        # 创建图数据库服务实例，用于管理文档之间的关系
        self.graph_store = GraphStore()
        logger.info("Document service initialized")

    async def create_document(self, document: Document) -> Document:
        """
        创建新文档，包括生成向量表示并存储到向量数据库和图数据库
        
        Args:
            document: 文档对象，包含标题、内容、类型等信息
            
        Returns:
            创建完成的文档对象，包含生成的向量表示
        """
        try:
            # 使用CLIP模型生成文档内容的向量表示
            embedding = await self.embedding_service.get_text_embedding(document.content)
            document.vector = embedding.tolist()
            
            # 将文档及其向量存储到向量数据库
            await self.vector_store.add_document(
                str(document.id),
                document.vector,
                document.dict(exclude={'vector'})  # 排除向量数据
            )
            
            # 在图数据库中创建文档节点
            await self.graph_store.create_document_node(
                str(document.id),
                document.dict(exclude={'vector', 'content'})  # 排除向量和内容数据
            )
            
            logger.info(f"Document {document.id} created successfully")
            return document
        except Exception as e:
            logger.error(f"Error creating document: {str(e)}")
            raise

    async def search_documents(
        self,
        query: str,
        doc_type: Optional[str] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        搜索文档，支持语义相似度搜索和按文档类型过滤
        
        Args:
            query: 搜索查询文本
            doc_type: 文档类型过滤条件（可选）
            top_k: 返回的最大结果数量
            
        Returns:
            相关文档列表，包含文档信息和相关文档
        """
        try:
            # 生成查询文本的向量表示
            query_embedding = await self.embedding_service.get_text_embedding(query)
            
            # 构建元数据过滤条件
            filter_metadata = {"doc_type": doc_type} if doc_type else None
            
            # 在向量数据库中搜索相似文档
            vector_results = await self.vector_store.search_similar(
                query_embedding.tolist(),
                n_results=top_k,
                filter_metadata=filter_metadata
            )
            
            # 对每个搜索结果，查找其在图数据库中的相关文档
            enriched_results = []
            for result in vector_results:
                # 获取与当前文档相关的其他文档
                related_docs = await self.graph_store.find_related_documents(
                    result["id"],
                    max_depth=1  # 只查找直接相关的文档
                )
                # 将相关文档信息添加到结果中
                result["related_documents"] = related_docs
                enriched_results.append(result)
            
            return enriched_results
        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}")
            raise

    async def create_document_relationship(
        self,
        from_id: UUID,
        to_id: UUID,
        relationship_type: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        创建文档之间的关系
        
        Args:
            from_id: 起始文档ID
            to_id: 目标文档ID
            relationship_type: 关系类型（如：RELATED_TO, REFERENCES等）
            properties: 关系的附加属性（可选）
        """
        try:
            # 在图数据库中创建文档关系
            await self.graph_store.create_relationship(
                str(from_id),
                str(to_id),
                relationship_type,
                properties
            )
            logger.info(f"Relationship created between documents {from_id} and {to_id}")
        except Exception as e:
            logger.error(f"Error creating document relationship: {str(e)}")
            raise

    async def delete_document(self, document_id: UUID) -> None:
        """
        删除文档，包括从向量数据库和图数据库中删除
        
        Args:
            document_id: 要删除的文档ID
        """
        try:
            # 从向量数据库中删除文档
            await self.vector_store.delete_document(str(document_id))
            
            # 从图数据库中删除文档节点及其关系
            await self.graph_store.delete_document_node(str(document_id))
            
            logger.info(f"Document {document_id} deleted successfully")
        except Exception as e:
            logger.error(f"Error deleting document: {str(e)}")
            raise

    async def update_document(self, document: Document) -> Document:
        """
        更新文档信息，包括重新生成向量表示并更新存储
        
        Args:
            document: 更新后的文档对象
            
        Returns:
            更新完成的文档对象
        """
        try:
            # 重新生成文档内容的向量表示
            embedding = await self.embedding_service.get_text_embedding(document.content)
            document.vector = embedding.tolist()
            document.updated_at = datetime.utcnow()  # 更新时间戳
            
            # 更新向量数据库中的文档
            await self.vector_store.update_document(
                str(document.id),
                document.vector,
                document.dict(exclude={'vector'})
            )
            
            # 更新图数据库中的文档节点
            await self.graph_store.delete_document_node(str(document.id))
            await self.graph_store.create_document_node(
                str(document.id),
                document.dict(exclude={'vector', 'content'})
            )
            
            logger.info(f"Document {document.id} updated successfully")
            return document
        except Exception as e:
            logger.error(f"Error updating document: {str(e)}")
            raise 