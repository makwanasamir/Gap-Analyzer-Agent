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
        
        jd = """
        Software Engineer - Full Stack
        
        We are looking for a Full Stack Software Engineer with:
        - 3+ years of experience in JavaScript/TypeScript
        - Strong knowledge of React and Node.js
        - Experience with cloud platforms (AWS or Azure)
        - Database experience (SQL and NoSQL)
        - Strong communication skills
        - Bachelor's degree in Computer Science
        """
        
        resume = """
        John Doe - Software Developer
        
        Experience:
        - 2 years at TechCorp as Frontend Developer
        - Built React applications
        - Used JavaScript and TypeScript
        - Worked with PostgreSQL database
        
        Education:
        - Bachelor's in Computer Science, State University
        
        Skills:
        - React, JavaScript, TypeScript
        - Node.js (basic)
        - PostgreSQL, MySQL
        - Git, Agile
        """
        
        result = await analyze_gap(jd, resume, "Identify gaps in skills and experience")
        
        # Verify result contains expected sections
        # Verify result contains expected sections or content
        # The prompt asks for gap analysis, so likely contains "Gap", "Criterion", "Addressed", etc.
        result_lower = result.lower()
        success_indicators = ["gap", "analysis", "criterion", "addressed", "missing", "matched"]
        found = [ind for ind in success_indicators if ind in result_lower]
        assert len(found) >= 2, f"Result did not contain enough analysis keywords. Got: {result[:200]}..."
        assert len(result) > 100


class TestInputValidation:
    """Integration tests for input validation."""
    
    @pytest.mark.asyncio
    async def test_validation_error_propagates(self):
        """Test that validation errors are raised correctly."""
        from src.analyze import validate_inputs
        
        is_valid, error = validate_inputs('', 'Valid resume content here', 'Objective')
        
        assert not is_valid
        assert "Document A is required" in error
    
    @pytest.mark.asyncio
    async def test_short_input_rejected(self):
        """Test that short inputs are rejected."""
        from src.analyze import validate_inputs
        
        is_valid, error = validate_inputs('Short', 'Valid resume content here that is long enough to pass validation', 'Objective')
        
        assert not is_valid
        assert "too short" in error


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
