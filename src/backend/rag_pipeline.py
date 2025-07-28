from typing import List, Dict, Optional
from document_processor import DocumentChunk
import json
import logging
import re
from collections import defaultdict

# Set up logging
logger = logging.getLogger(__name__)

class RAGPipeline:
    def __init__(self):
        self.chunks = []
        self.chunk_index = defaultdict(list)
        self.chunk_metadata = {}
        
    def add_document(self, chunks: List[DocumentChunk]):
        """Add processed chunks to the pipeline"""
        for chunk in chunks:
            self.chunks.append(chunk)
            self.chunk_metadata[chunk.chunk_id] = chunk.metadata
            
            # Create simple index for retrieval
            words = self._tokenize_text(chunk.content.lower())
            for word in words:
                if word not in self.chunk_index:
                    self.chunk_index[word] = []
                if chunk.chunk_id not in self.chunk_index[word]:
                    self.chunk_index[word].append(chunk.chunk_id)
        
        logger.info(f"Added {len(chunks)} chunks to RAG pipeline")
    
    def _tokenize_text(self, text: str) -> List[str]:
        """Tokenize text into words for indexing"""
        # Remove punctuation and split into words
        words = re.findall(r'\b\w+\b', text.lower())
        # Filter out very short words and common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'}
        return [word for word in words if len(word) > 2 and word not in stop_words]
    
    def find_relevant_chunks(self, query: str, top_k: int = 3) -> List[DocumentChunk]:
        """Find most relevant chunks for a query using simple keyword matching"""
        query_words = self._tokenize_text(query)
        
        if not query_words:
            # If no meaningful words in query, return first few chunks
            return self.chunks[:top_k]
        
        chunk_scores = defaultdict(int)
        
        # Score chunks based on word overlap
        for word in query_words:
            if word in self.chunk_index:
                for chunk_id in self.chunk_index[word]:
                    chunk_scores[chunk_id] += 1
        
        # Sort by relevance score
        sorted_chunks = sorted(chunk_scores.items(), key=lambda x: x[1], reverse=True)
        
        # Return top chunks
        relevant_chunks = []
        for chunk_id, score in sorted_chunks[:top_k]:
            chunk = next((c for c in self.chunks if c.chunk_id == chunk_id), None)
            if chunk:
                relevant_chunks.append(chunk)
        
        # If we don't have enough relevant chunks, add some from the beginning
        if len(relevant_chunks) < top_k:
            remaining = top_k - len(relevant_chunks)
            for chunk in self.chunks:
                if chunk not in relevant_chunks and len(relevant_chunks) < top_k:
                    relevant_chunks.append(chunk)
        
        logger.info(f"Found {len(relevant_chunks)} relevant chunks for query")
        return relevant_chunks
    
    def create_context_prompt(self, query: str, relevant_chunks: List[DocumentChunk]) -> str:
        """Create a context-aware prompt from relevant chunks"""
        if not relevant_chunks:
            return query
        
        context = "DOCUMENT CONTEXT:\n\n"
        
        for i, chunk in enumerate(relevant_chunks):
            # Add metadata if available
            metadata_info = ""
            if chunk.metadata.get("page_number"):
                metadata_info = f" (Page {chunk.metadata['page_number']})"
            if chunk.metadata.get("section"):
                metadata_info += f" (Section: {chunk.metadata['section']})"
            
            context += f"Section {i+1}{metadata_info}:\n{chunk.content}\n\n"
        
        context += f"USER QUERY: {query}\n\n"
        context += "Please answer the user's query based on the document context provided above. If the context doesn't contain enough information to answer the query, please say so."
        
        return context
    
    def create_enhanced_query(self, original_query: str, chunks: List[DocumentChunk]) -> str:
        """Create an enhanced query with document context"""
        if not chunks:
            return original_query
        
        # Create a summary of available content
        content_summary = []
        for chunk in chunks:
            # Take first 100 characters of each chunk for summary
            summary = chunk.content[:100] + "..." if len(chunk.content) > 100 else chunk.content
            content_summary.append(summary)
        
        enhanced_query = f"""Based on the following document content:

{' '.join(content_summary)}

Please answer this question: {original_query}

Provide a comprehensive answer using the document information provided."""
        
        return enhanced_query
    
    def get_pipeline_statistics(self) -> Dict:
        """Get statistics about the RAG pipeline"""
        total_chunks = len(self.chunks)
        total_words = sum(len(self._tokenize_text(chunk.content)) for chunk in self.chunks)
        
        # Count unique words in index
        unique_words = len(self.chunk_index)
        
        return {
            "total_chunks": total_chunks,
            "total_words": total_words,
            "unique_indexed_words": unique_words,
            "average_words_per_chunk": round(total_words / total_chunks, 2) if total_chunks > 0 else 0
        }
    
    def clear_pipeline(self):
        """Clear all chunks from the pipeline"""
        self.chunks = []
        self.chunk_index.clear()
        self.chunk_metadata.clear()
        logger.info("RAG pipeline cleared") 