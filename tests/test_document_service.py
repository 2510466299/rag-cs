import pytest
from uuid import uuid4
from datetime import datetime

from models.document import Document
from services.document_service import DocumentService

@pytest.fixture
def document_service():
    return DocumentService()

@pytest.fixture
def sample_document():
    return Document(
        title="测试文档",
        content="这是一个测试文档的内容。",
        doc_type="test",
        tags=["测试", "示例"],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

@pytest.mark.asyncio
async def test_create_document(document_service, sample_document):
    """测试创建文档"""
    created_doc = await document_service.create_document(sample_document)
    assert created_doc.id is not None
    assert created_doc.vector is not None
    assert len(created_doc.vector) > 0

@pytest.mark.asyncio
async def test_search_documents(document_service, sample_document):
    """测试搜索文档"""
    # 先创建一个文档
    created_doc = await document_service.create_document(sample_document)
    
    # 搜索文档
    results = await document_service.search_documents("测试文档")
    assert len(results) > 0
    assert results[0]["id"] == str(created_doc.id)

@pytest.mark.asyncio
async def test_create_relationship(document_service, sample_document):
    """测试创建文档关系"""
    # 创建两个文档
    doc1 = await document_service.create_document(sample_document)
    doc2 = await document_service.create_document(
        Document(
            title="相关文档",
            content="这是一个相关文档。",
            doc_type="test",
            tags=["测试", "相关"],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    )
    
    # 创建关系
    await document_service.create_document_relationship(
        doc1.id,
        doc2.id,
        "RELATED_TO"
    )
    
    # 验证关系
    results = await document_service.search_documents("测试文档")
    assert len(results) > 0
    assert len(results[0]["related_documents"]) > 0

@pytest.mark.asyncio
async def test_update_document(document_service, sample_document):
    """测试更新文档"""
    # 创建文档
    created_doc = await document_service.create_document(sample_document)
    
    # 更新文档
    created_doc.title = "更新后的文档"
    updated_doc = await document_service.update_document(created_doc)
    assert updated_doc.title == "更新后的文档"
    
    # 验证更新
    results = await document_service.search_documents("更新后的文档")
    assert len(results) > 0
    assert results[0]["metadata"]["title"] == "更新后的文档"

@pytest.mark.asyncio
async def test_delete_document(document_service, sample_document):
    """测试删除文档"""
    # 创建文档
    created_doc = await document_service.create_document(sample_document)
    
    # 删除文档
    await document_service.delete_document(created_doc.id)
    
    # 验证删除
    results = await document_service.search_documents("测试文档")
    assert len(results) == 0 