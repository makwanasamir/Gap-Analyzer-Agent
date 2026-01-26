"""Edge case and robustness tests for Gap Analysis Bot."""
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.file_handler import FileHandler
from src.analyze import validate_inputs

class TestEdgeCases:
    def test_empty_file(self):
        is_valid, error = validate_inputs('', '', '')
        assert not is_valid
        assert "Document A is required" in error

    def test_non_utf8_txt(self):
        # Use only latin-1 encodable characters
        content = "Resume - Cafe".encode("latin-1")
        assert isinstance(content, bytes)

    def test_too_many_resumes(self):
        # File/Resume upload scenario - use token based validation
        # Limit is 70k tokens ~ 90k words
        jd = "Valid JD with enough content." * 100  
        resumes_text = "Valid resume content. " * 30000 # ~90k words > 70k tokens
        
        is_valid, error = validate_inputs(jd, resumes_text, "Analyze gaps.", source="file")
        assert not is_valid
        assert "exceed" in error
        assert "tokens" in error

    def test_resume_with_script_injection(self):
        jd = "Valid JD with enough content."
        resume = "<script>alert('x')</script> Valid resume."
        is_valid, error = validate_inputs(jd, resume, "Analyze gaps.")
        assert is_valid  # Injection is not validation error
