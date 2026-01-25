"""Azure OpenAI client wrapper for gap analysis."""
# from openai import AzureOpenAI (Removed, using AsyncAzureOpenAI)
from .config import Config


class AzureOpenAIClient:
    """Client for Azure OpenAI API calls."""
    
    def __init__(self):
        if not Config.AZURE_OPENAI_ENDPOINT or not Config.AZURE_OPENAI_KEY:
            raise ValueError(
                "Azure OpenAI credentials not configured. "
                "Set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_KEY in .env"
            )
        
        from openai import AsyncAzureOpenAI
        self.client = AsyncAzureOpenAI(
            azure_endpoint=Config.AZURE_OPENAI_ENDPOINT,
            api_key=Config.AZURE_OPENAI_KEY,
            api_version=Config.AZURE_OPENAI_API_VERSION
        )
        self.deployment = Config.AZURE_OPENAI_DEPLOYMENT
    
    async def chat_completion(self, system_prompt: str, user_message: str) -> str:
        """
        Call Azure OpenAI chat completion.
        
        Args:
            system_prompt: System instructions for the model
            user_message: User input message
            
        Returns:
            Model response text
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=2000,
                temperature=0.1,
                top_p=0.95
            )
            
            if not response.choices:
                raise ValueError("Empty response from Azure OpenAI")
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            raise RuntimeError(f"Azure OpenAI API error: {str(e)}")
