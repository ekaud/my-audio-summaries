from abc import ABC, abstractmethod
from typing import Union, BinaryIO, TextIO

class DocumentProcessor(ABC):
    """Base class for document processors that convert various formats to text"""
    
    @abstractmethod
    def process(self, content: Union[bytes, str, BinaryIO, TextIO]) -> str:
        """
        Process a document and return its text content
        
        Args:
            content: The document content in various possible formats
                    - bytes: Raw document data
                    - str: Text content or file path
                    - BinaryIO: File-like object for binary content
                    - TextIO: File-like object for text content
        
        Returns:
            str: The extracted text content
        
        Raises:
            ValueError: If the document format is invalid or unsupported
            IOError: If there are issues reading the document
        """
        pass
    
    @abstractmethod
    def supports_mime_type(self, mime_type: str) -> bool:
        """
        Check if this processor supports a given MIME type
        
        Args:
            mime_type: The MIME type to check
            
        Returns:
            bool: True if this processor can handle the MIME type
        """
        pass 