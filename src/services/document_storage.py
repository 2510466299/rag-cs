from typing import Dict, List, Optional, Set
from fastapi import HTTPException
from neo4j.exceptions import ServiceUnavailable

class DocumentStorage:
    def get_document(self, doc_id: str) -> Optional[Dict]:
        """
        获取文档
        
        Args:
            doc_id: 文档ID
        
        Returns:
            Optional[Dict]: 文档信息，如果不存在则返回 None
        """
        query = """
            MATCH (d:Document {id: $doc_id})
            RETURN d.id as id,
                   d.title as title,
                   d.content as content,
                   d.type as type,
                   d.tags as tags,
                   d.created_at as created_at,
                   d.updated_at as updated_at
        """
        
        try:
            with self.driver.session() as session:
                result = session.run(query, doc_id=doc_id)
                record = result.single()
                
                if not record:
                    return None
                    
                return {
                    'id': record['id'],
                    'title': record['title'],
                    'content': record['content'],
                    'type': record['type'],
                    'tags': record['tags'],
                    'created_at': record['created_at'],
                    'updated_at': record['updated_at']
                }
                
        except Exception as e:
            logger.error(f"Error getting document: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=str(e)
            )

    def traverse_relations(self, start_id: str, relation_types: Optional[Set[str]] = None,
                          direction: str = "OUTGOING", max_depth: int = 3,
                          exclude_types: Optional[Set[str]] = None) -> Dict:
        """
        遍历文档关系图
        
        Args:
            start_id: 起始文档ID
            relation_types: 要遍历的关系类型集合
            direction: 遍历方向，可选值：OUTGOING（出边）, INCOMING（入边）, ALL（所有）
            max_depth: 最大遍历深度
            exclude_types: 要排除的关系类型集合
        
        Returns:
            Dict: 遍历结果，按深度组织的文档和关系信息
        """
        # 构建关系类型过滤条件
        type_conditions = []
        if relation_types:
            type_conditions.append(f"type(r) IN {list(relation_types)}")
        if exclude_types:
            type_conditions.append(f"NOT type(r) IN {list(exclude_types)}")
        
        type_filter = ""
        if type_conditions:
            type_filter = "WHERE " + " AND ".join(type_conditions)
        
        # 根据方向构建箭头
        if direction == "OUTGOING":
            arrow = "-[r]->"
        elif direction == "INCOMING":
            arrow = "<-[r]-"
        else:  # ALL
            arrow = "-[r]-"
        
        query = f"""
            MATCH (start:Document {{id: $start_id}})
            OPTIONAL MATCH path = (start){arrow}(related:Document)
            {type_filter}
            WITH related, path
            WHERE related IS NOT NULL
              AND length(path) <= $max_depth
            RETURN related.id as id,
                   related.title as title,
                   length(path) as depth,
                   [r in relationships(path) | type(r)] as relation_types,
                   [r in relationships(path) | r.properties] as properties
            ORDER BY depth
        """
        
        try:
            with self.driver.session() as session:
                result = session.run(query, 
                                   start_id=start_id,
                                   max_depth=max_depth)
                records = result.data()
                
                # 按深度组织结果
                traversal_result = {}
                for record in records:
                    depth = record['depth']
                    if depth not in traversal_result:
                        traversal_result[depth] = []
                    traversal_result[depth].append({
                        'id': record['id'],
                        'title': record['title'],
                        'relation_types': record['relation_types'],
                        'properties': record['properties']
                    })
                
                return traversal_result
                
        except Exception as e:
            logger.error(f"Error traversing relations: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=str(e)
            )

    def find_paths(self, start_id: str, end_id: str,
                   relation_types: Optional[Set[str]] = None,
                   max_depth: int = 5) -> List[Dict]:
        """
        查找两个文档之间的所有路径
        
        Args:
            start_id: 起始文档ID
            end_id: 目标文档ID
            relation_types: 要考虑的关系类型集合
            max_depth: 最大路径长度
        
        Returns:
            List[Dict]: 路径列表，每个路径包含节点和关系信息
        """
        # 构建关系类型过滤条件
        type_filter = ""
        if relation_types:
            type_filter = f"WHERE ALL(r in relationships(p) WHERE type(r) IN {list(relation_types)})"
        
        query = f"""
            MATCH (start:Document {{id: $start_id}}),
                  (end:Document {{id: $end_id}})
            OPTIONAL MATCH p = (start)-[*1..{max_depth}]-(end)
            {type_filter}
            WITH p, length(p) as path_length
            WHERE p IS NOT NULL
            ORDER BY path_length
            LIMIT 10
            RETURN [n in nodes(p) | n.id] as node_ids,
                   [n in nodes(p) | n.title] as node_titles,
                   [r in relationships(p) | type(r)] as relation_types,
                   [r in relationships(p) | r.properties] as properties,
                   path_length
        """
        
        try:
            with self.driver.session() as session:
                result = session.run(query,
                                   start_id=start_id,
                                   end_id=end_id)
                records = result.data()
                
                if not records:
                    return []
                
                paths = []
                for record in records:
                    path = {
                        'nodes': [
                            {'id': node_id, 'title': title}
                            for node_id, title in zip(record['node_ids'],
                                                    record['node_titles'])
                        ],
                        'relations': [
                            {
                                'type': rel_type,
                                'properties': props
                            }
                            for rel_type, props in zip(record['relation_types'],
                                                     record['properties'])
                        ],
                        'length': record['path_length']
                    }
                    paths.append(path)
                
                return paths
                
        except Exception as e:
            logger.error(f"Error finding paths: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=str(e)
            ) 