import asyncio
from datetime import datetime, timedelta
from loguru import logger

from src.main import fetch_and_process_documents

async def test_pipeline():
    """Test the document fetching and processing pipeline"""
    try:
        # Comment out audio generation temporarily
        original_generate_audio = None
        import src.main
        if hasattr(src.main, 'generate_audio_summary'):
            original_generate_audio = src.main.generate_audio_summary
            src.main.generate_audio_summary = lambda doc: None
        
        # Run the pipeline
        await fetch_and_process_documents()
        
        # Restore audio generation function
        if original_generate_audio:
            src.main.generate_audio_summary = original_generate_audio
            
    except Exception as e:
        logger.error(f"Pipeline test failed: {str(e)}")
        raise

if __name__ == "__main__":
    logger.info("Starting pipeline test...")
    asyncio.run(test_pipeline())
    logger.info("Pipeline test completed") 