import base64
import os
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
import re

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import yaml
from loguru import logger
import sys

from src.fetchers.base import DocumentFetcher, Document
from src.utils.auth import get_google_credentials

class GmailFetcher(DocumentFetcher):
    """Fetches documents from Gmail attachments"""

    def __init__(self, verbose: bool = False):
        """
        Initialize Gmail fetcher
        Args:
            verbose: If True, log detailed information about the fetching process
        """
        with open("config/default.yaml", "r") as f:
            self.config = yaml.safe_load(f)
        
        self.credentials = get_google_credentials(self.config["google"]["scopes"])
        self.gmail_service = build('gmail', 'v1', credentials=self.credentials)
        self.drive_service = build('drive', 'v3', credentials=self.credentials)
        self.docs_service = build('docs', 'v1', credentials=self.credentials)
        self.verbose = verbose
        
        # Cache for processed documents
        self._processed_attachments = set()  # Store (message_id, attachment_id) tuples
        self._processed_gdrive_resources = set()  # Store gdrive_resource_ids
        
        # Set up logging based on verbosity
        self._setup_logging()
    
    def _setup_logging(self):
        """Configure logging based on verbosity level"""
        logger.remove()  # Remove existing handlers
        
        if self.verbose:
            # In verbose mode, show DEBUG and above
            log_level = "DEBUG"
        else:
            # In normal mode, show WARNING and above
            log_level = "WARNING"
        
        # Configure console logging
        logger.add(sys.stderr, level=log_level)
        
        # Configure file logging (always includes all levels for debugging)
        logger.add(
            "logs/gmail_fetcher_{time}.log",
            level="DEBUG",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
        )

    def _log(self, level: str, message: str):
        """Helper method for logging"""
        # Always log to file (handled by loguru's level filtering)
        getattr(logger, level.lower())(message)

    async def fetch_documents(self, since: datetime) -> List[Document]:
        """Fetch both email attachments and linked Google Docs"""
        date_str = since.strftime("%Y/%m/%d")
        query = f"after:{date_str}"
        
        self._log('INFO', f"Searching with query: '{query}'")
        
        try:
            # Get all matching messages with full details
            results = self.gmail_service.users().messages().list(
                userId='me',
                q=query
            ).execute()
            messages = results.get('messages', [])
            
            if not messages:
                self._log('INFO', "No messages found")
                return []
                
            self._log('INFO', f"Found {len(messages)} emails")
            
            documents = []
            for message in messages:
                # Get full message details
                msg = self.gmail_service.users().messages().get(
                    userId='me',
                    id=message['id'],
                    format='full'
                ).execute()
                # Process attachments and Google Docs links
                documents.extend(await self._process_message(msg))
            self._log('INFO', "----end of fetch_documents----")
            self._log('INFO', f"Successfully processed {len(documents)} documents total")
            return documents
            
        except Exception as e:
            self._log('ERROR', f"Error in fetch_documents: {str(e)}")
            return []

    async def _process_message(self, msg: Dict) -> List[Document]:
        """Process a single email message for both attachments and Google Drive links"""
        documents = []
        headers = {h['name']: h['value'] for h in msg['payload']['headers']}
        
        self._log('INFO', f"******Processing message: {msg['id']}******")
        self._log('INFO', f"Subject: {headers.get('Subject', 'No subject')}")
        self._log('INFO', f"From: {headers.get('From', 'No sender')}")
        
        # Process attachments
        attachments = []
        for part in self._get_parts(msg['payload']):
            if filename := part.get('filename'):
                mime_type = part.get('mimeType', 'unknown')
                
                if self._is_supported_file_type(filename, mime_type):
                    if 'body' in part and 'attachmentId' in part['body']:
                        attachment_id = part['body']['attachmentId']
                        cache_key = (msg['id'], attachment_id)
                        
                        if cache_key in self._processed_attachments:
                            self._log('INFO', f"Skipping already processed attachment: {filename}")
                            continue
                            
                        try:
                            attachment = self._get_attachment(msg['id'], attachment_id)
                            self._processed_attachments.add(cache_key)
                            attachments.append(Document(
                                source='gmail.attachment',
                                title=filename,
                                content=attachment,
                                mime_type=mime_type,
                                url=f"https://mail.google.com/mail/u/0/#inbox/{msg['id']}",
                                timestamp=datetime.fromtimestamp(int(msg['internalDate'])/1000),
                                metadata={
                                    'subject': headers.get('Subject', ''),
                                    'from': headers.get('From', ''),
                                    'message_id': msg['id'],
                                    'attachment_id': attachment_id
                                }
                            ))
                        except Exception as e:
                            self._log('ERROR', f"Error processing attachment {filename}: {str(e)}")
        self._log('INFO', f"Found {len(attachments)} attachments")
        documents.extend(attachments)

        gdrive_resources = []
        # Process Google Drive links
        if body := self._get_email_body(msg):
            for gdrive_id in self._extract_gdrive_ids(body):
                self._log('DEBUG', f"Processing Google Drive ID: {gdrive_id}")
                
                if gdrive_id in self._processed_gdrive_resources:
                    self._log('INFO', f"Skipping already processed Google Drive resource: {gdrive_id}")
                    continue
                    
                try:
                    if doc := await self._fetch_gdrive_resource(gdrive_id):
                        self._processed_gdrive_resources.add(gdrive_id)
                        self._log('DEBUG', f"Successfully fetched document: {doc.title}")
                        gdrive_resources.append(doc)
                    else:
                        self._log('DEBUG', f"No document returned for ID: {gdrive_id}")
                except Exception as e:
                    self._log('ERROR', f"Error processing Google Drive resource {gdrive_id}: {str(e)}")
                    self._log('DEBUG', f"Exception type: {type(e)}")
        
        self._log('INFO', f"Found {len(gdrive_resources)} Google Drive resources")
        documents.extend(gdrive_resources)        
        return documents

    def _get_email_body(self, msg: Dict) -> str:
        """Extract email body text"""
        if 'parts' in msg['payload']:
            for part in msg['payload']['parts']:
                if part['mimeType'] == 'text/plain':
                    body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                    self._log('DEBUG', f"Found email body: {body[:200]}...")  # Log first 200 chars
                    return body
        self._log('DEBUG', "No plain text body found in email")
        return ""

    def _extract_gdrive_ids(self, text: str) -> List[str]:
        """Extract Google Drive resource IDs from text"""
        patterns = [
            r'docs\.google\.com/document/d/([a-zA-Z0-9-_]+)',
            r'docs\.google\.com/spreadsheets/d/([a-zA-Z0-9-_]+)',
            r'docs\.google\.com/presentation/d/([a-zA-Z0-9-_]+)'
        ]
        
        gdrive_ids = set()
        for pattern in patterns:
            matches = list(re.finditer(pattern, text))
            if matches:
                self._log('DEBUG', f"Found matches for pattern {pattern}: {[m.group(1) for m in matches]}")
            gdrive_ids.update(match.group(1) for match in matches)
        
        if gdrive_ids:
            self._log('DEBUG', f"Extracted Google Drive IDs: {gdrive_ids}")
        else:
            self._log('DEBUG', "No Google Drive IDs found in text")
            
        return list(gdrive_ids)

    async def _fetch_gdrive_resource(self, resource_id: str) -> Optional[Document]:
        """Fetch and process a Google Drive resource (Document, Sheet, or Presentation)"""
        try:
            self._log('DEBUG', f"Attempting to fetch Google Drive resource: {resource_id}")
            
            file_metadata = self.drive_service.files().get(
                fileId=resource_id,
                fields='name,mimeType,modifiedTime,owners'
            ).execute()
            
            self._log('DEBUG', f"Got metadata: {file_metadata}")
            
            mime_type = file_metadata['mimeType']
            
            # Map MIME types to source identifiers
            source_types = {
                'application/vnd.google-apps.document': 'gmail.gdrive.doc',
                'application/vnd.google-apps.spreadsheet': 'gmail.gdrive.sheet',
                'application/vnd.google-apps.presentation': 'gmail.gdrive.slides'
            }
            
            # Handle different Google Drive resource types
            if mime_type == 'application/vnd.google-apps.document':
                self._log('DEBUG', "Have determined this is a google doc, attempting to extract text")
                doc = self.docs_service.documents().get(documentId=resource_id).execute()
                content = self._extract_text_from_doc(doc)
                self._log('DEBUG', f"Successfully extracted text from Google Doc: {content[:200]}...")
            elif mime_type == 'application/vnd.google-apps.spreadsheet':
                self._log('DEBUG', "Have determined this is a google sheet, attempting to extract text")
                csv_content = self.drive_service.files().export(
                    fileId=resource_id,
                    mimeType='text/csv'
                ).execute().decode('utf-8')
                content = self._format_spreadsheet_content(csv_content)
            
            elif mime_type == 'application/vnd.google-apps.presentation':
                self._log('DEBUG', "Have determined this is a google slides, attempting to extract text")
                slides_content = self.drive_service.files().export(
                    fileId=resource_id,
                    mimeType='text/plain'
                ).execute().decode('utf-8')
                content = self._format_presentation_content(slides_content)
            
            else:
                self._log('WARNING', f"Unsupported Google Drive resource type: {mime_type}")
                return None

            return Document(
                source=source_types.get(mime_type, 'google_drive-other'),
                title=file_metadata['name'],
                content=content,
                mime_type='text/plain',
                url=f"https://docs.google.com/document/d/{resource_id}/",
                timestamp=datetime.fromisoformat(file_metadata['modifiedTime']),
                metadata={
                    'gdrive_id': resource_id,  # Changed from resource_id
                    'owner': file_metadata['owners'][0]['emailAddress'] if file_metadata.get('owners') else None,
                    'last_modified': file_metadata['modifiedTime'],
                    'original_mime_type': mime_type
                }
            )
        except Exception as e:
            self._log('ERROR', f"Could not fetch Google Drive resource {resource_id}: {str(e)}")
            return None

    def _extract_text_from_doc(self, doc: Dict) -> str:
        """Extract plain text from Google Doc structure"""
        text = []
        for elem in doc.get('body', {}).get('content', []):
            if 'paragraph' in elem:
                for part in elem['paragraph']['elements']:
                    if 'textRun' in part:
                        text.append(part['textRun'].get('content', ''))
        return ''.join(text)

    def _get_parts(self, payload):
        """Recursively get all parts from the email payload"""
        parts = []
        
        # If this part has parts, process them
        if 'parts' in payload:
            for part in payload['parts']:
                parts.extend(self._get_parts(part))
        
        # Add this part if it's not a container
        if payload.get('filename'):
            parts.append(payload)
            
        return parts

    def _get_attachment(self, msg_id: str, attachment_id: str) -> bytes:
        """Helper method to fetch the actual attachment data"""
        attachment = self.gmail_service.users().messages().attachments().get(
            userId='me',
            messageId=msg_id,
            id=attachment_id
        ).execute()

        data = attachment['data']
        return base64.urlsafe_b64decode(data)

    def _is_supported_file_type(self, filename: str, mime_type: str = None) -> bool:
        """Check if the file type is supported"""
        supported_types = {
            '.pdf': {'application/pdf'},
            '.txt': {'text/plain'},
            '.doc': {'application/msword'},
            '.docx': {'application/vnd.openxmlformats-officedocument.wordprocessingml.document'}
        }
        
        # Check file extension
        extension = None
        for ext in supported_types:
            if filename.lower().endswith(ext):
                extension = ext
                break
        
        if not extension:
            self._log('DEBUG', f"File {filename} does not have a supported extension")
            return False
        
        # If MIME type is provided, verify it matches the extension
        if mime_type and mime_type not in supported_types[extension]:
            self._log('WARNING', f"File {filename} has extension {extension} but MIME type {mime_type}")
            return False
        
        return True 

    def _format_spreadsheet_content(self, csv_content: str) -> str:
        """Format CSV content to be more readable"""
        import csv
        from io import StringIO
        
        output = []
        reader = csv.reader(StringIO(csv_content))
        
        # Get headers
        headers = next(reader, [])
        if headers:
            output.append("SPREADSHEET CONTENTS:")
            output.append("Headers: " + " | ".join(headers))
            output.append("-" * 40)
            
            # Process rows
            for row_num, row in enumerate(reader, 1):
                output.append(f"Row {row_num}:")
                for header, value in zip(headers, row):
                    if value.strip():  # Only include non-empty values
                        output.append(f"  {header}: {value}")
                output.append("")
        
        return "\n".join(output)

    def _format_presentation_content(self, slides_content: str) -> str:
        """Format presentation content with clear slide breaks"""
        slides = slides_content.split('\n\n')  # Assuming slides are separated by double newlines
        formatted_slides = []
        
        for i, slide in enumerate(slides, 1):
            if slide.strip():  # Only include non-empty slides
                formatted_slides.extend([
                    f"\nSLIDE {i}:",
                    "=" * 40,
                    slide.strip(),
                    ""
                ])
        
        return "\n".join(formatted_slides) 