"""Multi-agent orchestrator for fact-checking workflow."""
from typing import Dict, Any
import logging
from src.agents.extractor_agent import ExtractorAgent
from src.agents.verification_agent import VerificationAgent
from src.graph.neo4j_manager import Neo4jConnection

logger = logging.getLogger(__name__)


class FactCheckingOrchestrator:
    """Orchestrates the multi-agent fact-checking workflow."""
    
    def __init__(self, neo4j_conn: Neo4jConnection):
        """Initialize the orchestrator."""
        self.neo4j_conn = neo4j_conn
        self.extractor_agent = ExtractorAgent(neo4j_conn)
        self.verification_agent = VerificationAgent()
    
    def check_facts(self, query: str) -> Dict[str, Any]:
        """Execute the complete fact-checking workflow."""
        logger.info(f"Starting fact-checking workflow for query: {query}")
        
        # Step 1: Extract relevant sub-graph
        logger.info("Step 1: Extracting relevant sub-graph...")
        subgraph = self.extractor_agent.extract_subgraph(query)
        
        if not subgraph.get("nodes"):
            logger.warning("No relevant sub-graph found")
            return {
                "query": query,
                "success": False,
                "message": "No relevant information found in the knowledge graph",
                "subgraph": subgraph,
                "verification": None
            }
        
        # Step 2: Verify facts against ground truth
        logger.info("Step 2: Verifying facts against ground truth...")
        verification = self.verification_agent.verify_facts(subgraph, query)
        
        # Step 3: Generate answer with lineage
        logger.info("Step 3: Generating answer with lineage...")
        answer = self._generate_answer(query, subgraph, verification)
        
        return {
            "query": query,
            "success": True,
            "answer": answer,
            "subgraph": subgraph,
            "verification": verification,
            "confidence_score": verification.get("confidence_score", 0.0)
        }
    
    def _generate_answer(self, query: str, subgraph: Dict[str, Any], 
                        verification: Dict[str, Any]) -> str:
        """Generate a comprehensive answer based on subgraph and verification."""
        
        # Extract key information
        num_nodes = len(subgraph.get("nodes", []))
        num_relationships = len(subgraph.get("relationships", []))
        confidence = verification.get("confidence_score", 0.0)
        
        answer = f"Based on the knowledge graph analysis:\n\n"
        answer += f"Found {num_nodes} relevant entities and {num_relationships} relationships.\n"
        answer += f"Confidence Score: {confidence:.2f}\n\n"
        
        # Add verification analysis
        if verification.get("verification"):
            answer += "Verification Analysis:\n"
            answer += verification["verification"].get("analysis", "No analysis available")
            answer += "\n\n"
        
        # Add ground truth sources
        if verification.get("ground_truth"):
            answer += "Ground Truth Sources:\n"
            for entity, info in verification["ground_truth"].items():
                if isinstance(info, dict) and "url" in info:
                    answer += f"- {entity}: {info.get('url', 'N/A')}\n"
        
        return answer
