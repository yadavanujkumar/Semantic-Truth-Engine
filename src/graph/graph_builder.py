"""Graph builder for storing extracted entities and relationships."""
from typing import Dict, Any, List
import logging
from src.graph.neo4j_manager import Neo4jConnection
from src.pipeline.entity_extractor import GraphExtraction, Entity, Relationship

logger = logging.getLogger(__name__)


class GraphBuilder:
    """Build and populate the knowledge graph in Neo4j."""
    
    def __init__(self, neo4j_conn: Neo4jConnection):
        """Initialize graph builder."""
        self.neo4j_conn = neo4j_conn
        self.entity_id_map = {}  # Map entity names to Neo4j IDs
        
    def build_graph(self, extraction: GraphExtraction, source_document: str = None) -> Dict[str, Any]:
        """Build graph from extracted entities and relationships."""
        if not self.neo4j_conn.driver:
            self.neo4j_conn.connect()
        
        # Create document node if provided
        doc_id = None
        if source_document:
            doc_id = self._create_document_node(source_document)
        
        # Create entity nodes
        entity_stats = self._create_entity_nodes(extraction.entities, doc_id)
        
        # Create relationships
        relationship_stats = self._create_relationships(extraction.relationships)
        
        return {
            "entities_created": entity_stats["created"],
            "relationships_created": relationship_stats["created"],
            "document_id": doc_id
        }
    
    def _create_document_node(self, document_name: str) -> str:
        """Create a document node."""
        query = """
        MERGE (d:Document {name: $name})
        ON CREATE SET d.created_at = timestamp()
        RETURN id(d) as doc_id
        """
        result = self.neo4j_conn.execute_query(query, {"name": document_name})
        doc_id = result[0]["doc_id"] if result else None
        logger.info(f"Document node created/found: {document_name}")
        return doc_id
    
    def _create_entity_nodes(self, entities: List[Entity], doc_id: str = None) -> Dict[str, int]:
        """Create entity nodes in the graph."""
        created_count = 0
        
        for entity in entities:
            # Create or merge entity node
            query = """
            MERGE (e:Entity {name: $name})
            ON CREATE SET e.type = $type, e.created_at = timestamp()
            ON MATCH SET e.type = $type
            WITH e
            """
            
            # Set properties
            params = {
                "name": entity.name,
                "type": entity.type
            }
            
            # Add custom properties
            for key, value in entity.properties.items():
                if isinstance(value, (str, int, float, bool)):
                    params[f"prop_{key}"] = value
                    query += f"SET e.{key} = $prop_{key}\n"
            
            # Link to document if provided
            if doc_id:
                query += """
                WITH e
                MATCH (d:Document) WHERE id(d) = $doc_id
                MERGE (e)-[:EXTRACTED_FROM]->(d)
                """
                params["doc_id"] = doc_id
            
            query += "RETURN id(e) as entity_id, e.name as name"
            
            result = self.neo4j_conn.execute_query(query, params)
            if result:
                self.entity_id_map[entity.name] = result[0]["entity_id"]
                created_count += 1
        
        logger.info(f"Created/updated {created_count} entity nodes")
        return {"created": created_count}
    
    def _create_relationships(self, relationships: List[Relationship]) -> Dict[str, int]:
        """Create relationships between entities."""
        created_count = 0
        
        for rel in relationships:
            # Find source and target entities
            query = """
            MATCH (source:Entity {name: $source_name})
            MATCH (target:Entity {name: $target_name})
            """
            
            # Create relationship with properties
            rel_props = ""
            params = {
                "source_name": rel.source,
                "target_name": rel.target,
                "rel_type": rel.type.upper().replace(" ", "_")
            }
            
            if rel.properties:
                prop_parts = []
                for key, value in rel.properties.items():
                    if isinstance(value, (str, int, float, bool)):
                        params[f"prop_{key}"] = value
                        prop_parts.append(f"{key}: $prop_{key}")
                if prop_parts:
                    rel_props = "{" + ", ".join(prop_parts) + "}"
            
            # Use MERGE to avoid duplicate relationships
            query += f"""
            MERGE (source)-[r:{params['rel_type']} {rel_props}]->(target)
            ON CREATE SET r.created_at = timestamp()
            RETURN id(r) as rel_id
            """
            
            try:
                result = self.neo4j_conn.execute_query(query, params)
                if result:
                    created_count += 1
            except Exception as e:
                logger.warning(f"Failed to create relationship {rel.source}-[{rel.type}]->{rel.target}: {e}")
        
        logger.info(f"Created {created_count} relationships")
        return {"created": created_count}
    
    def get_entity_id(self, entity_name: str) -> str:
        """Get Neo4j ID for an entity by name."""
        if entity_name in self.entity_id_map:
            return self.entity_id_map[entity_name]
        
        query = "MATCH (e:Entity {name: $name}) RETURN id(e) as entity_id"
        result = self.neo4j_conn.execute_query(query, {"name": entity_name})
        if result:
            entity_id = result[0]["entity_id"]
            self.entity_id_map[entity_name] = entity_id
            return entity_id
        return None
