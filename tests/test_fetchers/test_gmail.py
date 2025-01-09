import asyncio
from datetime import datetime, timedelta
import pytest

from src.fetchers.gmail import GmailFetcher

@pytest.mark.asyncio
async def test_gmail_fetcher():
    fetcher = GmailFetcher()
    since = datetime.now() - timedelta(days=1)
    
    documents = await fetcher.fetch_documents(since)
    
    assert isinstance(documents, list)
    
    if documents:
        doc = documents[0]
        assert 'source' in doc
        assert doc['source'] == 'gmail'
        assert 'title' in doc
        assert 'content' in doc
        assert 'mime_type' in doc
        assert 'timestamp' in doc
        assert 'metadata' in doc
        print('passed all checks') 