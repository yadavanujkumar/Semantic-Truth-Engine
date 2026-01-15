"""Neo4j database connection and operations."""
from typing import List, Dict, Any, Optional
from neo4j import GraphDatabase
from src.config import config
import logging

logger = logging.getLogger(__name__)


class Neo4jConnection:
    """Neo4j database connection manager."""
    
    def __init__(self, uri: str = None, user: str = None, password: str = None):
        """Initialize Neo4j connection."""
        self.uri = uri or config.neo4j_uri
        self.user = user or config.neo4j_username
        self.password = password or config.neo4j_password
        self.driver = None
        
    def connect(self):
        """Establish connection to Neo4j."""
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
            logger.info("Successfully connected to Neo4j")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise
    
    def close(self):
        """Close the Neo4j connection."""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")
    
    def execute_query(self, query: str, parameters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Execute a Cypher query and return results."""
        if not self.driver:
            self.connect()
        
        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]
    
    def create_node(self, label: str, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Create a node in the graph."""
        props_str = ", ".join([f"{k}: ${k}" for k in properties.keys()])
        query = f"CREATE (n:{label} {{{props_str}}}) RETURN n"
        return self.execute_query(query, properties)
    
    def create_relationship(self, from_node_id: str, to_node_id: str, 
                          relationship_type: str, properties: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create a relationship between two nodes."""
        props = properties or {}
        props_str = ", ".join([f"{k}: ${k}" for k in props.keys()]) if props else ""
        
        query = f"""
        MATCH (a), (b)
        WHERE id(a) = $from_id AND id(b) = $to_id
        CREATE (a)-[r:{relationship_type} {{{props_str}}}]->(b)
        RETURN r
        """
        params = {"from_id": from_node_id, "to_id": to_node_id, **props}
        return self.execute_query(query, params)
    
    def find_path(self, start_node_id: str, end_node_id: str, max_depth: int = 5) -> List[Dict[str, Any]]:
        """Find paths between two nodes."""
        query = """
        MATCH path = shortestPath((start)-[*..%d]-(end))
        WHERE id(start) = $start_id AND id(end) = $end_id
        RETURN path
        """ % max_depth
        return self.execute_query(query, {"start_id": start_node_id, "end_id": end_node_id})
    
    def get_subgraph(self, node_ids: List[str], depth: int = 2) -> Dict[str, Any]:
        """Get a subgraph around specified nodes."""
        query = """
        MATCH (n)
        WHERE id(n) IN $node_ids
        CALL apoc.path.subgraphAll(n, {maxLevel: $depth})
        YIELD nodes, relationships
        RETURN nodes, relationships
        """
        return self.execute_query(query, {"node_ids": node_ids, "depth": depth})
    
    def search_nodes(self, label: str = None, property_name: str = None, 
                    property_value: Any = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for nodes matching criteria."""
        label_clause = f":{label}" if label else ""
        where_clause = f"WHERE n.{property_name} CONTAINS $value" if property_name and property_value else ""
        
        query = f"""
        MATCH (n{label_clause})
        {where_clause}
        RETURN n
        LIMIT $limit
        """
        params = {"limit": limit}
        if property_value:
            params["value"] = property_value
        
        return self.execute_query(query, params)
    
    def clear_database(self):
        """Clear all nodes and relationships (use with caution!)."""
        query = "MATCH (n) DETACH DELETE n"
        self.execute_query(query)
        logger.warning("Database cleared")
    
    def create_indexes(self):
        """Create useful indexes for the knowledge graph."""
        indexes = [
            "CREATE INDEX entity_name IF NOT EXISTS FOR (n:Entity) ON (n.name)",
            "CREATE INDEX entity_type IF NOT EXISTS FOR (n:Entity) ON (n.type)",
            "CREATE INDEX document_title IF NOT EXISTS FOR (n:Document) ON (n.title)",
        ]
        for index_query in indexes:
            try:
                self.execute_query(index_query)
                logger.info(f"Created index: {index_query}")
            except Exception as e:
                logger.warning(f"Index creation failed or already exists: {e}")


# Global Neo4j connection instance
neo4j_conn = Neo4jConnection()
