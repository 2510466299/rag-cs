import requests
import json
import time
from typing import Dict, List, Optional

def create_document(title: str, content: str, doc_type: str, tags: list):
    """创建文档"""
    url = "http://localhost:8000/api/v1/documents/"
    headers = {"Content-Type": "application/json"}
    data = {
        "title": title,
        "content": content,
        "doc_type": doc_type,
        "tags": tags
    }
    
    response = requests.post(url, headers=headers, json=data)
    print(f"\n创建文档 '{title}' 响应:")
    print(json.dumps(response.json(), ensure_ascii=False, indent=2))
    return response.json()["id"]

def create_relation(source_id: str, target_id: str, relation_type: str, properties: Dict = None):
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

def get_document_relations(doc_id: str, relation_type: str = None, direction: str = "all"):
    """获取文档关系"""
    params = {"relation_type": relation_type, "direction": direction}
    url = f"http://localhost:8000/api/v1/documents/{doc_id}/relations/"
    
    response = requests.get(url, params=params)
    print(f"\n获取文档关系响应 (文档ID: {doc_id}):")
    print(json.dumps(response.json(), ensure_ascii=False, indent=2))
    return response.json()

if __name__ == "__main__":
    print("=== 文档关系管理测试 ===")
    
    # 1. 创建测试文档
    docs = [
        {
            "title": "产品功能概述",
            "content": "本文档提供产品的核心功能和特性说明。",
            "doc_type": "overview",
            "tags": ["产品", "功能", "概述"]
        },
        {
            "title": "快速入门指南",
            "content": "帮助新用户快速上手的入门指南。",
            "doc_type": "guide",
            "tags": ["入门", "指南"]
        },
        {
            "title": "系统要求",
            "content": "详细的系统要求和环境配置说明。",
            "doc_type": "requirements",
            "tags": ["系统", "配置"]
        },
        {
            "title": "高级功能教程",
            "content": "面向专业用户的高级功能使用说明。",
            "doc_type": "tutorial",
            "tags": ["高级", "教程"]
        },
        {
            "title": "常见问题解答",
            "content": "用户最常遇到的问题和解决方案。",
            "doc_type": "faq",
            "tags": ["FAQ", "问题"]
        }
    ]
    
    print("\n1. 创建测试文档...")
    doc_ids = []
    for doc in docs:
        doc_id = create_document(**doc)
        doc_ids.append(doc_id)
        time.sleep(1)
    
    # 2. 创建文档关系
    print("\n2. 创建文档关系...")
    relations = [
        {
            "source_id": doc_ids[0],  # 产品功能概述 -> 快速入门指南
            "target_id": doc_ids[1],
            "relation_type": "NEXT_STEP",
            "properties": {
                "order": 1,
                "description": "基础入门"
            }
        },
        {
            "source_id": doc_ids[2],  # 系统要求 -> 快速入门指南
            "target_id": doc_ids[1],
            "relation_type": "PREREQUISITE",
            "properties": {
                "importance": "high",
                "description": "安装前必读"
            }
        },
        {
            "source_id": doc_ids[1],  # 快速入门指南 -> 高级功能教程
            "target_id": doc_ids[3],
            "relation_type": "PARENT_OF",
            "properties": {
                "category": "tutorials"
            }
        },
        {
            "source_id": doc_ids[3],  # 高级功能教程 -> FAQ
            "target_id": doc_ids[4],
            "relation_type": "REFERENCES",
            "properties": {
                "section": "troubleshooting",
                "description": "常见问题参考"
            }
        },
        {
            "source_id": doc_ids[0],  # 产品功能概述 <-> 高级功能教程
            "target_id": doc_ids[3],
            "relation_type": "RELATED_TO",
            "properties": {
                "type": "functionality",
                "description": "功能详解"
            }
        }
    ]
    
    for relation in relations:
        create_relation(**relation)
        time.sleep(1)
    
    # 3. 测试关系查询
    print("\n3. 测试关系查询...")
    
    # 3.1 查询所有关系
    get_document_relations(doc_ids[0])
    
    # 3.2 查询特定类型的关系
    get_document_relations(doc_ids[1], relation_type="PARENT_OF")
    
    # 3.3 查询入向关系
    get_document_relations(doc_ids[4], direction="incoming")
    
    # 3.4 查询双向关系
    get_document_relations(doc_ids[3], relation_type="RELATED_TO")
    
    print("\n测试完成!") 