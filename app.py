"""Main entry point for the M365 Gap Analysis Agent (Teams AI)."""
from aiohttp import web
from aiohttp.web import Request, Response
from botbuilder.core.bot_framework_adapter import BotFrameworkAdapterSettings
# Note: In a pure SDK model, we'd rely on the SDK's host, but for Azure Web App we need a listener.
# We import the pre-configured 'app' from src.agent

from src.config import Config
from src.agent import app as agent_app
from src.logger import setup_logger

# Setup logging
LOGGER = setup_logger("app")

# Validate config
try:
    Config.validate()
except ValueError as e:
    LOGGER.warning(f"Configuration Warning: {e}")

async def messages(req: Request) -> Response:
    """Handle incoming bot messages via Teams AI Application."""
    try:
        # The Application object has a process method that handles everything
        response = await agent_app.process(req)
        
        if response:
            return response
        
        return Response(status=200)
    except Exception as e:
        LOGGER.error(f"Error in messages handler: {e}", exc_info=True)
        return Response(status=500, text=str(e))

async def health_check(req: Request) -> Response:
    """Simple health check endpoint."""
    return Response(text="Gap Analysis Bot is Running!", status=200)

# Init web app globally for Gunicorn
APP = web.Application()
APP.router.add_post("/api/messages", messages)
APP.router.add_get("/", health_check)

if __name__ == "__main__":
    LOGGER.info(f"🚀 M365 Gap Analysis Agent (Teams AI) starting on port {Config.PORT}")
    LOGGER.info(f"   Mode: {'Local Dev' if not Config.APP_ID else 'Production'}")
    
    # Bind to 0.0.0.0 to be accessible from all interfaces
    web.run_app(APP, host="0.0.0.0", port=Config.PORT)
