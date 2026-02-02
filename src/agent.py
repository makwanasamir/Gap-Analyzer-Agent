"""
M365 Agent Application Definition.
This file contains the core Application instance and logic registration.
"""
from teams import Application, ApplicationOptions, TeamsAdapter
from teams.state import TurnState
from botbuilder.core import MemoryStorage

from src.config import Config
from src.bot import GapAnalysisBot, AppState

# Initialize MemoryStorage
storage = MemoryStorage()

# ==========================================
# CRITICAL FIX: TeamsAdapter Constructor
# TeamsAdapter.__init__ takes a CONFIGURATION object as 1st arg, NOT BotFrameworkAuthentication!
# It also accepts credentials_factory as a keyword arg which we MUST use!
# ==========================================

from botframework.connector.auth import (
    PasswordServiceClientCredentialFactory,
    AuthenticationConfiguration
)



# Create credential factory DIRECTLY with explicit values
# This is passed to TeamsAdapter via credentials_factory kwarg
credential_factory = PasswordServiceClientCredentialFactory(
    app_id=Config.APP_ID,
    password=Config.APP_PASSWORD,
    tenant_id=Config.APP_TENANT_ID  # CRITICAL for SingleTenant
)



# CRITICAL: TeamsAdapter expects a CONFIGURATION object with MicrosoftApp* attributes!
# It passes this to ConfigurationBotFrameworkAuthentication which uses getattr()
# The attribute names MUST match what ConfigurationBotFrameworkAuthentication expects
class TeamsAdapterConfig:
    """Configuration object for TeamsAdapter with required attributes."""
    MicrosoftAppId = Config.APP_ID
    MicrosoftAppPassword = Config.APP_PASSWORD
    MicrosoftAppType = Config.APP_TYPE  # "SingleTenant"
    MicrosoftAppTenantId = Config.APP_TENANT_ID

adapter_config = TeamsAdapterConfig()



# Create TeamsAdapter with:
# 1. Configuration object with MicrosoftApp* attributes  
# 2. credentials_factory to use our PasswordServiceClientCredentialFactory
teams_adapter = TeamsAdapter(
    adapter_config,  # Configuration object
    credentials_factory=credential_factory,  # Use our factory!
    auth_configuration=AuthenticationConfiguration()
)



app_options = ApplicationOptions(
    storage=storage,
    adapter=teams_adapter
)

# Create the Application instance
app = Application[AppState](app_options)

# Register the bot's handlers
GapAnalysisBot.register_handlers(app)

# Export the app instance
__all__ = ["app"]
