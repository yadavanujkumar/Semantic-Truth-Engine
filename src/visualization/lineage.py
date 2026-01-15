"""Lineage tracking and explainability for query results."""
from typing import Dict, Any, List, Tuple
import logging
from src.graph.neo4j_manager import Neo4jConnection

logger = logging.getLogger(__name__)


class LineageTracker:
    """Track and visualize lineage paths through the knowledge graph."""
    
    def __init__(self, neo4j_conn: Neo4jConnection):
        """Initialize the lineage tracker."""
        self.neo4j_conn = neo4j_conn
    
    def generate_lineage_map(self, query: str, subgraph: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a lineage map showing paths traversed to answer the query."""
        logger.info(f"Generating lineage map for query: {query}")
        
        nodes = subgraph.get("nodes", [])
        relationships = subgraph.get("relationships", [])
        
        if not nodes:
            return {
                "query": query,
                "paths": [],
                "visualization_data": None,
                "explanation": "No data available to generate lineage map"
            }
        
        # Extract paths from subgraph
        paths = self._extract_paths(nodes, relationships)
        
        # Create visualization data
        viz_data = self._create_visualization_data(nodes, relationships)
        
        # Generate explanation
        explanation = self._generate_explanation(paths, query)
        
        return {
            "query": query,
            "paths": paths,
            "visualization_data": viz_data,
            "explanation": explanation,
            "num_nodes": len(nodes),
            "num_relationships": len(relationships)
        }
    
    def find_path_between_entities(self, start_entity: str, end_entity: str, 
                                   max_depth: int = 5) -> Dict[str, Any]:
        """Find and visualize paths between two specific entities."""
        logger.info(f"Finding path from {start_entity} to {end_entity}")
        
        query = """
        MATCH (start:Entity {name: $start_name})
        MATCH (end:Entity {name: $end_name})
        MATCH path = shortestPath((start)-[*..%d]-(end))
        RETURN path, length(path) as path_length
        """ % max_depth
        
        try:
            results = self.neo4j_conn.execute_query(
                query, 
                {"start_name": start_entity, "end_name": end_entity}
            )
            
            if not results:
                return {
                    "found": False,
                    "message": f"No path found between {start_entity} and {end_entity}"
                }
            
            # Extract path information
            path_data = results[0]
            path = path_data.get("path")
            path_length = path_data.get("path_length", 0)
            
            # Parse path into nodes and relationships
            lineage = self._parse_path(path)
            
            return {
                "found": True,
                "start_entity": start_entity,
                "end_entity": end_entity,
                "path_length": path_length,
                "lineage": lineage,
                "explanation": self._explain_path(lineage)
            }
            
        except Exception as e:
            logger.error(f"Error finding path: {e}")
            return {
                "found": False,
                "error": str(e)
            }
    
    def _extract_paths(self, nodes: List[Any], relationships: List[Any]) -> List[Dict[str, Any]]:
        """Extract meaningful paths from nodes and relationships."""
        paths = []
        
        # Group relationships by connected nodes
        for rel in relationships:
            if rel and hasattr(rel, '__dict__'):
                rel_dict = rel.__dict__ if hasattr(rel, '__dict__') else rel
                
                path = {
                    "start": self._extract_node_name(rel_dict.get("start")),
                    "relationship": rel_dict.get("type", "RELATED_TO"),
                    "end": self._extract_node_name(rel_dict.get("end")),
                    "properties": rel_dict.get("_properties", {})
                }
                paths.append(path)
        
        return paths
    
    def _extract_node_name(self, node) -> str:
        """Extract node name from various node formats."""
        if isinstance(node, str):
            return node
        if isinstance(node, dict):
            return node.get("name", "Unknown")
        if hasattr(node, "_properties"):
            return node._properties.get("name", "Unknown")
        return "Unknown"
    
    def _create_visualization_data(self, nodes: List[Any], 
                                   relationships: List[Any]) -> Dict[str, Any]:
        """Create data structure for graph visualization."""
        viz_nodes = []
        viz_edges = []
        
        # Process nodes
        for i, node in enumerate(nodes):
            if node:
                node_dict = node.__dict__ if hasattr(node, '__dict__') else node
                props = node_dict.get("_properties", {}) if isinstance(node_dict, dict) else {}
                
                viz_nodes.append({
                    "id": i,
                    "label": props.get("name", f"Node_{i}"),
                    "type": props.get("type", "Entity"),
                    "properties": props
                })
        
        # Process relationships
        for rel in relationships:
            if rel:
                rel_dict = rel.__dict__ if hasattr(rel, '__dict__') else rel
                
                viz_edges.append({
                    "source": self._extract_node_name(rel_dict.get("start")),
                    "target": self._extract_node_name(rel_dict.get("end")),
                    "label": rel_dict.get("type", "RELATED_TO"),
                    "properties": rel_dict.get("_properties", {})
                })
        
        return {
            "nodes": viz_nodes,
            "edges": viz_edges
        }
    
    def _generate_explanation(self, paths: List[Dict[str, Any]], query: str) -> str:
        """Generate human-readable explanation of the lineage."""
        if not paths:
            return "No paths found in the knowledge graph."
        
        explanation = f"To answer '{query}', the system traversed the following paths:\n\n"
        
        for i, path in enumerate(paths[:5], 1):  # Limit to first 5 paths
            explanation += f"{i}. {path['start']} → [{path['relationship']}] → {path['end']}\n"
        
        if len(paths) > 5:
            explanation += f"\n... and {len(paths) - 5} more paths"
        
        return explanation
    
    def _parse_path(self, path) -> List[Dict[str, Any]]:
        """Parse a Neo4j path object into a list of steps."""
        lineage = []
        
        # This is a simplified parser - actual implementation depends on Neo4j driver version
        if hasattr(path, 'nodes') and hasattr(path, 'relationships'):
            nodes = path.nodes
            rels = path.relationships
            
            for i, rel in enumerate(rels):
                step = {
                    "from": nodes[i].get("name", f"Node_{i}"),
                    "relationship": rel.type,
                    "to": nodes[i + 1].get("name", f"Node_{i+1}")
                }
                lineage.append(step)
        
        return lineage
    
    def _explain_path(self, lineage: List[Dict[str, Any]]) -> str:
        """Generate explanation for a path."""
        if not lineage:
            return "No path information available"
        
        explanation = "Path: "
        steps = []
        
        for step in lineage:
            steps.append(f"{step['from']} →[{step['relationship']}]→ {step['to']}")
        
        explanation += " → ".join(steps)
        return explanation
