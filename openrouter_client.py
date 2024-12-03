import os
import requests
import json
import logging
from pathlib import Path
from dotenv import load_dotenv

class OpenRouterClient:
    """Client for interacting with OpenRouter API to get LLM summaries"""
    
    def __init__(self):
        # Load environment variables from ~/.env
        env_path = Path.home() / '.env'
        if not load_dotenv(env_path):
            logging.warning(f"Could not load {env_path}")
            
        self.api_key = os.getenv('OPENROUTER_API_KEY')
        self.site_url = os.getenv('YOUR_SITE_URL', 'http://localhost')
        self.app_name = os.getenv('YOUR_APP_NAME', 'Coding Agent Orchestrator')
        
        if not self.api_key:
            raise ValueError(f"OPENROUTER_API_KEY not found in {env_path}")
            
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        
    def chat_completion(self, system_message: str = "", user_message: str = "", model="google/gemini-flash-1.5"):
        """Get a summary of the coding session logs"""
        try:
            response = requests.post(
                url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "HTTP-Referer": self.site_url,
                    "X-Title": self.app_name,
                },
                json={
                    "model": model,
                    "messages": [
                        {
                            "role": "system",
                            "content": system_message
                        },
                        {
                            "role": "user",
                            "content": user_message
                        }
                    ]
                }
            )
            
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
            
        except Exception as e:
            logging.error(f"Error getting session summary: {e}")
            return f"Error generating summary: {str(e)}"
