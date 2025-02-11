import os
import json
import logging
import litellm
from pathlib import Path
from dotenv import load_dotenv
from litellm import completion

class LiteLLMClient:
    """Client for interacting with LLMs to get summaries with JSON mode"""
    
    def __init__(self, provider: str = "openrouter"):
        # Configuration for API keys
        self.api_key_config = {
            "openrouter": os.getenv("OPENROUTER_API_KEY"),
            "togetherai": os.getenv("TOGETHERAI_API_KEY"),
            # Add more providers as needed
        }

        # Load environment variables from ~/.env (fallback)
        env_path = Path.home() / '.env'
        if not load_dotenv(env_path):
            logging.warning(f"Could not load {env_path}")

        self.provider = provider
        self.api_key = self.api_key_config.get(provider)

        if not self.api_key:
            raise ValueError(f"API key for provider '{provider}' not found in environment variables or config.")

        litellm.success_callback=["helicone"]
        
    def chat_completion(self, system_message: str = "", user_message: str = "", model_type="orchestrator", agent_id=0):
        # Get the appropriate model based on type
        from database import get_model_config
        config = get_model_config()
        
        # Default models - all use Gemini Flash
        DEFAULT_MODELS = {
            "orchestrator": "openrouter/google/gemini-flash-1.5",  # Default model for orchestrator
            "aider": "openrouter/google/gemini-flash-1.5",        # Default model for aider
            "agent": "openrouter/google/gemini-flash-1.5"         # Default model for agent
        }
        
        # Get model from config or use default
        model = config.get(f"{model_type}_model", DEFAULT_MODELS[model_type]) if config else DEFAULT_MODELS[model_type]
        
        logging.info(f"Using {model_type} model: {model} with provider: {self.provider}")
        try:
            response = completion(
                model=model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                api_key=self.api_key,
                metadata={
                    "agent_id": agent_id
                },
                response_format={"type": "json_object"}
            )
            
            # Strip markdown code blocks if present
            content = response.choices[0].message.content
            if content.startswith('```json') and content.endswith('```'):
                content = content[7:-3].strip()  # Remove ```json and trailing ```
            elif content.startswith('```') and content.endswith('```'):
                content = content[3:-3].strip()  # Remove ``` and trailing ```
            
            return content
            
        except Exception as e:
            logging.error(f"Error in chat_completion:", exc_info=True)
            logging.error(f"Model type: {model_type}")
            logging.error(f"Model: {model}")
            logging.error(f"System message length: {len(system_message)}")
            logging.error(f"User message length: {len(user_message)}")
            return json.dumps({
                "error": str(e),
                "model": model,
                "model_type": model_type,
                "provider": self.provider
            })
