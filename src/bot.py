"""Gap Analysis Bot using Teams AI SDK (M365 Agents SDK)."""
from typing import List, Optional
from dataclasses import dataclass, field
from teams import Application
from teams.state import TurnState
from botbuilder.schema import Activity, ActivityTypes, ChannelAccount
from botbuilder.core import MessageFactory, TurnContext

from .logger import setup_logger
from .cards import (
    get_welcome_card,
    get_welcome_card_completed,
    get_docA_upload_card,
    get_docA_upload_card_completed,
    get_docA_received_card,
    get_docA_received_card_completed,
    get_docB_received_card,
    get_docB_received_card_completed,
    get_result_card,
    get_result_card_completed,
    get_error_card,
    get_error_card_completed,
    get_text_input_card,
    get_text_input_card_completed,
)
from .analyze import analyze_gap
from .file_handler import FileHandler

LOGGER = setup_logger(__name__)

# --- State Management ---

class AppState(TurnState):
    """Custom state for the application."""
    pass

# --- Bot Logic Implementation ---

class GapAnalysisBot:
    """Helper class to register handlers for the Gap Analysis Agent."""
    
    MAX_DOCB_FILES = 10

    @staticmethod
    def _get_session(state: AppState) -> dict:
        """Helper to get or initialize the user session state."""
        # state.user is a dictionary-like object that persists
        if "state" not in state.user:
            LOGGER.info("State not found in user session. Initializing new session.")
            GapAnalysisBot._reset_session(state.user)
        else:
            LOGGER.info(f"Retrieved existing session. State={state.user.get('state')}, LastCardID={state.user.get('last_card_id')}")
        return state.user

    @staticmethod
    def _reset_session(user_state: dict):
        """Reset the user session variables."""
        # Avoid user_state.clear() as it might mess with SDK change tracking
        user_state["state"] = "idle"
        user_state["docA_text"] = ""
        user_state["docA_filename"] = ""
        user_state["docA_texts"] = []
        user_state["docA_filenames"] = []
        user_state["docB_text"] = ""
        user_state["docB_filename"] = ""
        user_state["docB_texts"] = []
        user_state["docB_filenames"] = []
        user_state["analysis_objective"] = ""
        user_state["input_source"] = "paste"
        user_state["last_card_id"] = None
        user_state["last_card_type"] = None
        user_state["last_card_data"] = {}
        user_state["active_card_guid"] = None # Clear validity token

    @staticmethod
    async def _complete_active_card(context: TurnContext, session: dict):
        """Helper to force-complete the active card before a reset."""
        last_id = session.get("last_card_id")
        last_type = session.get("last_card_type")
        last_data = session.get("last_card_data", {})
        
        if last_id and last_type:
            try:
                completed_card = GapAnalysisBot._get_completed_card_for_type(last_type, last_data)
                update_activity = Activity(
                    type=ActivityTypes.message,
                    id=last_id,
                    attachments=[completed_card],
                    conversation=context.activity.conversation,
                    recipient=context.activity.from_property,
                    from_property=context.activity.recipient
                )
                await context.update_activity(update_activity)
                LOGGER.info(f"Force-completed old card {last_id} before reset")
            except Exception as e:
                LOGGER.info(f"Failed to complete card before reset: {e}")

    @staticmethod
    def register_handlers(app: Application[AppState]):
        """Register Teams AI handlers."""
        
        @app.activity(ActivityTypes.conversation_update)
        async def on_conversation_update(context: TurnContext, state: AppState):
            LOGGER.info(f"Received conversation_update: type={context.activity.type}")
            if context.activity.members_added:
                for member in context.activity.members_added:
                    if member.id != context.activity.recipient.id:
                        await context.send_activity(
                            MessageFactory.text("Welcome to the **Gap Analysis Bot**! Type **start** to begin.")
                        )
            return True

        import re
        # Use \s* to handle leading/trailing whitespace
        @app.message(re.compile(r"^\s*(start|hi|hello|help|begin)\s*$", re.IGNORECASE))
        async def start_command(context: TurnContext, state: AppState):
            session = GapAnalysisBot._get_session(state)
            # Fix: Complete previous card AND reset session BEFORE sending welcome
            await GapAnalysisBot._complete_active_card(context, session)
            GapAnalysisBot._reset_session(session)
            await GapAnalysisBot._send_card(context, session, get_welcome_card(), "welcome")
            return True

        @app.message(re.compile(r"^\s*about\s*$", re.IGNORECASE))
        async def about_command(context: TurnContext, state: AppState):
            about_text = (
                "**General Gap Analysis Agent**\n\n"
                "Compare any two documents to find gaps based on your analysis objective.\n\n"
                "**Supported file formats:** PDF, Word (.docx), Text (.txt)\n\n"
                "Type **start** to begin!"
            )
            await context.send_activity(MessageFactory.text(about_text))
            return True

        @app.message(re.compile(r"^\s*status\s*$", re.IGNORECASE))
        async def status_command(context: TurnContext, state: AppState):
            session = GapAnalysisBot._get_session(state)
            status = f"State: {session.get('state')}\nDocA: {session.get('docA_filename') or 'None'}\nDocB: {session.get('docB_filename') or 'None'}"
            await context.send_activity(MessageFactory.text(status))
            return True

        @app.message(re.compile(r"^\s*(cancel|reset)\s*$", re.IGNORECASE))
        async def reset_command(context: TurnContext, state: AppState):
            session = GapAnalysisBot._get_session(state)
            await GapAnalysisBot._complete_active_card(context, session)
            GapAnalysisBot._reset_session(session)
            await context.send_activity(MessageFactory.text("Session reset. Type **start** to begin."))
            return True

        @app.message(re.compile(r".*", re.DOTALL))
        async def catch_all(context: TurnContext, state: AppState):
            text = context.activity.text or ""
            session = GapAnalysisBot._get_session(state)
            
            # Simple check to avoid double handling if regex failed slightly but intended as command
            if re.match(r"^\s*(start|hi|hello|help|begin|about|status|cancel|reset)\s*$", text, re.IGNORECASE):
                 return True

            # 1. Handle Adaptive Card submissions first (they often have no text)
            if context.activity.value:
                # Stale card check: Strict validation
                value = context.activity.value
                card_id = value.get("cardId")
                valid_guid = session.get("active_card_guid")
                
                # If either is missing, or they don't match, reject it.
                if not card_id or not valid_guid or card_id != valid_guid:
                    LOGGER.info(f"Ignoring stale/invalid card submission. Received: {card_id}, Expected: {valid_guid}")
                    return True
                
                await GapAnalysisBot._handle_card_submit(context, state)
                return True
            
            # 2. Handle file attachments
            attachments = context.activity.attachments or []
            file_attachments = [a for a in attachments if a.content_type and 'image' not in a.content_type.lower()]
            if file_attachments:
                await GapAnalysisBot._handle_file_attachments(context, state, file_attachments)
                return True

            # 3. Default fallback for unmatched text
            if not text:
                 return True

            # Gate: Only show welcome if we are effectively idle/lost, to prevent spam during flows
            if session.get("state") != "idle":
                return True

            await context.send_activity(MessageFactory.text("Hello! Type **start** to begin gap analysis."))
            await GapAnalysisBot._send_card(context, session, get_welcome_card(), "welcome")
            return True

    @staticmethod
    def _get_completed_card_for_type(card_type: str, card_data: dict):
        if card_type == "welcome": return get_welcome_card_completed()
        if card_type == "docA_upload": return get_docA_upload_card_completed()
        if card_type == "docA_received": return get_docA_received_card_completed(card_data.get("filename", ""))
        if card_type == "docB_received": return get_docB_received_card_completed(card_data.get("filename", ""), card_data.get("objective", ""))
        if card_type == "text_input":
            return get_text_input_card_completed(card_data.get("docA", ""), card_data.get("docB", ""), card_data.get("objective", ""))
        if card_type == "result":
            return get_result_card_completed(card_data.get("result", ""), card_data.get("docA_name", ""), card_data.get("docB_names", []))
        if card_type == "error": return get_error_card_completed(card_data.get("message", ""))
        return get_welcome_card_completed()

    @staticmethod
    async def _send_card(context: TurnContext, session: dict, card_attachment, card_type: str, card_data: dict = None):
        import uuid
        import json
        
        # Generate a unique ID for this card interaction to prevent stale clicks
        interaction_id = str(uuid.uuid4())
        
        # Inject the interaction ID into the card actions
        # Note: This limits us to hacking the JSON, but it's the most reliable way 
        # given we use static card definitions.
        if hasattr(card_attachment, 'content') and isinstance(card_attachment.content, dict):
            # Deep replace placeholder
            card_json_str = json.dumps(card_attachment.content)
            card_json_str = card_json_str.replace("CARD_ID_PLACEHOLDER", interaction_id)
            card_attachment.content = json.loads(card_json_str)

        last_id = session.get("last_card_id")
        last_type = session.get("last_card_type")
        
        if last_id and last_type:
            try:
                completed_card = GapAnalysisBot._get_completed_card_for_type(last_type, session.get("last_card_data") or {})
                # Explicitly set conversation and other fields for update to ensure better compat
                update_activity = Activity(
                    type=ActivityTypes.message,
                    id=last_id,
                    attachments=[completed_card],
                    conversation=context.activity.conversation,
                    recipient=context.activity.from_property,
                    from_property=context.activity.recipient
                )
                await context.update_activity(update_activity)
                LOGGER.info(f"Updated old card {last_id} ({last_type}) to completed state")
            except Exception as e:
                # Update might fail if the card was already updated or channel doesn't support it
                LOGGER.info(f"Best-effort update of old card failed (non-critical): {e}") 
        else:
             LOGGER.info(f"Skipping card update. LastID={last_id}, LastType={last_type}")
        
        # Update session with NEW GUID only after old card is handled
        session["active_card_guid"] = interaction_id
        
        response = await context.send_activity(MessageFactory.attachment(card_attachment))
        if response and response.id:
            session["last_card_id"] = response.id
            session["last_card_type"] = card_type
            session["last_card_data"] = card_data or {}
            LOGGER.info(f"New card sent and tracked: type={card_type}, id={response.id}")
        else:
            LOGGER.warning(f"New card sent but NO ID returned. Replacement will not work next turn. Response={response}")

    @staticmethod
    async def _handle_card_submit(context: TurnContext, state: AppState):
        value = context.activity.value or {}
        action = value.get("action", "")
        session = GapAnalysisBot._get_session(state)
        
        if action == "uploadDocs":
            session["state"] = "waiting_docA"
            await GapAnalysisBot._send_card(context, session, get_docA_upload_card(), "docA_upload")
        elif action == "pasteText":
            await GapAnalysisBot._send_card(context, session, get_text_input_card(session.get("docA_text"), session.get("docB_text"), session.get("analysis_objective")), "text_input", {"docA": session.get("docA_text"), "docB": session.get("docB_text"), "objective": session.get("analysis_objective")})
        elif action == "analyzeText":
            await GapAnalysisBot._handle_text_analysis(context, state, value)
        elif action == "analyzeFiles":
            objective = value.get("analysisObjective", "").strip()
            session["analysis_objective"] = objective or "Compare Source against Target documents"
            await GapAnalysisBot._run_analysis(context, state)
        elif action == "docB_received":
            # Re-send the objective prompt (Change Objective button)
            await GapAnalysisBot._send_card(context, session, get_docB_received_card(session.get("docB_filename"), session.get("analysis_objective")), "docB_received", {"filename": session.get("docB_filename"), "objective": session.get("analysis_objective")})
        elif action == "startOver":
            await GapAnalysisBot._complete_active_card(context, session)
            GapAnalysisBot._reset_session(session)
            await GapAnalysisBot._send_card(context, session, get_welcome_card(), "welcome")
        else:
            await GapAnalysisBot._send_card(context, session, get_welcome_card(), "welcome")

    @staticmethod
    async def _handle_text_analysis(context: TurnContext, state: AppState, value: dict):
        session = GapAnalysisBot._get_session(state)
        docA = value.get("docA", "").strip()
        docB = value.get("docB", "").strip()
        analysis_objective = value.get("analysisObjective", "").strip()
        
        session["input_source"] = "paste"
        session["docA_text"] = docA
        session["docA_filename"] = "Pasted Document A"
        session["docB_text"] = docB
        session["docB_filename"] = "Pasted Document B"
        session["analysis_objective"] = analysis_objective
        
        # Save the submitted data so the update logic can render the completed card correctly
        session["last_card_data"] = {
            "docA": docA,
            "docB": docB,
            "objective": analysis_objective
        }
        
        # Explicitly update the card *before* analysis for immediate UX feedback
        last_id = session.get("last_card_id")
        if last_id:
            try:
                # Use current submitted data for completion state
                completed_card = get_text_input_card_completed(docA, docB, analysis_objective)
                update_activity = Activity(
                    type=ActivityTypes.message,
                    id=last_id,
                    attachments=[completed_card],
                    conversation=context.activity.conversation,
                    recipient=context.activity.from_property,
                    from_property=context.activity.recipient
                )
                await context.update_activity(update_activity)
                LOGGER.info(f"Immediate update of Input Card {last_id} successful")
            except Exception as e:
                LOGGER.warning(f"Immediate update of Input Card failed: {e}")
        
        # Clear last_card_id so _send_card (called later) doesn't try to update it again
        session["last_card_id"] = None
        session["last_card_type"] = None
        
        await GapAnalysisBot._run_analysis(context, state)

    @staticmethod
    async def _handle_file_attachments(context: TurnContext, state: AppState, attachments: list):
        session = GapAnalysisBot._get_session(state)
        if session.get("state") == "idle": session["state"] = "waiting_docA"
        session["input_source"] = "file"
        
        current_state = session.get("state")
        if current_state == "waiting_docA":
            await GapAnalysisBot._process_docA_upload(context, state, attachments)
        elif current_state == "waiting_docB":
            await GapAnalysisBot._process_docB_upload(context, state, attachments)

    @staticmethod
    async def _process_docA_upload(context: TurnContext, state: AppState, attachments: list):
        session = GapAnalysisBot._get_session(state)
        processed = []
        
        limit = 10 # Using 10 as default if MAX_DOCA_FILES not defined
        
        for attachment in attachments[:limit]:
            filename = attachment.name or "document_a"
            if not FileHandler.is_supported(filename): continue
            try:
                # Use bot credentials for SharePoint file downloads
                text = await FileHandler.process_attachment_with_bot_credentials(
                    attachment.content_url, filename
                )
                session["docA_texts"].append(text)
                session["docA_filenames"].append(filename)
                processed.append(filename)
            except Exception as e:
                LOGGER.error(f"Error processing {filename}: {e}")
        
        if not processed:
            error_msg = "No valid files were processed. Please try again with PDF, Word, or Text files."
            await GapAnalysisBot._send_card(context, session, get_error_card(error_msg), "error", {"message": error_msg})
            return
        
        session["docA_text"] = "\n\n".join([f"## File: {n}\n{t}" for n, t in zip(session["docA_filenames"], session["docA_texts"])])
        session["docA_filename"] = processed[0] if len(processed) == 1 else f"{len(processed)} File(s)"
        session["state"] = "waiting_docB"
        
        # NOTE: docA_received card requires the filename for its completed state too.
        # _send_card will save this data into last_card_data.
        await GapAnalysisBot._send_card(context, session, get_docA_received_card(session["docA_filename"]), "docA_received", {"filename": session["docA_filename"]})

    @staticmethod
    async def _process_docB_upload(context: TurnContext, state: AppState, attachments: list):
        session = GapAnalysisBot._get_session(state)
        processed = []
        
        for attachment in attachments[:GapAnalysisBot.MAX_DOCB_FILES]:
            filename = attachment.name or "document_b"
            if not FileHandler.is_supported(filename): continue
            try:
                # Use bot credentials for SharePoint file downloads
                text = await FileHandler.process_attachment_with_bot_credentials(
                    attachment.content_url, filename
                )
                session["docB_texts"].append(text)
                session["docB_filenames"].append(filename)
                processed.append(filename)
            except Exception as e:
                LOGGER.error(f"Error processing {filename}: {e}")
        
        if not processed:
            error_msg = "No valid files were processed. Please try again."
            await GapAnalysisBot._send_card(context, session, get_error_card(error_msg), "error", {"message": error_msg})
            return
        
        session["docB_text"] = "\n\n".join([f"## File: {n}\n{t}" for n, t in zip(session["docB_filenames"], session["docB_texts"])])
        session["docB_filename"] = f"{len(session['docB_filenames'])} File(s)"
        
        # Send confirmation card and ask for objective
        await GapAnalysisBot._send_card(
            context, 
            session, 
            get_docB_received_card(session["docB_filename"], session.get("analysis_objective", "")), 
            "docB_received", 
            {"filename": session["docB_filename"], "objective": session.get("analysis_objective", "")}
        )

    @staticmethod
    async def _run_analysis(context: TurnContext, state: AppState):
        session = GapAnalysisBot._get_session(state)
        await context.send_activity(Activity(type=ActivityTypes.typing))
        try:
            analysis_result = await analyze_gap(session.get("docA_text"), session.get("docB_text"), session.get("analysis_objective"), source=session.get("input_source"))
            await GapAnalysisBot._send_card(
                context, 
                session, 
                get_result_card(analysis_result, session.get("docA_filename"), [session.get("docB_filename")], source=session.get("input_source")), 
                "result", 
                {"result": analysis_result, "docA_name": session.get("docA_filename"), "docB_names": [session.get("docB_filename")], "source": session.get("input_source")}
            )
        except ValueError as e:

            error_msg = str(e)
            await GapAnalysisBot._send_card(context, session, get_error_card(error_msg), "error", {"message": error_msg})
        except Exception as e:
            LOGGER.error(f"Analysis error: {e}", exc_info=True)
            error_msg = f"Analysis failed: {str(e)}"
            await GapAnalysisBot._send_card(context, session, get_error_card(error_msg), "error", {"message": error_msg})
