"""Example script demonstrating the Semantic Truth Engine."""
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent))

from src.graph.neo4j_manager import Neo4jConnection
from src.pipeline.ingestion import IngestionPipeline
from src.agents.orchestrator import FactCheckingOrchestrator
from src.pipeline.text_to_cypher import TextToCypherConverter
from src.visualization.lineage import LineageTracker
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def example_ingestion():
    """Example: Ingest a sample document."""
    print("\n" + "=" * 60)
    print("Example 1: Document Ingestion")
    print("=" * 60)
    
    # Connect to Neo4j
    conn = Neo4jConnection()
    conn.connect()
    
    # Create pipeline
    pipeline = IngestionPipeline(conn)
    
    # Ingest sample document
    sample_file = Path(__file__).parent / "data" / "uploads" / "sample_document.txt"
    
    if sample_file.exists():
        print(f"\nIngesting: {sample_file.name}")
        result = pipeline.ingest_document(sample_file)
        
        if result["success"]:
            print(f"✓ Successfully processed {result['file_name']}")
            print(f"  - Text length: {result['text_length']} characters")
            print(f"  - Entities extracted: {result['entities']}")
            print(f"  - Relationships extracted: {result['relationships']}")
        else:
            print(f"✗ Failed to process {result['file_name']}")
            print(f"  Error: {result.get('error')}")
    else:
        print(f"Sample file not found: {sample_file}")
    
    conn.close()


def example_natural_language_query():
    """Example: Query using natural language."""
    print("\n" + "=" * 60)
    print("Example 2: Natural Language Query")
    print("=" * 60)
    
    # Connect to Neo4j
    conn = Neo4jConnection()
    conn.connect()
    
    # Create converter
    converter = TextToCypherConverter(conn)
    
    # Example query
    query = "What companies does Microsoft own?"
    print(f"\nQuery: {query}")
    
    result = converter.query(query)
    
    if result["success"]:
        print(f"✓ Query successful (attempts: {result['attempts']})")
        print(f"\nGenerated Cypher:")
        print(f"  {result['cypher']}")
        print(f"\nResults: {len(result['data'])} records found")
    else:
        print(f"✗ Query failed: {result.get('error')}")
    
    conn.close()


def example_fact_checking():
    """Example: Fact-checking with agents."""
    print("\n" + "=" * 60)
    print("Example 3: Fact-Checking")
    print("=" * 60)
    
    # Connect to Neo4j
    conn = Neo4jConnection()
    conn.connect()
    
    # Create orchestrator
    orchestrator = FactCheckingOrchestrator(conn)
    
    # Example fact-check query
    query = "Is LinkedIn owned by Microsoft?"
    print(f"\nQuery: {query}")
    
    result = orchestrator.check_facts(query)
    
    if result["success"]:
        print(f"✓ Fact-check completed")
        print(f"\nConfidence Score: {result['confidence_score']:.2%}")
        print(f"\nAnswer:")
        print(result['answer'])
    else:
        print(f"✗ Fact-check failed: {result.get('message')}")
    
    conn.close()


def example_lineage_tracking():
    """Example: Track lineage between entities."""
    print("\n" + "=" * 60)
    print("Example 4: Lineage Tracking")
    print("=" * 60)
    
    # Connect to Neo4j
    conn = Neo4jConnection()
    conn.connect()
    
    # Create tracker
    tracker = LineageTracker(conn)
    
    # Find path between entities
    start = "Microsoft"
    end = "LinkedIn"
    print(f"\nFinding path from '{start}' to '{end}'...")
    
    result = tracker.find_path_between_entities(start, end)
    
    if result["found"]:
        print(f"✓ Path found (length: {result['path_length']})")
        print(f"\n{result['explanation']}")
    else:
        print(f"✗ No path found")
    
    conn.close()


def main():
    """Run all examples."""
    print("=" * 60)
    print("Semantic Truth Engine - Examples")
    print("=" * 60)
    
    try:
        # Run examples
        example_ingestion()
        example_natural_language_query()
        example_fact_checking()
        example_lineage_tracking()
        
        print("\n" + "=" * 60)
        print("All examples completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Error running examples: {e}")
        print("\nMake sure:")
        print("1. Neo4j is running and accessible")
        print("2. OpenAI API key is configured")
        print("3. Run setup.py first if you haven't")


if __name__ == "__main__":
    main()
