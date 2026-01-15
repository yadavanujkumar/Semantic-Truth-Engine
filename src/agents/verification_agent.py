"""Verification Agent for fact-checking against ground truth."""
from typing import List, Dict, Any, Optional
import logging
import wikipedia
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from src.config import config

logger = logging.getLogger(__name__)


class VerificationAgent:
    """Agent responsible for verifying facts against ground truth sources."""
    
    def __init__(self):
        """Initialize the Verification Agent."""
        self.llm = ChatOpenAI(
            model=config.openai_model,
            temperature=0,
            openai_api_key=config.openai_api_key
        )
    
    def verify_facts(self, subgraph: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Verify facts from the subgraph against ground truth."""
        logger.info(f"Verifying facts for query: {query}")
        
        # Extract key facts from subgraph
        facts = self._extract_facts_from_subgraph(subgraph)
        
        # Get ground truth from Wikipedia
        ground_truth = self._get_ground_truth(subgraph.get("entities", []))
        
        # Perform verification
        verification_result = self._compare_facts(facts, ground_truth, query)
        
        return {
            "query": query,
            "facts": facts,
            "ground_truth": ground_truth,
            "verification": verification_result,
            "confidence_score": verification_result.get("confidence", 0.0)
        }
    
    def _extract_facts_from_subgraph(self, subgraph: Dict[str, Any]) -> List[str]:
        """Extract key facts from the subgraph."""
        facts = []
        
        # Extract facts from relationships
        for rel in subgraph.get("relationships", []):
            if rel and hasattr(rel, '__dict__'):
                rel_dict = rel.__dict__ if hasattr(rel, '__dict__') else rel
                # Create fact statement from relationship
                fact = f"{rel_dict.get('start', 'Entity')} {rel_dict.get('type', 'RELATED_TO')} {rel_dict.get('end', 'Entity')}"
                facts.append(fact)
        
        # Extract facts from nodes
        for node in subgraph.get("nodes", []):
            if node and hasattr(node, '__dict__'):
                node_dict = node.__dict__ if hasattr(node, '__dict__') else node
                node_props = node_dict.get('_properties', {})
                if 'name' in node_props and 'type' in node_props:
                    fact = f"{node_props['name']} is a {node_props['type']}"
                    facts.append(fact)
        
        logger.info(f"Extracted {len(facts)} facts from subgraph")
        return facts
    
    def _get_ground_truth(self, entities: List[str]) -> Dict[str, str]:
        """Get ground truth information from Wikipedia."""
        ground_truth = {}
        
        for entity in entities[:5]:  # Limit to first 5 entities to avoid rate limits
            try:
                # Search Wikipedia
                search_results = wikipedia.search(entity, results=1)
                if search_results:
                    page_title = search_results[0]
                    page = wikipedia.page(page_title, auto_suggest=False)
                    ground_truth[entity] = {
                        "title": page.title,
                        "summary": page.summary[:500],  # First 500 chars
                        "url": page.url
                    }
                    logger.info(f"Retrieved ground truth for: {entity}")
            except Exception as e:
                logger.warning(f"Could not retrieve Wikipedia info for {entity}: {e}")
                ground_truth[entity] = {"error": str(e)}
        
        return ground_truth
    
    def _compare_facts(self, facts: List[str], ground_truth: Dict[str, Any], query: str) -> Dict[str, Any]:
        """Compare extracted facts with ground truth using LLM."""
        
        # Prepare ground truth text
        gt_text = ""
        for entity, info in ground_truth.items():
            if isinstance(info, dict) and "summary" in info:
                gt_text += f"\n{entity}: {info['summary']}\n"
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert fact-checker. Compare the facts from the knowledge graph with ground truth information.
For each fact, determine if it is:
- VERIFIED: Confirmed by ground truth
- CONTRADICTED: Contradicts ground truth
- UNVERIFIED: Not enough information to verify
- UNKNOWN: No ground truth available

Provide a confidence score (0-1) for your verification.
Return your analysis in a structured format."""),
            ("user", """Query: {query}

Facts from Knowledge Graph:
{facts}

Ground Truth Information:
{ground_truth}

Analyze each fact and provide:
1. Verification status for key facts
2. Overall confidence score (0-1)
3. Summary of findings""")
        ])
        
        try:
            messages = prompt.format_messages(
                query=query,
                facts="\n".join(f"- {fact}" for fact in facts[:10]),  # Limit to 10 facts
                ground_truth=gt_text or "No ground truth available"
            )
            
            response = self.llm.invoke(messages)
            
            # Parse confidence score from response
            confidence = self._extract_confidence_score(response.content)
            
            return {
                "analysis": response.content,
                "confidence": confidence,
                "facts_checked": len(facts),
                "ground_truth_sources": len(ground_truth)
            }
        except Exception as e:
            logger.error(f"Error comparing facts: {e}")
            return {
                "analysis": f"Error during verification: {e}",
                "confidence": 0.0,
                "facts_checked": 0,
                "ground_truth_sources": 0
            }
    
    def _extract_confidence_score(self, text: str) -> float:
        """Extract confidence score from verification text."""
        # Look for patterns like "confidence: 0.8" or "confidence score: 80%"
        import re
        
        patterns = [
            r'confidence[:\s]+([0-9.]+)',
            r'([0-9.]+)\s*confidence',
            r'score[:\s]+([0-9.]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                try:
                    score = float(match.group(1))
                    # Normalize to 0-1 range
                    if score > 1:
                        score = score / 100
                    return min(max(score, 0.0), 1.0)
                except ValueError:
                    continue
        
        # Default confidence score
        return 0.5
