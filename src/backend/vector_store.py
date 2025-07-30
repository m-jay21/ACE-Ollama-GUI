import numpy as np
import pickle
import os
import logging
from typing import List, Dict, Tuple, Optional
from sentence_transformers import SentenceTransformer
import faiss
from document_processor import DocumentChunk

# Set up logging
logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", dimension: int = 384):
        """
        Initialize vector store with sentence transformer model
        
        Args:
            model_name: Name of the sentence transformer model
            dimension: Dimension of the embeddings
        """
        self.model_name = model_name
        self.dimension = dimension
        self.model = None
        self.index = None
        self.chunks = []
        self.chunk_metadata = {}
        
        # Initialize the model
        self._load_model()
        
    def _load_model(self):
        """Load the sentence transformer model"""
        try:
            logger.info(f"Loading sentence transformer model: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info("Model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            raise
    
    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for a list of texts"""
        try:
            embeddings = self.model.encode(texts, show_progress_bar=False)
            logger.info(f"Generated embeddings for {len(texts)} texts")
            return embeddings
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise
    
    def add_documents(self, chunks: List[DocumentChunk]):
        """Add document chunks to the vector store"""
        if not chunks:
            return
        
        # Extract texts and metadata
        texts = [chunk.content for chunk in chunks]
        chunk_ids = [chunk.chunk_id for chunk in chunks]
        
        # Generate embeddings
        embeddings = self.generate_embeddings(texts)
        
        # Store chunks and metadata
        self.chunks.extend(chunks)
        for chunk in chunks:
            self.chunk_metadata[chunk.chunk_id] = chunk.metadata
        
        # Create or update FAISS index
        if self.index is None:
            # Create new index
            self.index = faiss.IndexFlatIP(self.dimension)  # Inner product for cosine similarity
        
        # Add embeddings to index
        self.index.add(embeddings.astype('float32'))
        
        logger.info(f"Added {len(chunks)} chunks to vector store")
    
    def search(self, query: str, top_k: int = 3) -> List[Tuple[DocumentChunk, float]]:
        """
        Search for similar chunks using semantic similarity
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of (chunk, similarity_score) tuples
        """
        if not self.chunks or self.index is None:
            return []
        
        try:
            # Generate embedding for query
            query_embedding = self.generate_embeddings([query])
            
            # Search the index
            scores, indices = self.index.search(
                query_embedding.astype('float32'), 
                min(top_k, len(self.chunks))
            )
            
            # Return results with chunks and scores
            results = []
            for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
                if idx < len(self.chunks):
                    chunk = self.chunks[idx]
                    results.append((chunk, float(score)))
            
            logger.info(f"Found {len(results)} similar chunks for query")
            return results
            
        except Exception as e:
            logger.error(f"Error searching vector store: {e}")
            return []
    
    def semantic_search(self, query: str, top_k: int = 3) -> List[DocumentChunk]:
        """Perform semantic search and return chunks only"""
        results = self.search(query, top_k)
        return [chunk for chunk, score in results]
    
    def get_similarity_scores(self, query: str, top_k: int = 3) -> List[Tuple[str, float]]:
        """Get similarity scores for debugging"""
        results = self.search(query, top_k)
        return [(chunk.content[:100] + "...", score) for chunk, score in results]
    
    def save_index(self, filepath: str):
        """Save the FAISS index to disk"""
        try:
            # Save FAISS index
            faiss.write_index(self.index, filepath + ".faiss")
            
            # Save chunks and metadata
            with open(filepath + ".pkl", "wb") as f:
                pickle.dump({
                    "chunks": self.chunks,
                    "chunk_metadata": self.chunk_metadata,
                    "model_name": self.model_name,
                    "dimension": self.dimension
                }, f)
            
            logger.info(f"Saved vector store to {filepath}")
        except Exception as e:
            logger.error(f"Error saving vector store: {e}")
            raise
    
    def load_index(self, filepath: str):
        """Load the FAISS index from disk"""
        try:
            # Load FAISS index
            self.index = faiss.read_index(filepath + ".faiss")
            
            # Load chunks and metadata
            with open(filepath + ".pkl", "rb") as f:
                data = pickle.load(f)
                self.chunks = data["chunks"]
                self.chunk_metadata = data["chunk_metadata"]
                self.model_name = data["model_name"]
                self.dimension = data["dimension"]
            
            logger.info(f"Loaded vector store from {filepath}")
        except Exception as e:
            logger.error(f"Error loading vector store: {e}")
            raise
    
    def get_statistics(self) -> Dict:
        """Get statistics about the vector store"""
        return {
            "total_chunks": len(self.chunks),
            "index_size": self.index.ntotal if self.index else 0,
            "embedding_dimension": self.dimension,
            "model_name": self.model_name,
            "total_tokens": sum(chunk.token_count for chunk in self.chunks),
            "average_tokens_per_chunk": sum(chunk.token_count for chunk in self.chunks) / len(self.chunks) if self.chunks else 0
        }
    
    def clear(self):
        """Clear all data from the vector store"""
        self.chunks = []
        self.chunk_metadata = {}
        self.index = None
        logger.info("Vector store cleared") 