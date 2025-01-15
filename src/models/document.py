from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID, uuid4

class Document(BaseModel):
    """文档模型，用于存储和管理文档信息"""
    # 文档的唯一标识符，使用UUID自动生成
    id: UUID = Field(default_factory=uuid4)
    
    # 文档标题，必填字段
    title: str = Field(..., description="文档标题")
    
    # 文档正文内容，必填字段
    content: str = Field(..., description="文档内容")
    
    # 文档类型（如：手册、FAQ等），必填字段
    doc_type: str = Field(..., description="文档类型")
    
    # 文档标签列表，用于分类和检索，默认为空列表
    tags: List[str] = Field(default=[], description="文档标签")
    
    # 文档的向量表示，用于相似度计算，可选字段
    vector: Optional[List[float]] = Field(None, description="文档向量表示")
    
    # 文档创建时间，默认为当前UTC时间
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # 文档最后更新时间，默认为当前UTC时间
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        # 模型配置，提供示例数据
        json_schema_extra = {
            "example": {
                "title": "产品使用手册",
                "content": "这是一份产品使用说明文档...",
                "doc_type": "manual",
                "tags": ["使用说明", "产品文档"],
            }
        } 