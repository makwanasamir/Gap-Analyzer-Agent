"""Main entry point for the M365 Agent (Teams AI)."""
import sys
import traceback
from aiohttp import web
from botbuilder.core import MemoryStorage
from teams import Application, ApplicationOptions, TeamState

from src.config import Config
from src.logger import setup_logger
from src.actions import (
    welcome_action,
    handle_paste_text_action,
    handle_analyze_text_action,
    handle_start_over,
    handle_file_upload
)

# Setup logging
LOGGER = setup_logger("app")

try:
    Config.validate()
except ValueError as e:
    LOGGER.error(f"Config Error: {e}")

# Create Application
# We use MemoryStorage for local dev. In production, use blobstorage/cosmosdb.
storage = MemoryStorage()
app = Application(
    ApplicationOptions(
        bot_app_id=Config.APP_ID,
        storage=storage,
        adapter=None # Created automatically using env vars if None, or we can pass explicit adapter
    )
)

# --- Routes & Activities ---

@app.activity("membersAdded")
async def on_members_added(context, state):
    await welcome_action(context, state)

@app.message("start")
@app.message("hi")
@app.message("hello")
async def on_message_start(context, state):
    await welcome_action(context, state)

@app.message("about")
async def on_message_about(context, state):
    await context.send_activity("🎯 **Gap Analysis Agent** (M365 Toolkit Version)\nCompare docs to find gaps.")

@app.adaptive_card_action("pasteText")
async def on_paste_text_submit(context, state, data):
    await handle_paste_text_action(context, state, data)

@app.adaptive_card_action("analyzeText")
async def on_analyze_submit(context, state, data):
    await handle_analyze_text_action(context, state, data)

@app.adaptive_card_action("startOver")
async def on_start_over(context, state, data):
    await handle_start_over(context, state, data)
    
@app.adaptive_card_action("uploadDocs")
async def on_upload_docs_request(context, state, data):
    # Just show instructions or set state
    await context.send_activity("Please upload your Job Description file now.")
    state.conversation["step"] = "waiting_jd"

# Fallback for file attachments
@app.activity("message")
async def on_message_default(context, state):
    # Check for attachments
    if context.activity.attachments:
        files = [a for a in context.activity.attachments if a.content_type and 'image' not in a.content_type.lower()]
        if files:
            await handle_file_upload(context, state, files)
            return

    # If no attachments and not handled by regex above
    # Check text content
    text = (context.activity.text or "").strip().lower()
    if text not in ["start", "hi", "hello", "about"]:
         await context.send_activity("I didn't understand that. Type 'start' to begin.")

# --- Server Setup ---

async def messages(req: web.Request) -> web.Response:
    return await app.process_request(req)

if __name__ == "__main__":
    try:
        app_server = web.Application()
        app_server.router.add_post("/api/messages", messages)
        
        LOGGER.info(f"🚀 M365 Agent starting on port {Config.PORT}")
        web.run_app(app_server, host="0.0.0.0", port=Config.PORT)
    except Exception as e:
        LOGGER.critical(f"Server error: {e}")
        raise
