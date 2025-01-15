import requests
import json
import time
from typing import Dict, List, Optional

def create_document(title: str, content: str, doc_type: str, tags: list) -> str:
    """创建文档并返回文档ID"""
    url = "http://localhost:8000/api/v1/documents/"
    headers = {"Content-Type": "application/json"}
    data = {
        "title": title,
        "content": content,
        "doc_type": doc_type,
        "tags": tags,
        "embedding": [0.0] * 512  # 添加默认的embedding向量
    }
    
    response = requests.post(url, headers=headers, json=data)
    print(f"\n创建文档 '{title}' 响应:")
    print(json.dumps(response.json(), ensure_ascii=False, indent=2))
    return response.json()["id"]

def create_relation(source_id: str, target_id: str, relation_type: str, properties: Dict = None) -> Dict:
    """创建文档关系"""
    url = "http://localhost:8000/api/v1/documents/relations/"
    headers = {"Content-Type": "application/json"}
    data = {
        "source_id": source_id,
        "target_id": target_id,
        "relation_type": relation_type,
        "properties": properties or {}
    }
    
    response = requests.post(url, headers=headers, json=data)
    print(f"\n创建关系响应 ({relation_type}):")
    print(json.dumps(response.json(), ensure_ascii=False, indent=2))
    return response.json()

def get_document_relations(doc_id: str, relation_type: str = None, direction: str = "all") -> List[Dict]:
    """获取文档关系"""
    params = {"relation_type": relation_type, "direction": direction}
    url = f"http://localhost:8000/api/v1/documents/{doc_id}/relations/"
    
    response = requests.get(url, params=params)
    print(f"\n获取文档关系响应 (文档ID: {doc_id}):")
    print(json.dumps(response.json(), ensure_ascii=False, indent=2))
    return response.json()

def test_relation_count_limit():
    """测试关系数量限制"""
    print("\n=== 测试关系数量限制 ===")
    
    # 创建测试文档
    doc1_id = create_document(
        title="主文档",
        content="这是主文档的内容",
        doc_type="main",
        tags=["测试"]
    )
    
    # 创建多个前置条件文档并建立关系
    for i in range(6):  # 尝试创建6个前置条件(超过限制5个)
        doc_id = create_document(
            title=f"前置条件{i+1}",
            content=f"这是前置条件{i+1}的内容",
            doc_type="prerequisite",
            tags=["测试"]
        )
        
        # 创建前置条件关系
        try:
            create_relation(
                source_id=doc_id,
                target_id=doc1_id,
                relation_type="PREREQUISITE",
                properties={"importance": "high"}
            )
        except Exception as e:
            print(f"预期的错误: {str(e)}")
        
        time.sleep(1)

def test_relation_compatibility():
    """测试关系类型兼容性"""
    print("\n=== 测试关系类型兼容性 ===")
    
    # 创建测试文档
    parent_id = create_document(
        title="父文档",
        content="这是父文档的内容",
        doc_type="parent",
        tags=["测试"]
    )
    
    child_id = create_document(
        title="子文档",
        content="这是子文档的内容",
        doc_type="child",
        tags=["测试"]
    )
    
    # 创建父子关系
    create_relation(
        source_id=parent_id,
        target_id=child_id,
        relation_type="PARENT_OF",
        properties={}
    )
    
    # 尝试创建反向的父子关系(应该失败)
    try:
        create_relation(
            source_id=child_id,
            target_id=parent_id,
            relation_type="PARENT_OF",
            properties={}
        )
    except Exception as e:
        print(f"预期的错误: {str(e)}")
    
    time.sleep(1)

def test_circular_dependency():
    """测试循环依赖检测"""
    print("\n=== 测试循环依赖检测 ===")
    
    # 创建一系列文档形成环
    doc_ids = []
    for i in range(3):
        doc_id = create_document(
            title=f"文档{i+1}",
            content=f"这是文档{i+1}的内容",
            doc_type="test",
            tags=["测试"]
        )
        doc_ids.append(doc_id)
        time.sleep(1)
    
    # 创建循环依赖的关系
    try:
        # 文档1 -> 文档2
        create_relation(
            source_id=doc_ids[0],
            target_id=doc_ids[1],
            relation_type="NEXT_STEP",
            properties={"order": 1}
        )
        
        # 文档2 -> 文档3
        create_relation(
            source_id=doc_ids[1],
            target_id=doc_ids[2],
            relation_type="NEXT_STEP",
            properties={"order": 2}
        )
        
        # 文档3 -> 文档1 (应该失败)
        create_relation(
            source_id=doc_ids[2],
            target_id=doc_ids[0],
            relation_type="NEXT_STEP",
            properties={"order": 3}
        )
    except Exception as e:
        print(f"预期的错误: {str(e)}")
    
    time.sleep(1)

def test_relation_properties():
    """测试关系属性验证"""
    print("\n=== 测试关系属性验证 ===")
    
    # 创建测试文档
    doc1_id = create_document(
        title="源文档",
        content="这是源文档的内容",
        doc_type="source",
        tags=["测试"]
    )
    
    doc2_id = create_document(
        title="目标文档",
        content="这是目标文档的内容",
        doc_type="target",
        tags=["测试"]
    )
    
    # 测试缺少必需属性的情况
    try:
        create_relation(
            source_id=doc1_id,
            target_id=doc2_id,
            relation_type="NEXT_STEP",
            properties={}  # 缺少必需的order属性
        )
    except Exception as e:
        print(f"预期的错误: {str(e)}")
    
    # 测试提供正确属性的情况
    create_relation(
        source_id=doc1_id,
        target_id=doc2_id,
        relation_type="NEXT_STEP",
        properties={"order": 1}
    )
    
    time.sleep(1)

if __name__ == "__main__":
    print("=== 开始测试文档关系验证规则 ===\n")
    
    # 运行所有测试
    test_relation_count_limit()
    test_relation_compatibility()
    test_circular_dependency()
    test_relation_properties()
    
    print("\n=== 测试完成 ===") 