"""Adaptive Card definitions for the Gap Analysis Agent.

UI/UX Design Principles:
- Clean, minimal design with clear visual hierarchy
- Completed cards show SAME content as original, just without buttons
- Teams payload safe (< 28KB total)
"""
from botbuilder.core import CardFactory
from botbuilder.schema import Attachment


# =============================================================================
# ACTIVE CARDS (with buttons)
# =============================================================================

def get_welcome_card() -> Attachment:
    """Create the welcome card with instructions."""
    card = {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [
            {
                "type": "TextBlock",
                "text": "Gap Analysis Agent",
                "weight": "Bolder",
                "size": "Large",
                "wrap": True
            },
            {
                "type": "TextBlock",
                "text": "Compare two documents to identify gaps, mismatches, or missing elements.",
                "wrap": True,
                "spacing": "Small"
            },
            {
                "type": "ColumnSet",
                "spacing": "Medium",
                "columns": [
                    {
                        "type": "Column",
                        "width": "stretch",
                        "items": [
                            {
                                "type": "TextBlock",
                                "text": "**Document A** = Source / Current state",
                                "wrap": True
                            },
                            {
                                "type": "TextBlock",
                                "text": "**Document B** = Target / Requirements",
                                "wrap": True,
                                "spacing": "Small"
                            }
                        ]
                    }
                ]
            }
        ],
        "actions": [
            {
                "type": "Action.Submit",
                "title": "Paste Text",
                "data": {"action": "pasteText"},
                "style": "positive"
            },
            {
                "type": "Action.Submit",
                "title": "Attach Files",
                "data": {"action": "uploadDocs"}
            }
        ]
    }
    return CardFactory.adaptive_card(card)


def get_docA_upload_card() -> Attachment:
    """Card prompting user to upload Document A file."""
    card = {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [
            {
                "type": "TextBlock",
                "text": "Step 1: Attach Document A",
                "weight": "Bolder",
                "size": "Medium",
                "wrap": True
            },
            {
                "type": "TextBlock",
                "text": "Use the paperclip button below the chat to attach your source document.",
                "wrap": True,
                "spacing": "Small"
            },
            {
                "type": "TextBlock",
                "text": "Supported: PDF, Word (.docx), Text (.txt)",
                "wrap": True,
                "spacing": "Small",
                "isSubtle": True
            }
        ],
        "actions": [
            {
                "type": "Action.Submit",
                "title": "Back",
                "data": {"action": "startOver"}
            }
        ]
    }
    return CardFactory.adaptive_card(card)


def get_text_input_card(docA: str = "", docB: str = "", objective: str = "") -> Attachment:
    """Card with text input fields for documents and analysis objective."""
    card = {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [
            {
                "type": "TextBlock",
                "text": "Paste Your Documents",
                "weight": "Bolder",
                "size": "Medium",
                "wrap": True
            },
            {
                "type": "TextBlock",
                "text": "**Document A** (Source / Current)",
                "spacing": "Medium",
                "wrap": True
            },
            {
                "type": "Input.Text",
                "id": "docA",
                "isMultiline": True,
                "placeholder": "Paste Document A content here (max 10,000 chars)...",
                "maxLength": 10000,
                "value": docA
            },
            {
                "type": "TextBlock",
                "text": "**Document B** (Target / Requirements)",
                "spacing": "Medium",
                "wrap": True
            },
            {
                "type": "Input.Text",
                "id": "docB",
                "isMultiline": True,
                "placeholder": "Paste Document B content here (max 10,000 chars)...",
                "maxLength": 10000,
                "value": docB
            },
            {
                "type": "TextBlock",
                "text": "**Analysis Objective**",
                "spacing": "Medium",
                "wrap": True
            },
            {
                "type": "Input.Text",
                "id": "analysisObjective",
                "isMultiline": True,
                "placeholder": "What should I analyze? e.g., 'Find compliance gaps'...",
                "maxLength": 1000,
                "value": objective
            }
        ],
        "actions": [
            {
                "type": "Action.Submit",
                "title": "Analyze Gaps",
                "data": {"action": "analyzeText"},
                "style": "positive"
            },
            {
                "type": "Action.Submit",
                "title": "Back",
                "data": {"action": "startOver"}
            }
        ]
    }
    return CardFactory.adaptive_card(card)


def get_docA_received_card(filename: str) -> Attachment:
    """Card confirming Document A received and asking for Document B."""
    card = {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [
            {
                "type": "TextBlock",
                "text": "Document A Received",
                "weight": "Bolder",
                "size": "Medium",
                "color": "Good",
                "wrap": True
            },
            {
                "type": "TextBlock",
                "text": f"File: {filename}",
                "wrap": True,
                "spacing": "Small"
            },
            {
                "type": "TextBlock",
                "text": "Now attach Document B",
                "weight": "Bolder",
                "spacing": "Medium",
                "wrap": True
            },
            {
                "type": "TextBlock",
                "text": "Attach your target/requirements document(s).",
                "wrap": True,
                "spacing": "Small",
                "isSubtle": True
            }
        ],
        "actions": [
            {
                "type": "Action.Submit",
                "title": "Cancel",
                "data": {"action": "startOver"}
            }
        ]
    }
    return CardFactory.adaptive_card(card)


def get_result_card(analysis_result: str, docA_name: str, docB_names: list) -> Attachment:
    """Create the results Adaptive Card."""
    docB_display = ", ".join(docB_names) if docB_names else "Document B"
    
    card = {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [
            {
                "type": "TextBlock",
                "text": "Gap Analysis Results",
                "weight": "Bolder",
                "size": "Large",
                "wrap": True
            },
            {
                "type": "FactSet",
                "spacing": "Small",
                "facts": [
                    {"title": "Source (A):", "value": docA_name},
                    {"title": "Target (B):", "value": docB_display}
                ]
            },
            {
                "type": "TextBlock",
                "text": "---",
                "spacing": "Small"
            },
            {
                "type": "TextBlock",
                "text": analysis_result,
                "wrap": True,
                "spacing": "Small"
            }
        ],
        "actions": [
            {
                "type": "Action.Submit",
                "title": "Edit Inputs",
                "data": {"action": "pasteText"}
            },
            {
                "type": "Action.Submit",
                "title": "New Analysis",
                "data": {"action": "startOver"}
            }
        ]
    }
    return CardFactory.adaptive_card(card)


def get_error_card(error_message: str) -> Attachment:
    """Create the error Adaptive Card."""
    card = {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [
            {
                "type": "TextBlock",
                "text": "Error",
                "weight": "Bolder",
                "size": "Medium",
                "color": "Attention",
                "wrap": True
            },
            {
                "type": "TextBlock",
                "text": error_message,
                "wrap": True,
                "spacing": "Small"
            }
        ],
        "actions": [
            {
                "type": "Action.Submit",
                "title": "Try Again",
                "data": {"action": "startOver"}
            }
        ]
    }
    return CardFactory.adaptive_card(card)


# =============================================================================
# COMPLETED CARDS (SAME content as original, NO buttons)
# =============================================================================

def get_welcome_card_completed() -> Attachment:
    """Completed welcome card - same content, no buttons."""
    card = {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [
            {
                "type": "TextBlock",
                "text": "Gap Analysis Agent",
                "weight": "Bolder",
                "size": "Large",
                "wrap": True
            },
            {
                "type": "TextBlock",
                "text": "Compare two documents to identify gaps, mismatches, or missing elements.",
                "wrap": True,
                "spacing": "Small"
            },
            {
                "type": "ColumnSet",
                "spacing": "Medium",
                "columns": [
                    {
                        "type": "Column",
                        "width": "stretch",
                        "items": [
                            {
                                "type": "TextBlock",
                                "text": "**Document A** = Source / Current state",
                                "wrap": True
                            },
                            {
                                "type": "TextBlock",
                                "text": "**Document B** = Target / Requirements",
                                "wrap": True,
                                "spacing": "Small"
                            }
                        ]
                    }
                ]
            }
        ]
        # NO actions
    }
    return CardFactory.adaptive_card(card)


def get_docA_upload_card_completed() -> Attachment:
    """Completed Document A upload card - same content, no buttons."""
    card = {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [
            {
                "type": "TextBlock",
                "text": "Step 1: Attach Document A",
                "weight": "Bolder",
                "size": "Medium",
                "wrap": True
            },
            {
                "type": "TextBlock",
                "text": "Use the paperclip button below the chat to attach your source document.",
                "wrap": True,
                "spacing": "Small"
            },
            {
                "type": "TextBlock",
                "text": "Supported: PDF, Word (.docx), Text (.txt)",
                "wrap": True,
                "spacing": "Small",
                "isSubtle": True
            }
        ]
        # NO actions
    }
    return CardFactory.adaptive_card(card)


def get_text_input_card_completed(docA: str = "", docB: str = "", objective: str = "") -> Attachment:
    """Completed text input card - shows what user entered as TextBlocks, no input fields or buttons."""
    card = {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [
            {
                "type": "TextBlock",
                "text": "Paste Your Documents",
                "weight": "Bolder",
                "size": "Medium",
                "wrap": True
            },
            {
                "type": "TextBlock",
                "text": "**Document A** (Source / Current)",
                "spacing": "Medium",
                "wrap": True
            },
            {
                "type": "TextBlock",
                "text": docA if docA else "(empty)",
                "wrap": True,
                "spacing": "Small"
            },
            {
                "type": "TextBlock",
                "text": "**Document B** (Target / Requirements)",
                "spacing": "Medium",
                "wrap": True
            },
            {
                "type": "TextBlock",
                "text": docB if docB else "(empty)",
                "wrap": True,
                "spacing": "Small"
            },
            {
                "type": "TextBlock",
                "text": "**Analysis Objective**",
                "spacing": "Medium",
                "wrap": True
            },
            {
                "type": "TextBlock",
                "text": objective if objective else "(empty)",
                "wrap": True,
                "spacing": "Small"
            }
        ]
        # NO actions
    }
    return CardFactory.adaptive_card(card)


def get_docA_received_card_completed(filename: str) -> Attachment:
    """Completed Document A received card - same content, no buttons."""
    card = {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [
            {
                "type": "TextBlock",
                "text": "Document A Received",
                "weight": "Bolder",
                "size": "Medium",
                "color": "Good",
                "wrap": True
            },
            {
                "type": "TextBlock",
                "text": f"File: {filename}",
                "wrap": True,
                "spacing": "Small"
            },
            {
                "type": "TextBlock",
                "text": "Now attach Document B",
                "weight": "Bolder",
                "spacing": "Medium",
                "wrap": True
            },
            {
                "type": "TextBlock",
                "text": "Attach your target/requirements document(s).",
                "wrap": True,
                "spacing": "Small",
                "isSubtle": True
            }
        ]
        # NO actions
    }
    return CardFactory.adaptive_card(card)


def get_result_card_completed(analysis_result: str, docA_name: str, docB_names: list) -> Attachment:
    """Completed result card - same content, no buttons."""
    docB_display = ", ".join(docB_names) if docB_names else "Document B"
    
    card = {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [
            {
                "type": "TextBlock",
                "text": "Gap Analysis Results",
                "weight": "Bolder",
                "size": "Large",
                "wrap": True
            },
            {
                "type": "FactSet",
                "spacing": "Small",
                "facts": [
                    {"title": "Source (A):", "value": docA_name},
                    {"title": "Target (B):", "value": docB_display}
                ]
            },
            {
                "type": "TextBlock",
                "text": "---",
                "spacing": "Small"
            },
            {
                "type": "TextBlock",
                "text": analysis_result,
                "wrap": True,
                "spacing": "Small"
            }
        ]
        # NO actions
    }
    return CardFactory.adaptive_card(card)


def get_error_card_completed(error_message: str) -> Attachment:
    """Completed error card - same content, no buttons."""
    card = {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [
            {
                "type": "TextBlock",
                "text": "Error",
                "weight": "Bolder",
                "size": "Medium",
                "color": "Attention",
                "wrap": True
            },
            {
                "type": "TextBlock",
                "text": error_message,
                "wrap": True,
                "spacing": "Small"
            }
        ]
        # NO actions
    }
    return CardFactory.adaptive_card(card)
