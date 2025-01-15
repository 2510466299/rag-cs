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

def search_documents(query: str, limit: int = 5) -> List[Dict]:
    """搜索文档"""
    url = f"{BASE_URL}/documents/search/"
    data = {
        "query": query,
        "limit": limit,
        "neo4j_uri": NEO4J_URI,
        "neo4j_user": NEO4J_USER,
        "neo4j_password": NEO4J_PASSWORD
    }
    response = requests.post(url, json=data)
    print(f"\n搜索文档响应 (查询: {query}):")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    
    if response.status_code != 200:
        raise Exception(f"搜索文档失败: {response.json()}")
    
    return response.json()

def clear_documents() -> bool:
    """清理所有文档"""
    url = f"{BASE_URL}/documents/clear"
    params = {
        "neo4j_uri": NEO4J_URI,
        "neo4j_user": NEO4J_USER,
        "neo4j_password": NEO4J_PASSWORD
    }
    response = requests.post(url, params=params)
    print("\n清理文档响应:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    return response.status_code == 200

@pytest.fixture(scope="module")
def test_docs():
    """创建测试文档的fixture"""
    print("\n=== 创建测试文档 ===\n")
    
    # 清理现有文档
    clear_documents()
    
    docs = [
        create_document(
            "Python编程入门",
            "本文介绍Python编程的基础知识，包括变量、数据类型、控制流等。",
            "tutorial",
            ["Python", "编程", "入门"]
        ),
        create_document(
            "Python高级特性",
            "深入讲解Python的高级特性，如装饰器、生成器、上下文管理器等。",
            "advanced",
            ["Python", "高级", "特性"]
        ),
        create_document(
            "数据结构与算法",
            "介绍常见的数据结构和算法，包括数组、链表、树、图等。",
            "algorithm",
            ["数据结构", "算法"]
        ),
        create_document(
            "机器学习基础",
            "机器学习的基本概念和算法，包括监督学习、无监督学习等。",
            "ml",
            ["机器学习", "AI"]
        ),
        create_document(
            "深度学习实战",
            "使用Python实现深度学习模型，包括CNN、RNN、Transformer等。",
            "dl",
            ["深度学习", "Python", "AI"]
        )
    ]
    yield docs

def test_semantic_search(test_docs):
    """测试语义相似度搜索"""
    print("\n=== 测试语义相似度搜索 ===\n")
    
    try:
        # 1. 搜索Python相关内容
        print("\n1. 搜索Python相关内容...")
        results = search_documents("如何学习Python编程？")
        assert len(results) > 0, "搜索结果为空"
        assert any("Python" in doc["title"] for doc in results), "未找到相关文档"
        
        # 2. 搜索AI相关内容
        print("\n2. 搜索AI相关内容...")
        results = search_documents("人工智能和机器学习的区别")
        assert len(results) > 0, "搜索结果为空"
        assert any("机器学习" in doc["title"] or "深度学习" in doc["title"] 
                  for doc in results), "未找到相关文档"
        
        # 3. 搜索算法相关内容
        print("\n3. 搜索算法相关内容...")
        results = search_documents("常用的数据结构有哪些？")
        assert len(results) > 0, "搜索结果为空"
        assert any("数据结构" in doc["title"] or "算法" in doc["content"] 
                  for doc in results), "未找到相关文档"
        
        # 4. 限制搜索结果数量
        print("\n4. 测试结果数量限制...")
        limit = 2
        results = search_documents("Python", limit=limit)
        assert len(results) <= limit, f"搜索结果超过限制 {limit}"
        
    except Exception as e:
        print(f"\n错误: {str(e)}")
        raise 