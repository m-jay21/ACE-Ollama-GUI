import time
import tiktoken
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class TokenMetrics:
    """Token usage metrics for a single request"""
    input_tokens: int
    output_tokens: int
    total_tokens: int
    latency_ms: float
    processing_time: str
    timestamp: str
    model_name: str

@dataclass
class SourceChunk:
    """Source chunk information for attribution"""
    content: str
    similarity_score: float
    page_number: Optional[int] = None
    section: Optional[str] = None
    file_name: Optional[str] = None
    chunk_index: Optional[int] = None

@dataclass
class ProcessingResult:
    """Complete processing result with metrics and sources"""
    response: str
    metrics: TokenMetrics
    sources: List[SourceChunk]
    query_type: str
    template_used: str

class TokenTracker:
    """Enhanced token tracking and source attribution system"""
    
    def __init__(self, model_name: str = "unknown"):
        self.model_name = model_name
        self.encoding = None
        self._initialize_encoding()
    
    def _initialize_encoding(self):
        """Initialize tiktoken encoding"""
        try:
            # Use cl100k_base encoding (used by GPT-4, GPT-3.5-turbo)
            self.encoding = tiktoken.get_encoding("cl100k_base")
            logger.info("Initialized tiktoken encoding")
        except Exception as e:
            logger.warning(f"Could not initialize tiktoken encoding: {e}")
            self.encoding = None
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken"""
        if not self.encoding:
            # Fallback: rough estimation (1 token ≈ 4 characters)
            return len(text) // 4
        
        try:
            return len(self.encoding.encode(text))
        except Exception as e:
            logger.warning(f"Error counting tokens: {e}")
            # Fallback estimation
            return len(text) // 4
    
    def start_tracking(self) -> float:
        """Start timing a request"""
        return time.time()
    
    def create_metrics(self, 
                      input_text: str, 
                      output_text: str, 
                      start_time: float,
                      model_name: str = None) -> TokenMetrics:
        """Create token metrics for a request"""
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000
        
        input_tokens = self.count_tokens(input_text)
        output_tokens = self.count_tokens(output_text)
        total_tokens = input_tokens + output_tokens
        
        processing_time = f"{latency_ms:.1f}ms"
        
        return TokenMetrics(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            latency_ms=latency_ms,
            processing_time=processing_time,
            timestamp=datetime.now().isoformat(),
            model_name=model_name or self.model_name
        )
    
    def create_source_chunks(self, 
                           chunks: List[Any], 
                           similarity_scores: List[tuple]) -> List[SourceChunk]:
        """Create source chunk information for attribution"""
        source_chunks = []
        
        for i, (chunk, score) in enumerate(zip(chunks, similarity_scores)):
            source_chunk = SourceChunk(
                content=chunk.content,
                similarity_score=score[1] if isinstance(score, tuple) else score,
                page_number=chunk.metadata.get('page_number'),
                section=chunk.metadata.get('section'),
                file_name=chunk.metadata.get('file_name'),
                chunk_index=i + 1
            )
            source_chunks.append(source_chunk)
        
        return source_chunks
    
    def create_processing_result(self,
                               response: str,
                               input_text: str,
                               start_time: float,
                               chunks: List[Any] = None,
                               similarity_scores: List[tuple] = None,
                               query_type: str = "unknown",
                               template_used: str = "default",
                               model_name: str = None) -> ProcessingResult:
        """Create complete processing result with metrics and sources"""
        
        # Create metrics
        metrics = self.create_metrics(input_text, response, start_time, model_name)
        
        # Create source chunks if available
        sources = []
        if chunks and similarity_scores:
            sources = self.create_source_chunks(chunks, similarity_scores)
        
        return ProcessingResult(
            response=response,
            metrics=metrics,
            sources=sources,
            query_type=query_type,
            template_used=template_used
        )
    
    def format_metrics_for_display(self, metrics: TokenMetrics) -> Dict[str, str]:
        """Format metrics for UI display"""
        return {
            "input_tokens": f"{metrics.input_tokens:,}",
            "output_tokens": f"{metrics.output_tokens:,}",
            "total_tokens": f"{metrics.total_tokens:,}",
            "latency": f"{metrics.latency_ms:.1f}ms",
            "processing_time": metrics.processing_time,
            "model": metrics.model_name
        }
    
    def format_sources_for_display(self, sources: List[SourceChunk]) -> List[Dict[str, Any]]:
        """Format source chunks for UI display"""
        formatted_sources = []
        
        for source in sources:
            # Truncate content for display
            display_content = source.content[:200] + "..." if len(source.content) > 200 else source.content
            
            formatted_source = {
                "content": display_content,
                "full_content": source.content,
                "score": f"{source.similarity_score:.3f}",
                "page": source.page_number,
                "section": source.section,
                "file_name": source.file_name,
                "index": source.chunk_index
            }
            formatted_sources.append(formatted_source)
        
        return formatted_sources
    
    def create_debug_info(self, result: ProcessingResult) -> Dict[str, Any]:
        """Create debug information for troubleshooting"""
        return {
            "query_type": result.query_type,
            "template_used": result.template_used,
            "metrics": {
                "input_tokens": result.metrics.input_tokens,
                "output_tokens": result.metrics.output_tokens,
                "total_tokens": result.metrics.total_tokens,
                "latency_ms": result.metrics.latency_ms,
                "model": result.metrics.model_name
            },
            "sources_count": len(result.sources),
            "sources": [
                {
                    "index": source.chunk_index,
                    "score": source.similarity_score,
                    "page": source.page_number,
                    "section": source.section,
                    "content_preview": source.content[:100] + "..." if len(source.content) > 100 else source.content
                }
                for source in result.sources
            ]
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get token tracker statistics"""
        return {
            "model_name": self.model_name,
            "encoding_available": self.encoding is not None,
            "encoding_type": "cl100k_base" if self.encoding else "fallback"
        } 