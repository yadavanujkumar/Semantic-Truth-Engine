"""Setup script to initialize the Semantic Truth Engine."""
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent))

from src.graph.neo4j_manager import Neo4jConnection
from src.config import config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def setup_neo4j():
    """Set up Neo4j database with indexes."""
    try:
        logger.info("Connecting to Neo4j...")
        conn = Neo4jConnection()
        conn.connect()
        
        logger.info("Creating indexes...")
        conn.create_indexes()
        
        logger.info("Setup completed successfully!")
        logger.info(f"Neo4j URI: {config.neo4j_uri}")
        
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        logger.error("\nPlease ensure:")
        logger.error("1. Neo4j is running")
        logger.error("2. Connection details in .env are correct")
        logger.error("3. You have the necessary permissions")
        return False


def verify_configuration():
    """Verify that all necessary configuration is present."""
    issues = []
    
    if not config.openai_api_key:
        issues.append("OPENAI_API_KEY not set in .env")
    
    if not config.neo4j_password:
        issues.append("NEO4J_PASSWORD not set in .env")
    
    if issues:
        logger.warning("Configuration issues found:")
        for issue in issues:
            logger.warning(f"  - {issue}")
        logger.warning("\nPlease update your .env file")
        return False
    
    logger.info("Configuration verified ✓")
    return True


def main():
    """Main setup function."""
    print("=" * 60)
    print("Semantic Truth Engine - Setup")
    print("=" * 60)
    print()
    
    # Verify configuration
    if not verify_configuration():
        print("\n⚠️  Please fix configuration issues before proceeding")
        return
    
    print("\n✓ Configuration looks good")
    
    # Setup Neo4j
    print("\nSetting up Neo4j database...")
    if setup_neo4j():
        print("\n✓ Setup completed successfully!")
        print("\nYou can now run the application:")
        print("  streamlit run app.py")
    else:
        print("\n✗ Setup failed")
        print("Please check the error messages above")


if __name__ == "__main__":
    main()
