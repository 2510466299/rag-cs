import requests
import json
import time

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

def search_documents(query: str):
    """搜索文档"""
    url = "http://localhost:8000/api/v1/documents/search/"
    headers = {"Content-Type": "application/json"}
    data = {
        "query": query,
        "limit": 5
    }
    
    response = requests.post(url, headers=headers, json=data)
    print(f"\n搜索文档响应 (查询: {query}):")
    print(json.dumps(response.json(), ensure_ascii=False, indent=2))

if __name__ == "__main__":
    print("=== API功能测试 ===")
    
    # 1. 创建多个测试文档
    docs = [
        {
            "title": "产品使用手册",
            "content": "本手册详细介绍了产品的使用方法，包括安装、配置和日常维护。请仔细阅读本手册以获得最佳使用体验。",
            "doc_type": "manual",
            "tags": ["使用手册", "产品文档", "入门指南"]
        },
        {
            "title": "常见问题解答",
            "content": "这里收集了用户最常遇到的问题和解决方案，包括账号管理、功能使用和故障排除等内容。",
            "doc_type": "faq",
            "tags": ["FAQ", "问题解答", "故障排除"]
        },
        {
            "title": "系统维护指南",
            "content": "本文档面向系统管理员，详细说明了系统维护的步骤和注意事项，包括备份、更新和性能优化。",
            "doc_type": "technical",
            "tags": ["系统维护", "技术文档", "管理员指南"]
        }
    ]
    
    for doc in docs:
        create_document(**doc)
        time.sleep(1)  # 添加延时以确保向量计算完成
    
    # 2. 测试不同的搜索查询
    queries = [
        "产品使用方法",
        "常见问题",
        "系统维护",
        "备份和更新",
        "账号管理"
    ]
    
    for query in queries:
        search_documents(query)
        time.sleep(1)  # 添加延时以避免请求过快 