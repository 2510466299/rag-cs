from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Set
from pydantic import BaseModel, Field
from enum import Enum
import logging
from datetime import datetime
import json

from services.embedding import EmbeddingService
from services.document_store import DocumentStore
from models.relations import (
    RelationType, 
    validate_relation_properties, 
    get_inverse_relation,
    is_bidirectional,
    validate_relation_creation
)

# 设置日志编码
logging.basicConfig(encoding='utf-8')

# 创建路由器
router = APIRouter()

# 依赖注入函数
def get_embedding_service():
    return EmbeddingService()

def get_document_store(
    neo4j_uri: str = Query("bolt://localhost:7687"),
    neo4j_user: str = Query("neo4j"),
    neo4j_password: str = Query("yunjipassword")
):
    """从查询参数获取Neo4j连接信息"""
    return DocumentStore(
        uri=neo4j_uri,
        username=neo4j_user,
        password=neo4j_password
    )

# 请求/响应模型
class DocumentCreate(BaseModel):
    title: str
    content: str
    doc_type: str
    tags: Optional[List[str]] = None
    embedding: Optional[List[float]] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class DocumentResponse(BaseModel):
    id: str
    title: str
    content: str
    type: str
    tags: List[str]
    created_at: str
    updated_at: str
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    doc_type: Optional[str] = None
    tags: Optional[List[str]] = None

class SearchQuery(BaseModel):
    query: str
    limit: Optional[int] = 5

# 添加关系管理的请求模型
class RelationCreate(BaseModel):
    source_id: str
    target_id: str
    relation_type: RelationType
    properties: Optional[Dict] = None

class RelationResponse(BaseModel):
    source_id: str
    target_id: str
    relation_type: str
    properties: Dict
    created_at: str

# 批量操作的请求模型
class BatchRelationCreate(BaseModel):
    relations: List[RelationCreate]

class BatchRelationDelete(BaseModel):
    relations: List[Dict[str, str]]  # List of {source_id, target_id, relation_type}

class PathQuery(BaseModel):
    start_id: str
    end_id: str
    relation_types: Optional[List[str]] = None
    max_depth: Optional[int] = 5
    
class TraversalDirection(str, Enum):
    OUTGOING = "outgoing"
    INCOMING = "incoming"
    ALL = "all"

class TraversalQuery(BaseModel):
    start_id: str
    relation_types: Optional[List[str]] = None
    direction: TraversalDirection = TraversalDirection.ALL
    max_depth: Optional[int] = 3
    exclude_types: Optional[List[str]] = None

# API端点
@router.post("/documents/", response_model=DocumentResponse)
async def create_document(
    document: DocumentCreate,
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    document_store: DocumentStore = Depends(get_document_store)
):
    """创建新文档"""
    try:
        # 如果没有提供embedding，则生成文档的向量表示
        embedding = document.embedding if document.embedding is not None else embedding_service.get_text_embedding(document.content).tolist()
        
        # 创建文档
        doc = document_store.create_document(
            title=document.title,
            content=document.content,
            doc_type=document.doc_type,
            embedding=embedding,
            tags=document.tags
        )
        
        if not doc:
            raise HTTPException(status_code=500, detail="Failed to create document")
            
        return doc
    except Exception as e:
        logging.error(f"Error creating document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents/{doc_id}", response_model=DocumentResponse)
async def get_document(
    doc_id: str,
    document_store: DocumentStore = Depends(get_document_store)
):
    """获取文档信息"""
    doc = document_store.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

@router.put("/documents/{doc_id}", response_model=DocumentResponse)
async def update_document(
    doc_id: str,
    updates: DocumentUpdate,
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    document_store: DocumentStore = Depends(get_document_store)
):
    """更新文档信息"""
    try:
        # 获取现有文档
        existing_doc = document_store.get_document(doc_id)
        if not existing_doc:
            raise HTTPException(status_code=404, detail="Document not found")
            
        # 准备更新数据
        update_data = updates.dict(exclude_unset=True)
        
        # 如果内容被更新，重新生成向量
        if "content" in update_data:
            embedding = embedding_service.get_text_embedding(update_data["content"])
            update_data["embedding"] = embedding.tolist()
            
        # 更新文档
        success = document_store.update_document(doc_id, **update_data)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update document")
            
        # 返回更新后的文档
        return document_store.get_document(doc_id)
    except Exception as e:
        logging.error(f"Error updating document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/documents/{doc_id}")
async def delete_document(
    doc_id: str,
    document_store: DocumentStore = Depends(get_document_store)
):
    """删除文档"""
    success = document_store.delete_document(doc_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"message": "Document deleted successfully"}

@router.post("/documents/search/", response_model=List[DocumentResponse])
async def search_documents(
    query: SearchQuery,
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    document_store: DocumentStore = Depends(get_document_store)
):
    """搜索相似文档"""
    try:
        # 生成查询文本的向量表示
        query_embedding = embedding_service.get_text_embedding(query.query)
        
        # 搜索相似文档
        similar_docs = document_store.find_similar_documents(
            embedding=query_embedding,
            limit=query.limit
        )
        
        return similar_docs
    except Exception as e:
        logging.error(f"Error searching documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 添加关系管理的API端点
@router.post("/documents/relations/", response_model=RelationResponse)
async def create_relation(
    relation: RelationCreate,
    document_store: DocumentStore = Depends(get_document_store)
):
    """创建文档间的关系"""
    try:
        # 验证源文档和目标文档是否存在
        source_doc = document_store.get_document(relation.source_id)
        if not source_doc:
            raise HTTPException(status_code=404, detail="Source document not found")
            
        target_doc = document_store.get_document(relation.target_id)
        if not target_doc:
            raise HTTPException(status_code=404, detail="Target document not found")
        
        # 添加创建时间
        properties = relation.properties or {}
        properties["created_at"] = datetime.utcnow().isoformat()
        
        # 使用新的验证规则
        is_valid, error_message = validate_relation_creation(
            doc_id=relation.source_id,
            target_id=relation.target_id,
            relation_type=relation.relation_type,
            properties=properties,
            document_store=document_store
        )
        
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_message)
        
        # 创建主关系
        success = document_store.create_relation(
            doc_id1=relation.source_id,
            doc_id2=relation.target_id,
            relation_type=relation.relation_type.value,
            properties=properties
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to create relation")
            
        # 如果是双向关系或有反向关系，创建反向关系
        if is_bidirectional(relation.relation_type):
            document_store.create_relation(
                doc_id1=relation.target_id,
                doc_id2=relation.source_id,
                relation_type=relation.relation_type.value,
                properties=properties
            )
        elif inverse_relation := get_inverse_relation(relation.relation_type):
            document_store.create_relation(
                doc_id1=relation.target_id,
                doc_id2=relation.source_id,
                relation_type=inverse_relation.value,
                properties=properties
            )
        
        return {
            "source_id": relation.source_id,
            "target_id": relation.target_id,
            "relation_type": relation.relation_type.value,
            "properties": properties,
            "created_at": properties["created_at"]
        }
    except Exception as e:
        logging.error(f"Error creating relation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents/{doc_id}/relations/")
async def get_document_relations(
    doc_id: str,
    relation_type: Optional[str] = None,
    direction: Optional[str] = "all",
    document_store: DocumentStore = Depends(get_document_store)
):
    """获取文档的关系
    
    Args:
        doc_id: 文档ID
        relation_type: 关系类型（可选）
        direction: 关系方向 (incoming/outgoing/all)
    """
    try:
        # 验证文档是否存在
        doc = document_store.get_document(doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
            
        # 获取关系
        relations = document_store.get_document_relations(
            doc_id=doc_id,
            relation_type=relation_type,
            direction=direction
        )
        
        return relations
    except Exception as e:
        logging.error(f"Error getting relations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/documents/relations/{source_id}/{target_id}/{relation_type}")
async def delete_relation(
    source_id: str,
    target_id: str,
    relation_type: str,
    document_store: DocumentStore = Depends(get_document_store)
):
    """删除文档间的关系"""
    try:
        success = document_store.delete_relation(
            doc_id1=source_id,
            doc_id2=target_id,
            relation_type=relation_type
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Relation not found")
            
        return {"message": "Relation deleted successfully"}
    except Exception as e:
        logging.error(f"Error deleting relation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 批量操作API端点
@router.post("/documents/relations/batch", response_model=List[RelationResponse])
async def create_relations_batch(
    batch: BatchRelationCreate,
    document_store: DocumentStore = Depends(get_document_store)
):
    """批量创建文档关系"""
    try:
        results = []
        errors = []
        
        for relation in batch.relations:
            try:
                # 验证源文档和目标文档是否存在
                source_doc = document_store.get_document(relation.source_id)
                if not source_doc:
                    raise ValueError(f"Source document {relation.source_id} not found")
                    
                target_doc = document_store.get_document(relation.target_id)
                if not target_doc:
                    raise ValueError(f"Target document {relation.target_id} not found")
                
                # 添加创建时间
                properties = relation.properties or {}
                properties["created_at"] = datetime.utcnow().isoformat()
                
                # 使用验证规则
                is_valid, error_message = validate_relation_creation(
                    doc_id=relation.source_id,
                    target_id=relation.target_id,
                    relation_type=relation.relation_type,
                    properties=properties,
                    document_store=document_store
                )
                
                if not is_valid:
                    raise ValueError(error_message)
                
                # 创建主关系
                success = document_store.create_relation(
                    doc_id1=relation.source_id,
                    doc_id2=relation.target_id,
                    relation_type=relation.relation_type.value,
                    properties=properties
                )
                
                if not success:
                    raise ValueError("Failed to create relation")
                
                # 处理双向关系
                if is_bidirectional(relation.relation_type):
                    document_store.create_relation(
                        doc_id1=relation.target_id,
                        doc_id2=relation.source_id,
                        relation_type=relation.relation_type.value,
                        properties=properties
                    )
                elif inverse_relation := get_inverse_relation(relation.relation_type):
                    document_store.create_relation(
                        doc_id1=relation.target_id,
                        doc_id2=relation.source_id,
                        relation_type=inverse_relation.value,
                        properties=properties
                    )
                
                results.append({
                    "source_id": relation.source_id,
                    "target_id": relation.target_id,
                    "relation_type": relation.relation_type.value,
                    "properties": properties,
                    "created_at": properties["created_at"]
                })
                
            except Exception as e:
                errors.append({
                    "source_id": relation.source_id,
                    "target_id": relation.target_id,
                    "error": str(e)
                })
        
        if errors:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Some relations failed to create",
                    "errors": errors,
                    "success": results
                }
            )
            
        return results
    except Exception as e:
        logging.error(f"Error in batch relation creation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/documents/relations/batch")
async def delete_relations_batch(
    batch: BatchRelationDelete,
    document_store: DocumentStore = Depends(get_document_store)
):
    """批量删除文档关系"""
    try:
        results = []
        errors = []
        
        for relation in batch.relations:
            try:
                success = document_store.delete_relation(
                    doc_id1=relation["source_id"],
                    doc_id2=relation["target_id"],
                    relation_type=relation["relation_type"]
                )
                
                if success:
                    results.append(relation)
                else:
                    errors.append({
                        **relation,
                        "error": "Relation not found"
                    })
                    
            except Exception as e:
                errors.append({
                    **relation,
                    "error": str(e)
                })
        
        if errors:
            raise HTTPException(
                status_code=400,
                detail={
                    "message": "Some relations failed to delete",
                    "errors": errors,
                    "success": results
                }
            )
            
        return {"message": "Relations deleted successfully", "deleted": results}
    except Exception as e:
        logging.error(f"Error in batch relation deletion: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 关系图遍历API端点
@router.get("/documents/{doc_id}/path/{target_id}")
async def find_path_between_documents(
    doc_id: str,
    target_id: str,
    relation_types: Optional[List[str]] = None,
    max_depth: Optional[int] = 5,
    document_store: DocumentStore = Depends(get_document_store)
):
    """查找两个文档之间的路径"""
    try:
        # 验证文档是否存在
        source_doc = document_store.get_document(doc_id)
        if not source_doc:
            raise HTTPException(status_code=404, detail="Source document not found")
            
        target_doc = document_store.get_document(target_id)
        if not target_doc:
            raise HTTPException(status_code=404, detail="Target document not found")
        
        # 查找路径
        paths = document_store.find_paths(
            start_id=doc_id,
            end_id=target_id,
            relation_types=relation_types,
            max_depth=max_depth
        )
        
        if not paths:
            return {"message": "No path found between documents"}
            
        return {"paths": paths}
    except Exception as e:
        logging.error(f"Error finding path: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents/paths/", response_model=List[Dict])
async def find_paths(
    start_id: str,
    end_id: str,
    relation_types: Optional[List[str]] = None,
    max_depth: Optional[int] = 5,
    document_store: DocumentStore = Depends(get_document_store)
):
    """查找两个文档之间的路径"""
    try:
        paths = document_store.find_paths(
            start_id=start_id,
            end_id=end_id,
            relation_types=relation_types,
            max_depth=max_depth
        )
        return paths
    except Exception as e:
        logging.error(f"Error finding paths: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/documents/{doc_id}/relations/traverse", response_model=List[Dict])
async def traverse_relations(
    doc_id: str,
    direction: TraversalDirection = TraversalDirection.ALL,
    relation_types: Optional[List[str]] = None,
    max_depth: Optional[int] = 3,
    document_store: DocumentStore = Depends(get_document_store)
):
    """遍历文档关系"""
    try:
        relations = document_store.traverse_relations(
            doc_id=doc_id,
            direction=direction.value,
            relation_types=relation_types,
            max_depth=max_depth
        )
        return relations
    except Exception as e:
        logging.error(f"Error traversing relations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/documents/clear")
async def clear_documents(
    document_store: DocumentStore = Depends(get_document_store)
):
    """清理所有文档"""
    try:
        success = document_store.clear_all_documents()
        if not success:
            raise HTTPException(status_code=500, detail="Failed to clear documents")
        return {"message": "All documents cleared successfully"}
    except Exception as e:
        logging.error(f"Error clearing documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 