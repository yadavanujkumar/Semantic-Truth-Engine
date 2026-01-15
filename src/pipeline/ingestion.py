"""Main ingestion pipeline for documents."""
from pathlib import Path
from typing import Dict, Any
import logging
from src.utils.document_processor import DocumentProcessor
from src.pipeline.entity_extractor import EntityExtractor
from src.graph.graph_builder import GraphBuilder
from src.graph.neo4j_manager import Neo4jConnection
from src.config import config

logger = logging.getLogger(__name__)


class IngestionPipeline:
    """End-to-end pipeline for document ingestion and graph creation."""
    
    def __init__(self, neo4j_conn: Neo4jConnection = None):
        """Initialize the ingestion pipeline."""
        self.doc_processor = DocumentProcessor()
        self.entity_extractor = EntityExtractor()
        self.neo4j_conn = neo4j_conn or Neo4jConnection()
        self.graph_builder = GraphBuilder(self.neo4j_conn)
    
    def ingest_document(self, file_path: Path) -> Dict[str, Any]:
        """Ingest a single document and build its knowledge graph."""
        logger.info(f"Starting ingestion of document: {file_path}")
        
        try:
            # Step 1: Extract text from document
            doc_data = self.doc_processor.process_document(file_path)
            logger.info(f"Extracted {doc_data['text_length']} characters from {doc_data['file_name']}")
            
            # Step 2: Chunk the text
            chunks = self.doc_processor.chunk_text(
                doc_data['text'],
                chunk_size=config.chunk_size,
                chunk_overlap=config.chunk_overlap
            )
            
            # Step 3: Extract entities and relationships
            extraction = self.entity_extractor.extract_from_chunks(chunks)
            logger.info(f"Extracted {len(extraction.entities)} entities and {len(extraction.relationships)} relationships")
            
            # Step 4: Build the knowledge graph
            graph_stats = self.graph_builder.build_graph(extraction, doc_data['file_name'])
            
            return {
                "success": True,
                "file_name": doc_data['file_name'],
                "text_length": doc_data['text_length'],
                "chunks": len(chunks),
                "entities": len(extraction.entities),
                "relationships": len(extraction.relationships),
                "graph_stats": graph_stats
            }
            
        except Exception as e:
            logger.error(f"Error ingesting document {file_path}: {e}")
            return {
                "success": False,
                "file_name": file_path.name,
                "error": str(e)
            }
    
    def ingest_multiple_documents(self, file_paths: list[Path]) -> list[Dict[str, Any]]:
        """Ingest multiple documents."""
        results = []
        for file_path in file_paths:
            result = self.ingest_document(file_path)
            results.append(result)
        return results
