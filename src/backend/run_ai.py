import argparse
import os
import sys
import logging
from ai_tool import runData, runImage, validate_input, validate_model_name
import pdf_tool
from pdf_enhanced import EnhancedPDFProcessor
from rag_pipeline import RAGPipeline

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
    allowed_extensions = ['.pdf', '.png', '.jpg', '.jpeg', '.bmp', '.gif']
    
    if ext not in allowed_extensions:
        raise ValueError(f"Unsupported file type: {ext}. Supported types: {', '.join(allowed_extensions)}")
    
    return file_path

def process_pdf_with_chunking(file_path: str, query: str, model: str):
    """Process PDF using enhanced chunking and RAG pipeline"""
    try:
        # Initialize enhanced PDF processor
        pdf_processor = EnhancedPDFProcessor()
        
        # Extract and chunk the PDF
        print("Processing document chunks...", flush=True)
        chunks = pdf_processor.extract_with_structure(file_path)
        
        if not chunks:
            print("Warning: No content could be extracted from the PDF.", flush=True)
            return
        
        # Get processing statistics
        stats = pdf_processor.get_processing_statistics(chunks)
        print(f"Document processed: {stats.get('total_chunks', 0)} chunks created", flush=True)
        
        # Create RAG pipeline
        rag = RAGPipeline()
        rag.add_document(chunks)
        
        # Find relevant chunks for the query
        relevant_chunks = rag.find_relevant_chunks(query, top_k=3)
        
        # Create context-aware prompt
        enhanced_query = rag.create_context_prompt(query, relevant_chunks)
        
        # Process with AI
        for word in runData(enhanced_query, model):
            print(word, end='', flush=True)
            
    except Exception as e:
        logger.error(f"Error in enhanced PDF processing: {e}")
        print(f"Error processing PDF: {str(e)}", flush=True)

def main():
    try:
        parser = argparse.ArgumentParser(description="Process AI Query with optional file input.")
        parser.add_argument('--query', type=str, required=True, help="The user query text")
        parser.add_argument('--model', type=str, required=True, help="The AI model to use")
        parser.add_argument('--file', type=str, default="", help="Optional file path (PDF or image)")
        parser.add_argument('--use-chunking', action='store_true', help="Use enhanced document chunking for PDFs")
        
        args = parser.parse_args()
        
        # Validate inputs
        query = validate_input(args.query)
        model = validate_model_name(args.model)
        file_path = validate_file_path(args.file)

        if file_path:
            ext = os.path.splitext(file_path)[1].lower()
            if ext == ".pdf":
                if args.use_chunking:
                    # Use enhanced chunking and RAG pipeline
                    process_pdf_with_chunking(file_path, query, model)
                else:
                    # Use legacy PDF processing
                    try:
                        # Extract PDF text and prepend it to the query
                        pdf_text = pdf_tool.extract_text_from_pdf(file_path)
                        if pdf_text:
                            query = "PDF TEXT:\n" + pdf_text + "\nUSER QUERY:\n" + query
                        else:
                            print("Warning: No text could be extracted from the PDF.", flush=True)
                    except Exception as e:
                        print(f"Error processing PDF: {str(e)}", flush=True)
                        return
                    
                    # Process as a text-based query
                    for word in runData(query, model):
                        print(word, end='', flush=True)
                    
            elif ext in [".png", ".jpg", ".jpeg", ".bmp", ".gif"]:
                # Process as an image-based query
                for word in runImage(query, file_path):
                    print(word, end='', flush=True)
            else:
                print("Unsupported file type.", flush=True)
        else:
            # No file provided; process as a normal text query.
            for word in runData(query, model):
                print(word, end='', flush=True)
                
    except ValueError as e:
        print(f"Validation error: {str(e)}", flush=True)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error in run_ai: {e}")
        print(f"An unexpected error occurred: {str(e)}", flush=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
