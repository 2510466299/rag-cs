import requests
import json
import pytest
from typing import Dict, List, Optional
from datetime import datetime

BASE_URL = "http://localhost:8000/api/v1"
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "yunjipassword"

def create_document(title: str, content: str, doc_type: str, tags: List[str]) -> Dict:
    """创建文档"""
    url = f"{BASE_URL}/documents/"
    data = {
        "title": title,
        "content": content,
        "doc_type": doc_type,
        "tags": tags,
        "embedding": [0.0] * 512  # 添加一个默认的embedding向量
    }
    response = requests.post(url, json=data)
    print(f"\n创建文档 '{title}' 响应:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    
    if response.status_code != 200:
        raise Exception(f"创建文档失败: {response.json()}")
    
    return response.json()

def create_relations_batch(relations: List[Dict]) -> Dict:
    """批量创建关系"""
    url = f"{BASE_URL}/documents/relations/batch"
    response = requests.post(url, json={"relations": relations})
    print("\n批量创建关系响应:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    return response.json()

def delete_relations_batch(relations: List[Dict]) -> Dict:
    """批量删除关系"""
    url = f"{BASE_URL}/documents/relations/batch"
    response = requests.delete(url, json={"relations": relations})
    print("\n批量删除关系响应:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    return response.json()

def find_paths(start_id: str, end_id: str, relation_types: Optional[List[str]] = None) -> Dict:
    """查找文档路径"""
    url = f"{BASE_URL}/documents/paths/"
    params = {
        "start_id": start_id,
        "end_id": end_id,
        "neo4j_uri": NEO4J_URI,
        "neo4j_user": NEO4J_USER,
        "neo4j_password": NEO4J_PASSWORD
    }
    if relation_types:
        params["relation_types"] = relation_types
    response = requests.get(url, params=params)
    print(f"\n查找路径响应 (从 {start_id} 到 {end_id}):")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    return response.json()

def traverse_relations(doc_id: str, direction: str = "outgoing",
                      relation_types: Optional[List[str]] = None) -> Dict:
    """遍历文档关系"""
    url = f"{BASE_URL}/documents/{doc_id}/relations/traverse"
    params = {
        "direction": direction.lower(),
        "neo4j_uri": NEO4J_URI,
        "neo4j_user": NEO4J_USER,
        "neo4j_password": NEO4J_PASSWORD
    }
    if relation_types:
        params["relation_types"] = relation_types
    response = requests.get(url, params=params)
    print(f"\n遍历关系响应 (文档ID: {doc_id}):")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    return response.json()

@pytest.fixture(scope="module")
def test_docs():
    """创建测试文档的fixture"""
    print("\n=== 创建测试文档 ===\n")
    docs = [
        create_document("产品介绍", "产品的基本介绍和功能概述", "introduction", ["产品", "介绍"]),
        create_document("安装指南", "详细的安装步骤和注意事项", "guide", ["安装", "指南"]),
        create_document("配置说明", "系统配置和参数设置说明", "configuration", ["配置", "设置"]),
        create_document("使用教程", "产品使用方法和最佳实践", "tutorial", ["教程", "使用"]),
        create_document("故障排除", "常见问题和解决方案", "troubleshooting", ["故障", "问题"])
    ]
    yield docs

def test_batch_operations(test_docs):
    """测试批量操作"""
    print("\n=== 测试批量操作 ===\n")
    
    try:
        # 1. 批量创建关系
        print("\n1. 批量创建关系...")
        relations = [
            {
                "source_id": test_docs[0]["id"],
                "target_id": test_docs[1]["id"],
                "relation_type": "NEXT_STEP",
                "properties": {"order": 1}
            },
            {
                "source_id": test_docs[1]["id"],
                "target_id": test_docs[2]["id"],
                "relation_type": "NEXT_STEP",
                "properties": {"order": 2}
            },
            {
                "source_id": test_docs[2]["id"],
                "target_id": test_docs[3]["id"],
                "relation_type": "NEXT_STEP",
                "properties": {"order": 3}
            },
            {
                "source_id": test_docs[3]["id"],
                "target_id": test_docs[4]["id"],
                "relation_type": "REFERENCES",
                "properties": {"section": "troubleshooting"}
            }
        ]
        result = create_relations_batch(relations)
        assert result is not None, "批量创建关系失败"
        
        # 2. 批量删除关系
        print("\n2. 批量删除关系...")
        relations_to_delete = [
            {
                "source_id": test_docs[2]["id"],
                "target_id": test_docs[3]["id"],
                "relation_type": "NEXT_STEP"
            }
        ]
        result = delete_relations_batch(relations_to_delete)
        assert result is not None, "批量删除关系失败"
        
    except Exception as e:
        print(f"\n错误: {str(e)}")
        raise

def test_graph_traversal(test_docs):
    """测试图遍历"""
    print("\n=== 测试图遍历 ===\n")
    
    try:
        # 1. 查找文档路径
        print("1. 查找文档路径...")
        paths = find_paths(test_docs[0]["id"], test_docs[4]["id"])
        assert isinstance(paths, list), "路径返回格式错误"
        
        # 2. 遍历文档关系
        print("\n2. 遍历文档关系...")
        # 测试不同方向的遍历
        outgoing = traverse_relations(test_docs[0]["id"], "outgoing", ["NEXT_STEP"])
        assert isinstance(outgoing, list), "出向关系返回格式错误"
        
        incoming = traverse_relations(test_docs[0]["id"], "incoming", ["NEXT_STEP"])
        assert isinstance(incoming, list), "入向关系返回格式错误"
        
        all_relations = traverse_relations(test_docs[0]["id"], "all", ["NEXT_STEP", "REFERENCES"])
        assert isinstance(all_relations, list), "所有关系返回格式错误"
        
    except Exception as e:
        print(f"\n错误: {str(e)}")
        raise 