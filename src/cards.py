"""Adaptive Card definitions for the Gap Analysis Bot."""
from botbuilder.core import CardFactory
from botbuilder.schema import Attachment


def get_welcome_card() -> Attachment:
    """Create the welcome card with instructions."""
    card = {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [
            {
                "type": "TextBlock",
                "text": "🎯 General Gap Analysis Agent",
                "weight": "Bolder",
                "size": "Large",
                "wrap": True
            },
            {
                "type": "TextBlock",
                "text": "Compare any two documents (A = source/current, B = target/ideal/guardrails) to find gaps based on your analysis objective.",
                "wrap": True,
                "spacing": "Small"
            },
            {
                "type": "TextBlock",
                "text": "📋 Choose an option:",
                "weight": "Bolder",
                "spacing": "Medium",
                "wrap": True
            }
        ],
        "actions": [
            {
                "type": "Action.Submit",
                "title": "📝 Paste Text",
                "data": {
                    "action": "pasteText"
                },
                "style": "positive"
            },
            {
                "type": "Action.Submit",
                "title": "📎 Attach Files (Teams only)",
                "data": {
                    "action": "uploadDocs"
                }
            }
        ]
    }
    return CardFactory.adaptive_card(card)


def get_jd_upload_card() -> Attachment:
    """Card prompting user to upload JD file."""
    card = {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [
            {
                "type": "TextBlock",
                "text": "📄 Attach Job Description File",
                "weight": "Bolder",
                "size": "Medium",
                "wrap": True
            },
            {
                "type": "TextBlock",
                "text": "In Teams: Use the 📎 paperclip button at the bottom of the chat to attach your file, then send.",
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
                "title": "← Back to Menu",
                "data": {
                    "action": "startOver"
                }
            }
        ]
    }
    return CardFactory.adaptive_card(card)


def get_text_input_card(docA: str = "", docB: str = "", objective: str = "") -> Attachment:
    """Card with text input fields for JD and Resume."""
    card = {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [
            {
                "type": "TextBlock",
                "text": "🎯 General Gap Analysis - Paste Text",
                "weight": "Bolder",
                "size": "Large",
                "wrap": True
            },
            {
                "type": "TextBlock",
                "text": "Document A (Source/Current)",
                "weight": "Bolder",
                "spacing": "Medium",
                "wrap": True
            },
            {
                "type": "Input.Text",
                "id": "docA",
                "isMultiline": True,
                "placeholder": "Paste the full text of Document A (source/current state) here...",
                "maxLength": 20000,
                "value": docA
            },
            {
                "type": "TextBlock",
                "text": "Document B (Target/Ideal/Guardrails)",
                "weight": "Bolder",
                "spacing": "Medium",
                "wrap": True
            },
            {
                "type": "Input.Text",
                "id": "docB",
                "isMultiline": True,
                "placeholder": "Paste the full text of Document B (target/ideal/requirements) here...",
                "maxLength": 20000,
                "value": docB
            },
            {
                "type": "TextBlock",
                "text": "Analysis Objective",
                "weight": "Bolder",
                "spacing": "Medium",
                "wrap": True
            },
            {
                "type": "Input.Text",
                "id": "analysisObjective",
                "isMultiline": True,
                "placeholder": "Describe the analysis objective, e.g. 'Find compliance gaps', 'Check for missing controls', 'Compare for completeness'...",
                "maxLength": 2000,
                "value": objective
            }
        ],
        "actions": [
            {
                "type": "Action.Submit",
                "title": "🔍 Analyze Gaps",
                "data": {
                    "action": "analyzeText"
                },
                "style": "positive"
            },
            {
                "type": "Action.Submit",
                "title": "← Back",
                "data": {
                    "action": "startOver"
                }
            }
        ]
    }
    return CardFactory.adaptive_card(card)


def get_jd_received_card(filename: str) -> Attachment:
    """Card confirming JD received and asking for resumes."""
    card = {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [
            {
                "type": "TextBlock",
                "text": "✅ Job Description Received",
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
                "text": "📎 Now upload Resume(s)",
                "weight": "Bolder",
                "spacing": "Medium",
                "wrap": True
            },
            {
                "type": "TextBlock",
                "text": "Attach up to 10 resume files (PDF, Word, or Text) and send.",
                "wrap": True,
                "spacing": "Small"
            }
        ],
        "actions": [
            {
                "type": "Action.Submit",
                "title": "❌ Cancel & Start Over",
                "data": {
                    "action": "startOver"
                }
            }
        ]
    }
    return CardFactory.adaptive_card(card)


def get_processing_card(jd_filename: str, resume_count: int) -> Attachment:
    """Card showing processing status."""
    card = {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [
            {
                "type": "TextBlock",
                "text": "⏳ Analyzing...",
                "weight": "Bolder",
                "size": "Medium",
                "wrap": True
            },
            {
                "type": "TextBlock",
                "text": f"📄 JD: {jd_filename}",
                "wrap": True,
                "spacing": "Small"
            },
            {
                "type": "TextBlock",
                "text": f"📎 Resumes: {resume_count} file(s)",
                "wrap": True,
                "spacing": "Small"
            },
            {
                "type": "TextBlock",
                "text": "Please wait while I analyze the gaps...",
                "wrap": True,
                "spacing": "Medium",
                "isSubtle": True
            }
        ]
    }
    return CardFactory.adaptive_card(card)


def get_result_card(analysis_result: str, jd_filename: str, resume_filenames: list) -> Attachment:
    """Create the results Adaptive Card."""
    card = {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [
            {
                "type": "TextBlock",
                "text": "📊 Gap Analysis Results",
                "weight": "Bolder",
                "size": "Large",
                "wrap": True
            },
            {
                "type": "TextBlock",
                "text": f"**JD:** {jd_filename}",
                "wrap": True,
                "spacing": "Small"
            },
            {
                "type": "TextBlock",
                "text": f"**Resumes analyzed:** {len(resume_filenames)}",
                "wrap": True,
                "spacing": "Small"
            },
            {
                "type": "TextBlock",
                "text": "---",
                "wrap": True,
                "spacing": "Medium"
            },
            {
                "type": "TextBlock",
                "text": analysis_result,
                "wrap": True,
                "spacing": "Medium"
            }
        ],
        "actions": [
            {
                "type": "Action.Submit",
                "title": "✏️ Edit Inputs",
                "data": {
                    "action": "pasteText"
                }
            },
            {
                "type": "Action.Submit",
                "title": "🔄 New Analysis (Clear)",
                "data": {
                    "action": "startOver"
                }
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
                "text": "⚠️ Error",
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
                "title": "🔄 Start Over",
                "data": {
                    "action": "startOver"
                }
            }
        ]
    }
    return CardFactory.adaptive_card(card)


# Keep old function for backward compatibility
def get_analysis_card() -> Attachment:
    """Backward compatible - redirects to welcome card."""
    return get_welcome_card()
