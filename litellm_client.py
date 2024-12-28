import os
import json
import logging
from pathlib import Path
from dotenv import load_dotenv
from litellm import completion

class LiteLLMClient:
    """Client for interacting with LLMs to get summaries with JSON mode"""
    
    def __init__(self):
        # Load environment variables from ~/.env
        env_path = Path.home() / '.env'
        if not load_dotenv(env_path):
            logging.warning(f"Could not load {env_path}")
            
        self.api_key = os.getenv('OPENROUTER_API_KEY')
        
        if not self.api_key:
            raise ValueError(f"OPENROUTER_API_KEY not found in {env_path}")
        
    def chat_completion(self, system_message: str = "", user_message: str = "", model_type="orchestrator"):
        """Get a summary of the coding session logs using JSON mode"""
        # Get the appropriate model based on type
        from database import get_model_config
        config = get_model_config()
        
        # Default models - all use Gemini Flash
        DEFAULT_MODELS = {
            "orchestrator": "openrouter/google/gemini-flash-1.5",
            "aider": "openrouter/google/gemini-flash-1.5",
            "agent": "openrouter/google/gemini-flash-1.5"
        }
        
        # Get model from config or use default
        model = config.get(f"{model_type}_model", DEFAULT_MODELS[model_type]) if config else DEFAULT_MODELS[model_type]
        
        logging.info(f"Using {model_type} model: {model}")
        """Get a summary of the coding session logs using JSON mode"""
        try:
            response = completion(
                model=model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                api_key=self.api_key,
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
                "model_type": model_type
            })
