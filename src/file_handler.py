"""File handling utilities for extracting text from documents."""
import io
import httpx
from typing import Optional


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
