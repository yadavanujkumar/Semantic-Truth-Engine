"""Document processing utilities for PDF and DOCX files."""
from pathlib import Path
from typing import List, Dict, Any
import logging
from pypdf import PdfReader
from docx import Document

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Process various document formats."""
    
    @staticmethod
    def extract_text_from_pdf(file_path: Path) -> str:
        """Extract text from PDF file."""
        try:
            reader = PdfReader(str(file_path))
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            logger.info(f"Extracted text from PDF: {file_path.name}")
            return text
        except Exception as e:
            logger.error(f"Error extracting text from PDF {file_path}: {e}")
            raise
    
    @staticmethod
    def extract_text_from_docx(file_path: Path) -> str:
        """Extract text from DOCX file."""
        try:
            doc = Document(str(file_path))
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            logger.info(f"Extracted text from DOCX: {file_path.name}")
            return text
        except Exception as e:
            logger.error(f"Error extracting text from DOCX {file_path}: {e}")
            raise
    
    @staticmethod
    def extract_text_from_txt(file_path: Path) -> str:
        """Extract text from TXT file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            logger.info(f"Extracted text from TXT: {file_path.name}")
            return text
        except Exception as e:
            logger.error(f"Error extracting text from TXT {file_path}: {e}")
            raise
    
    @classmethod
    def process_document(cls, file_path: Path) -> Dict[str, Any]:
        """Process a document and extract text based on file type."""
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        suffix = file_path.suffix.lower()
        
        if suffix == ".pdf":
            text = cls.extract_text_from_pdf(file_path)
        elif suffix in [".docx", ".doc"]:
            text = cls.extract_text_from_docx(file_path)
        elif suffix == ".txt":
            text = cls.extract_text_from_txt(file_path)
        else:
            raise ValueError(f"Unsupported file format: {suffix}")
        
        return {
            "file_name": file_path.name,
            "file_path": str(file_path),
            "text": text,
            "text_length": len(text)
        }
    
    @staticmethod
    def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split text into overlapping chunks."""
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start = end - overlap
        
        logger.info(f"Split text into {len(chunks)} chunks")
        return chunks
