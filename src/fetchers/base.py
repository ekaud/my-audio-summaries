from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class Document(BaseModel):
    """Data model for documents fetched from any source"""
    source: str
    title: str
    content: bytes | str
    mime_type: str
    url: Optional[str] = None
    timestamp: datetime
    metadata: Dict[str, Any]
    extracted_text: Optional[str] = None  # Store processed text content

    def process_with(self, processor) -> str:
        """
        Process the document with a given processor and store the result
        
        Args:
            processor: A DocumentProcessor instance that supports this document's mime_type
            
        Returns:
            str: The extracted text
            
        Raises:
            ValueError: If the processor doesn't support this document's mime_type
        """
        if not processor.supports_mime_type(self.mime_type):
            raise ValueError(f"Processor does not support mime_type: {self.mime_type}")
        
        self.extracted_text = processor.process(self.content)
        return self.extracted_text

class DocumentFetcher(ABC):
    """Base class for all document fetchers"""
    
    @abstractmethod
    async def fetch_documents(self, since: datetime) -> List[Document]:
        """
        Fetch documents from the source
        Args:
            since: datetime - fetch documents after this time
        Returns:
            List of Document objects
        """
        pass 