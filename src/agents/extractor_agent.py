"""Extractor Agent for retrieving relevant sub-graphs."""
from typing import List, Dict, Any
import logging
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from src.graph.neo4j_manager import Neo4jConnection
from src.config import config

logger = logging.getLogger(__name__)


class ExtractorAgent:
    """Agent responsible for extracting relevant sub-graphs based on queries."""
    
    def __init__(self, neo4j_conn: Neo4jConnection):
        """Initialize the Extractor Agent."""
        self.neo4j_conn = neo4j_conn
        self.llm = ChatOpenAI(
            model=config.openai_model,
            temperature=0,
            openai_api_key=config.openai_api_key
        )
    
    def extract_subgraph(self, query: str, max_nodes: int = 50) -> Dict[str, Any]:
        """Extract a relevant sub-graph for the given query."""
        logger.info(f"Extracting sub-graph for query: {query}")
        
        # Step 1: Identify relevant entities from the query
        entities = self._identify_entities_from_query(query)
        
        if not entities:
            logger.warning("No entities identified from query")
            return {"nodes": [], "relationships": [], "entities": []}
        
        # Step 2: Search for matching nodes in the graph
        matching_nodes = []
        for entity in entities:
            nodes = self.neo4j_conn.search_nodes(
                property_name="name",
                property_value=entity,
                limit=5
            )
            matching_nodes.extend(nodes)
        
        if not matching_nodes:
            logger.warning("No matching nodes found in graph")
            return {"nodes": [], "relationships": [], "entities": entities}
        
        # Step 3: Get sub-graph around these nodes
        node_ids = [node['n']['id'] if 'id' in node.get('n', {}) else None for node in matching_nodes]
        node_ids = [nid for nid in node_ids if nid]
        
        # Query for subgraph with relationships
        subgraph = self._get_subgraph_with_relationships(node_ids, depth=2)
        
        logger.info(f"Extracted sub-graph with {len(subgraph['nodes'])} nodes and {len(subgraph['relationships'])} relationships")
        
        return {
            "nodes": subgraph["nodes"],
            "relationships": subgraph["relationships"],
            "entities": entities,
            "query": query
        }
    
    def _identify_entities_from_query(self, query: str) -> List[str]:
        """Identify key entities mentioned in the query using LLM."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at identifying key entities in questions.
Extract all important entities (people, organizations, products, locations, concepts) from the query.
Return only the entity names, one per line, without any additional text or formatting."""),
            ("user", "Query: {query}")
        ])
        
        try:
            messages = prompt.format_messages(query=query)
            response = self.llm.invoke(messages)
            entities = [line.strip() for line in response.content.split('\n') if line.strip()]
            logger.info(f"Identified entities: {entities}")
            return entities
        except Exception as e:
            logger.error(f"Error identifying entities: {e}")
            return []
    
    def _get_subgraph_with_relationships(self, node_ids: List[int], depth: int = 2) -> Dict[str, Any]:
        """Get subgraph with nodes and relationships."""
        # Simple approach: get nodes and their immediate relationships
        query = """
        MATCH (n:Entity)
        WHERE id(n) IN $node_ids
        OPTIONAL MATCH (n)-[r]-(connected)
        RETURN 
            collect(DISTINCT n) as nodes,
            collect(DISTINCT connected) as connected_nodes,
            collect(DISTINCT r) as relationships
        """
        
        try:
            result = self.neo4j_conn.execute_query(query, {"node_ids": node_ids})
            if result:
                all_nodes = result[0].get("nodes", []) + result[0].get("connected_nodes", [])
                # Remove None values
                all_nodes = [n for n in all_nodes if n is not None]
                relationships = [r for r in result[0].get("relationships", []) if r is not None]
                
                return {
                    "nodes": all_nodes,
                    "relationships": relationships
                }
        except Exception as e:
            logger.error(f"Error getting subgraph: {e}")
        
        return {"nodes": [], "relationships": []}
