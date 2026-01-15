"""Entity and relationship extraction using LLM."""
from typing import List, Dict, Any, Tuple
import logging
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from src.config import config

logger = logging.getLogger(__name__)


class Entity(BaseModel):
    """Represents an extracted entity."""
    name: str = Field(description="The name of the entity")
    type: str = Field(description="The type/category of the entity (e.g., Person, Organization, Location, Product)")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Additional properties of the entity")


class Relationship(BaseModel):
    """Represents a relationship between two entities."""
    source: str = Field(description="The source entity name")
    target: str = Field(description="The target entity name")
    type: str = Field(description="The type of relationship (e.g., OWNS, WORKS_AT, LOCATED_IN)")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Additional properties of the relationship")


class GraphExtraction(BaseModel):
    """Represents the complete graph extraction result."""
    entities: List[Entity] = Field(description="List of extracted entities")
    relationships: List[Relationship] = Field(description="List of extracted relationships")


class EntityExtractor:
    """Extract entities and relationships from text using LLM."""
    
    def __init__(self, model_name: str = None):
        """Initialize the entity extractor."""
        self.model_name = model_name or config.openai_model
        self.llm = ChatOpenAI(
            model=self.model_name,
            temperature=0,
            openai_api_key=config.openai_api_key
        )
        self.parser = PydanticOutputParser(pydantic_object=GraphExtraction)
        
    def extract_entities_and_relationships(self, text: str) -> GraphExtraction:
        """Extract entities and relationships from text."""
        
        extraction_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert at extracting structured information from text.
Extract all entities (people, organizations, locations, products, concepts) and their relationships from the given text.

For entities, identify:
- Name: The exact name of the entity
- Type: Category like Person, Organization, Location, Product, Concept, Event, etc.
- Properties: Any additional relevant information

For relationships, identify:
- Source: The starting entity
- Target: The ending entity  
- Type: The relationship type (use verbs in UPPERCASE like OWNS, MANAGES, LOCATED_IN, PRODUCES, etc.)
- Properties: Any additional context about the relationship

{format_instructions}

Be thorough and extract all meaningful entities and relationships."""),
            ("user", "Text to analyze:\n\n{text}")
        ])
        
        try:
            prompt = extraction_prompt.format_messages(
                text=text,
                format_instructions=self.parser.get_format_instructions()
            )
            
            response = self.llm.invoke(prompt)
            result = self.parser.parse(response.content)
            
            logger.info(f"Extracted {len(result.entities)} entities and {len(result.relationships)} relationships")
            return result
            
        except Exception as e:
            logger.error(f"Error extracting entities and relationships: {e}")
            # Return empty result on error
            return GraphExtraction(entities=[], relationships=[])
    
    def extract_from_chunks(self, chunks: List[str]) -> GraphExtraction:
        """Extract entities and relationships from multiple text chunks."""
        all_entities = []
        all_relationships = []
        entity_map = {}  # To deduplicate entities
        
        for i, chunk in enumerate(chunks):
            logger.info(f"Processing chunk {i+1}/{len(chunks)}")
            extraction = self.extract_entities_and_relationships(chunk)
            
            # Deduplicate entities by name
            for entity in extraction.entities:
                if entity.name not in entity_map:
                    entity_map[entity.name] = entity
                    all_entities.append(entity)
                else:
                    # Merge properties if entity already exists
                    entity_map[entity.name].properties.update(entity.properties)
            
            all_relationships.extend(extraction.relationships)
        
        logger.info(f"Total: {len(all_entities)} unique entities and {len(all_relationships)} relationships")
        return GraphExtraction(entities=all_entities, relationships=all_relationships)
