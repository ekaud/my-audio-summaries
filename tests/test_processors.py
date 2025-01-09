import pytest
from datetime import datetime
from pathlib import Path

from src.fetchers.base import Document
from src.processors.pdf import PDFProcessor
from src.processors.text import TextProcessor
from src.main import ProcessorRegistry, setup_processors

@pytest.fixture
def processor_registry():
    return setup_processors()

@pytest.fixture
def sample_pdf_doc():
    pdf_path = Path("tests/example-documents/Attention is all you need.pdf")
    with open(pdf_path, "rb") as f:
        content = f.read()
    
    return Document(
        source="test",
        title="Attention is all you need.pdf",
        content=content,
        mime_type="application/pdf",
        timestamp=datetime.now(),
        metadata={"test": True}
    )

@pytest.fixture
def sample_text_doc():
    text_path = Path("tests/example-documents/mock-BoD-draft.txt")
    with open(text_path, "r") as f:
        content = f.read()
    
    return Document(
        source="test",
        title="mock-BoD-draft.txt",
        content=content,
        mime_type="text/plain",
        timestamp=datetime.now(),
        metadata={"test": True}
    )

def test_processor_registry(processor_registry):
    """Test that processor registry correctly maps MIME types to processors"""
    assert isinstance(processor_registry.get_processor("application/pdf"), PDFProcessor)
    assert isinstance(processor_registry.get_processor("text/plain"), TextProcessor)
    assert processor_registry.get_processor("application/unknown") is None

def test_pdf_processing(sample_pdf_doc):
    """Test PDF document processing"""
    processor = PDFProcessor()
    
    # Process the document
    text = sample_pdf_doc.process_with(processor)
    
    # Verify processing worked
    assert text is not None
    assert len(text) > 0
    assert "attention" in text.lower()
    assert sample_pdf_doc.extracted_text == text

def test_text_processing(sample_text_doc):
    """Test text document processing"""
    processor = TextProcessor()
    
    # Process the document
    text = sample_text_doc.process_with(processor)
    
    # Verify processing worked
    assert text is not None
    assert len(text) > 0
    assert "board members" in text.lower()
    assert sample_text_doc.extracted_text == text

def test_wrong_mime_type(sample_pdf_doc):
    """Test that using wrong processor raises error"""
    processor = TextProcessor()
    
    with pytest.raises(ValueError) as exc_info:
        sample_pdf_doc.process_with(processor)
    assert "does not support mime_type" in str(exc_info.value)

def test_process_with_stores_text(sample_pdf_doc):
    """Test that process_with stores the extracted text"""
    processor = PDFProcessor()
    
    # Before processing
    assert sample_pdf_doc.extracted_text is None
    
    # Process
    text = sample_pdf_doc.process_with(processor)
    
    # After processing
    assert sample_pdf_doc.extracted_text is not None
    assert sample_pdf_doc.extracted_text == text
