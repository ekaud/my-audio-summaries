# My Audio Summaries - Project Context

## Project Overview

This project fetches documents from various sources (Gmail, Google Calendar, Hacker News) and generates compelling audio summaries using AI. It processes different document types (PDFs, Google Docs, plain text) and converts them into engaging podcast-style audio content.

## Directory Structure

```
my-audio-summaries/
├── src/                    # Main source code
│   ├── fetchers/          # Document fetchers for different sources
│   ├── processors/        # Document processors for different formats
│   ├── audio/            # Audio generation and utilities
│   └── utils/            # Shared utilities
├── tests/                # Test files and examples
├── config/              # Configuration files
├── credentials/         # API credentials and tokens
├── logs/               # Log files
├── output/             # Generated audio and transcripts
│   ├── audio/          # Generated MP3 files
│   └── transcripts/    # Generated transcripts
└── notebooks/          # Jupyter notebooks for testing
```

## System Architecture

1. **Document Fetching Layer** (`src/fetchers/`)

   - Base fetcher interface defining common functionality
   - Specialized fetchers for different sources (Gmail, Google Drive)
   - Handles authentication and API interactions

2. **Document Processing Layer** (`src/processors/`)

   - Converts different document formats to plain text
   - Supports PDF, plain text, and Google Workspace formats
   - Extensible for new document types

3. **Audio Generation Layer** (`src/audio/`)

   - Converts processed text into natural dialogue
   - Generates audio using text-to-speech
   - Manages audio file storage and cleanup

4. **Utility Layer** (`src/utils/`)
   - Authentication helpers
   - Logging configuration
   - File management utilities

## Core Data Model

The system is built around the `Document` class, which represents a document from any source:

```python
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
```

## Data Flow

1. **Document Fetching**

   - Fetchers retrieve documents from various sources
   - Documents are wrapped in the `Document` class
   - Metadata and original content are preserved

2. **Document Processing**

   - Documents are processed based on their MIME type
   - Text is extracted and stored in `extracted_text`
   - Original content is preserved for reference

3. **Audio Generation**
   - Extracted text is converted to dialogue format
   - Dialogue is converted to audio using TTS
   - Audio files and transcripts are saved to output directory

## Configuration

The project uses multiple configuration sources:

- `config/default.yaml` for general settings
- `.env` for sensitive credentials
- Command-line arguments for runtime options

## Logging

Detailed logging is implemented throughout:

- Log files are stored in `logs/` directory
- Different log levels (DEBUG, INFO, WARNING, ERROR)
- Timestamps and contextual information included
