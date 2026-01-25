"""
Action Handlers for the M365 Agent
"""
from typing import Dict, Any, List
from teams import Application, TurnContext, MemoryStorage, TurnState
from botbuilder.core import MessageFactory, ActionTypes
from botbuilder.schema import Attachment

from src.cards import (
    get_welcome_card,
    get_jd_upload_card,
    get_jd_received_card,
    get_result_card,
    get_error_card,
    get_text_input_card,
)
from src.analyze import analyze_gap
from src.file_handler import FileHandler

import logging
logger = logging.getLogger(__name__)

# State definitions (mimicking session)
# In Teams AI, we use TurnState['conversation'] or 'user' scopes.
# We will define a typed state class essentially.

class AppState(TurnState):
    """Application state."""
    # We can add custom properties here if needed, 
    # but basic TurnState usually wraps temp/user/conversation.
    pass

async def welcome_action(context: TurnContext, state: TurnState):
    """Send welcome card."""
    card = get_welcome_card()
    await context.send_activity(MessageFactory.attachment(card))

async def handle_paste_text_action(context: TurnContext, state: TurnState, data: Dict[str, Any]):
    """Handle 'Paste Text' action from card."""
    # Retrieve existing state if any
    conversaton = state.conversation
    docA = conversaton.get("docA_text", "")
    docB = conversaton.get("docB_text", "")
    objective = conversaton.get("analysis_objective", "")
    
    await context.send_activity(
        MessageFactory.attachment(get_text_input_card(docA, docB, objective))
    )

async def handle_analyze_text_action(context: TurnContext, state: TurnState, data: Dict[str, Any]):
    """Handle 'Analyze Gaps' action from card."""
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
        await context.send_activity(MessageFactory.attachment(get_error_card("Inputs too short. Please check your text.")))
        return

    await context.send_activity(f"⏳ Analyzing...")
    
    try:
        result = await analyze_gap(docA, docB, objective)
        # Show result
        await context.send_activity(
            MessageFactory.attachment(get_result_card(result, "Pasted Document A", ["Pasted Document B"]))
        )
    except Exception as e:
        await context.send_activity(MessageFactory.attachment(get_error_card(f"Error: {e}")))

async def handle_start_over(context: TurnContext, state: TurnState, data: Dict[str, Any]):
    """Handle reset."""
    state.conversation.clear()
    await welcome_action(context, state)

async def handle_file_upload(context: TurnContext, state: TurnState, attachments: List[Attachment]):
    """Handle file uploads (logic ported from bot.py)."""
    # Simple state machine using conversation state
    current_step = state.conversation.get("step", "idle")
    
    if current_step == "idle":
        state.conversation["step"] = "waiting_jd"
    
    if state.conversation["step"] == "waiting_jd":
         # Process JD (First file)
         if not attachments:
             return
         
         att = attachments[0]
         name = att.name or "unknown"
         
         if not FileHandler.is_supported(name):
             await context.send_activity(f"Unsupported file: {name}")
             return
             
         try:
             text = await FileHandler.process_attachment(att.content_url, name)
             state.conversation["docA_text"] = text
             state.conversation["docA_filename"] = name
             state.conversation["step"] = "waiting_resumes"
             
             await context.send_activity(MessageFactory.attachment(get_jd_received_card(name)))
         except Exception as e:
             await context.send_activity(f"Error reading file: {e}")
             
    elif state.conversation["step"] == "waiting_resumes":
        # Process Resumes
        resumes = []
        for att in attachments:
            name = att.name or "unknown"
            if FileHandler.is_supported(name):
                 try:
                     text = await FileHandler.process_attachment(att.content_url, name)
                     resumes.append((name, text))
                 except:
                     pass
        
        if not resumes:
            await context.send_activity("No valid resumes found.")
            return

        # Combine resumes for DocB (This logic might need refinement if analyzing separately, 
        # but current analyze_gap takes one docB. We'll join them).
        full_resume_text = "\n\n---\n\n".join([r[1] for r in resumes])
        resume_names = [r[0] for r in resumes]
        
        state.conversation["docB_text"] = full_resume_text
        state.conversation["docB_filename"] = f"{len(resumes)} Resumes"
        
        # We need an objective. If we haven't asked, simple default or ask.
        # For simplicity in this port, we assume a default objective if using file flow, 
        # OR we could show an input card. Let's use a default for the file flow to match previous behavior
        # (Actually previous output didn't specific objective input for file flow? 
        # It used session.analysis_objective which defaults to empty. analyze_gap requires it.)
        
        # Let's prompt for objective if missing
        if not state.conversation.get("analysis_objective"):
             # We could show an input card here or just set default
             state.conversation["analysis_objective"] = "Compare candidate skills against job requirements"
        
        await context.send_activity("⏳ Analyzing files...")
        try:
            result = await analyze_gap(
                state.conversation["docA_text"], 
                state.conversation["docB_text"], 
                state.conversation["analysis_objective"]
            )
            await context.send_activity(
                MessageFactory.attachment(get_result_card(result, state.conversation["docA_filename"], resume_names))
            )
            # Reset step but keep data for edit if needed? 
            # Actually flow usually ends here.
            state.conversation["step"] = "idle" 
        except Exception as e:
            await context.send_activity(f"Analysis Error: {e}")
