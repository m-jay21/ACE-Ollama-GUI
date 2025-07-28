import re
import tiktoken
from typing import List, Dict, Optional
from dataclasses import dataclass
import logging
import hashlib

# Set up logging
logger = logging.getLogger(__name__)

@dataclass
class DocumentChunk:
    """Represents a processed document chunk"""
    content: str
    chunk_id: str
    metadata: Dict
    token_count: int
    page_number: Optional[int] = None
    section_title: Optional[str] = None

class DocumentProcessor:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.encoding = tiktoken.get_encoding("cl100k_base")
        
    def preprocess_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
            
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters but keep punctuation and common symbols
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)\[\]\{\}\"\']', '', text)
        
        # Normalize line breaks
        text = text.replace('\n', ' ').replace('\r', ' ')
        
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def split_by_sentences(self, text: str) -> List[str]:
        """Split text into sentences using smart boundaries"""
        if not text:
            return []
            
        # Split on sentence endings followed by space
        # This handles common sentence endings: . ! ? 
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        # Clean up sentences
        cleaned_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(sentence) > 3:  # Filter out very short fragments
                cleaned_sentences.append(sentence)
        
        return cleaned_sentences
    
    def create_chunks(self, text: str, metadata: Dict = None) -> List[DocumentChunk]:
        """Create intelligent chunks from text"""
        if not text:
            return []
            
        # Preprocess text
        clean_text = self.preprocess_text(text)
        
        # Split into sentences
        sentences = self.split_by_sentences(clean_text)
        
        if not sentences:
            return []
        
        chunks = []
        current_chunk = []
        current_tokens = 0
        
        for sentence in sentences:
            sentence_tokens = len(self.encoding.encode(sentence))
            
            # If adding this sentence would exceed chunk size and we have content
            if current_tokens + sentence_tokens > self.chunk_size and current_chunk:
                # Create chunk
                chunk_content = ' '.join(current_chunk)
                chunk_id = self._generate_chunk_id(chunk_content, metadata)
                
                chunk = DocumentChunk(
                    content=chunk_content,
                    chunk_id=chunk_id,
                    metadata=metadata or {},
                    token_count=current_tokens
                )
                chunks.append(chunk)
                
                # Start new chunk with overlap
                overlap_sentences = current_chunk[-2:] if len(current_chunk) >= 2 else current_chunk
                current_chunk = overlap_sentences + [sentence]
                current_tokens = sum(len(self.encoding.encode(s)) for s in current_chunk)
            else:
                current_chunk.append(sentence)
                current_tokens += sentence_tokens
        
        # Add final chunk
        if current_chunk:
            chunk_content = ' '.join(current_chunk)
            chunk_id = self._generate_chunk_id(chunk_content, metadata)
            
            chunk = DocumentChunk(
                content=chunk_content,
                chunk_id=chunk_id,
                metadata=metadata or {},
                token_count=current_tokens
            )
            chunks.append(chunk)
        
        logger.info(f"Created {len(chunks)} chunks from text")
        return chunks
    
    def _generate_chunk_id(self, content: str, metadata: Dict = None) -> str:
        """Generate a unique chunk ID based on content and metadata"""
        # Create a hash of the content and metadata
        hash_input = content + str(metadata or {})
        chunk_hash = hashlib.md5(hash_input.encode()).hexdigest()[:8]
        return f"chunk_{chunk_hash}"
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text"""
        return len(self.encoding.encode(text))
    
    def get_chunk_statistics(self, chunks: List[DocumentChunk]) -> Dict:
        """Get statistics about the chunks"""
        if not chunks:
            return {}
        
        total_chunks = len(chunks)
        total_tokens = sum(chunk.token_count for chunk in chunks)
        avg_tokens = total_tokens / total_chunks if total_chunks > 0 else 0
        
        return {
            "total_chunks": total_chunks,
            "total_tokens": total_tokens,
            "average_tokens_per_chunk": round(avg_tokens, 2),
            "chunk_size_limit": self.chunk_size,
            "chunk_overlap": self.chunk_overlap
        } 