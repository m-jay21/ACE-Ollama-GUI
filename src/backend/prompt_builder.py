from typing import List, Dict, Optional, Any
from document_processor import DocumentChunk
import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)

class PromptTemplate:
    """Base class for prompt templates"""
    
    def __init__(self, template: str, variables: Dict[str, Any] = None):
        self.template = template
        self.variables = variables or {}
    
    def format(self, **kwargs) -> str:
        """Format the template with provided variables"""
        # Merge template variables with provided kwargs
        all_vars = {**self.variables, **kwargs}
        
        # Simple template formatting with {variable} syntax
        formatted = self.template
        for key, value in all_vars.items():
            placeholder = f"{{{key}}}"
            if placeholder in formatted:
                formatted = formatted.replace(placeholder, str(value))
        
        return formatted

class PromptBuilder:
    """Enhanced prompt builder with dynamic templates and context injection"""
    
    def __init__(self):
        self.templates = self._initialize_templates()
        self.conversation_history = []
        self.max_history_length = 5
    
    def _initialize_templates(self) -> Dict[str, PromptTemplate]:
        """Initialize default prompt templates"""
        templates = {}
        
        # Default RAG template
        templates["default_rag"] = PromptTemplate(
            template="""You are a helpful AI assistant with access to relevant document information.

DOCUMENT CONTEXT:
{context}

CONVERSATION HISTORY:
{history}

USER QUERY: {query}

INSTRUCTIONS:
- Answer based on the provided document context
- If the context doesn't contain enough information, say so
- Be concise but comprehensive
- Cite specific parts of the document when relevant

ANSWER:"""
        )
        
        # Analysis template for detailed document analysis
        templates["analysis"] = PromptTemplate(
            template="""You are an expert document analyst. Analyze the following document content:

DOCUMENT CONTENT:
{context}

ANALYSIS REQUEST: {query}

Please provide a detailed analysis including:
- Key points and insights
- Important findings
- Relevant details
- Any patterns or trends identified

ANALYSIS:"""
        )
        
        # Summary template for document summarization
        templates["summary"] = PromptTemplate(
            template="""You are a skilled summarizer. Create a comprehensive summary of the following document:

DOCUMENT CONTENT:
{context}

SUMMARY REQUEST: {query}

Please provide:
- Main points and key insights
- Important details and findings
- Structured summary with clear sections

SUMMARY:"""
        )
        
        # Q&A template for specific questions
        templates["qa"] = PromptTemplate(
            template="""You are a helpful assistant answering questions about a document.

DOCUMENT CONTENT:
{context}

QUESTION: {query}

Please provide:
- Direct answer to the question
- Supporting evidence from the document
- Additional relevant information if available

ANSWER:"""
        )
        
        return templates
    
    def add_to_conversation_history(self, user_query: str, ai_response: str):
        """Add a conversation turn to history"""
        self.conversation_history.append({
            "user": user_query,
            "ai": ai_response,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep only recent history
        if len(self.conversation_history) > self.max_history_length:
            self.conversation_history = self.conversation_history[-self.max_history_length:]
    
    def format_conversation_history(self) -> str:
        """Format conversation history for prompt inclusion"""
        if not self.conversation_history:
            return "No previous conversation."
        
        history_text = []
        for i, turn in enumerate(self.conversation_history[-3:], 1):  # Last 3 turns
            history_text.append(f"Turn {i}:")
            history_text.append(f"User: {turn['user']}")
            history_text.append(f"AI: {turn['ai']}")
            history_text.append("")
        
        return "\n".join(history_text)
    
    def format_context(self, chunks: List[DocumentChunk], include_metadata: bool = True) -> str:
        """Format document chunks into structured context"""
        if not chunks:
            return "No relevant document content found."
        
        context_parts = []
        
        for i, chunk in enumerate(chunks, 1):
            # Format chunk content
            content = chunk.content.strip()
            
            # Add metadata if requested
            metadata_info = ""
            if include_metadata and chunk.metadata:
                metadata_parts = []
                if chunk.metadata.get("page_number"):
                    metadata_parts.append(f"Page {chunk.metadata['page_number']}")
                if chunk.metadata.get("section"):
                    metadata_parts.append(f"Section: {chunk.metadata['section']}")
                if chunk.metadata.get("file_name"):
                    metadata_parts.append(f"File: {chunk.metadata['file_name']}")
                
                if metadata_parts:
                    metadata_info = f" [{', '.join(metadata_parts)}]"
            
            # Create formatted chunk
            chunk_text = f"Section {i}{metadata_info}:\n{content}\n"
            context_parts.append(chunk_text)
        
        return "\n".join(context_parts)
    
    def detect_query_type(self, query: str) -> str:
        """Detect the type of query to select appropriate template"""
        query_lower = query.lower()
        
        # Analysis keywords
        analysis_keywords = ["analyze", "analysis", "examine", "investigate", "study", "review"]
        if any(keyword in query_lower for keyword in analysis_keywords):
            return "analysis"
        
        # Summary keywords
        summary_keywords = ["summarize", "summary", "summarise", "overview", "brief", "outline"]
        if any(keyword in query_lower for keyword in summary_keywords):
            return "summary"
        
        # Q&A keywords (default)
        qa_keywords = ["what", "how", "why", "when", "where", "who", "explain", "describe", "tell me"]
        if any(keyword in query_lower for keyword in qa_keywords):
            return "qa"
        
        return "default_rag"
    
    def build_prompt(self, 
                    query: str, 
                    chunks: List[DocumentChunk], 
                    template_name: str = None,
                    include_history: bool = True,
                    include_metadata: bool = True) -> str:
        """
        Build an enhanced prompt with dynamic template selection
        
        Args:
            query: User's query
            chunks: Relevant document chunks
            template_name: Specific template to use (auto-detected if None)
            include_history: Whether to include conversation history
            include_metadata: Whether to include chunk metadata
            
        Returns:
            Formatted prompt string
        """
        try:
            # Auto-detect template if not specified
            if template_name is None:
                template_name = self.detect_query_type(query)
            
            # Get template
            template = self.templates.get(template_name, self.templates["default_rag"])
            
            # Format context
            context = self.format_context(chunks, include_metadata)
            
            # Format history
            history = self.format_conversation_history() if include_history else "No previous conversation."
            
            # Build prompt
            prompt = template.format(
                query=query,
                context=context,
                history=history,
                chunk_count=len(chunks),
                timestamp=datetime.now().isoformat()
            )
            
            logger.info(f"Built prompt using template '{template_name}' with {len(chunks)} chunks")
            return prompt
            
        except Exception as e:
            logger.error(f"Error building prompt: {e}")
            # Fallback to simple prompt
            return f"Based on the following document content:\n\n{self.format_context(chunks)}\n\nQuestion: {query}\n\nAnswer:"
    
    def create_debug_prompt(self, query: str, chunks: List[DocumentChunk]) -> Dict[str, Any]:
        """Create a debug version showing prompt construction details"""
        debug_info = {
            "query": query,
            "detected_template": self.detect_query_type(query),
            "chunk_count": len(chunks),
            "chunks_with_metadata": []
        }
        
        for i, chunk in enumerate(chunks):
            chunk_info = {
                "index": i + 1,
                "content_preview": chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content,
                "metadata": chunk.metadata,
                "length": len(chunk.content)
            }
            debug_info["chunks_with_metadata"].append(chunk_info)
        
        return debug_info
    
    def add_custom_template(self, name: str, template: str, variables: Dict[str, Any] = None):
        """Add a custom prompt template"""
        self.templates[name] = PromptTemplate(template, variables)
        logger.info(f"Added custom template '{name}'")
    
    def get_available_templates(self) -> List[str]:
        """Get list of available template names"""
        return list(self.templates.keys())
    
    def clear_conversation_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        logger.info("Conversation history cleared") 