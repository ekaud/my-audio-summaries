from typing import Union, BinaryIO, TextIO
from pathlib import Path
import io

from pypdf import PdfReader
from loguru import logger

from .base import DocumentProcessor

class PDFProcessor(DocumentProcessor):
    """Processor for PDF documents"""
    
    def supports_mime_type(self, mime_type: str) -> bool:
        """Check if this processor supports the given MIME type"""
        return mime_type.lower() in {'application/pdf'}
    
    def process(self, content: Union[bytes, str, BinaryIO, TextIO]) -> str:
        """Extract text content from a PDF document"""
        try:
            # Handle different input types
            if isinstance(content, (str, Path)):
                # Treat as file path
                with open(content, 'rb') as f:
                    reader = PdfReader(f)
                    return self._extract_text(reader)
            elif isinstance(content, bytes):
                # Raw PDF data
                reader = PdfReader(io.BytesIO(content))
                return self._extract_text(reader)
            elif isinstance(content, (BinaryIO, TextIO)):
                # File-like object
                reader = PdfReader(content)
                return self._extract_text(reader)
            else:
                raise ValueError(f"Unsupported content type: {type(content)}")
            
        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}")
            raise
    
    def _extract_text(self, reader: PdfReader) -> str:
        """Extract text from a PDF reader object"""
        try:
            text_parts = []
            
            # Process each page
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
            
            # Join all parts with double newlines for clear page separation
            return "\n\n".join(text_parts)
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            raise 