import os
import logging
from typing import List, Dict, Optional
from pathlib import Path
import csv
import json
import re

# Set up logging
logger = logging.getLogger(__name__)

class DocumentLoader:
    """Universal document loader for multiple file types"""
    
    def __init__(self):
        self.supported_extensions = {
            '.txt': self._load_text_file,
            '.md': self._load_markdown_file,
            '.csv': self._load_csv_file,
            '.json': self._load_json_file,
            '.docx': self._load_docx_file,
            '.doc': self._load_doc_file,
            '.pdf': self._load_pdf_file  # Will be handled by existing PDF processor
        }
    
    def validate_file_path(self, file_path: str) -> str:
        """Validate file path and check if it's a supported format"""
        if not isinstance(file_path, str):
            raise ValueError("File path must be a string")
        
        if not os.path.exists(file_path):
            raise ValueError(f"File does not exist: {file_path}")
        
        # Check file size (limit to 50MB)
        file_size = os.path.getsize(file_path)
        if file_size > 50 * 1024 * 1024:  # 50MB
            raise ValueError("File too large. Maximum size is 50MB")
        
        # Check file extension
        ext = Path(file_path).suffix.lower()
        if ext not in self.supported_extensions:
            supported = ', '.join(self.supported_extensions.keys())
            raise ValueError(f"Unsupported file type: {ext}. Supported types: {supported}")
        
        return file_path
    
    def load_document(self, file_path: str) -> Dict:
        """
        Load document content based on file type
        
        Returns:
            Dict with 'content', 'metadata', and 'file_type'
        """
        file_path = self.validate_file_path(file_path)
        ext = Path(file_path).suffix.lower()
        
        try:
            # Get the appropriate loader function
            loader_func = self.supported_extensions.get(ext)
            if not loader_func:
                raise ValueError(f"No loader found for file type: {ext}")
            
            # Load the document
            content = loader_func(file_path)
            
            # Create metadata
            metadata = {
                "file_path": file_path,
                "file_type": ext[1:],  # Remove the dot
                "file_size": os.path.getsize(file_path),
                "file_name": Path(file_path).name
            }
            
            return {
                "content": content,
                "metadata": metadata,
                "file_type": ext[1:]
            }
            
        except Exception as e:
            logger.error(f"Error loading document {file_path}: {e}")
            raise ValueError(f"Failed to load document: {str(e)}")
    
    def _load_text_file(self, file_path: str) -> str:
        """Load plain text file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return content
        except UnicodeDecodeError:
            # Try with different encoding
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
            return content
    
    def _load_markdown_file(self, file_path: str) -> str:
        """Load markdown file (same as text for now)"""
        return self._load_text_file(file_path)
    
    def _load_csv_file(self, file_path: str) -> str:
        """Load CSV file and convert to readable text"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)
            
            if not rows:
                return "Empty CSV file"
            
            # Convert to readable text
            content = []
            for i, row in enumerate(rows):
                if i == 0:
                    # Header row
                    content.append(f"Headers: {', '.join(row)}")
                else:
                    # Data row
                    content.append(f"Row {i}: {', '.join(row)}")
            
            return "\n".join(content)
        except Exception as e:
            logger.error(f"Error loading CSV file: {e}")
            return f"Error reading CSV file: {str(e)}"
    
    def _load_json_file(self, file_path: str) -> str:
        """Load JSON file and convert to readable text"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Convert JSON to readable text
            return self._json_to_text(data)
        except Exception as e:
            logger.error(f"Error loading JSON file: {e}")
            return f"Error reading JSON file: {str(e)}"
    
    def _json_to_text(self, data, indent=0) -> str:
        """Convert JSON data to readable text"""
        if isinstance(data, dict):
            lines = []
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    lines.append(f"{'  ' * indent}{key}:")
                    lines.append(self._json_to_text(value, indent + 1))
                else:
                    lines.append(f"{'  ' * indent}{key}: {value}")
            return "\n".join(lines)
        elif isinstance(data, list):
            lines = []
            for i, item in enumerate(data):
                if isinstance(item, (dict, list)):
                    lines.append(f"{'  ' * indent}Item {i}:")
                    lines.append(self._json_to_text(item, indent + 1))
                else:
                    lines.append(f"{'  ' * indent}Item {i}: {item}")
            return "\n".join(lines)
        else:
            return str(data)
    
    def _load_docx_file(self, file_path: str) -> str:
        """Load DOCX file using python-docx"""
        try:
            # Try to import python-docx
            try:
                from docx import Document
            except ImportError:
                return "Error: python-docx not installed. Install with: pip install python-docx"
            
            doc = Document(file_path)
            content = []
            
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    content.append(paragraph.text)
            
            return "\n".join(content)
        except Exception as e:
            logger.error(f"Error loading DOCX file: {e}")
            return f"Error reading DOCX file: {str(e)}"
    
    def _load_doc_file(self, file_path: str) -> str:
        """Load DOC file (legacy Word format)"""
        try:
            # Try to import python-docx2txt
            try:
                import docx2txt
            except ImportError:
                return "Error: docx2txt not installed. Install with: pip install docx2txt"
            
            content = docx2txt.process(file_path)
            return content if content else "Empty DOC file"
        except Exception as e:
            logger.error(f"Error loading DOC file: {e}")
            return f"Error reading DOC file: {str(e)}"
    
    def _load_pdf_file(self, file_path: str) -> str:
        """Load PDF file using existing PDF processor"""
        try:
            from enhanced_pdf_processor import EnhancedPDFProcessor
            processor = EnhancedPDFProcessor()
            chunks = processor.extract_with_structure(file_path)
            
            # Combine all chunks into one text
            content = "\n\n".join([chunk.content for chunk in chunks])
            return content
        except Exception as e:
            logger.error(f"Error loading PDF file: {e}")
            return f"Error reading PDF file: {str(e)}"
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported file formats"""
        return list(self.supported_extensions.keys())
    
    def is_supported(self, file_path: str) -> bool:
        """Check if file type is supported"""
        try:
            ext = Path(file_path).suffix.lower()
            return ext in self.supported_extensions
        except:
            return False 