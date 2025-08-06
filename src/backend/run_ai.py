import argparse
import os
import sys
import logging
import time
from ai_tool import runData, runImage, validate_input, validate_model_name
import legacy_pdf_tool as pdf_tool
from enhanced_pdf_processor import EnhancedPDFProcessor
from rag_pipeline import RAGPipeline
from document_loader import DocumentLoader
from document_processor import DocumentProcessor
from token_tracker import TokenTracker
from metrics_collector import get_metrics_collector

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def validate_file_path(file_path):
    """Validate file path and type"""
    if not file_path or not isinstance(file_path, str):
        return None
    
    file_path = file_path.strip()
    if not file_path:
        return None
    
    if not os.path.exists(file_path):
        raise ValueError(f"File does not exist: {file_path}")
    
    # Check file extension
    ext = os.path.splitext(file_path)[1].lower()
    allowed_extensions = ['.pdf', '.txt', '.md', '.csv', '.json', '.docx', '.doc', '.png', '.jpg', '.jpeg', '.bmp', '.gif']
    
    if ext not in allowed_extensions:
        raise ValueError(f"Unsupported file type: {ext}. Supported types: {', '.join(allowed_extensions)}")
    
    return file_path

def process_document_with_enhanced_rag(file_path: str, query: str, model: str):
    """Process any supported document using enhanced RAG with semantic search, vector embeddings, and dynamic prompt construction"""
    try:
        # Initialize token tracker
        token_tracker = TokenTracker(model)
        start_time = token_tracker.start_tracking()
        
        # Initialize document loader
        loader = DocumentLoader()
        
        # Load document content
        print("*Loading document...*", flush=True)
        doc_data = loader.load_document(file_path)
        content = doc_data['content']
        metadata = doc_data['metadata']
        
        if not content or content.strip() == "":
            print("*Warning: No content could be extracted from the document.*", flush=True)
            return
        
        print(f"*Document loaded: {metadata['file_name']} ({metadata['file_type']})*", flush=True)
        
        # Initialize document processor for chunking
        doc_processor = DocumentProcessor()
        
        # Create chunks from document content
        print("*Processing document chunks...*", flush=True)
        chunks = doc_processor.create_chunks(content, metadata)
        
        if not chunks:
            print("*Warning: No chunks could be created from the document.*", flush=True)
            return
        
        print(f"*Document processed: {len(chunks)} chunks created*", flush=True)
        
        # Create RAG pipeline with vector embeddings
        print("*Generating vector embeddings...*", flush=True)
        rag = RAGPipeline()
        rag.add_document(chunks)
        
        # Get pipeline statistics
        pipeline_stats = rag.get_pipeline_statistics()
        print(f"*Vector embeddings created: {pipeline_stats.get('embedding_model', 'Unknown')} model*", flush=True)
        
        # Detect query type for template selection
        query_type = rag.detect_query_type(query)
        print(f"*Query type detected: {query_type}*", flush=True)
        
        # Find relevant chunks using semantic search
        print("*Performing semantic search...*", flush=True)
        relevant_chunks = rag.find_relevant_chunks(query, top_k=3)
        
        # Get similarity scores for source attribution
        similarity_scores = rag.get_similarity_scores(query, top_k=3)
        if similarity_scores:
            print("*Found relevant content using semantic search*", flush=True)
        
        # Create enhanced context-aware prompt with dynamic templates
        enhanced_query = rag.create_context_prompt(query, relevant_chunks, template_name=query_type)
        
        # Process with AI and collect response
        ai_response = ""
        for word in runData(enhanced_query, model):
            print(word, end='', flush=True)
            ai_response += word
        
        # Add conversation turn to history for future context
        rag.add_conversation_turn(query, ai_response)
        
        # Create processing result with metrics and sources
        processing_result = token_tracker.create_processing_result(
            response=ai_response,
            input_text=enhanced_query,
            start_time=start_time,
            chunks=relevant_chunks,
            similarity_scores=similarity_scores,
            query_type=query_type,
            template_used=query_type,
            model_name=model
        )
        
        # Record metrics for dashboard (non-blocking)
        try:
            get_metrics_collector().record_query({
                'model_name': model,
                'input_tokens': processing_result.metrics.input_tokens,
                'output_tokens': processing_result.metrics.output_tokens,
                'total_tokens': processing_result.metrics.total_tokens,
                'latency_ms': processing_result.metrics.latency_ms,
                'query_type': query_type,
                'file_processed': True,
                'success': True
            })
        except Exception as e:
            # Don't let metrics collection interfere with the main query
            logger.warning(f"Metrics recording failed: {e}")
        
        # Print enhanced metrics
        metrics = token_tracker.format_metrics_for_display(processing_result.metrics)
        print(f"\n*METRICS: {metrics['total_tokens']} tokens • {metrics['latency']} • {len(processing_result.sources)} sources*", flush=True)
        
        # Print source information
        if processing_result.sources:
            sources = token_tracker.format_sources_for_display(processing_result.sources)
            print("*SOURCES USED:*", flush=True)
            for i, source in enumerate(sources, 1):
                print(f"*{i}. Score: {source['score']} • Page: {source.get('page', 'N/A')} • {source['content'][:50]}...*", flush=True)
            
    except Exception as e:
        logger.error(f"Error in enhanced RAG processing: {e}")
        print(f"Error in enhanced RAG processing: {str(e)}", flush=True)
        sys.exit(1)

def process_document_with_simple_extraction(file_path: str, query: str, model: str):
    """Process document with simple text extraction (basic fallback method)"""
    try:
        # Initialize token tracker
        token_tracker = TokenTracker(model)
        start_time = token_tracker.start_tracking()
        
        # Initialize document loader
        loader = DocumentLoader()
        
        # Load document content
        doc_data = loader.load_document(file_path)
        content = doc_data['content']
        
        if not content or content.strip() == "":
            print("Warning: No content could be extracted from the document.", flush=True)
            return
        
        # Simple text processing
        enhanced_query = f"DOCUMENT TEXT:\n{content}\n\nUSER QUERY:\n{query}"
        
        # Process with AI and collect response
        ai_response = ""
        for word in runData(enhanced_query, model):
            print(word, end='', flush=True)
            ai_response += word
        
        # Create processing result with metrics
        processing_result = token_tracker.create_processing_result(
            response=ai_response,
            input_text=enhanced_query,
            start_time=start_time,
            model_name=model
        )
        
        # Record metrics for dashboard (non-blocking)
        try:
            get_metrics_collector().record_query({
                'model_name': model,
                'input_tokens': processing_result.metrics.input_tokens,
                'output_tokens': processing_result.metrics.output_tokens,
                'total_tokens': processing_result.metrics.total_tokens,
                'latency_ms': processing_result.metrics.latency_ms,
                'query_type': 'document',
                'file_processed': True,
                'success': True
            })
        except Exception as e:
            # Don't let metrics collection interfere with the main query
            logger.warning(f"Metrics recording failed: {e}")
        
        # Print metrics
        metrics = token_tracker.format_metrics_for_display(processing_result.metrics)
        print(f"\n*METRICS: {metrics['total_tokens']} tokens • {metrics['latency']}*", flush=True)
        
        # Ensure clean exit
        sys.exit(0)
            
    except Exception as e:
        logger.error(f"Error in simple document processing: {e}")
        print(f"Error in simple document processing: {str(e)}", flush=True)
        sys.exit(1)

def main():
    try:
        parser = argparse.ArgumentParser(description="Process AI Query with optional file input.")
        parser.add_argument('--query', type=str, required=True, help="The user query text")
        parser.add_argument('--model', type=str, required=True, help="The AI model to use")
        parser.add_argument('--file', type=str, default="", help="Optional file path (PDF, TXT, MD, CSV, JSON, DOCX, DOC, or image)")
        parser.add_argument('--use-semantic-search', action='store_true', help="Use semantic search with vector embeddings")
        
        args = parser.parse_args()
        
        # Validate inputs
        query = validate_input(args.query)
        model = validate_model_name(args.model)
        file_path = validate_file_path(args.file)

        if file_path:
            ext = os.path.splitext(file_path)[1].lower()
            
            # Document types that support semantic search
            document_types = ['.pdf', '.txt', '.md', '.csv', '.json', '.docx', '.doc']
            image_types = ['.png', '.jpg', '.jpeg', '.bmp', '.gif']
            
            if ext in document_types:
                if args.use_semantic_search:
                    # Use enhanced RAG processing with semantic search
                    process_document_with_enhanced_rag(file_path, query, model)
                else:
                    # Use simple document processing
                    process_document_with_simple_extraction(file_path, query, model)
                    
            elif ext in image_types:
                # Process as an image-based query
                for word in runImage(query, file_path):
                    print(word, end='', flush=True)
                sys.exit(0)
            else:
                print("Unsupported file type.", flush=True)
                sys.exit(1)
        else:
            # No file provided; process as a normal text query with token tracking.
            token_tracker = TokenTracker(model)
            start_time = token_tracker.start_tracking()
            
            ai_response = ""
            for word in runData(query, model):
                print(word, end='', flush=True)
                ai_response += word
            
            # Create processing result with metrics
            processing_result = token_tracker.create_processing_result(
                response=ai_response,
                input_text=query,
                start_time=start_time,
                model_name=model
            )
            
            # Record metrics for dashboard (non-blocking)
            try:
                get_metrics_collector().record_query({
                    'model_name': model,
                    'input_tokens': processing_result.metrics.input_tokens,
                    'output_tokens': processing_result.metrics.output_tokens,
                    'total_tokens': processing_result.metrics.total_tokens,
                    'latency_ms': processing_result.metrics.latency_ms,
                    'query_type': 'text',
                    'file_processed': False,
                    'success': True
                })
            except Exception as e:
                # Don't let metrics collection interfere with the main query
                logger.warning(f"Metrics recording failed: {e}")
            
            # Print metrics
            metrics = token_tracker.format_metrics_for_display(processing_result.metrics)
            print(f"\n*METRICS: {metrics['total_tokens']} tokens • {metrics['latency']}*", flush=True)
            
            # Ensure clean exit
            sys.exit(0)
                
    except ValueError as e:
        print(f"Validation error: {str(e)}", flush=True)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error in run_ai: {e}")
        print(f"An unexpected error occurred: {str(e)}", flush=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
    # Ensure we exit cleanly
    sys.exit(0)
