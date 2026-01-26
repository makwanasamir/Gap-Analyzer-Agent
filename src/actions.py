"""
Action Handlers for the M365 Agent
"""
from typing import Dict, Any, List
from botbuilder.core import TurnContext, MessageFactory
from botbuilder.schema import Attachment
from teams.state import TurnState

from src.cards import (
    get_welcome_card,
    get_docA_upload_card,
    get_docA_received_card,
    get_result_card,
    get_error_card,
    get_text_input_card,
)
from src.analyze import analyze_gap
from src.file_handler import FileHandler

import logging
logger = logging.getLogger(__name__)


async def welcome_action(context: TurnContext, state: TurnState) -> None:
    """Send welcome card."""
    # Initialize conversation state if needed
    if not hasattr(state, 'conversation'):
        state.conversation = {}
    
    card = get_welcome_card()
    await context.send_activity(MessageFactory.attachment(card))


async def handle_paste_text_action(context: TurnContext, state: TurnState, data: Dict[str, Any]) -> None:
    """Handle 'Paste Text' action from card."""
    if not hasattr(state, 'conversation'):
        state.conversation = {}
    
    # Retrieve existing state if any
    docA = state.conversation.get("docA_text", "")
    docB = state.conversation.get("docB_text", "")
    objective = state.conversation.get("analysis_objective", "")
    
    await context.send_activity(
        MessageFactory.attachment(get_text_input_card(docA, docB, objective))
    )


async def handle_analyze_text_action(context: TurnContext, state: TurnState, data: Dict[str, Any]) -> None:
    """Handle 'Analyze Gaps' action from card."""
    if not hasattr(state, 'conversation'):
        state.conversation = {}
    
    docA = data.get("docA", "").strip()
    docB = data.get("docB", "").strip()
    objective = data.get("analysisObjective", "").strip()
    
    # Save to state
    state.conversation["docA_text"] = docA
    state.conversation["docB_text"] = docB
    state.conversation["analysis_objective"] = objective
    state.conversation["docA_filename"] = "Pasted Document A"
    state.conversation["docB_filename"] = "Pasted Document B"

    # Validate
    if len(docA) < 20 or len(docB) < 20 or len(objective) < 5:
        await context.send_activity(
            MessageFactory.attachment(
                get_error_card("Inputs too short. Please check your text.")
            )
        )
        return

    await context.send_activity(MessageFactory.text("⏳ Analyzing..."))
    
    try:
        result = await analyze_gap(docA, docB, objective)
        # Show result
        await context.send_activity(
            MessageFactory.attachment(
                get_result_card(result, "Pasted Document A", ["Pasted Document B"])
            )
        )
    except Exception as e:
        logger.error(f"Analysis error: {e}", exc_info=True)
        await context.send_activity(
            MessageFactory.attachment(get_error_card(f"Error: {e}"))
        )


async def handle_start_over(context: TurnContext, state: TurnState, data: Dict[str, Any]) -> None:
    """Handle reset."""
    if hasattr(state, 'conversation'):
        state.conversation.clear()
    await welcome_action(context, state)


async def handle_file_upload(context: TurnContext, state: TurnState, attachments: List[Attachment]) -> None:
    """Handle file uploads."""
    # Initialize conversation state
    if not hasattr(state, 'conversation'):
        state.conversation = {}
    
    current_step = state.conversation.get("step", "idle")
    
    # Initialize step if first time
    if current_step == "idle":
        state.conversation["step"] = "waiting_jd"
        await context.send_activity(
            MessageFactory.text("📄 Please upload your Job Description file.")
        )
        return
    
    # Process JD (First file)
    if state.conversation["step"] == "waiting_jd":
        if not attachments:
            await context.send_activity(
                MessageFactory.text("No attachments found.")
            )
            return
        
        att = attachments[0]
        name = att.name or "unknown"
        
        if not FileHandler.is_supported(name):
            await context.send_activity(
                MessageFactory.text(f"❌ Unsupported file: {name}. Please upload PDF or DOCX.")
            )
            return
            
        try:
            text = await FileHandler.process_attachment(att.content_url, name)
            state.conversation["docA_text"] = text
            state.conversation["docA_filename"] = name
            state.conversation["step"] = "waiting_resumes"
            
            await context.send_activity(
                MessageFactory.attachment(get_docA_received_card(name))
            )
            await context.send_activity(
                MessageFactory.text("📄 Now please upload candidate resumes.")
            )
        except Exception as e:
            logger.error(f"File processing error: {e}", exc_info=True)
            await context.send_activity(
                MessageFactory.text(f"❌ Error reading file: {e}")
            )
    
    # Process Resumes
    elif state.conversation["step"] == "waiting_resumes":
        resumes = []
        for att in attachments:
            name = att.name or "unknown"
            if FileHandler.is_supported(name):
                try:
                    text = await FileHandler.process_attachment(att.content_url, name)
                    resumes.append((name, text))
                except Exception as e:
                    logger.error(f"Resume processing error: {e}", exc_info=True)
        
        if not resumes:
            await context.send_activity(
                MessageFactory.text("❌ No valid resumes found.")
            )
            return

        # Combine resumes for DocB
        full_resume_text = "\n\n---\n\n".join([r[1] for r in resumes])
        resume_names = [r[0] for r in resumes]
        
        state.conversation["docB_text"] = full_resume_text
        state.conversation["docB_filename"] = f"{len(resumes)} Resume(s)"
        
        # Set default objective if not provided
        if not state.conversation.get("analysis_objective"):
            state.conversation["analysis_objective"] = "Compare candidate skills against job requirements"
        
        await context.send_activity(MessageFactory.text("⏳ Analyzing files..."))
        
        try:
            result = await analyze_gap(
                state.conversation["docA_text"], 
                state.conversation["docB_text"], 
                state.conversation["analysis_objective"]
            )
            await context.send_activity(
                MessageFactory.attachment(
                    get_result_card(
                        result, 
                        state.conversation["docA_filename"], 
                        resume_names
                    )
                )
            )
            state.conversation["step"] = "idle"
        except Exception as e:
            logger.error(f"Analysis error: {e}", exc_info=True)
            await context.send_activity(
                MessageFactory.text(f"❌ Analysis Error: {e}")
            )
