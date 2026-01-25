"""Tests for file_handler.py - File type detection and text extraction."""
import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.file_handler import FileHandler


class TestGetFileExtension:
    """Test cases for get_file_extension method."""
    
    def test_pdf_extension(self):
        """Test PDF file extension detection."""
        assert FileHandler.get_file_extension("resume.pdf") == ".pdf"
    
    def test_docx_extension(self):
        """Test DOCX file extension detection."""
        assert FileHandler.get_file_extension("resume.docx") == ".docx"
    
    def test_doc_extension(self):
        """Test DOC file extension detection."""
        assert FileHandler.get_file_extension("resume.doc") == ".doc"
    
    def test_txt_extension(self):
        """Test TXT file extension detection."""
        assert FileHandler.get_file_extension("resume.txt") == ".txt"
    
    def test_uppercase_extension(self):
        """Test uppercase extension is converted to lowercase."""
        assert FileHandler.get_file_extension("resume.PDF") == ".pdf"
        assert FileHandler.get_file_extension("resume.DOCX") == ".docx"
    
    def test_no_extension(self):
        """Test file without extension."""
        assert FileHandler.get_file_extension("resume") == ""
    
    def test_hidden_file(self):
        """Test hidden file (starts with dot)."""
        assert FileHandler.get_file_extension(".gitignore") == ".gitignore"
    
    def test_multiple_dots(self):
        """Test filename with multiple dots."""
        assert FileHandler.get_file_extension("my.resume.2024.pdf") == ".pdf"
    
    def test_empty_filename(self):
        """Test empty filename."""
        assert FileHandler.get_file_extension("") == ""


class TestIsSupported:
    """Test cases for is_supported method."""
    
    def test_supported_pdf(self):
        """Test PDF is supported."""
        assert FileHandler.is_supported("resume.pdf") is True
    
    def test_supported_docx(self):
        """Test DOCX is supported."""
        assert FileHandler.is_supported("resume.docx") is True
    
    def test_supported_doc(self):
        """Test DOC is supported."""
        assert FileHandler.is_supported("resume.doc") is True
    
    def test_supported_txt(self):
        """Test TXT is supported."""
        assert FileHandler.is_supported("resume.txt") is True
    
    def test_unsupported_jpg(self):
        """Test JPG is not supported."""
        assert FileHandler.is_supported("photo.jpg") is False
    
    def test_unsupported_png(self):
        """Test PNG is not supported."""
        assert FileHandler.is_supported("photo.png") is False
    
    def test_unsupported_exe(self):
        """Test EXE is not supported."""
        assert FileHandler.is_supported("program.exe") is False
    
    def test_unsupported_zip(self):
        """Test ZIP is not supported."""
        assert FileHandler.is_supported("archive.zip") is False
    
    def test_no_extension(self):
        """Test file without extension is not supported."""
        assert FileHandler.is_supported("resume") is False


class TestExtractTextFromTxt:
    """Test cases for extract_text_from_txt method."""
    
    def test_utf8_content(self):
        """Test UTF-8 encoded content."""
        content = "Hello, World!".encode('utf-8')
        result = FileHandler.extract_text_from_txt(content)
        assert result == "Hello, World!"
    
    def test_utf8_unicode(self):
        """Test UTF-8 with unicode characters."""
        content = "Hello, 世界! 🎯".encode('utf-8')
        result = FileHandler.extract_text_from_txt(content)
        assert result == "Hello, 世界! 🎯"
    
    def test_latin1_content(self):
        """Test Latin-1 encoded content."""
        content = "Café résumé".encode('latin-1')
        result = FileHandler.extract_text_from_txt(content)
        assert "Caf" in result
    
    def test_empty_content(self):
        """Test empty content."""
        content = b""
        result = FileHandler.extract_text_from_txt(content)
        assert result == ""
    
    def test_multiline_content(self):
        """Test multiline content."""
        content = "Line 1\nLine 2\nLine 3".encode('utf-8')
        result = FileHandler.extract_text_from_txt(content)
        assert "Line 1" in result
        assert "Line 2" in result
        assert "Line 3" in result


class TestExtractText:
    """Test cases for extract_text method."""
    
    def test_extract_txt(self):
        """Test extracting text from TXT."""
        content = b"This is a test resume."
        result = FileHandler.extract_text(content, "resume.txt")
        assert result == "This is a test resume."
    
    def test_unsupported_extension(self):
        """Test unsupported file extension raises error."""
        content = b"Some content"
        with pytest.raises(ValueError) as exc_info:
            FileHandler.extract_text(content, "file.xyz")
        assert "Unsupported file type" in str(exc_info.value)


class TestConstants:
    """Test cases for FileHandler constants."""
    
    def test_supported_extensions(self):
        """Test supported extensions are defined correctly."""
        assert '.txt' in FileHandler.SUPPORTED_EXTENSIONS
        assert '.pdf' in FileHandler.SUPPORTED_EXTENSIONS
        assert '.docx' in FileHandler.SUPPORTED_EXTENSIONS
        assert '.doc' in FileHandler.SUPPORTED_EXTENSIONS
    
    def test_max_file_size(self):
        """Test max file size is 10 MB."""
        assert FileHandler.MAX_FILE_SIZE == 10 * 1024 * 1024


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
