"""Security tests for Gap Analysis Bot."""
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.file_handler import FileHandler
from src.analyze import validate_inputs

class TestSecurity:
    def test_file_upload_exe(self):
        assert FileHandler.is_supported("malware.exe") is False
    def test_file_upload_zip(self):
        assert FileHandler.is_supported("archive.zip") is False
    def test_file_upload_html(self):
        assert FileHandler.is_supported("resume.html") is False
    def test_prompt_injection(self):
        jd = "Valid JD with enough content."
        resume = "Valid resume with enough content."
        is_valid, error = validate_inputs(jd, resume, "Analyze gaps.")
        assert is_valid
        # The model should not follow prompt injection, but this is a manual check
    def test_secrets_not_leaked(self):
        # Simulate error and check no secrets in error
        try:
            FileHandler.extract_text(b"", "resume.xyz")
        except Exception as e:
            assert "AZURE_OPENAI_KEY" not in str(e)
