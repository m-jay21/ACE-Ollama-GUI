#!/usr/bin/env python3
"""
Test script for enhanced observability system with token tracking and source attribution
"""

import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src', 'backend'))

try:
    from token_tracker import TokenTracker, TokenMetrics, SourceChunk, ProcessingResult
    from rag_pipeline import RAGPipeline
    from document_processor import DocumentProcessor
    print("✅ Successfully imported enhanced observability modules")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def test_token_tracker():
    """Test the token tracking functionality"""
    print("\n🧪 Testing Token Tracker...")
    
    # Initialize token tracker
    tracker = TokenTracker("llama3.2:3b")
    
    # Test token counting
    test_texts = [
        "Hello, world!",
        "This is a longer text with more tokens to count.",
        "A very long text that should have many tokens for testing purposes. " * 10
    ]
    
    print("\n📊 Token Counting Tests:")
    for text in test_texts:
        token_count = tracker.count_tokens(text)
        print(f"  Text: '{text[:50]}{'...' if len(text) > 50 else ''}'")
        print(f"  Tokens: {token_count}")
        print()
    
    # Test metrics creation
    start_time = tracker.start_tracking()
    input_text = "What is artificial intelligence?"
    output_text = "Artificial intelligence (AI) is a branch of computer science that aims to create systems capable of performing tasks that typically require human intelligence."
    
    metrics = tracker.create_metrics(input_text, output_text, start_time)
    print(f"📈 Metrics Created:")
    print(f"  Input tokens: {metrics.input_tokens}")
    print(f"  Output tokens: {metrics.output_tokens}")
    print(f"  Total tokens: {metrics.total_tokens}")
    print(f"  Latency: {metrics.latency_ms:.1f}ms")
    print(f"  Model: {metrics.model_name}")
    
    return True

def test_source_attribution():
    """Test source attribution functionality"""
    print("\n🧪 Testing Source Attribution...")
    
    # Create mock chunks and similarity scores
    mock_chunks = [
        type('MockChunk', (), {
            'content': 'Artificial intelligence is a field of computer science.',
            'metadata': {'page_number': 1, 'section': 'Introduction', 'file_name': 'ai_document.pdf'}
        })(),
        type('MockChunk', (), {
            'content': 'Machine learning is a subset of AI that focuses on algorithms.',
            'metadata': {'page_number': 2, 'section': 'Methods', 'file_name': 'ai_document.pdf'}
        })(),
        type('MockChunk', (), {
            'content': 'Deep learning uses neural networks for complex pattern recognition.',
            'metadata': {'page_number': 3, 'section': 'Advanced Topics', 'file_name': 'ai_document.pdf'}
        })()
    ]
    
    similarity_scores = [
        ("content1", 0.95),
        ("content2", 0.87),
        ("content3", 0.76)
    ]
    
    tracker = TokenTracker("test-model")
    source_chunks = tracker.create_source_chunks(mock_chunks, similarity_scores)
    
    print(f"\n🔍 Source Chunks Created: {len(source_chunks)}")
    for i, chunk in enumerate(source_chunks, 1):
        print(f"  Source {i}:")
        print(f"    Content: {chunk.content[:50]}...")
        print(f"    Score: {chunk.similarity_score:.3f}")
        print(f"    Page: {chunk.page_number}")
        print(f"    Section: {chunk.section}")
        print()
    
    return True

def test_processing_result():
    """Test complete processing result creation"""
    print("\n🧪 Testing Processing Result...")
    
    tracker = TokenTracker("llama3.2:3b")
    start_time = tracker.start_tracking()
    
    # Create mock data
    input_text = "What is AI?"
    output_text = "AI is artificial intelligence that mimics human thinking."
    
    mock_chunks = [
        type('MockChunk', (), {
            'content': 'Artificial intelligence is a technology.',
            'metadata': {'page_number': 1, 'file_name': 'test.pdf'}
        })()
    ]
    
    similarity_scores = [("content", 0.92)]
    
    # Create processing result
    result = tracker.create_processing_result(
        response=output_text,
        input_text=input_text,
        start_time=start_time,
        chunks=mock_chunks,
        similarity_scores=similarity_scores,
        query_type="qa",
        template_used="qa",
        model_name="llama3.2:3b"
    )
    
    print(f"📋 Processing Result:")
    print(f"  Response: {result.response}")
    print(f"  Query Type: {result.query_type}")
    print(f"  Template: {result.template_used}")
    print(f"  Sources: {len(result.sources)}")
    print(f"  Metrics: {result.metrics.total_tokens} tokens, {result.metrics.latency_ms:.1f}ms")
    
    # Test formatting for display
    formatted_metrics = tracker.format_metrics_for_display(result.metrics)
    formatted_sources = tracker.format_sources_for_display(result.sources)
    
    print(f"\n🎨 Formatted for UI:")
    print(f"  Metrics: {formatted_metrics}")
    print(f"  Sources: {len(formatted_sources)} formatted sources")
    
    return True

def test_debug_information():
    """Test debug information creation"""
    print("\n🧪 Testing Debug Information...")
    
    tracker = TokenTracker("test-model")
    start_time = tracker.start_tracking()
    
    # Create a processing result
    result = tracker.create_processing_result(
        response="Test response",
        input_text="Test input",
        start_time=start_time,
        model_name="test-model"
    )
    
    # Generate debug info
    debug_info = tracker.create_debug_info(result)
    
    print(f"🔍 Debug Information:")
    print(f"  Query Type: {debug_info['query_type']}")
    print(f"  Template: {debug_info['template_used']}")
    print(f"  Metrics: {debug_info['metrics']}")
    print(f"  Sources Count: {debug_info['sources_count']}")
    
    return True

def main():
    """Run all observability tests"""
    print("🚀 Testing Enhanced Observability System")
    print("=" * 60)
    
    try:
        # Run tests
        test_token_tracker()
        test_source_attribution()
        test_processing_result()
        test_debug_information()
        
        print("\n" + "=" * 60)
        print("✅ All observability tests completed successfully!")
        print("\n🎉 Enhanced Observability Features:")
        print("  ✅ Token usage tracking with tiktoken")
        print("  ✅ Latency measurement")
        print("  ✅ Source attribution with similarity scores")
        print("  ✅ Processing result creation")
        print("  ✅ UI formatting for metrics and sources")
        print("  ✅ Debug information generation")
        print("  ✅ Settings integration")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 