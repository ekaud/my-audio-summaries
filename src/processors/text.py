from typing import Union, BinaryIO, TextIO
from pathlib import Path

from loguru import logger

from .base import DocumentProcessor

class TextProcessor(DocumentProcessor):
    """Processor for plain text documents"""
    
    def supports_mime_type(self, mime_type: str) -> bool:
        """Check if this processor supports the given MIME type"""
        return mime_type.lower() in {'text/plain'}
    
    def process(self, content: Union[bytes, str, BinaryIO, TextIO]) -> str:
        """Process a text document and return its content"""
        try:
            # Handle different input types
            if isinstance(content, (str, Path)):
                # If it's a path, read the file
                if isinstance(content, str) and '\n' in content:
                    # If it contains newlines, treat as raw text
                    return content
                # Otherwise treat as file path
                with open(content, 'r', encoding='utf-8') as f:
                    return f.read()
            
            elif isinstance(content, bytes):
                # Try to decode bytes as UTF-8
                return content.decode('utf-8')
            
            elif isinstance(content, (BinaryIO, TextIO)):
                # Read from file-like object
                if isinstance(content, TextIO):
                    return content.read()
                else:
                    return content.read().decode('utf-8')
            
            else:
                raise ValueError(f"Unsupported content type: {type(content)}")
            
        except Exception as e:
            logger.error(f"Error processing text document: {str(e)}")
            raise 