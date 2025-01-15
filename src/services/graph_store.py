from neo4j import GraphDatabase, Driver
from typing import Dict, List, Any, Optional
from config.config import settings
from loguru import logger
import json

class GraphStore:
    """图数据库服务，用于管理文档之间的关系"""
    
    def __init__(self):
        """初始化Neo4j数据库连接"""
        try:
            # 创建Neo4j数据库连接
            self.driver = GraphDatabase.driver(
                settings.NEO4J_URI,                              # 数据库URI
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)  # 认证信息
            )
            # 验证数据库连接是否正常
            self.driver.verify_connectivity()
            logger.info("Neo4j connection established successfully")
        except Exception as e:
            logger.error(f"Error connecting to Neo4j: {str(e)}")
            raise

    def close(self):
        """关闭数据库连接，释放资源"""
        self.driver.close()

    async def create_document_node(
        self,
        document_id: str,
        properties: Dict[str, Any]
    ) -> None:
        """
        在图数据库中创建文档节点
        
        Args:
            document_id: 文档唯一标识符
            properties: 节点属性（标题、类型、创建时间等）
        """
        try:
            # 创建会话并执行写入操作
            with self.driver.session() as session:
                session.execute_write(self._create_document_node, document_id, properties)
            logger.info(f"Document node {document_id} created successfully")
        except Exception as e:
            logger.error(f"Error creating document node: {str(e)}")
            raise

    @staticmethod
    def _create_document_node(tx, document_id: str, properties: Dict[str, Any]):
        """
        创建文档节点的Cypher查询执行函数
        
        Args:
            tx: 数据库事务对象
            document_id: 文档ID
            properties: 节点属性
        """
        # 确保所有属性值都是基本类型
        node_props = {
            "id": document_id,
            "title": str(properties.get("title", "")),
            "type": str(properties.get("type", "")),
            "content": str(properties.get("content", "")),
            "tags": list(map(str, properties.get("tags", []))),
            "created_at": str(properties.get("created_at", "")),
            "updated_at": str(properties.get("updated_at", ""))
        }
        
        # 如果有embedding，将其转换为字符串
        if "embedding" in properties:
            node_props["embedding"] = json.dumps(properties["embedding"])
        
        # 构建创建节点的Cypher查询
        query = """
        CREATE (d:Document)
        SET d = $props
        """
        
        # 执行查询
        tx.run(query, props=node_props)

    async def create_relationship(
        self,
        from_id: str,
        to_id: str,
        relationship_type: str,
        properties: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        创建两个文档节点之间的关系
        
        Args:
            from_id: 起始文档ID
            to_id: 目标文档ID
            relationship_type: 关系类型（如：RELATED_TO, REFERENCES等）
            properties: 关系的属性（可选）
        """
        try:
            # 创建会话并执行写入操作
            with self.driver.session() as session:
                session.execute_write(
                    self._create_relationship,
                    from_id,
                    to_id,
                    relationship_type,
                    properties or {}
                )
            logger.info(f"Relationship created between {from_id} and {to_id}")
        except Exception as e:
            logger.error(f"Error creating relationship: {str(e)}")
            raise

    @staticmethod
    def _create_relationship(
        tx,
        from_id: str,
        to_id: str,
        relationship_type: str,
        properties: Dict[str, Any]
    ):
        """
        创建关系的Cypher查询执行函数
        
        Args:
            tx: 数据库事务对象
            from_id: 起始文档ID
            to_id: 目标文档ID
            relationship_type: 关系类型
            properties: 关系属性
        """
        # 构建创建关系的Cypher查询
        query = f"""
        MATCH (from:Document {{id: $from_id}})
        MATCH (to:Document {{id: $to_id}})
        CREATE (from)-[r:{relationship_type} $properties]->(to)
        """
        # 执行查询
        tx.run(query, from_id=from_id, to_id=to_id, properties=properties)

    async def find_related_documents(
        self,
        document_id: str,
        relationship_type: Optional[str] = None,
        max_depth: int = 2
    ) -> List[Dict[str, Any]]:
        """
        查找与指定文档相关的其他文档
        
        Args:
            document_id: 起始文档ID
            relationship_type: 指定的关系类型（可选）
            max_depth: 最大搜索深度（图的遍历层数）
            
        Returns:
            相关文档列表，包含文档信息和与起始文档的距离
        """
        try:
            # 创建会话并执行读取操作
            with self.driver.session() as session:
                result = session.execute_read(
                    self._find_related_documents,
                    document_id,
                    relationship_type,
                    max_depth
                )
            return result
        except Exception as e:
            logger.error(f"Error finding related documents: {str(e)}")
            raise

    @staticmethod
    def _find_related_documents(
        tx,
        document_id: str,
        relationship_type: Optional[str],
        max_depth: int
    ) -> List[Dict[str, Any]]:
        """
        查找相关文档的Cypher查询执行函数
        
        Args:
            tx: 数据库事务对象
            document_id: 文档ID
            relationship_type: 关系类型
            max_depth: 最大搜索深度
            
        Returns:
            相关文档列表
        """
        # 构建关系类型条件
        rel_type = f":{relationship_type}" if relationship_type else ""
        # 构建查询相关文档的Cypher查询
        query = f"""
        MATCH (start:Document {{id: $document_id}})
        MATCH path = (start)-[{rel_type}*1..{max_depth}]-(related:Document)
        RETURN DISTINCT related, length(path) as distance
        ORDER BY distance
        """
        # 执行查询并格式化结果
        result = tx.run(query, document_id=document_id)
        return [dict(record["related"].items()) for record in result]

    async def delete_document_node(self, document_id: str) -> None:
        """
        删除文档节点及其所有关系
        
        Args:
            document_id: 要删除的文档ID
        """
        try:
            # 创建会话并执行删除操作
            with self.driver.session() as session:
                session.execute_write(self._delete_document_node, document_id)
            logger.info(f"Document node {document_id} deleted successfully")
        except Exception as e:
            logger.error(f"Error deleting document node: {str(e)}")
            raise

    @staticmethod
    def _delete_document_node(tx, document_id: str):
        """
        删除文档节点的Cypher查询执行函数
        
        Args:
            tx: 数据库事务对象
            document_id: 文档ID
        """
        # 构建删除节点的Cypher查询（DETACH DELETE会同时删除节点的所有关系）
        query = """
        MATCH (d:Document {id: $document_id})
        DETACH DELETE d
        """
        # 执行查询
        tx.run(query, document_id=document_id) 

    async def traverse_relations(
        self,
        document_id: str,
        direction: str = "ALL",
        relation_types: Optional[List[str]] = None,
        max_depth: int = 3
    ) -> List[Dict[str, Any]]:
        """
        遍历文档关系
        
        Args:
            document_id: 起始文档ID
            direction: 遍历方向 (OUTGOING/INCOMING/ALL)
            relation_types: 指定的关系类型列表
            max_depth: 最大遍历深度
            
        Returns:
            相关文档和关系的列表
        """
        try:
            with self.driver.session() as session:
                result = session.execute_read(
                    self._traverse_relations,
                    document_id,
                    direction,
                    relation_types,
                    max_depth
                )
            return result
        except Exception as e:
            logger.error(f"Error traversing relations: {str(e)}")
            raise

    @staticmethod
    def _traverse_relations(
        tx,
        document_id: str,
        direction: str,
        relation_types: Optional[List[str]],
        max_depth: int
    ) -> List[Dict[str, Any]]:
        """遍历关系的Cypher查询执行函数"""
        # 构建关系类型条件
        rel_type = ""
        if relation_types:
            rel_type = f":{' | '.join(relation_types)}"

        # 根据方向构建查询
        direction_pattern = {
            "OUTGOING": "()-[r{}]->",
            "INCOMING": "<-[r{}]-",
            "ALL": "-[r{}]-"
        }.get(direction, "-[r{}]-")
        
        direction_pattern = direction_pattern.format(rel_type)

        # 构建查询
        query = f"""
        MATCH (start:Document {{id: $document_id}})
        MATCH path = (start){direction_pattern}(related:Document)
        WHERE length(path) <= $max_depth
        RETURN DISTINCT related, r, length(path) as distance
        ORDER BY distance
        """
        
        result = tx.run(query, document_id=document_id, max_depth=max_depth)
        return [{
            "document": dict(record["related"].items()),
            "relation": dict(record["r"].items()),
            "distance": record["distance"]
        } for record in result]

    async def find_paths(
        self,
        start_id: str,
        end_id: str,
        relation_types: Optional[List[str]] = None,
        max_depth: int = 5
    ) -> List[Dict[str, Any]]:
        """
        查找两个文档之间的所有路径
        
        Args:
            start_id: 起始文档ID
            end_id: 目标文档ID
            relation_types: 指定的关系类型列表
            max_depth: 最大路径长度
            
        Returns:
            路径列表，每个路径包含节点和关系信息
        """
        try:
            with self.driver.session() as session:
                result = session.execute_read(
                    self._find_paths,
                    start_id,
                    end_id,
                    relation_types,
                    max_depth
                )
            return result
        except Exception as e:
            logger.error(f"Error finding paths: {str(e)}")
            raise

    @staticmethod
    def _find_paths(
        tx,
        start_id: str,
        end_id: str,
        relation_types: Optional[List[str]],
        max_depth: int
    ) -> List[Dict[str, Any]]:
        """查找路径的Cypher查询执行函数"""
        # 构建关系类型条件
        rel_type = ""
        if relation_types:
            rel_type = f":{' | '.join(relation_types)}"

        # 构建查询
        query = f"""
        MATCH (start:Document {{id: $start_id}}), (end:Document {{id: $end_id}})
        MATCH path = (start)-[r{rel_type}*..{max_depth}]->(end)
        RETURN path,
               [node in nodes(path) | node {{.*}}] as nodes,
               [rel in relationships(path) | rel {{.*}}] as relations,
               length(path) as distance
        ORDER BY distance
        """
        
        result = tx.run(
            query,
            start_id=start_id,
            end_id=end_id
        )
        
        paths = []
        for record in result:
            paths.append({
                "nodes": record["nodes"],
                "relations": record["relations"],
                "distance": record["distance"]
            })
        return paths 