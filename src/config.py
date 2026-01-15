"""Configuration management for the Semantic Truth Engine."""
import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()


class Config(BaseModel):
    """Application configuration."""
    
    # OpenAI Settings
    openai_api_key: str = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    openai_model: str = Field(default="gpt-4-turbo-preview")
    
    # Neo4j Settings
    neo4j_uri: str = Field(default_factory=lambda: os.getenv("NEO4J_URI", "bolt://localhost:7687"))
    neo4j_username: str = Field(default_factory=lambda: os.getenv("NEO4J_USERNAME", "neo4j"))
    neo4j_password: str = Field(default_factory=lambda: os.getenv("NEO4J_PASSWORD", ""))
    
    # Application Settings
    max_retries: int = Field(default_factory=lambda: int(os.getenv("MAX_RETRIES", "3")))
    chunk_size: int = Field(default_factory=lambda: int(os.getenv("CHUNK_SIZE", "1000")))
    chunk_overlap: int = Field(default_factory=lambda: int(os.getenv("CHUNK_OVERLAP", "200")))
    
    # Paths
    base_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent)
    data_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent / "data")
    uploads_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent / "data" / "uploads")
    graphs_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent / "data" / "graphs")
    
    class Config:
        """Pydantic config."""
        arbitrary_types_allowed = True


# Global config instance
config = Config()
