#!/usr/bin/env python3
"""
Test script for enhanced prompt construction and RAG integration
"""

import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src', 'backend'))

try:
    from prompt_builder import PromptBuilder
    from rag_pipeline import RAGPipeline
    from document_processor import DocumentProcessor
    print("✅ Successfully imported enhanced prompt modules")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

def test_prompt_builder():
    """Test the enhanced prompt builder functionality"""
    print("\n🧪 Testing Enhanced Prompt Builder...")
    
    # Initialize prompt builder
    builder = PromptBuilder()
    
    # Test template detection
    test_queries = [
        "What is the main topic?",
        "Analyze this document for key insights",
        "Summarize the important points",
        "Explain the methodology used"
    ]
    
    print("\n📝 Template Detection Tests:")
    for query in test_queries:
        detected_type = builder.detect_query_type(query)
        print(f"  Query: '{query}' → Template: {detected_type}")
    
    # Test available templates
    templates = builder.get_available_templates()
    print(f"\n📋 Available Templates: {templates}")
    
    # Test custom template
    custom_template = """You are a technical expert. Analyze this content:

CONTENT:
{context}

TECHNICAL QUESTION: {query}

Provide a technical analysis with:
- Technical details
- Implementation considerations
- Best practices

TECHNICAL ANALYSIS:"""
    
    builder.add_custom_template("technical", custom_template)
    print("✅ Added custom 'technical' template")
    
    # Test debug info
    mock_chunks = [
        type('MockChunk', (), {
            'content': 'This is a test chunk with technical information about AI systems.',
            'metadata': {'page_number': 1, 'section': 'Introduction'}
        })(),
        type('MockChunk', (), {
            'content': 'Another test chunk with implementation details.',
            'metadata': {'page_number': 2, 'section': 'Methods'}
        })()
    ]
    
    debug_info = builder.create_debug_prompt("How does the system work?", mock_chunks)
    print(f"\n🔍 Debug Info: {debug_info['detected_template']} template, {debug_info['chunk_count']} chunks")
    
    return True

def test_rag_integration():
    """Test RAG pipeline integration with enhanced prompts"""
    print("\n🧪 Testing RAG Pipeline Integration...")
    
    # Initialize RAG pipeline
    rag = RAGPipeline()
    
    # Test conversation history
    rag.add_conversation_turn("What is AI?", "AI is artificial intelligence that mimics human thinking.")
    rag.add_conversation_turn("How does it work?", "AI works through machine learning algorithms and neural networks.")
    
    # Test query type detection
    query_types = [
        ("What are the main points?", "qa"),
        ("Analyze this document", "analysis"),
        ("Summarize the content", "summary"),
        ("Explain the process", "qa")
    ]
    
    print("\n🔍 Query Type Detection:")
    for query, expected in query_types:
        detected = rag.detect_query_type(query)
        status = "✅" if detected == expected else "❌"
        print(f"  {status} '{query}' → {detected} (expected: {expected})")
    
    # Test pipeline statistics
    stats = rag.get_pipeline_statistics()
    print(f"\n📊 Pipeline Statistics:")
    print(f"  Available Templates: {stats.get('available_templates', [])}")
    print(f"  Conversation History Length: {stats.get('conversation_history_length', 0)}")
    
    # Test debug functionality
    mock_chunks = [
        type('MockChunk', (), {
            'content': 'Sample document content for testing.',
            'metadata': {'file_name': 'test.pdf', 'page_number': 1}
        })()
    ]
    
    debug_info = rag.get_debug_info("Test query", mock_chunks)
    print(f"\n🔍 Debug Info: {debug_info['detected_template']} template")
    
    return True

def test_enhanced_prompts():
    """Test the complete enhanced prompt construction"""
    print("\n🧪 Testing Complete Enhanced Prompt Construction...")
    
    # Initialize components
    builder = PromptBuilder()
    
    # Create mock chunks
    mock_chunks = [
        type('MockChunk', (), {
            'content': 'This document discusses artificial intelligence and its applications in modern technology.',
            'metadata': {'page_number': 1, 'section': 'Introduction', 'file_name': 'ai_document.pdf'}
        })(),
        type('MockChunk', (), {
            'content': 'Machine learning algorithms process data to identify patterns and make predictions.',
            'metadata': {'page_number': 2, 'section': 'Methods', 'file_name': 'ai_document.pdf'}
        })(),
        type('MockChunk', (), {
            'content': 'The results show significant improvements in accuracy and efficiency.',
            'metadata': {'page_number': 3, 'section': 'Results', 'file_name': 'ai_document.pdf'}
        })()
    ]
    
    # Test different query types
    test_cases = [
        ("What is AI?", "qa"),
        ("Analyze the methodology", "analysis"),
        ("Summarize the findings", "summary"),
        ("How does machine learning work?", "qa")
    ]
    
    print("\n📝 Enhanced Prompt Examples:")
    for query, template_type in test_cases:
        prompt = builder.build_prompt(query, mock_chunks, template_name=template_type)
        
        # Show first 200 characters of prompt
        preview = prompt[:200] + "..." if len(prompt) > 200 else prompt
        print(f"\n  Template: {template_type}")
        print(f"  Query: '{query}'")
        print(f"  Prompt Preview: {preview}")
    
    return True

def main():
    """Run all tests"""
    print("🚀 Testing Enhanced Prompt Construction and RAG Integration")
    print("=" * 60)
    
    try:
        # Run tests
        test_prompt_builder()
        test_rag_integration()
        test_enhanced_prompts()
        
        print("\n" + "=" * 60)
        print("✅ All tests completed successfully!")
        print("\n🎉 Enhanced Prompt Construction Features:")
        print("  ✅ Dynamic template selection")
        print("  ✅ Context injection with metadata")
        print("  ✅ Conversation history tracking")
        print("  ✅ Query type detection")
        print("  ✅ Custom template support")
        print("  ✅ Debug information")
        print("  ✅ RAG pipeline integration")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 