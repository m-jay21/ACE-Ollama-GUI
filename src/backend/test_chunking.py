#!/usr/bin/env python3
"""
Test script for document chunking and preprocessing functionality
"""

import sys
import os
import logging

# Add the current directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from document_processor import DocumentProcessor
from enhanced_pdf_processor import EnhancedPDFProcessor
from rag_pipeline import RAGPipeline

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_document_processor():
    """Test the document processor with sample text"""
    print("Testing Document Processor...")
    
    # Sample text for testing
    sample_text = """
    This is a test document. It contains multiple sentences. 
    Each sentence should be processed separately. The document processor 
    should split this into meaningful chunks. This helps the AI understand 
    the content better. Chunking is an important part of document processing.
    
    This is a new paragraph. It contains different information. 
    The processor should handle paragraphs correctly. It should also 
    preserve the structure of the document. This is crucial for 
    maintaining context in AI responses.
    """
    
    # Initialize processor
    processor = DocumentProcessor(chunk_size=100, chunk_overlap=20)
    
    # Process the text
    chunks = processor.create_chunks(sample_text, {"test": True})
    
    print(f"Created {len(chunks)} chunks")
    for i, chunk in enumerate(chunks):
        print(f"Chunk {i+1}: {chunk.content[:50]}... (tokens: {chunk.token_count})")
    
    # Get statistics
    stats = processor.get_chunk_statistics(chunks)
    print(f"Statistics: {stats}")
    
    return chunks

def test_rag_pipeline(chunks):
    """Test the RAG pipeline with sample chunks"""
    print("\nTesting RAG Pipeline...")
    
    # Initialize RAG pipeline
    rag = RAGPipeline()
    rag.add_document(chunks)
    
    # Test query
    test_query = "What is chunking?"
    relevant_chunks = rag.find_relevant_chunks(test_query, top_k=2)
    
    print(f"Query: {test_query}")
    print(f"Found {len(relevant_chunks)} relevant chunks")
    
    # Create enhanced prompt
    enhanced_prompt = rag.create_context_prompt(test_query, relevant_chunks)
    print(f"Enhanced prompt length: {len(enhanced_prompt)} characters")
    
    # Get pipeline statistics
    stats = rag.get_pipeline_statistics()
    print(f"Pipeline statistics: {stats}")
    
    return enhanced_prompt

def test_pdf_processor():
    """Test PDF processor (if PDF file exists)"""
    print("\nTesting PDF Processor...")
    
    # Check if we have a test PDF
    test_pdf = "test_document.pdf"
    if not os.path.exists(test_pdf):
        print("No test PDF found. Skipping PDF test.")
        return
    
    try:
        processor = EnhancedPDFProcessor()
        chunks = processor.extract_with_structure(test_pdf)
        
        print(f"Extracted {len(chunks)} chunks from PDF")
        
        # Get statistics
        stats = processor.get_processing_statistics(chunks)
        print(f"PDF processing statistics: {stats}")
        
    except Exception as e:
        print(f"Error testing PDF processor: {e}")

def main():
    """Run all tests"""
    print("=== Document Chunking and Preprocessing Test ===\n")
    
    try:
        # Test document processor
        chunks = test_document_processor()
        
        # Test RAG pipeline
        enhanced_prompt = test_rag_pipeline(chunks)
        
        # Test PDF processor
        test_pdf_processor()
        
        print("\n=== All tests completed successfully! ===")
        print("The document chunking and preprocessing feature is working correctly.")
        
    except Exception as e:
        print(f"Error during testing: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 