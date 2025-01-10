import pytest
from datetime import datetime
from pathlib import Path

from src.fetchers.base import Document
from src.audio.generator import generate_dialogue, get_mp3, generate_audio_summary, DialogueItem
from src.processors.pdf import PDFProcessor

@pytest.fixture
def sample_text():
    """Load a sample text file for testing"""
    text_path = Path("tests/example-documents/mock-BoD-draft.txt")
    with open(text_path, "r") as f:
        return f.read()

@pytest.fixture
def sample_document(sample_text):
    """Create a test document with extracted text"""
    return Document(
        source="test",
        title="test_doc.txt",
        content=sample_text,
        mime_type="text/plain",
        timestamp=datetime.now(),
        metadata={"test": True},
        extracted_text=sample_text
    )

@pytest.fixture
def sample_pdf_document():
    """Create a test document from a PDF file"""
    pdf_path = Path("tests/example-documents/Gene therapy for deafness.pdf")
    with open(pdf_path, "rb") as f:
        content = f.read()
    
    # Create document without extracted text first
    doc = Document(
        source="test",
        title="Gene therapy for deafness.pdf",
        content=content,
        mime_type="application/pdf",
        timestamp=datetime.now(),
        metadata={"test": True}
    )
    
    # Process PDF to get extracted text
    processor = PDFProcessor()
    doc.process_with(processor)
    
    return doc

def test_dialogue_generation(sample_text):
    """Test that dialogue is generated correctly"""
    dialogue = generate_dialogue(sample_text)
    
    # Check dialogue structure
    assert dialogue.scratchpad  # Should have planning notes
    assert dialogue.dialogue    # Should have dialogue items
    assert len(dialogue.dialogue) > 0
    
    # Check dialogue content
    first_line = dialogue.dialogue[0]
    assert isinstance(first_line, DialogueItem)
    assert first_line.text
    assert first_line.speaker in ["female-1", "male-1", "female-2"]
    assert first_line.voice in ["alloy", "onyx", "shimmer"]

def test_mp3_generation():
    """Test that audio is generated correctly"""
    test_text = "Hello, this is a test."
    audio = get_mp3(test_text, "alloy")
    
    # Check that we got valid MP3 data
    assert audio.startswith(b'\xFF\xFB')  # MP3 magic number
    assert len(audio) > 0

@pytest.mark.asyncio
async def test_audio_summary_generation(sample_document):
    """Test the full audio summary generation pipeline"""
    audio, transcript = await generate_audio_summary(sample_document)
    
    # Check audio
    assert isinstance(audio, bytes)
    assert len(audio) > 0
    assert audio.startswith(b'\xFF\xFB')  # MP3 magic number
    
    # Check transcript
    assert isinstance(transcript, str)
    assert len(transcript) > 0
    assert ":" in transcript  # Should have speaker labels

@pytest.mark.asyncio
async def test_audio_summary_no_text():
    """Test error handling when document has no extracted text"""
    doc = Document(
        source="test",
        title="empty.txt",
        content="",
        mime_type="text/plain",
        timestamp=datetime.now(),
        metadata={},
        extracted_text=None
    )
    
    with pytest.raises(ValueError) as exc_info:
        await generate_audio_summary(doc)
    assert "has no extracted text" in str(exc_info.value) 

@pytest.mark.asyncio
async def test_pdf_to_audio_pipeline(sample_pdf_document):
    """Test the complete pipeline from PDF to audio"""
    # Verify PDF text extraction worked
    assert sample_pdf_document.extracted_text
    assert "gene therapy" in sample_pdf_document.extracted_text.lower()
    
    # Generate audio summary
    audio, transcript = await generate_audio_summary(sample_pdf_document)
    
    # Check audio
    assert isinstance(audio, bytes)
    assert len(audio) > 0
    assert audio.startswith(b'\xFF\xFB')  # MP3 magic number
    
    # Check transcript
    assert isinstance(transcript, str)
    assert len(transcript) > 0
    assert ":" in transcript  # Should have speaker labels
    
    # Check that key concepts from PDF appear in transcript
    assert "gene therapy" in transcript.lower()
    assert "deafness" in transcript.lower() 