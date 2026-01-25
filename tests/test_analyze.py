"""Tests for analyze.py - Input validation and gap analysis."""
import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.analyze import validate_inputs, SYSTEM_PROMPT


class TestValidateInputs:
    """Test cases for validate_inputs function (generic Document A/B and analysis objective)."""
    
    def test_valid_inputs(self):
        docA = "This is a valid Document A with enough content to pass validation."
        docB = "This is a valid Document B with enough content to pass validation."
        objective = "Find the key differences between the two documents."
        is_valid, error = validate_inputs(docA, docB, objective)
        assert is_valid is True
        assert error == ""

    def test_empty_docA(self):
        docA = ""
        docB = "Valid Document B."
        objective = "Analyze gaps."
        is_valid, error = validate_inputs(docA, docB, objective)
        assert is_valid is False
        assert "Document A is required" in error

    def test_empty_docB(self):
        docA = "Valid Document A."
        docB = ""
        objective = "Analyze gaps."
        is_valid, error = validate_inputs(docA, docB, objective)
        assert is_valid is False
        assert "Document B is required" in error

    def test_empty_objective(self):
        docA = "Valid Document A."
        docB = "Valid Document B."
        objective = ""
        is_valid, error = validate_inputs(docA, docB, objective)
        assert is_valid is False
        assert "Analysis objective is required" in error

    def test_short_docA(self):
        docA = "Short"
        docB = "Valid Document B with enough content."
        objective = "Analyze gaps."
        is_valid, error = validate_inputs(docA, docB, objective)
        assert is_valid is False
        assert "too short" in error

    def test_short_docB(self):
        docA = "Valid Document A with enough content."
        docB = "Short"
        objective = "Analyze gaps."
        is_valid, error = validate_inputs(docA, docB, objective)
        assert is_valid is False
        assert "too short" in error

    def test_short_objective(self):
        docA = "Valid Document A with enough content."
        docB = "Valid Document B with enough content."
        objective = "Gap"
        is_valid, error = validate_inputs(docA, docB, objective)
        assert is_valid is False
        assert "too short" in error

    def test_input_too_long(self):
        docA = "A" * 7000
        docB = "B" * 7000
        objective = "Analyze gaps."
        is_valid, error = validate_inputs(docA, docB, objective)
        assert is_valid is False
        assert "too long" in error
        assert "12,000" in error

    def test_input_at_length_limit(self):
        docA = "A" * 6000
        docB = "B" * 5990
        objective = "1234567890"
        is_valid, error = validate_inputs(docA, docB, objective)
        assert is_valid is True
        assert error == ""

    def test_none_docA(self):
        docA = None
        docB = "Valid Document B."
        objective = "Analyze gaps."
        is_valid, error = validate_inputs(docA, docB, objective)
        assert is_valid is False
        assert "Document A is required" in error

    def test_none_docB(self):
        docA = "Valid Document A."
        docB = None
        objective = "Analyze gaps."
        is_valid, error = validate_inputs(docA, docB, objective)
        assert is_valid is False
        assert "Document B is required" in error

    def test_none_objective(self):
        docA = "Valid Document A."
        docB = "Valid Document B."
        objective = None
        is_valid, error = validate_inputs(docA, docB, objective)
        assert is_valid is False
        assert "Analysis objective is required" in error


class TestSystemPrompt:
    """Test cases for the system prompt."""
    
    def test_system_prompt_exists(self):
        """Test that system prompt is defined."""
        assert SYSTEM_PROMPT is not None
        assert len(SYSTEM_PROMPT) > 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
