from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable

def test_connection():
    # Neo4j连接参数
    uri = "bolt://localhost:7687"
    user = "neo4j"
    password = "yunjipassword"
    
    try:
        # 创建驱动实例
        driver = GraphDatabase.driver(uri, auth=(user, password))
        
        # 验证连接
        driver.verify_connectivity()
        
        print("✅ 成功连接到Neo4j数据库!")
        
        # 获取数据库版本
        with driver.session() as session:
            result = session.run("CALL dbms.components() YIELD name, versions, edition")
            record = result.single()
            print(f"数据库版本信息：")
            print(f"- 名称: {record['name']}")
            print(f"- 版本: {record['versions'][0]}")
            print(f"- 版本类型: {record['edition']}")
            
        driver.close()
        
    except ServiceUnavailable as e:
        print("❌ 无法连接到Neo4j数据库!")
        print(f"错误信息: {str(e)}")
    except Exception as e:
        print("❌ 发生错误!")
        print(f"错误信息: {str(e)}")

if __name__ == "__main__":
    test_connection() 