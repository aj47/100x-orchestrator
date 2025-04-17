import os
import json
import logging
import litellm
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
        
        # Initialize API keys dictionary
        self.api_keys = {}
        
        # Load API keys for different providers
        self.api_keys["openrouter"] = os.getenv('OPENROUTER_API_KEY')
        self.api_keys["anthropic"] = os.getenv('ANTHROPIC_API_KEY')
        self.api_keys["openai"] = os.getenv('OPENAI_API_KEY')
        self.api_keys["together"] = os.getenv('TOGETHER_API_KEY')
        self.api_keys["azure"] = os.getenv('AZURE_API_KEY')
        self.api_keys["cohere"] = os.getenv('COHERE_API_KEY')
        self.api_keys["mistral"] = os.getenv('MISTRAL_API_KEY')
        self.api_keys["groq"] = os.getenv('GROQ_API_KEY')
        
        # Default to OpenRouter if no other keys are available
        if not any(self.api_keys.values()):
            raise ValueError(f"No API keys found in {env_path}. At least one provider API key is required.")

        litellm.success_callback=["helicone"]
    
    def _get_provider_from_model(self, model):
        """Extract provider from model string"""
        if model.startswith("openrouter/"):
            return "openrouter"
        elif model.startswith("anthropic/") or "claude" in model:
            return "anthropic"
        elif model.startswith("openai/") or "gpt" in model:
            return "openai"
        elif model.startswith("together/") or "togethercomputer" in model:
            return "together"
        elif model.startswith("azure/"):
            return "azure"
        elif model.startswith("cohere/") or "command" in model:
            return "cohere"
        elif model.startswith("mistral/") or "mistral" in model:
            return "mistral"
        elif model.startswith("groq/"):
            return "groq"
        else:
            # Default to openrouter if provider can't be determined
            return "openrouter"
        
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
        
        # Determine the provider based on the model
        provider = self._get_provider_from_model(model)
        
        # Get the appropriate API key
        api_key = self.api_keys.get(provider)
        
        # If the API key for the specified provider is not available, log a warning and try to use an available key
        if not api_key:
            logging.warning(f"API key for provider '{provider}' not found. Checking for alternative providers.")
            # Find the first available API key
            for available_provider, available_key in self.api_keys.items():
                if available_key:
                    provider = available_provider
                    api_key = available_key
                    logging.warning(f"Using '{provider}' API key instead.")
                    break
            
            if not api_key:
                error_msg = f"No API key available for any provider. Please set at least one provider API key."
                logging.error(error_msg)
                return json.dumps({
                    "error": error_msg,
                    "model": model,
                    "model_type": model_type
                })
        
        logging.info(f"Using {model_type} model: {model} with provider: {provider}")
        try:
            response = completion(
                model=model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                api_key=api_key,
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
            logging.error(f"Provider: {provider}")
            logging.error(f"System message length: {len(system_message)}")
            logging.error(f"User message length: {len(user_message)}")
            return json.dumps({
                "error": str(e),
                "model": model,
                "model_type": model_type,
                "provider": provider
            })
