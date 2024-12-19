import os
import logging
from logging_config import configure_logging

# Initialize logging
configure_logging()
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
        
    def chat_completion(self, system_message: str = "", user_message: str = "", model="openrouter/google/gemini-flash-1.5"):
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
            
            return response.choices[0].message.content
            
        except Exception as e:
            logging.error(f"Error getting session summary: {e}")
            return f"Error generating summary: {str(e)}"
