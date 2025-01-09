import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Type

from loguru import logger

from src.fetchers.gmail import GmailFetcher
from src.fetchers.base import Document
from src.processors.base import DocumentProcessor
from src.processors.pdf import PDFProcessor
from src.processors.text import TextProcessor  # We'll need to create this
# from src.audio.generator import generate_audio_summary  # We'll migrate this from docs-to-audio

class ProcessorRegistry:
    """Registry for document processors"""
    
    def __init__(self):
        self._processors: Dict[str, DocumentProcessor] = {}
    
    def register(self, mime_types: List[str], processor: DocumentProcessor):
        """Register a processor for one or more MIME types"""
        for mime_type in mime_types:
            self._processors[mime_type.lower()] = processor
    
    def get_processor(self, mime_type: str) -> DocumentProcessor:
        """Get the appropriate processor for a MIME type"""
        return self._processors.get(mime_type.lower())

def setup_processors() -> ProcessorRegistry:
    """Initialize and configure document processors"""
    registry = ProcessorRegistry()
    
    # Register processors for different MIME types
    registry.register(['application/pdf'], PDFProcessor())
    registry.register(['text/plain'], TextProcessor())
    # Add more processors as needed
    
    return registry

async def process_documents(documents: List[Document], registry: ProcessorRegistry) -> List[Document]:
    """Process documents with appropriate processors"""
    processed_docs = []
    
    for doc in documents:
        if processor := registry.get_processor(doc.mime_type):
            try:
                logger.info(f"Processing document: {doc.title}")
                doc.process_with(processor)
                processed_docs.append(doc)
            except Exception as e:
                logger.error(f"Failed to process {doc.title}: {str(e)}")
                continue
        else:
            logger.warning(f"No processor found for MIME type: {doc.mime_type}")
    
    return processed_docs

async def fetch_and_process_documents():
    """Main function to fetch and process documents"""
    # Initialize fetchers
    fetchers = [
        GmailFetcher()
    ]
    
    # Initialize processor registry
    processor_registry = setup_processors()
    
    # Fetch documents from last 72 hours
    since = datetime.now() - timedelta(days=3)
    
    try:
        # Gather documents from all sources concurrently
        tasks = [fetcher.fetch_documents(since) for fetcher in fetchers]
        all_documents = await asyncio.gather(*tasks)
        
        # Flatten results
        documents = [doc for source_docs in all_documents for doc in source_docs]
        logger.info(f"Fetched {len(documents)} documents")
        
        # Process documents
        processed_docs = await process_documents(documents, processor_registry)
        logger.info(f"Successfully processed {len(processed_docs)} documents")
        
        # Generate audio summaries
        for doc in processed_docs:
            if doc.extracted_text:
                try:
                    audio_file = await generate_audio_summary(doc)
                    logger.info(f"Generated audio summary for: {doc.title}")
                except Exception as e:
                    logger.error(f"Failed to generate audio for {doc.title}: {str(e)}")
            else:
                logger.warning(f"No extracted text available for: {doc.title}")
    
    except Exception as e:
        logger.error(f"Error in fetch_and_process_documents: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(fetch_and_process_documents()) 