import fitz
from document_processor import DocumentProcessor, DocumentChunk
from typing import List, Dict, Optional
import logging
import os

# Set up logging
logger = logging.getLogger(__name__)

class EnhancedPDFProcessor:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.doc_processor = DocumentProcessor(chunk_size, chunk_overlap)
        
    def validate_pdf_path(self, pdf_path: str) -> str:
        """Validate PDF file path and existence"""
        if not isinstance(pdf_path, str):
            raise ValueError("PDF path must be a string")
        
        if not os.path.exists(pdf_path):
            raise ValueError("PDF file does not exist")
        
        if not pdf_path.lower().endswith('.pdf'):
            raise ValueError("File must be a PDF")
        
        # Check file size (limit to 50MB for PDFs)
        file_size = os.path.getsize(pdf_path)
        if file_size > 50 * 1024 * 1024:  # 50MB
            raise ValueError("PDF file too large. Maximum size is 50MB")
        
        return pdf_path
        
    def extract_with_structure(self, pdf_path: str) -> List[DocumentChunk]:
        """Extract PDF with preserved structure and intelligent chunking"""
        try:
            # Validate the PDF path
            pdf_path = self.validate_pdf_path(pdf_path)
            
            # Open the PDF document
            doc = fitz.open(pdf_path)
            
            if doc.page_count == 0:
                logger.warning("PDF has no pages")
                doc.close()
                return []
            
            all_chunks = []
            max_pages = 100  # Limit to prevent memory issues
            
            # Extract text from each page with structure preservation
            for page_num in range(min(doc.page_count, max_pages)):
                try:
                    page = doc.load_page(page_num)
                    
                    # Extract text with layout preservation
                    text_blocks = page.get_text("dict")["blocks"]
                    
                    page_text = ""
                    for block in text_blocks:
                        if "lines" in block:
                            for line in block["lines"]:
                                for span in line["spans"]:
                                    page_text += span["text"] + " "
                    
                    # Create metadata for this page
                    metadata = {
                        "page_number": page_num + 1,
                        "file_path": pdf_path,
                        "document_type": "pdf",
                        "total_pages": doc.page_count
                    }
                    
                    # Process page text into chunks
                    page_chunks = self.doc_processor.create_chunks(page_text, metadata)
                    all_chunks.extend(page_chunks)
                    
                except Exception as e:
                    logger.warning(f"Error extracting text from page {page_num}: {e}")
                    continue
            
            doc.close()
            
            logger.info(f"Successfully processed PDF: {len(all_chunks)} chunks created")
            return all_chunks
            
        except fitz.FileDataError as e:
            logger.error(f"PDF file is corrupted or invalid: {e}")
            raise ValueError("PDF file is corrupted or invalid")
        except fitz.PasswordError as e:
            logger.error(f"PDF is password protected: {e}")
            raise ValueError("PDF is password protected")
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            raise ValueError(f"Failed to extract text from PDF: {str(e)}")
    
    def extract_sections(self, pdf_path: str) -> Dict[str, List[DocumentChunk]]:
        """Extract PDF with section-based chunking (identifies headers and sections)"""
        try:
            # Validate the PDF path
            pdf_path = self.validate_pdf_path(pdf_path)
            
            # Open the PDF document
            doc = fitz.open(pdf_path)
            
            if doc.page_count == 0:
                logger.warning("PDF has no pages")
                doc.close()
                return {}
            
            sections = {}
            current_section = "main"
            current_text = ""
            
            max_pages = 100  # Limit to prevent memory issues
            
            for page_num in range(min(doc.page_count, max_pages)):
                try:
                    page = doc.load_page(page_num)
                    
                    # Extract text with layout preservation
                    text_blocks = page.get_text("dict")["blocks"]
                    
                    for block in text_blocks:
                        if "lines" in block:
                            for line in block["lines"]:
                                for span in line["spans"]:
                                    text = span["text"]
                                    
                                    # Check if this might be a header (larger font, bold, etc.)
                                    font_size = span.get("size", 12)
                                    is_bold = span.get("flags", 0) & 2**4  # Bold flag
                                    
                                    # Simple header detection
                                    if font_size > 14 or is_bold:
                                        # This might be a header, start new section
                                        if current_text.strip():
                                            # Process current section
                                            metadata = {
                                                "page_number": page_num + 1,
                                                "file_path": pdf_path,
                                                "document_type": "pdf",
                                                "section": current_section
                                            }
                                            chunks = self.doc_processor.create_chunks(current_text, metadata)
                                            if chunks:
                                                sections[current_section] = chunks
                                        
                                        # Start new section
                                        current_section = text.strip()[:50]  # Use first 50 chars as section name
                                        current_text = text + " "
                                    else:
                                        current_text += text + " "
                    
                except Exception as e:
                    logger.warning(f"Error extracting text from page {page_num}: {e}")
                    continue
            
            # Process final section
            if current_text.strip():
                metadata = {
                    "page_number": page_num + 1,
                    "file_path": pdf_path,
                    "document_type": "pdf",
                    "section": current_section
                }
                chunks = self.doc_processor.create_chunks(current_text, metadata)
                if chunks:
                    sections[current_section] = chunks
            
            doc.close()
            
            logger.info(f"Successfully processed PDF with sections: {len(sections)} sections found")
            return sections
            
        except Exception as e:
            logger.error(f"Error extracting sections from PDF: {e}")
            raise ValueError(f"Failed to extract sections from PDF: {str(e)}")
    
    def get_processing_statistics(self, chunks: List[DocumentChunk]) -> Dict:
        """Get statistics about the PDF processing"""
        if not chunks:
            return {}
        
        # Get basic statistics from document processor
        stats = self.doc_processor.get_chunk_statistics(chunks)
        
        # Add PDF-specific statistics
        pages_processed = set()
        for chunk in chunks:
            if chunk.metadata.get("page_number"):
                pages_processed.add(chunk.metadata["page_number"])
        
        stats.update({
            "pages_processed": len(pages_processed),
            "total_pages": chunks[0].metadata.get("total_pages", 0) if chunks else 0,
            "processing_method": "enhanced_chunking"
        })
        
        return stats 