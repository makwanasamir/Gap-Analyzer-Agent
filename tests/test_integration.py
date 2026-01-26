"""Integration tests for the Gap Analysis Bot."""
import pytest
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestEndToEndWorkflow:
    """End-to-end workflow tests (require Azure OpenAI credentials)."""
    
    @pytest.mark.skipif(
        not os.getenv("AZURE_OPENAI_ENDPOINT"),
        reason="Azure OpenAI credentials not configured"
    )
    @pytest.mark.asyncio
    async def test_full_analysis_workflow(self):
        """Test full gap analysis with real Azure OpenAI call."""
        from src.analyze import analyze_gap
        
        docA = """
        System Requirements Specification
        
        We are looking for a system with:
        - High availability (99.9%)
        - RESTful API architecture
        - Secure authentication (OAuth 2.0)
        - Relational database storage
        """
        
        docB = """
        Proposed Architecture
        
        Features:
        - API built with GraphQL
        - MongoDB storage
        - Basic authentication
        - 99.0% uptime SLA
        """
        
        result = await analyze_gap(docA, docB, "Identify gaps in requirements compliance")
        
        # Verify result contains expected sections
        # Verify result contains expected sections or content
        # The prompt asks for gap analysis, so likely contains "Gap", "Criterion", "Addressed", etc.
        result_lower = result.lower()
        success_indicators = ["gap", "analysis", "criterion", "addressed", "missing", "matched", 
                             "status", "severity", "recommendation", "conflict", "misalignment"]
        found = [ind for ind in success_indicators if ind in result_lower]
        assert len(found) >= 2, f"Result did not contain enough analysis keywords. Got: {result[:200]}..."
        assert len(result) > 100


class TestInputValidation:
    """Integration tests for input validation."""
    
    @pytest.mark.asyncio
    async def test_validation_error_propagates(self):
        """Test that validation errors are raised correctly."""
        from src.analyze import validate_inputs
        
        is_valid, error = validate_inputs('', 'Valid Document B content here', 'Objective')
        
        assert not is_valid
        assert "Document A is required" in error
    
    @pytest.mark.asyncio
    async def test_short_input_rejected(self):
        """Test that short inputs are rejected."""
        from src.analyze import validate_inputs
        
        is_valid, error = validate_inputs('Short', 'Valid Document B that is long enough to pass validation', 'Objective')
        
        assert not is_valid
        assert "too short" in error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
