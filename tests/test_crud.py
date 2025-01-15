import requests
import json
from typing import Dict

BASE_URL = "http://localhost:8000/api/v1"

def test_create_document() -> Dict:
    """测试创建文档"""
    print("\n=== 测试创建文档 ===")
    
    # 准备测试数据
    document = {
        "title": "产品使用手册",
        "content": "这是一份详细的产品使用说明，包含了产品的主要功能和操作步骤。",
        "doc_type": "manual",
        "tags": ["产品", "说明书", "使用指南"]
    }
    
    # 发送请求
    response = requests.post(f"{BASE_URL}/documents/", json=document)
    
    # 打印结果
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print("创建的文档:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return result
    else:
        print(f"错误: {response.text}")
        return None

def test_get_document(doc_id: str):
    """测试获取文档"""
    print("\n=== 测试获取文档 ===")
    
    # 发送请求
    response = requests.get(f"{BASE_URL}/documents/{doc_id}")
    
    # 打印结果
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print("获取的文档:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"错误: {response.text}")

def test_update_document(doc_id: str):
    """测试更新文档"""
    print("\n=== 测试更新文档 ===")
    
    # 准备更新数据
    updates = {
        "title": "产品使用手册 v2",
        "content": "这是更新后的产品使用说明，增加了更多详细内容和示例。",
        "tags": ["产品", "说明书", "使用指南", "v2"]
    }
    
    # 发送请求
    response = requests.put(f"{BASE_URL}/documents/{doc_id}", json=updates)
    
    # 打印结果
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print("更新后的文档:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"错误: {response.text}")

def test_search_documents():
    """测试文档搜索"""
    print("\n=== 测试文档搜索 ===")
    
    # 准备搜索查询
    query = {
        "query": "产品使用说明",
        "limit": 5
    }
    
    # 发送请求
    response = requests.post(f"{BASE_URL}/documents/search/", json=query)
    
    # 打印结果
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        results = response.json()
        print("搜索结果:")
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        print(f"错误: {response.text}")

def test_delete_document(doc_id: str):
    """测试删除文档"""
    print("\n=== 测试删除文档 ===")
    
    # 发送请求
    response = requests.delete(f"{BASE_URL}/documents/{doc_id}")
    
    # 打印结果
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print("删除结果:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"错误: {response.text}")

def run_tests():
    """运行所有测试"""
    # 创建文档并获取ID
    doc = test_create_document()
    if not doc:
        print("创建文档失败，终止测试")
        return
    
    doc_id = doc["id"]
    
    # 测试其他操作
    test_get_document(doc_id)
    test_update_document(doc_id)
    test_search_documents()
    test_delete_document(doc_id)
    
    print("\n所有测试完成!")

if __name__ == "__main__":
    run_tests() 