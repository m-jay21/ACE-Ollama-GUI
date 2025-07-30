from typing import List, Dict, Optional
from document_processor import DocumentChunk
from vector_store import VectorStore
from prompt_builder import PromptBuilder
import logging
import os

# Set up logging
logger = logging.getLogger(__name__)

class RAGPipeline:
    def __init__(self, vector_store_path: str = None):
        """
        Initialize RAG pipeline with vector embeddings for semantic search
        
        Args:
            vector_store_path: Path to save/load vector store
        """
        self.vector_store = VectorStore()
        self.vector_store_path = vector_store_path or "vector_store"
        self.prompt_builder = PromptBuilder()
        
        # Try to load existing vector store
        if os.path.exists(self.vector_store_path + ".faiss"):
            try:
                self.vector_store.load_index(self.vector_store_path)
                logger.info("Loaded existing vector store")
            except Exception as e:
                logger.warning(f"Could not load existing vector store: {e}")
    
    def add_document(self, chunks: List[DocumentChunk]):
        """Add document chunks to the vector store"""
        try:
            self.vector_store.add_documents(chunks)
            
            # Save the updated vector store
            if self.vector_store_path:
                self.vector_store.save_index(self.vector_store_path)
                
            logger.info(f"Added {len(chunks)} chunks to RAG pipeline")
        except Exception as e:
            logger.error(f"Error adding documents to vector store: {e}")
            raise
    
    def find_relevant_chunks(self, query: str, top_k: int = 3) -> List[DocumentChunk]:
        """
        Find relevant chunks using semantic search
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of relevant document chunks
        """
        try:
            relevant_chunks = self.vector_store.semantic_search(query, top_k)
            logger.info(f"Found {len(relevant_chunks)} semantically relevant chunks")
            return relevant_chunks
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []
    
    def get_similarity_scores(self, query: str, top_k: int = 3) -> List[tuple]:
        """Get similarity scores for debugging and analysis"""
        return self.vector_store.get_similarity_scores(query, top_k)
    
    def create_context_prompt(self, query: str, relevant_chunks: List[DocumentChunk], template_name: str = None) -> str:
        """Create an enhanced context-aware prompt using dynamic templates"""
        if not relevant_chunks:
            return query
        
        # Use the enhanced prompt builder
        return self.prompt_builder.build_prompt(
            query=query,
            chunks=relevant_chunks,
            template_name=template_name,
            include_history=True,
            include_metadata=True
        )
    
    def create_enhanced_query(self, original_query: str, chunks: List[DocumentChunk]) -> str:
        """Create an enhanced query with semantic context"""
        if not chunks:
            return original_query
        
        # Create a summary of available content
        content_summary = []
        for chunk in chunks:
            # Take first 100 characters of each chunk for summary
            summary = chunk.content[:100] + "..." if len(chunk.content) > 100 else chunk.content
            content_summary.append(summary)
        
        enhanced_query = f"""Based on the following semantically relevant document content:

{' '.join(content_summary)}

Please answer this question: {original_query}

Provide a comprehensive answer using the document information provided."""
        
        return enhanced_query
    
    def get_pipeline_statistics(self) -> Dict:
        """Get statistics about the RAG pipeline"""
        vector_stats = self.vector_store.get_statistics()
        
        return {
            **vector_stats,
            "search_method": "semantic_search",
            "embedding_model": self.vector_store.model_name,
            "vector_dimension": self.vector_store.dimension,
            "available_templates": self.prompt_builder.get_available_templates(),
            "conversation_history_length": len(self.prompt_builder.conversation_history)
        }
    
    def clear_pipeline(self):
        """Clear all data from the pipeline"""
        self.vector_store.clear()
        
        # Remove saved files
        if self.vector_store_path:
            for ext in [".faiss", ".pkl"]:
                try:
                    os.remove(self.vector_store_path + ext)
                except FileNotFoundError:
                    pass
        
        logger.info("RAG pipeline cleared")
    
    def save_pipeline(self, filepath: str = None):
        """Save the pipeline state"""
        path = filepath or self.vector_store_path
        self.vector_store.save_index(path)
        logger.info(f"RAG pipeline saved to {path}")
    
    def load_pipeline(self, filepath: str = None):
        """Load the pipeline state"""
        path = filepath or self.vector_store_path
        self.vector_store.load_index(path)
        logger.info(f"RAG pipeline loaded from {path}")
    
    def add_conversation_turn(self, user_query: str, ai_response: str):
        """Add a conversation turn to the prompt builder's history"""
        self.prompt_builder.add_to_conversation_history(user_query, ai_response)
    
    def clear_conversation_history(self):
        """Clear conversation history"""
        self.prompt_builder.clear_conversation_history()
    
    def get_debug_info(self, query: str, chunks: List[DocumentChunk]) -> Dict:
        """Get debug information about prompt construction"""
        return self.prompt_builder.create_debug_prompt(query, chunks)
    
    def add_custom_template(self, name: str, template: str, variables: Dict = None):
        """Add a custom prompt template"""
        self.prompt_builder.add_custom_template(name, template, variables)
    
    def detect_query_type(self, query: str) -> str:
        """Detect the type of query for template selection"""
        return self.prompt_builder.detect_query_type(query) 