"""Text-to-Cypher interface with self-correction."""
from typing import Dict, Any, Optional
import logging
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from src.graph.neo4j_manager import Neo4jConnection
from src.config import config

logger = logging.getLogger(__name__)


class TextToCypherConverter:
    """Convert natural language queries to Cypher queries with self-correction."""
    
    def __init__(self, neo4j_conn: Neo4jConnection):
        """Initialize the converter."""
        self.neo4j_conn = neo4j_conn
        self.llm = ChatOpenAI(
            model=config.openai_model,
            temperature=0,
            openai_api_key=config.openai_api_key
        )
        self.max_retries = config.max_retries
    
    def query(self, natural_language_query: str) -> Dict[str, Any]:
        """Convert natural language to Cypher and execute with self-correction."""
        logger.info(f"Processing query: {natural_language_query}")
        
        # Get graph schema
        schema = self._get_graph_schema()
        
        # Try to generate and execute query with retries
        for attempt in range(self.max_retries):
            logger.info(f"Attempt {attempt + 1}/{self.max_retries}")
            
            # Generate Cypher query
            cypher_query = self._generate_cypher(natural_language_query, schema, attempt)
            
            if not cypher_query:
                continue
            
            # Execute query
            result = self._execute_cypher(cypher_query)
            
            # Check if result is valid
            if result["success"]:
                if result["data"]:
                    logger.info(f"Query successful on attempt {attempt + 1}")
                    return {
                        "success": True,
                        "query": natural_language_query,
                        "cypher": cypher_query,
                        "data": result["data"],
                        "attempts": attempt + 1
                    }
                else:
                    logger.warning(f"Query returned no results on attempt {attempt + 1}")
                    # Try again with feedback
                    continue
            else:
                logger.warning(f"Query failed on attempt {attempt + 1}: {result.get('error')}")
                # Try again with error feedback
                continue
        
        # All attempts failed
        return {
            "success": False,
            "query": natural_language_query,
            "error": "Failed to generate valid Cypher query after all retries",
            "attempts": self.max_retries
        }
    
    def _get_graph_schema(self) -> str:
        """Get the current graph schema."""
        schema_query = """
        CALL db.labels() YIELD label
        RETURN collect(label) as labels
        """
        
        rel_query = """
        CALL db.relationshipTypes() YIELD relationshipType
        RETURN collect(relationshipType) as relationships
        """
        
        try:
            labels_result = self.neo4j_conn.execute_query(schema_query)
            rels_result = self.neo4j_conn.execute_query(rel_query)
            
            labels = labels_result[0].get("labels", []) if labels_result else []
            relationships = rels_result[0].get("relationships", []) if rels_result else []
            
            schema = f"Node Labels: {', '.join(labels)}\n"
            schema += f"Relationship Types: {', '.join(relationships)}"
            
            return schema
        except Exception as e:
            logger.error(f"Error getting schema: {e}")
            return "Node Labels: Entity, Document\nRelationship Types: EXTRACTED_FROM"
    
    def _generate_cypher(self, query: str, schema: str, attempt: int) -> Optional[str]:
        """Generate Cypher query from natural language."""
        
        system_message = """You are an expert at converting natural language questions to Cypher queries for Neo4j.

Graph Schema:
{schema}

Guidelines:
- Use MATCH for reading data
- Use proper WHERE clauses for filtering
- Return relevant nodes and relationships
- Use LIMIT to avoid returning too much data (default LIMIT 10)
- Ensure the query is syntactically correct
- Focus on Entity nodes with 'name' and 'type' properties

Return ONLY the Cypher query without any explanation or markdown formatting."""
        
        if attempt > 0:
            system_message += "\n\nPrevious attempt failed. Try a simpler or different approach."
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_message),
            ("user", "Question: {query}\n\nGenerate a Cypher query:")
        ])
        
        try:
            messages = prompt.format_messages(query=query, schema=schema)
            response = self.llm.invoke(messages)
            cypher = response.content.strip()
            
            # Clean up the response
            cypher = cypher.replace("```cypher", "").replace("```", "").strip()
            
            logger.info(f"Generated Cypher: {cypher}")
            return cypher
        except Exception as e:
            logger.error(f"Error generating Cypher: {e}")
            return None
    
    def _execute_cypher(self, cypher_query: str) -> Dict[str, Any]:
        """Execute a Cypher query and return results."""
        try:
            if not self.neo4j_conn.driver:
                self.neo4j_conn.connect()
            
            result = self.neo4j_conn.execute_query(cypher_query)
            
            return {
                "success": True,
                "data": result
            }
        except Exception as e:
            logger.error(f"Error executing Cypher: {e}")
            return {
                "success": False,
                "error": str(e),
                "data": []
            }
    
    def validate_cypher(self, cypher_query: str) -> Dict[str, Any]:
        """Validate a Cypher query without executing it."""
        try:
            # Try to explain the query (dry run)
            explain_query = f"EXPLAIN {cypher_query}"
            result = self.neo4j_conn.execute_query(explain_query)
            
            return {
                "valid": True,
                "message": "Query is syntactically valid"
            }
        except Exception as e:
            return {
                "valid": False,
                "error": str(e)
            }
