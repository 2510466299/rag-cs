from enum import Enum
from typing import Dict, Optional, List, Set, Tuple
from pydantic import BaseModel, Field
from datetime import datetime

class RelationType(str, Enum):
    """文档关系类型枚举"""
    
    # 顺序关系
    NEXT_STEP = "NEXT_STEP"           # 下一步
    PREREQUISITE = "PREREQUISITE"      # 前置条件
    FOLLOWS = "FOLLOWS"               # 后续内容
    
    # 引用关系
    REFERENCES = "REFERENCES"         # 引用
    CITED_BY = "CITED_BY"            # 被引用
    
    # 关联关系
    RELATED_TO = "RELATED_TO"        # 相关
    SIMILAR_TO = "SIMILAR_TO"        # 相似
    ALTERNATIVE = "ALTERNATIVE"       # 替代方案
    
    # 组织关系
    PARENT_OF = "PARENT_OF"          # 父文档
    CHILD_OF = "CHILD_OF"            # 子文档
    BELONGS_TO = "BELONGS_TO"        # 属于
    
    # 功能关系
    EXPLAINS = "EXPLAINS"            # 解释
    IMPLEMENTS = "IMPLEMENTS"        # 实现
    EXTENDS = "EXTENDS"              # 扩展
    
    # 问题解决关系
    SOLVES = "SOLVES"               # 解决
    CAUSES = "CAUSES"               # 导致
    PREVENTS = "PREVENTS"           # 预防

class RelationMetadata(BaseModel):
    """关系类型的元数据"""
    
    description: str
    bidirectional: bool = False
    required_properties: List[str] = []
    inverse_relation: Optional[str] = None

# 关系类型的元数据定义
RELATION_METADATA: Dict[RelationType, RelationMetadata] = {
    RelationType.NEXT_STEP: RelationMetadata(
        description="指示文档之间的顺序关系",
        bidirectional=False,
        required_properties=["order"],
        inverse_relation=None
    ),
    RelationType.PREREQUISITE: RelationMetadata(
        description="指示文档是另一个文档的前置条件",
        bidirectional=False,
        required_properties=["importance"],
        inverse_relation=None
    ),
    RelationType.REFERENCES: RelationMetadata(
        description="指示文档引用了另一个文档",
        bidirectional=False,
        required_properties=["section"],
        inverse_relation=RelationType.CITED_BY
    ),
    RelationType.CITED_BY: RelationMetadata(
        description="指示文档被另一个文档引用",
        bidirectional=False,
        required_properties=["section"],
        inverse_relation=RelationType.REFERENCES
    ),
    RelationType.RELATED_TO: RelationMetadata(
        description="指示文档之间的一般关联关系",
        bidirectional=True,
        required_properties=["type"],
        inverse_relation=None
    ),
    RelationType.SIMILAR_TO: RelationMetadata(
        description="指示文档之间的相似关系",
        bidirectional=True,
        required_properties=["similarity_score"],
        inverse_relation=None
    ),
    RelationType.ALTERNATIVE: RelationMetadata(
        description="指示文档提供了替代方案",
        bidirectional=True,
        required_properties=["scenario"],
        inverse_relation=None
    ),
    RelationType.PARENT_OF: RelationMetadata(
        description="指示文档是另一个文档的父级",
        bidirectional=False,
        required_properties=[],
        inverse_relation=RelationType.CHILD_OF
    ),
    RelationType.CHILD_OF: RelationMetadata(
        description="指示文档是另一个文档的子级",
        bidirectional=False,
        required_properties=[],
        inverse_relation=RelationType.PARENT_OF
    ),
    RelationType.EXPLAINS: RelationMetadata(
        description="指示文档解释了另一个文档的内容",
        bidirectional=False,
        required_properties=["aspect"],
        inverse_relation=None
    ),
    RelationType.IMPLEMENTS: RelationMetadata(
        description="指示文档实现了另一个文档描述的功能",
        bidirectional=False,
        required_properties=["version"],
        inverse_relation=None
    ),
    RelationType.SOLVES: RelationMetadata(
        description="指示文档解决了另一个文档描述的问题",
        bidirectional=False,
        required_properties=["solution_type"],
        inverse_relation=None
    )
}

def validate_relation_properties(relation_type: RelationType, properties: Dict) -> bool:
    """验证关系属性是否满足要求
    
    Args:
        relation_type: 关系类型
        properties: 关系属性
        
    Returns:
        属性是否有效
    """
    metadata = RELATION_METADATA.get(relation_type)
    if not metadata:
        return False
        
    # 检查必需属性
    for required_prop in metadata.required_properties:
        if required_prop not in properties:
            return False
            
    return True

def get_inverse_relation(relation_type: RelationType) -> Optional[RelationType]:
    """获取关系的反向关系类型
    
    Args:
        relation_type: 关系类型
        
    Returns:
        反向关系类型，如果没有则返回None
    """
    metadata = RELATION_METADATA.get(relation_type)
    if metadata and metadata.inverse_relation:
        return RelationType(metadata.inverse_relation)
    return None

def is_bidirectional(relation_type: RelationType) -> bool:
    """检查关系是否是双向的
    
    Args:
        relation_type: 关系类型
        
    Returns:
        是否双向关系
    """
    metadata = RELATION_METADATA.get(relation_type)
    return metadata.bidirectional if metadata else False 

# 关系验证配置
class RelationValidationConfig:
    """关系验证配置"""
    
    # 每个文档最大关系数量
    MAX_RELATIONS_PER_DOC = 50
    
    # 最大关系深度(用于循环检测)
    MAX_RELATION_DEPTH = 10
    
    # 每种关系类型的最大数量
    MAX_RELATIONS_BY_TYPE = {
        RelationType.NEXT_STEP: 1,      # 一个文档只能有一个下一步
        RelationType.PREREQUISITE: 5,    # 最多5个前置条件
        RelationType.PARENT_OF: 100,     # 父文档可以有多个子文档
        RelationType.CHILD_OF: 1,        # 一个文档只能有一个父文档
    }
    
    # 关系类型兼容性规则
    # 定义哪些关系类型不能同时存在
    INCOMPATIBLE_RELATIONS = {
        RelationType.PARENT_OF: {RelationType.CHILD_OF},  # 父子关系互斥
        RelationType.NEXT_STEP: {RelationType.PREREQUISITE},  # 下一步和前置条件互斥
    }

def check_relation_count(doc_id: str, relation_type: RelationType, current_count: int) -> bool:
    """检查关系数量是否超过限制
    
    Args:
        doc_id: 文档ID
        relation_type: 关系类型
        current_count: 当前关系数量
        
    Returns:
        是否允许创建新关系
    """
    # 检查总关系数量
    if current_count >= RelationValidationConfig.MAX_RELATIONS_PER_DOC:
        return False
        
    # 检查特定类型的关系数量
    if relation_type in RelationValidationConfig.MAX_RELATIONS_BY_TYPE:
        type_limit = RelationValidationConfig.MAX_RELATIONS_BY_TYPE[relation_type]
        if current_count >= type_limit:
            return False
            
    return True

def check_relation_compatibility(
    doc_id: str,
    target_id: str,
    relation_type: RelationType,
    existing_relations: List[Dict]
) -> bool:
    """检查关系类型兼容性
    
    Args:
        doc_id: 源文档ID
        target_id: 目标文档ID
        relation_type: 待创建的关系类型
        existing_relations: 已存在的关系列表
        
    Returns:
        关系类型是否兼容
    """
    # 获取不兼容的关系类型
    incompatible_types = RelationValidationConfig.INCOMPATIBLE_RELATIONS.get(relation_type, set())
    
    # 检查现有关系是否有不兼容的类型
    for relation in existing_relations:
        existing_type = RelationType(relation["relation_type"])
        if existing_type in incompatible_types:
            return False
            
    return True

def detect_circular_dependency(
    doc_id: str,
    target_id: str,
    relation_type: RelationType,
    document_store,
    visited: Optional[Set[str]] = None,
    depth: int = 0
) -> bool:
    """检测是否存在循环依赖
    
    Args:
        doc_id: 源文档ID
        target_id: 目标文档ID
        relation_type: 关系类型
        document_store: 文档存储服务实例
        visited: 已访问的文档ID集合
        depth: 当前深度
        
    Returns:
        是否存在循环依赖
    """
    # 初始化已访问集合
    if visited is None:
        visited = set()
    
    # 检查深度是否超过限制
    if depth >= RelationValidationConfig.MAX_RELATION_DEPTH:
        return True
        
    # 如果目标文档已经访问过，说明存在循环
    if target_id in visited:
        return True
        
    # 将当前文档加入已访问集合
    visited.add(doc_id)
    
    # 获取目标文档的所有关系
    target_relations = document_store.get_document_relations(
        doc_id=target_id,
        direction="outgoing"
    )
    
    # 递归检查每个关系
    for relation in target_relations:
        next_target = relation["target_id"]
        if detect_circular_dependency(
            target_id,
            next_target,
            RelationType(relation["relation_type"]),
            document_store,
            visited,
            depth + 1
        ):
            return True
            
    # 移除当前文档(回溯)
    visited.remove(doc_id)
    return False

def validate_relation_creation(
    doc_id: str,
    target_id: str,
    relation_type: RelationType,
    properties: Dict,
    document_store
) -> Tuple[bool, str]:
    """完整的关系创建验证
    
    Args:
        doc_id: 源文档ID
        target_id: 目标文档ID
        relation_type: 关系类型
        properties: 关系属性
        document_store: 文档存储服务实例
        
    Returns:
        (是否验证通过, 错误信息)
    """
    # 1. 验证关系属性
    if not validate_relation_properties(relation_type, properties):
        return False, f"关系类型 {relation_type} 缺少必需的属性"
    
    # 2. 获取现有关系
    existing_relations = document_store.get_document_relations(doc_id)
    current_count = len([r for r in existing_relations if r["relation_type"] == relation_type.value])
    
    # 3. 检查关系数量
    if not check_relation_count(doc_id, relation_type, current_count):
        return False, f"超过关系数量限制 (类型: {relation_type})"
    
    # 4. 检查关系兼容性
    if not check_relation_compatibility(doc_id, target_id, relation_type, existing_relations):
        return False, f"关系类型 {relation_type} 与现有关系不兼容"
    
    # 5. 检查循环依赖
    if detect_circular_dependency(doc_id, target_id, relation_type, document_store):
        return False, "检测到循环依赖"
    
    return True, "" 