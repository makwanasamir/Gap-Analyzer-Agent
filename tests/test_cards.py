"""Tests for cards.py - Adaptive Card generation."""
import pytest
import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock botbuilder imports for testing without the package
class MockCardFactory:
    @staticmethod
    def adaptive_card(card_content):
        return {"type": "adaptive_card", "content": card_content}

class MockAttachment:
    pass

# Patch imports before importing cards
sys.modules['botbuilder'] = type(sys)('botbuilder')
sys.modules['botbuilder.core'] = type(sys)('botbuilder.core')
sys.modules['botbuilder.schema'] = type(sys)('botbuilder.schema')
sys.modules['botbuilder.core'].CardFactory = MockCardFactory
sys.modules['botbuilder.schema'].Attachment = MockAttachment


class TestWelcomeCard:
    """Test cases for welcome card."""
    
    def test_welcome_card_import(self):
        """Test welcome card can be imported."""
        from src.cards import get_welcome_card
        assert callable(get_welcome_card)
    
    def test_welcome_card_structure(self):
        """Test welcome card has correct structure."""
        from src.cards import get_welcome_card
        card = get_welcome_card()
        
        assert card is not None
        assert "content" in card
        content = card["content"]
        
        assert content["type"] == "AdaptiveCard"
        assert "body" in content
        assert "actions" in content
    
    def test_welcome_card_has_title(self):
        """Test welcome card has title."""
        from src.cards import get_welcome_card
        card = get_welcome_card()
        content = card["content"]
        
        body = content["body"]
        title_blocks = [b for b in body if b.get("type") == "TextBlock" and "Gap Analysis" in b.get("text", "")]
        assert len(title_blocks) > 0
    
    def test_welcome_card_has_actions(self):
        """Test welcome card has action buttons."""
        from src.cards import get_welcome_card
        card = get_welcome_card()
        content = card["content"]
        
        actions = content["actions"]
        assert len(actions) >= 2
        
        action_titles = [a.get("title", "") for a in actions]
        assert any("Paste" in t for t in action_titles)
        assert any("Attach" in t for t in action_titles)


class TestTextInputCard:
    """Test cases for text input card."""
    
    def test_text_input_card_structure(self):
        """Test text input card has correct structure."""
        from src.cards import get_text_input_card
        card = get_text_input_card()
        
        assert card is not None
        content = card["content"]
        
        assert content["type"] == "AdaptiveCard"
        assert "body" in content
        assert "actions" in content
    
    def test_text_input_card_has_inputs(self):
        """Test text input card has docA, docB, and analysisObjective input fields."""
        from src.cards import get_text_input_card
        card = get_text_input_card()
        content = card["content"]
        
        body = content["body"]
        input_fields = [b for b in body if b.get("type") == "Input.Text"]
        
        assert len(input_fields) >= 3
        
        input_ids = [b['id'] for b in body if 'id' in b]
        assert 'docA' in input_ids
        assert 'docB' in input_ids
        assert 'analysisObjective' in input_ids
    
    def test_text_input_card_has_analyze_action(self):
        """Test text input card has analyze action."""
        from src.cards import get_text_input_card
        card = get_text_input_card()
        content = card["content"]
        
        actions = content["actions"]
        analyze_actions = [a for a in actions if a.get("data", {}).get("action") == "analyzeText"]
        
        assert len(analyze_actions) == 1


class TestResultCard:
    """Test cases for result card."""
    
    def test_result_card_structure(self):
        """Test result card has correct structure."""
        from src.cards import get_result_card
        
        analysis = "## Matched Skills\n- Python\n- JavaScript"
        analysis = "## Matched Skills\n- Python\n- JavaScript"
        jd_filename = "document_a.txt"
        resume_filenames = ["document_b_1.pdf", "document_b_2.docx"]
        
        card = get_result_card(analysis, jd_filename, resume_filenames)
        
        assert card is not None
        content = card["content"]
        
        assert content["type"] == "AdaptiveCard"
        assert "body" in content
    
    def test_result_card_displays_analysis(self):
        """Test result card displays analysis text."""
        from src.cards import get_result_card
        
        analysis = "This is the gap analysis result."
        jd_filename = "doc_a.txt"
        resume_filenames = ["doc_b.pdf"]
        
        card = get_result_card(analysis, jd_filename, resume_filenames)
        content = card["content"]
        
        body = content["body"]
        text_blocks = [b for b in body if b.get("type") == "TextBlock"]
        
        texts = [b.get("text", "") for b in text_blocks]
        assert any(analysis in t for t in texts)
    
    def test_result_card_has_start_over_action(self):
        """Test result card has start over action."""
        from src.cards import get_result_card
        
        card = get_result_card("Analysis", "jd.txt", ["resume.pdf"])
        content = card["content"]
        
        actions = content["actions"]
        start_over = [a for a in actions if a.get("data", {}).get("action") == "startOver"]
        
        assert len(start_over) == 1


class TestErrorCard:
    """Test cases for error card."""
    
    def test_error_card_structure(self):
        """Test error card has correct structure."""
        from src.cards import get_error_card
        
        card = get_error_card("Something went wrong!")
        
        assert card is not None
        content = card["content"]
        
        assert content["type"] == "AdaptiveCard"
    
    def test_error_card_displays_message(self):
        """Test error card displays error message."""
        from src.cards import get_error_card
        
        error_msg = "File too large to process."
        card = get_error_card(error_msg)
        content = card["content"]
        
        body = content["body"]
        texts = [b.get("text", "") for b in body if b.get("type") == "TextBlock"]
        
        assert any(error_msg in t for t in texts)
    
    def test_error_card_has_warning_indicator(self):
        """Test error card has warning/error indicator."""
        from src.cards import get_error_card
        
        card = get_error_card("Error")
        content = card["content"]
        
        body = content["body"]
        texts = [b.get("text", "") for b in body if b.get("type") == "TextBlock"]
        
        # Should have error/warning emoji or text
        assert any("⚠️" in t or "Error" in t for t in texts)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
