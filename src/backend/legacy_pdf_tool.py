import fitz
import logging
import os

# Set up logging
logger = logging.getLogger(__name__)

def validate_pdf_path(pdf_path):
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

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF with comprehensive error handling"""
    try:
        # Validate the PDF path
        pdf_path = validate_pdf_path(pdf_path)
        
        # Open the PDF document
        doc = fitz.open(pdf_path)
        
        if doc.page_count == 0:
            logger.warning("PDF has no pages")
            doc.close()
            return ""
        
        text = ""
        max_pages = 100  # Limit to prevent memory issues
        
        # Extract text from each page
        for page_num in range(min(doc.page_count, max_pages)):
            try:
                page = doc.load_page(page_num)
                page_text = page.get_text("text")
                if page_text:
                    text += page_text + "\n"
            except Exception as e:
                logger.warning(f"Error extracting text from page {page_num}: {e}")
                continue
        
        doc.close()
        
        # Clean up the extracted text
        if text:
            # Remove excessive whitespace
            text = ' '.join(text.split())
            # Limit text length to prevent memory issues
            if len(text) > 100000:  # 100KB limit
                text = text[:100000] + "... [text truncated]"
        
        return text
        
    except fitz.FileDataError as e:
        logger.error(f"PDF file is corrupted or invalid: {e}")
        raise ValueError("PDF file is corrupted or invalid")
    except fitz.PasswordError as e:
        logger.error(f"PDF is password protected: {e}")
        raise ValueError("PDF is password protected")
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {e}")
        raise ValueError(f"Failed to extract text from PDF: {str(e)}")
