"""File handling utilities for extracting text from documents."""
import io
import httpx
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class FileHandler:
    """Handles downloading and extracting text from various file formats."""
    
    SUPPORTED_EXTENSIONS = {'.txt', '.pdf', '.docx', '.doc'}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
    
    @staticmethod
    def get_file_extension(filename: str) -> str:
        """Get lowercase file extension."""
        if '.' in filename:
            return '.' + filename.rsplit('.', 1)[-1].lower()
        return ''
    
    @staticmethod
    def is_supported(filename: str) -> bool:
        """Check if file type is supported."""
        ext = FileHandler.get_file_extension(filename)
        return ext in FileHandler.SUPPORTED_EXTENSIONS
    
    @staticmethod
    async def download_file(url: str, auth_token: Optional[str] = None) -> bytes:
        """Download file from URL."""
        headers = {}
        if auth_token:
            headers['Authorization'] = f'Bearer {auth_token}'
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, follow_redirects=True)
            response.raise_for_status()
            return response.content

    @staticmethod
    async def download_file_with_bot_credentials(url: str) -> bytes:
        """Download file using the Bot's app credentials via Microsoft Graph API.
        
        This is required for SharePoint/OneDrive files in Teams.
        The app registration MUST have Sites.Read.All or Files.Read.All 
        API permissions with admin consent for this to work.
        """
        try:
            from msal import ConfidentialClientApplication
            from src.config import Config
            import re
            import urllib.parse
            
            # SharePoint files require Graph API access
            authority = f"https://login.microsoftonline.com/{Config.APP_TENANT_ID}"
            scope = ["https://graph.microsoft.com/.default"]
            
            logger.info(f"Attempting Graph API token acquisition for tenant: {Config.APP_TENANT_ID}")
            
            # Create MSAL app for client credentials flow
            msal_app = ConfidentialClientApplication(
                client_id=Config.APP_ID,
                client_credential=Config.APP_PASSWORD,
                authority=authority
            )
            
            # Acquire token using client credentials (app-only)
            result = msal_app.acquire_token_silent(scope, account=None)
            if not result:
                result = msal_app.acquire_token_for_client(scopes=scope)
            
            if "access_token" not in result:
                error = result.get("error", "Unknown")
                error_desc = result.get("error_description", "No description")
                raise PermissionError(f"Failed to get Graph token: {error} - {error_desc}")
            
            token = result["access_token"]
            logger.info(f"Got Graph API token successfully")
            
            headers = {
                'Authorization': f'Bearer {token}',
                'Accept': 'application/octet-stream'
            }
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Convert SharePoint URL to Graph API format
                # Format: https://tenant-my.sharepoint.com/personal/user_domain/Documents/path/file.pdf
                
                if "sharepoint.com" in url.lower():
                    logger.info(f"Converting SharePoint URL to Graph API format...")
                    
                    # Extract hostname and path from URL
                    parsed = urllib.parse.urlparse(url)
                    hostname = parsed.netloc  # e.g., o365testlabca-my.sharepoint.com
                    path = urllib.parse.unquote(parsed.path)  # Decode URL encoding
                    
                    logger.info(f"Hostname: {hostname}, Path: {path}")
                    
                    # For personal OneDrive URLs (contains -my.sharepoint.com)
                    # Format: /personal/{user_folder}/Documents/{file_path}
                    if "-my.sharepoint.com" in hostname:
                        # Extract user folder and file path
                        match = re.match(r'/personal/([^/]+)/Documents/(.+)$', path)
                        if match:
                            user_folder = match.group(1)  # e.g., testmaker2_o365testlab_ca
                            file_path = match.group(2)    # e.g., Microsoft Teams Chat Files/file.pdf
                            
                            logger.info(f"OneDrive for Business - User: {user_folder}, File: {file_path}")
                            
                            # Use Graph API to get the site and drive
                            # First, resolve the site  
                            site_url = f"https://graph.microsoft.com/v1.0/sites/{hostname}:/personal/{user_folder}"
                            logger.info(f"Resolving site: {site_url}")
                            
                            site_response = await client.get(site_url, headers={'Authorization': f'Bearer {token}'})
                            
                            if site_response.status_code == 200:
                                site_data = site_response.json()
                                site_id = site_data.get("id")
                                logger.info(f"Site resolved, ID: {site_id}")
                                
                                # Now get the file content via drive
                                file_download_url = f"https://graph.microsoft.com/v1.0/sites/{site_id}/drive/root:/{file_path}:/content"
                                logger.info(f"Downloading via: {file_download_url}")
                                
                                file_response = await client.get(file_download_url, headers=headers, follow_redirects=True)
                                file_response.raise_for_status()
                                return file_response.content
                            else:
                                logger.warning(f"Site resolution failed: {site_response.status_code} - {site_response.text[:200]}")
                    
                    # For regular SharePoint sites
                    else:
                        # Try to resolve via shares API using sharing URL
                        # Encode the URL for the shares endpoint
                        import base64
                        encoded_url = base64.urlsafe_b64encode(url.encode()).decode().rstrip('=')
                        shares_url = f"https://graph.microsoft.com/v1.0/shares/u!{encoded_url}/driveItem/content"
                        
                        logger.info(f"Trying shares API: {shares_url}")
                        
                        shares_response = await client.get(shares_url, headers=headers, follow_redirects=True)
                        if shares_response.status_code == 200:
                            return shares_response.content
                        else:
                            logger.warning(f"Shares API failed: {shares_response.status_code}")
                
                # Fallback: try direct URL (might work for some configurations)
                response = await client.get(url, headers=headers, follow_redirects=True)
                response.raise_for_status()
                return response.content
                
        except Exception as e:
            logger.error(f"Failed to download with Graph API: {e}")
            # Fallback: try without authentication (for public URLs or testing)
            logger.info("Trying fallback download without auth...")
            return await FileHandler.download_file(url, None)

    
    @staticmethod
    def extract_text_from_pdf(content: bytes) -> str:
        """Extract text from PDF bytes."""
        try:
            try:
                from pypdf import PdfReader  # preferred modern package
            except ImportError:
                try:
                    from PyPDF2 import PdfReader  # fallback
                except ImportError as e:
                    raise ImportError(
                        "pypdf or PyPDF2 is required to extract PDF files. "
                        "Install one with: pip install pypdf or pip install PyPDF2"
                    ) from e

            pdf_file = io.BytesIO(content)
            reader = PdfReader(pdf_file)
            text_parts = []
            for page in reader.pages:
                # support different reader APIs
                if hasattr(page, "extract_text"):
                    page_text = page.extract_text()
                elif hasattr(page, "get_text"):
                    page_text = page.get_text()
                else:
                    page_text = None
                if page_text:
                    text_parts.append(page_text)
            return '\n'.join(text_parts)
        except Exception as e:
            raise ValueError(f"Failed to extract text from PDF: {e}")
    
    @staticmethod
    def extract_text_from_docx(content: bytes) -> str:
        """Extract text from DOCX bytes."""
        try:
            try:
                from docx import Document
            except ImportError as e:
                raise ImportError(
                    "python-docx is required to extract DOCX files. "
                    "Install it with: pip install python-docx"
                ) from e

            docx_file = io.BytesIO(content)
            doc = Document(docx_file)
            text_parts = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_parts.append(paragraph.text)
            return '\n'.join(text_parts)
        except Exception as e:
            raise ValueError(f"Failed to extract text from DOCX: {e}")
    
    @staticmethod
    def extract_text_from_txt(content: bytes) -> str:
        """Extract text from TXT bytes."""
        try:
            # Try UTF-8 first, then fallback to latin-1
            try:
                return content.decode('utf-8')
            except UnicodeDecodeError:
                return content.decode('latin-1')
        except Exception as e:
            raise ValueError(f"Failed to extract text from TXT: {e}")
    
    @staticmethod
    def extract_text(content: bytes, filename: str) -> str:
        """Extract text from file content based on extension."""
        ext = FileHandler.get_file_extension(filename)
        
        if ext == '.pdf':
            return FileHandler.extract_text_from_pdf(content)
        elif ext in ['.docx', '.doc']:
            return FileHandler.extract_text_from_docx(content)
        elif ext == '.txt':
            return FileHandler.extract_text_from_txt(content)
        else:
            raise ValueError(f"Unsupported file type: {ext}")
    
    @staticmethod
    async def process_attachment(url: str, filename: str, auth_token: Optional[str] = None) -> str:
        """Download and extract text from an attachment."""
        if not FileHandler.is_supported(filename):
            raise ValueError(
                f"Unsupported file type: {filename}. "
                f"Supported: PDF, Word (.docx), Text (.txt)"
            )
        
        content = await FileHandler.download_file(url, auth_token)
        
        if len(content) > FileHandler.MAX_FILE_SIZE:
            raise ValueError(
                f"File too large: {len(content) / 1024 / 1024:.1f} MB. "
                f"Maximum size is {FileHandler.MAX_FILE_SIZE / 1024 / 1024:.0f} MB."
            )
        
        return FileHandler.extract_text(content, filename)

    @staticmethod
    async def process_attachment_with_bot_credentials(url: str, filename: str) -> str:
        """Download and extract text using Bot's credentials.
        
        This method should be used for Teams file attachments which are 
        hosted on SharePoint and require authentication.
        """
        if not FileHandler.is_supported(filename):
            raise ValueError(
                f"Unsupported file type: {filename}. "
                f"Supported: PDF, Word (.docx), Text (.txt)"
            )
        
        content = await FileHandler.download_file_with_bot_credentials(url)
        
        if len(content) > FileHandler.MAX_FILE_SIZE:
            raise ValueError(
                f"File too large: {len(content) / 1024 / 1024:.1f} MB. "
                f"Maximum size is {FileHandler.MAX_FILE_SIZE / 1024 / 1024:.0f} MB."
            )
        
        return FileHandler.extract_text(content, filename)
