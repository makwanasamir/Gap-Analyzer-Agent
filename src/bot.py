"""Gap Analysis Bot - handles messages, file attachments, and Adaptive Card submissions."""
from botbuilder.core import (
    ActivityHandler, 
    TurnContext, 
    MessageFactory,
    ConversationState,
    UserState,
)
from botbuilder.schema import ChannelAccount, Activity, ActivityTypes
from .logger import setup_logger

from .cards import (
    get_welcome_card,
    get_welcome_card_completed,
    get_docA_upload_card,
    get_docA_upload_card_completed,
    get_docA_received_card,
    get_docA_received_card_completed,
    get_result_card,
    get_result_card_completed,
    get_error_card,
    get_error_card_completed,
    get_text_input_card,
    get_text_input_card_completed,
)
from .analyze import analyze_gap
from .file_handler import FileHandler


class UserSession:
    """Track user's upload state and card history."""
    def __init__(self):
        self.state = "idle"  # idle, waiting_docA, waiting_docB
        self.docA_text = ""
        self.docA_filename = ""
        self.docB_text = ""  # Combined text
        self.docB_filename = "" # Display name for combined text
        self.docB_texts = []    # List of individual file texts
        self.docB_filenames = [] # List of individual filenames
        self.analysis_objective = ""
        self.input_source = "paste"  # "paste" or "file"
        # Card tracking
        self.last_card_id = None
        self.last_card_type = None  # "welcome", "docA_upload", "text_input", etc.
        self.last_card_data = {}    # Data needed for completed version
        
    def reset(self):
        self.state = "idle"
        self.docA_text = ""
        self.docA_filename = ""
        self.docB_text = ""
        self.docB_filename = ""
        self.docB_texts = []
        self.docB_filenames = []
        self.analysis_objective = ""
        self.input_source = "paste"
        self.last_card_id = None
        self.last_card_type = None
        self.last_card_data = {}


class GapAnalysisBot(ActivityHandler):
    """Bot that handles gap analysis between documents."""
    
    MAX_DOCB_FILES = 10
    
    def __init__(self, conversation_state: ConversationState, user_state: UserState):
        if conversation_state is None:
            raise TypeError("[GapAnalysisBot]: Missing parameter. conversation_state is required")
        if user_state is None:
            raise TypeError("[GapAnalysisBot]: Missing parameter. user_state is required")

        self.conversation_state = conversation_state
        self.user_state = user_state
        self.session_accessor = self.user_state.create_property("UserSession")
        self.logger = setup_logger(__name__)

    async def on_turn(self, turn_context: TurnContext):
        await super().on_turn(turn_context)
        await self.conversation_state.save_changes(turn_context)
        await self.user_state.save_changes(turn_context)

    def _get_completed_card_for_type(self, card_type: str, card_data: dict):
        """Get the completed version of a card based on its type."""
        if card_type == "welcome":
            return get_welcome_card_completed()
        elif card_type == "docA_upload":
            return get_docA_upload_card_completed()
        elif card_type == "docA_received":
            return get_docA_received_card_completed(card_data.get("filename", ""))
        elif card_type == "text_input":
            return get_text_input_card_completed(
                card_data.get("docA", ""),
                card_data.get("docB", ""),
                card_data.get("objective", "")
            )
        elif card_type == "result":
            return get_result_card_completed(
                card_data.get("result", ""),
                card_data.get("docA_name", ""),
                card_data.get("docB_names", [])
            )
        elif card_type == "error":
            return get_error_card_completed(card_data.get("message", ""))
        else:
            return get_welcome_card_completed()

    async def _send_card(
        self, 
        turn_context: TurnContext, 
        session: UserSession, 
        card_attachment,
        card_type: str,
        card_data: dict = None
    ):
        """Send a new card and update the previous card to show as completed.
        
        Args:
            turn_context: Bot turn context
            session: User session
            card_attachment: The new card to send
            card_type: Type identifier for this card (for creating completed version later)
            card_data: Data needed to create the completed version of this card
        """
        # Try to update the old card to show completed state
        if session.last_card_id and session.last_card_type:
            try:
                completed_card = self._get_completed_card_for_type(
                    session.last_card_type, 
                    session.last_card_data or {}
                )
                update_activity = Activity(
                    type=ActivityTypes.message,
                    id=session.last_card_id,
                    attachments=[completed_card]
                )
                await turn_context.update_activity(update_activity)
                self.logger.info(f"Updated old card {session.last_card_id} ({session.last_card_type}) to completed")
            except Exception as e:
                # Update may fail in some channels (e.g., Agents Playground)
                self.logger.warning(f"Could not update old card: {e}")
        
        # Send the new card
        response = await turn_context.send_activity(
            MessageFactory.attachment(card_attachment)
        )
        
        # Store new card's tracking info
        if response and response.id:
            session.last_card_id = response.id
            session.last_card_type = card_type
            session.last_card_data = card_data or {}
            self.logger.info(f"Sent new card type={card_type}, id={response.id}")
        else:
            self.logger.warning(f"No response ID for new card type={card_type}")

    async def on_message_activity(self, turn_context: TurnContext):
        """Handle incoming messages and file attachments."""
        session = await self.session_accessor.get(turn_context, UserSession)

        # Adaptive Card submission
        if turn_context.activity.value:
            await self._handle_card_submit(turn_context, session)
            return
            
        # File attachments
        attachments = turn_context.activity.attachments or []
        file_attachments = [a for a in attachments if a.content_type and 'image' not in a.content_type.lower()]
        if file_attachments:
            await self._handle_file_attachments(turn_context, session, file_attachments)
            return
            
        # Text commands
        text = (turn_context.activity.text or "").strip().lower()
        if text in ["start", "hi", "hello", "help", "begin"]:
            session.reset()
            await self._send_card(
                turn_context, session, 
                get_welcome_card(), 
                "welcome"
            )
        elif text == "about":
            about_text = (
                "**General Gap Analysis Agent**\n\n"
                "Compare any two documents to find gaps based on your analysis objective.\n\n"
                "**Supported file formats:** PDF, Word (.docx), Text (.txt)\n\n"
                "Type **start** to begin!"
            )
            await turn_context.send_activity(MessageFactory.text(about_text))
        elif text == "status":
            status = f"State: {session.state}\nDocA: {session.docA_filename or 'None'}\nDocB: {session.docB_filename or 'None'}"
            await turn_context.send_activity(MessageFactory.text(status))
        elif text in ["cancel", "reset"]:
            session.reset()
            await turn_context.send_activity(MessageFactory.text("Session reset. Type **start** to begin."))
        else:
            await turn_context.send_activity(
                MessageFactory.text("Hello! Type **start** to begin gap analysis.")
            )
            await self._send_card(
                turn_context, session, 
                get_welcome_card(), 
                "welcome"
            )
    
    async def on_members_added_activity(
        self, members_added: list[ChannelAccount], turn_context: TurnContext
    ):
        """Handle new members."""
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity(
                    MessageFactory.text("Welcome to the **Gap Analysis Bot**! Type **start** to begin.")
                )
    
    async def _handle_card_submit(self, turn_context: TurnContext, session: UserSession):
        """Handle Adaptive Card submissions."""
        value = turn_context.activity.value or {}
        action = value.get("action", "")
        
        if action == "uploadDocs":
            session.state = "waiting_docA"
            await self._send_card(
                turn_context, session, 
                get_docA_upload_card(), 
                "docA_upload"
            )
        elif action == "pasteText":
            await self._send_card(
                turn_context, session,
                get_text_input_card(
                    session.docA_text, 
                    session.docB_text, 
                    session.analysis_objective
                ),
                "text_input",
                {
                    "docA": session.docA_text,
                    "docB": session.docB_text,
                    "objective": session.analysis_objective
                }
            )
        elif action == "analyzeText":
            await self._handle_text_analysis(turn_context, session, value)
        elif action == "startOver":
            # Update old card FIRST, then reset session
            await self._send_card(
                turn_context, session, 
                get_welcome_card(), 
                "welcome"
            )
            # Reset after sending (so we start fresh for next interaction)
            session.state = "idle"
            session.docA_text = ""
            session.docA_filename = ""
            session.docB_text = ""
            session.docB_filename = ""
            session.docB_texts = []
            session.docB_filenames = []
            session.analysis_objective = ""
        else:
            await self._send_card(
                turn_context, session, 
                get_welcome_card(), 
                "welcome"
            )
    
    async def _handle_text_analysis(
        self, turn_context: TurnContext, session: UserSession, value: dict
    ):
        """Handle gap analysis from pasted text."""
        docA = value.get("docA", "").strip()
        docB = value.get("docB", "").strip()
        analysis_objective = value.get("analysisObjective", "").strip()
        
        # Set source to paste mode
        session.input_source = "paste"
            
        # Save to session (for Edit Inputs to work)
        session.docA_text = docA
        session.docA_filename = "Pasted Document A"
        session.docB_text = docB
        session.docB_filename = "Pasted Document B"
        session.analysis_objective = analysis_objective
        
        self.logger.info(f"Analyze Gaps clicked. last_card_id={session.last_card_id}, last_card_type={session.last_card_type}")
        self.logger.info(f"docA length: {len(docA)}, docB length: {len(docB)}")
        
        # Update the text input card to completed FIRST (before analysis)
        # This shows the user's entered text without buttons
        if session.last_card_id:
            try:
                completed_card = get_text_input_card_completed(docA, docB, analysis_objective)
                update_activity = Activity(
                    type=ActivityTypes.message,
                    id=session.last_card_id,
                    attachments=[completed_card]
                )
                await turn_context.update_activity(update_activity)
                self.logger.info(f"Updated card {session.last_card_id} to text_input_completed")
            except Exception as e:
                self.logger.warning(f"Could not update text_input card: {e}")
        else:
            self.logger.warning("No last_card_id to update!")
        
        # Clear last_card tracking since we're about to send a new card
        session.last_card_id = None
        session.last_card_type = None
        
        # Run analysis
        await self._run_analysis(turn_context, session)
    
    async def _handle_file_attachments(
        self, turn_context: TurnContext, session: UserSession, attachments: list
    ):
        """Handle uploaded file attachments."""
        if session.state == "idle":
            session.state = "waiting_docA"
        
        # Mark as file upload source for token-based validation
        session.input_source = "file"
        
        if session.state == "waiting_docA":
            await self._process_docA_upload(turn_context, session, attachments)
        elif session.state == "waiting_docB":
            await self._process_docB_upload(turn_context, session, attachments)
    
    async def _process_docA_upload(
        self, turn_context: TurnContext, session: UserSession, attachments: list
    ):
        """Process Document A file upload."""
        if not attachments:
            error_msg = "No file was attached."
            await self._send_card(
                turn_context, session,
                get_error_card(error_msg),
                "error",
                {"message": error_msg}
            )
            return
            
        attachment = attachments[0]
        filename = attachment.name or "document"
        
        if not FileHandler.is_supported(filename):
            error_msg = f"Unsupported file type: {filename}. Please use PDF, Word, or Text files."
            await self._send_card(
                turn_context, session,
                get_error_card(error_msg),
                "error",
                {"message": error_msg}
            )
            return
        
        try:
            content_url = attachment.content_url
            text = await FileHandler.process_attachment(content_url, filename)
            
            session.docA_text = text
            session.docA_filename = filename
            session.state = "waiting_docB"
            
            await self._send_card(
                turn_context, session,
                get_docA_received_card(filename),
                "docA_received",
                {"filename": filename}
            )
            
        except Exception as e:
            self.logger.error(f"Error processing file: {e}", exc_info=True)
            error_msg = f"Error processing file: {str(e)}"
            await self._send_card(
                turn_context, session,
                get_error_card(error_msg),
                "error",
                {"message": error_msg}
            )
    
    async def _process_docB_upload(
        self, turn_context: TurnContext, session: UserSession, attachments: list
    ):
        """Process Document B file uploads."""
        processed = []
        
        for attachment in attachments[:self.MAX_DOCB_FILES]:
            filename = attachment.name or "document_b"
            
            if not FileHandler.is_supported(filename):
                continue
            
            try:
                content_url = attachment.content_url
                text = await FileHandler.process_attachment(content_url, filename)
                
                session.docB_texts.append(text)
                session.docB_filenames.append(filename)
                processed.append(filename)
            except Exception as e:
                self.logger.error(f"Error processing {filename}: {e}")
        
        if not processed:
            error_msg = "No valid files were processed. Please try again."
            await self._send_card(
                turn_context, session,
                get_error_card(error_msg),
                "error",
                {"message": error_msg}
            )
            return
        
        # Set docB variables and run analysis
        session.docB_text = "\n\n---\n\n".join(session.docB_texts)
        session.docB_filename = f"{len(session.docB_filenames)} File(s)"
        session.analysis_objective = "Compare Source against Target documents"
        
        await self._run_analysis(turn_context, session)
    
    async def _run_analysis(self, turn_context: TurnContext, session: UserSession):
        """Run the gap analysis."""
        await turn_context.send_activity(Activity(type=ActivityTypes.typing))
        try:
            analysis_result = await analyze_gap(
                session.docA_text,
                session.docB_text,
                session.analysis_objective,
                source=session.input_source
            )
            
            await self._send_card(
                turn_context, session,
                get_result_card(
                    analysis_result,
                    session.docA_filename,
                    [session.docB_filename]
                ),
                "result",
                {
                    "result": analysis_result,
                    "docA_name": session.docA_filename,
                    "docB_names": [session.docB_filename]
                }
            )
        except ValueError as e:
            # Validation errors
            error_msg = str(e)
            await self._send_card(
                turn_context, session,
                get_error_card(error_msg),
                "error",
                {"message": error_msg}
            )
        except Exception as e:
            # Unexpected errors
            self.logger.error(f"Analysis error: {e}", exc_info=True)
            error_msg = f"Analysis failed: {str(e)}"
            await self._send_card(
                turn_context, session,
                get_error_card(error_msg),
                "error",
                {"message": error_msg}
            )
