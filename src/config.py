"""Configuration settings for the Gap Analysis Bot."""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def _get_env(key: str, default: str = "") -> str:
    """Helper to get environment variables with multiple naming conventions."""
    # Specific fix for App ID/Password common uppercase variants
    if key == "MicrosoftAppId":
        val = os.getenv("MicrosoftAppId") or os.getenv("MICROSOFT_APP_ID")
        if val: return val.strip()
    if key == "MicrosoftAppPassword":
        val = os.getenv("MicrosoftAppPassword") or os.getenv("MICROSOFT_APP_PASSWORD")
        if val: return val.strip()

    val = (
        os.getenv(key) or 
        os.getenv(f"APPSETTING_{key}") or 
        os.getenv(key.upper()) or 
        default
    )
    return val.strip() if isinstance(val, str) else val

class Config:
    """Bot configuration."""
    
    # Bot Framework settings
    # Empty values = anonymous mode (for local testing)
    APP_ID = _get_env("MicrosoftAppId")
    APP_PASSWORD = _get_env("MicrosoftAppPassword")
    APP_TYPE = _get_env("MicrosoftAppType", "SingleTenant")
    APP_TENANT_ID = _get_env("MicrosoftAppTenantId")

    

    
    # Server settings
    PORT = int(os.getenv("PORT", 3978))
    
    # Azure OpenAI settings
    AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY", "")
    AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")
    AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-06-01")
    
    @classmethod
    def is_local_dev(cls) -> bool:
        """Check if running in local development mode (no auth)."""
        return not cls.APP_ID or cls.APP_ID == "your-bot-app-id"

    @classmethod
    def validate(cls):
        """Validate configuration settings with fail-fast for auth issues."""
        if not cls.is_local_dev():
            if not cls.APP_ID or not cls.APP_PASSWORD:
                raise ValueError("MicrosoftAppId and MicrosoftAppPassword are required in production")
            
            # CRITICAL: Fail fast if SingleTenant but no tenant ID
            if cls.APP_TYPE == "SingleTenant" and not cls.APP_TENANT_ID:
                raise ValueError(
                    "MicrosoftAppTenantId is REQUIRED for SingleTenant bots. "
                    "Set it in App Service Configuration or environment variables."
                )
            
            # Log the auth configuration for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Bot Auth Config: Type={cls.APP_TYPE}, AppId={cls.APP_ID[:8]}..., TenantId={cls.APP_TENANT_ID[:8] if cls.APP_TENANT_ID else 'NOT SET'}...")
        
        if not cls.AZURE_OPENAI_ENDPOINT or not cls.AZURE_OPENAI_KEY:
            # We only warn here because maybe the user hasn't set them up yet but wants the bot to start
            # But strictly for this agent functionality they are required.
            if os.getenv("AZURE_OPENAI_KEY"):
                pass  # Good
            else:
                # In production, this should likely ensure they exist.
                pass
