from typing import Dict, List, Optional, Set
from datetime import datetime
from neo4j import GraphDatabase
import logging
from uuid import uuid4
import json
import numpy as np

class DocumentStore:
    """文档存储服务，使用Neo4j管理文档及其关系"""
    
    def __init__(self, uri: str, username: str, password: str):
        """初始化Neo4j连接
        
        Args:
            uri: Neo4j数据库URI
            username: 用户名
            password: 密码
        """
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
        self._init_constraints()
        logging.info("Connected to Neo4j database")
    
    def _init_constraints(self):
        """初始化数据库约束"""
        with self.driver.session() as session:
            # 确保文档ID的唯一性
            session.run("""
                CREATE CONSTRAINT document_id IF NOT EXISTS
                FOR (d:Document) REQUIRE d.id IS UNIQUE
            """)
    
    def close(self):
        """关闭数据库连接"""
        self.driver.close()
    
    def create_document(self, title: str, content: str, doc_type: str,
                       embedding: List[float], tags: Optional[List[str]] = None) -> Dict:
        """创建新文档
        
        Args:
            title: 文档标题
            content: 文档内容
            doc_type: 文档类型
            embedding: 文档的向量表示
            tags: 文档标签列表
            
        Returns:
            新创建文档的信息
        """
        doc_id = str(uuid4())
        created_at = datetime.utcnow().isoformat()
        
        with self.driver.session() as session:
            # 使用参数化查询创建节点，分步设置属性以避免类型错误
            result = session.run("""
                CREATE (d:Document)
                SET d.id = $id,
                    d.title = $title,
                    d.content = $content,
                    d.type = $type,
                    d.tags = $tags,
                    d.created_at = $created_at,
                    d.updated_at = $created_at,
                    d.embedding = $embedding
                RETURN d
            """, {
                "id": doc_id,
                "title": title,
                "content": content,
                "type": doc_type,
                "tags": tags or [],
                "created_at": created_at,
                "embedding": json.dumps(embedding)
            })
            
            record = result.single()
            if record:
                doc = record["d"]
                return {
                    "id": doc["id"],
                    "title": doc["title"],
                    "content": doc["content"],
                    "type": doc["type"],
                    "tags": doc["tags"],
                    "created_at": doc["created_at"],
                    "updated_at": doc["updated_at"],
                    "embedding": json.loads(doc["embedding"])
                }
            else:
                raise Exception("Failed to create document")
    
    def get_document(self, doc_id: str) -> Optional[Dict]:
        """获取文档信息
        
        Args:
            doc_id: 文档ID
            
        Returns:
            文档信息字典，如果文档不存在则返回None
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (d:Document {id: $id})
                RETURN d
            """, id=doc_id)
            
            record = result.single()
            if record:
                doc = record["d"]
                return {
                    "id": doc["id"],
                    "title": doc["title"],
                    "content": doc["content"],
                    "type": doc["type"],
                    "embedding": json.loads(doc["embedding"]),
                    "tags": doc["tags"],
                    "created_at": doc["created_at"],
                    "updated_at": doc["updated_at"]
                }
        return None
    
    def update_document(self, doc_id: str, **updates) -> bool:
        """更新文档信息
        
        Args:
            doc_id: 文档ID
            **updates: 要更新的字段
            
        Returns:
            更新是否成功
        """
        updates["updated_at"] = datetime.utcnow().isoformat()
        
        # 如果更新包含embedding，将其转换为JSON字符串，确保使用UTF-8编码
        if "embedding" in updates:
            updates["embedding"] = json.dumps(updates["embedding"], ensure_ascii=False)
        
        with self.driver.session() as session:
            result = session.run("""
                MATCH (d:Document {id: $id})
                SET d += $updates
                RETURN d
            """, id=doc_id, updates=updates)
            
            return result.single() is not None
    
    def delete_document(self, doc_id: str) -> bool:
        """删除文档
        
        Args:
            doc_id: 文档ID
            
        Returns:
            删除是否成功
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (d:Document {id: $id})
                DELETE d
                RETURN count(d) as count
            """, id=doc_id)
            
            return result.single()["count"] > 0
    
    def create_relation(self, doc_id1: str, doc_id2: str, relation_type: str,
                       properties: Optional[Dict] = None) -> bool:
        """创建文档间的关系
        
        Args:
            doc_id1: 第一个文档ID
            doc_id2: 第二个文档ID
            relation_type: 关系类型
            properties: 关系属性
            
        Returns:
            创建是否成功
        """
        # 使用参数化查询的替代方案
        query = f"""
            MATCH (d1:Document {{id: $id1}})
            MATCH (d2:Document {{id: $id2}})
            MERGE (d1)-[r:{relation_type}]->(d2)
            SET r += $properties
            RETURN r
        """
        
        with self.driver.session() as session:
            result = session.run(
                query,
                id1=doc_id1,
                id2=doc_id2,
                properties=properties or {}
            )
            
            return result.single() is not None
            
    def get_document_relations(self, doc_id: str, relation_type: Optional[str] = None,
                             direction: str = "all") -> List[Dict]:
        """获取文档的关系
        
        Args:
            doc_id: 文档ID
            relation_type: 关系类型（可选）
            direction: 关系方向 (incoming/outgoing/all)
            
        Returns:
            关系列表
        """
        with self.driver.session() as session:
            # 构建查询
            if direction == "incoming":
                match_clause = "MATCH (d2:Document)-[r]->(d1:Document {id: $id})"
            elif direction == "outgoing":
                match_clause = "MATCH (d1:Document {id: $id})-[r]->(d2:Document)"
            else:  # all
                match_clause = """
                    MATCH (d1:Document {id: $id})
                    MATCH (d2:Document)
                    MATCH (d1)-[r]-(d2)
                """
            
            # 添加关系类型过滤
            where_clause = "WHERE type(r) = $relation_type" if relation_type else ""
            
            # 完整查询
            query = f"""
                {match_clause}
                {where_clause}
                RETURN d1, d2, r, type(r) as relation_type
            """
            
            result = session.run(query, id=doc_id, relation_type=relation_type)
            
            relations = []
            for record in result:
                d1, d2, r, rel_type = record["d1"], record["d2"], record["r"], record["relation_type"]
                relation = {
                    "source_id": d1["id"],
                    "source_title": d1["title"],
                    "target_id": d2["id"],
                    "target_title": d2["title"],
                    "relation_type": rel_type,
                    "properties": dict(r)
                }
                relations.append(relation)
            
            return relations
            
    def delete_relation(self, doc_id1: str, doc_id2: str, relation_type: str) -> bool:
        """删除文档关系"""
        with self.driver.session() as session:
            # 使用参数化查询，但关系类型需要直接嵌入查询字符串
            query = f"""
            MATCH (d1:Document {{id: $id1}})-[r:{relation_type}]->(d2:Document {{id: $id2}})
            DELETE r
            RETURN count(r) as deleted_count
            """
            
            result = session.run(
                query,
                id1=doc_id1,
                id2=doc_id2
            )
            
            return result.single()["deleted_count"] > 0
            
    def get_related_documents(self, doc_id: str, relation_type: Optional[str] = None,
                            max_depth: int = 2) -> List[Dict]:
        """获取相关文档（包括直接和间接关系）
        
        Args:
            doc_id: 文档ID
            relation_type: 关系类型（可选）
            max_depth: 最大关系深度
            
        Returns:
            相关文档列表，包含关系路径信息
        """
        with self.driver.session() as session:
            # 构建关系类型过滤
            rel_filter = f":{relation_type}" if relation_type else ""
            
            # 使用可变长度路径查询
            result = session.run(f"""
                MATCH path = (d1:Document {{id: $id}})-[r{rel_filter}*1..{max_depth}]-(d2:Document)
                WHERE d2.id <> $id
                RETURN d2, [rel in relationships(path) | type(rel)] as relation_types,
                       length(path) as distance
                ORDER BY distance
            """, id=doc_id)
            
            related_docs = []
            for record in result:
                doc = record["d2"]
                related_docs.append({
                    "id": doc["id"],
                    "title": doc["title"],
                    "content": doc["content"],
                    "type": doc["type"],
                    "tags": doc["tags"],
                    "relation_types": record["relation_types"],
                    "distance": record["distance"]
                })
            
            return related_docs
    
    def find_similar_documents(self, embedding: List[float], limit: int = 5) -> List[Dict]:
        """查找与给定向量最相似的文档
        
        Args:
            embedding: 查询向量（浮点数列表）
            limit: 返回结果数量
            
        Returns:
            相似文档列表，按相似度降序排序
        """
        # 将查询向量转换为numpy数组并确保是一维的
        query_embedding = np.array(embedding).flatten()
        
        with self.driver.session() as session:
            # 获取所有文档，按创建时间降序排序
            result = session.run("""
                MATCH (d:Document)
                RETURN d
                ORDER BY d.created_at DESC
            """)
            
            # 在Python中计算相似度
            documents = []
            for record in result:
                doc = record["d"]
                try:
                    # 确保文档向量也是一维的
                    doc_embedding = np.array(json.loads(doc["embedding"])).flatten()
                    
                    # 计算余弦相似度
                    dot_product = np.dot(query_embedding, doc_embedding)
                    query_norm = np.linalg.norm(query_embedding)
                    doc_norm = np.linalg.norm(doc_embedding)
                    similarity = dot_product / (query_norm * doc_norm) if query_norm * doc_norm != 0 else 0
                    
                    documents.append({
                        "id": doc["id"],
                        "title": doc["title"],
                        "content": doc["content"],
                        "type": doc["type"],
                        "tags": doc["tags"],
                        "created_at": doc["created_at"],
                        "updated_at": doc["updated_at"],
                        "similarity": float(similarity)
                    })
                except (KeyError, json.JSONDecodeError, TypeError) as e:
                    logging.error(f"Error processing document {doc['id']}: {str(e)}")
                    continue
            
            # 按相似度排序并返回前limit个结果
            documents.sort(key=lambda x: x["similarity"], reverse=True)
            return documents[:limit]
    
    def find_paths(self, start_id: str, end_id: str,
                  relation_types: Optional[List[str]] = None,
                  max_depth: int = 5) -> List[Dict]:
        """查找两个文档之间的路径
        
        Args:
            start_id: 起始文档ID
            end_id: 目标文档ID
            relation_types: 关系类型列表
            max_depth: 最大路径长度
            
        Returns:
            路径列表
        """
        with self.driver.session() as session:
            # 构建关系类型过滤
            rel_type_filter = ""
            if relation_types:
                rel_type_filter = f"WHERE ALL(r IN relationships(p) WHERE type(r) IN {relation_types})"
            
            # 查询路径
            query = f"""
                MATCH p = shortestPath((d1:Document {{id: $start_id}})-[*..{max_depth}]-(d2:Document {{id: $end_id}}))
                {rel_type_filter}
                RETURN p
            """
            
            result = session.run(query, start_id=start_id, end_id=end_id)
            
            paths = []
            for record in result:
                path = record["p"]
                path_info = {
                    "nodes": [],
                    "relationships": []
                }
                
                # 添加节点信息
                for node in path.nodes:
                    node_info = dict(node)
                    node_info["embedding"] = json.loads(node_info["embedding"])
                    path_info["nodes"].append(node_info)
                
                # 添加关系信息
                for rel in path.relationships:
                    rel_info = {
                        "source_id": rel.start_node["id"],
                        "target_id": rel.end_node["id"],
                        "type": rel.type,
                        "properties": dict(rel)
                    }
                    path_info["relationships"].append(rel_info)
                
                paths.append(path_info)
            
            return paths
    
    def traverse_relations(self, doc_id: str, direction: str = "all",
                         relation_types: Optional[List[str]] = None,
                         max_depth: int = 3) -> List[Dict]:
        """遍历文档关系
        
        Args:
            doc_id: 文档ID
            direction: 遍历方向 (outgoing/incoming/all)
            relation_types: 关系类型列表
            max_depth: 最大遍历深度
            
        Returns:
            关系列表
        """
        with self.driver.session() as session:
            # 构建方向和关系类型过滤
            if direction.lower() == "outgoing":
                direction_pattern = "-[r]->"
            elif direction.lower() == "incoming":
                direction_pattern = "<-[r]-"
            else:  # all
                direction_pattern = "-[r]-"
            
            rel_type_filter = ""
            if relation_types:
                rel_type_filter = f"WHERE type(r) IN {relation_types}"
            
            # 查询关系
            query = f"""
                MATCH (d1:Document {{id: $doc_id}})
                MATCH (d1){direction_pattern}(d2:Document)
                {rel_type_filter}
                RETURN d1, d2, r, type(r) as relation_type
            """
            
            result = session.run(query, doc_id=doc_id)
            
            relations = []
            for record in result:
                d1, d2, r, rel_type = record["d1"], record["d2"], record["r"], record["relation_type"]
                relation = {
                    "source_id": d1["id"],
                    "source_title": d1["title"],
                    "target_id": d2["id"],
                    "target_title": d2["title"],
                    "relation_type": rel_type,
                    "properties": dict(r)
                }
                relations.append(relation)
            
            return relations 
    
    def clear_all_documents(self) -> bool:
        """清理数据库中的所有文档
        
        Returns:
            是否成功清理
        """
        with self.driver.session() as session:
            try:
                # 删除所有文档及其关系
                result = session.run("""
                    MATCH (d:Document)
                    DETACH DELETE d
                    RETURN count(d) as count
                """)
                return result.single()["count"] > 0
            except Exception as e:
                logging.error(f"Error clearing documents: {str(e)}")
                return False 