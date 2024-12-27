import os
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
        
    def chat_completion(self, system_message: str = "", user_message: str = "", model=None):
        """Get a summary of the coding session logs using JSON mode"""
        # If no model specified, use the default orchestrator model
        if model is None:
            from database import get_model_config
            config = get_model_config()
            if config and 'orchestrator_model' in config:
                model = config['orchestrator_model']
            else:
                model = "openrouter/google/gemini-flash-1.5"
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
            logging.error(f"Error response from litellm: {str(e)}")
            return f"Error generating summary: {str(e)}"
