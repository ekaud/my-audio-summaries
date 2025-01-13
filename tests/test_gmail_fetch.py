import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from datetime import datetime, timedelta
import argparse
from io import BytesIO
from pathlib import Path
from loguru import logger
from pypdf import PdfReader

from src.fetchers.gmail import GmailFetcher

async def test_fetch(verbose: bool = False):
    """Test Gmail fetcher with both attachments and Google Doc links"""
    # Initialize the fetcher with verbosity setting
    fetcher = GmailFetcher(verbose=verbose)
    
    # Fetch documents from the last 7 days
    since = datetime.now() - timedelta(days=7)
    print('****Begin Fetch****')
    print(f"The current date is {datetime.now()}")
    try:
        documents = await fetcher.fetch_documents(since)
        
        # Group documents by type
        pdfs = []
        gdrive_docs = []
        gdrive_sheets = []
        gdrive_slides = []
        
        for doc in documents:
            if doc.source == 'gmail.attachment':
                pdfs.append(doc)
            elif doc.source == 'gmail.gdrive.doc':
                gdrive_docs.append(doc)
            elif doc.source == 'gmail.gdrive.sheet':
                gdrive_sheets.append(doc)
            elif doc.source == 'gmail.gdrive.slides':
                gdrive_slides.append(doc)
        
        # Print summary
        print(f"\nFound {len(documents)} total documents:")
        print(f"- {len(pdfs)} PDF attachments")
        print(f"- {len(gdrive_docs)} Google Docs")
        print(f"- {len(gdrive_sheets)} Google Sheets")
        print(f"- {len(gdrive_slides)} Google Slides")
        
        # Test PDF content
        if pdfs:
            print("\nTesting PDF attachments:")
            for pdf in pdfs:
                try:
                    reader = PdfReader(BytesIO(pdf.content))
                    num_pages = len(reader.pages)
                    first_page_preview = reader.pages[0].extract_text()[:100]
                    print(f"\n{pdf.title} ({num_pages} pages)")
                    print(f"Preview: {first_page_preview}...")
                except Exception as e:
                    print(f"Error reading PDF {pdf.title}: {str(e)}")
        
        # Test Google Drive content
        gdrive_resources = gdrive_docs + gdrive_sheets + gdrive_slides
        if gdrive_resources:
            print("\nTesting Google Drive content:")
            for doc in gdrive_resources:
                print(f"\n{doc.title} ({doc.source})")
                print(f"Preview: {doc.content[:100]}...")
                print(f"URL: {doc.url}")
                print(f"Owner: {doc.metadata.get('owner', 'Unknown')}")
        
        return documents
        
    except Exception as e:
        logger.error(f"Error during fetch: {str(e)}")
        return []

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test Gmail fetcher')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose logging')
    parser.add_argument('--save', action='store_true', help='Save documents to examples directory')
    args = parser.parse_args()
    
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Run the async function
    documents = asyncio.run(test_fetch(verbose=args.verbose))
    
   # Optionally save documents
    if args.save: 
        examples_dir = Path("tests/example-documents")
        examples_dir.mkdir(exist_ok=True)
        
        for doc in documents:
            try:
                if doc.source == 'gmail.attachment':
                    # Save PDFs as binary
                    pdf_path = examples_dir / doc.title
                    with open(pdf_path, 'wb') as f:
                        f.write(doc.content)
                    print(f"Saved PDF: {doc.title}")
                
                elif doc.source.startswith('gmail.gdrive.'):
                    # Save Google Drive content as text
                    clean_title = doc.title.replace('/', '_')  # Handle potential slashes in title
                    txt_path = examples_dir / f"{clean_title}.txt"
                    with open(txt_path, 'w', encoding='utf-8') as f:
                        # Add metadata at the top of the file
                        f.write(f"Title: {doc.title}\n")
                        f.write(f"Type: {doc.source}\n")
                        f.write(f"URL: {doc.url}\n")
                        f.write(f"Owner: {doc.metadata.get('owner', 'Unknown')}\n")
                        f.write("\n" + "="*50 + "\n\n")
                        f.write(doc.content)
                    print(f"Saved {doc.source}: {clean_title}.txt")
                    
            except Exception as e:
                print(f"Error saving {doc.title}: {str(e)}")