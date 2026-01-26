"""Main entry point for the M365 Gap Analysis Agent."""
from aiohttp import web
from aiohttp.web import Request, Response
from botbuilder.core import (
    BotFrameworkAdapter, 
    BotFrameworkAdapterSettings, 
    MemoryStorage, 
    ConversationState, 
    UserState,
    TurnContext,
)
from botbuilder.schema import Activity

from src.config import Config
from src.bot import GapAnalysisBot
from src.logger import setup_logger

# Setup logging
LOGGER = setup_logger("app")

# Validate config
try:
    Config.validate()
except ValueError as e:
    LOGGER.warning(f"Configuration Warning: {e}")

# Create adapter - use empty strings for local dev to skip auth
SETTINGS = BotFrameworkAdapterSettings(
    app_id="",
    app_password=""
)
ADAPTER = BotFrameworkAdapter(SETTINGS)

# Error handler
async def on_error(context: TurnContext, error: Exception):
    LOGGER.error(f"Bot error: {error}", exc_info=True)
    try:
        await context.send_activity("Sorry, an error occurred. Please try again.")
    except:
        pass

ADAPTER.on_turn_error = on_error

# Create state storage - MemoryStorage for local dev
# Note: In production, use Azure Blob Storage or Cosmos DB for persistence
STORAGE = MemoryStorage()
CONVERSATION_STATE = ConversationState(STORAGE)
USER_STATE = UserState(STORAGE)

# Create bot
BOT = GapAnalysisBot(CONVERSATION_STATE, USER_STATE)


async def messages(req: Request) -> Response:
    """Handle incoming bot messages."""
    if "application/json" not in req.headers.get("Content-Type", ""):
        return Response(status=415)

    try:
        body = await req.json()
        activity = Activity().deserialize(body)
        auth_header = req.headers.get("Authorization", "")
        
        # Define bot logic
        async def bot_logic(turn_context: TurnContext):
            await BOT.on_turn(turn_context)
        
        # Try processing with adapter
        try:
            await ADAPTER.process_activity(activity, auth_header, bot_logic)
        except PermissionError:
            # Auth failed
            if Config.is_local_dev():
                # Bypass auth only in local dev
                LOGGER.debug("Auth bypassed for local dev")
                context = TurnContext(ADAPTER, activity)
                
                # Run bot logic directly
                await BOT.on_turn(context)
                
                # Save state manually since we bypassed the adapter
                await CONVERSATION_STATE.save_changes(context)
                await USER_STATE.save_changes(context)
            else:
                # In production, reject unauthorized requests
                LOGGER.warning("Unauthorized request rejected in production mode")
                return Response(status=401, text="Unauthorized")
        
        return Response(status=200)
        
    except Exception as e:
        LOGGER.error(f"Error: {e}", exc_info=True)
        return Response(status=500, text=str(e))


# Init web app globally for Gunicorn
APP = web.Application()
APP.router.add_post("/api/messages", messages)

if __name__ == "__main__":
    LOGGER.info(f"🚀 M365 Gap Analysis Agent starting on port {Config.PORT}")
    LOGGER.info(f"   Mode: {'Local Dev' if not Config.APP_ID else 'Production'}")
    
    web.run_app(APP, host="127.0.0.1", port=Config.PORT)
