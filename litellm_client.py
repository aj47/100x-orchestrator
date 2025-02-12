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
            
        # Load API keys for all supported providers
        self.provider_keys = {
            "openai": os.getenv("OPENAI_API_KEY"),
            "azure_openai": os.getenv("AZURE_OPENAI_API_KEY"),
            "azure_ai": os.getenv("AZURE_AI_API_KEY"),
            "aiml": os.getenv("AIML_API_KEY"),
            "vertex": os.getenv("VERTEXAI_API_KEY"),
            "together_ai": os.getenv("TOGETHERAI_API_KEY"),
            "anthropic": os.getenv("ANTHROPIC_API_KEY"),
            "aws_sagemaker": os.getenv("AWS_SAGEMAKER_API_KEY"),
            "aws_bedrock": os.getenv("AWS_BEDROCK_API_KEY"),
            "mistral": os.getenv("MISTRAL_API_KEY"),
            "codestral": os.getenv("CODESTRAL_API_KEY"),
            "cohere": os.getenv("COHERE_API_KEY"),
            "anyscale": os.getenv("ANYSCALE_API_KEY"),
            "huggingface": os.getenv("HUGGINGFACE_API_KEY"),
            "databricks": os.getenv("DATABRICKS_API_KEY"),
            "deepgram": os.getenv("DEEPGRAM_API_KEY"),
            "watsonx": os.getenv("WATSONX_API_KEY"),
            "predibase": os.getenv("PREDIBASE_API_KEY"),
            "nvidia": os.getenv("NVIDIA_NIM_API_KEY"),
            "xai": os.getenv("XAI_API_KEY"),
            "lm_studio": os.getenv("LM_STUDIO_API_KEY"),
            "cerebras": os.getenv("CEREBRAS_API_KEY"),
            "volcano": os.getenv("VOLCANO_API_KEY"),
            "triton": os.getenv("TRITON_API_KEY"),
            "ollama": os.getenv("OLLAMA_API_KEY"),
            "perplexity": os.getenv("PERPLEXITY_API_KEY"),
            "friendliai": os.getenv("FRIENDLIAI_API_KEY"),
            "galadriel": os.getenv("GALADRELI_API_KEY"),
            "topaz": os.getenv("TOPAZ_API_KEY"),
            "groq": os.getenv("GROQ_API_KEY"),
            "github": os.getenv("GITHUB_API_KEY"),
            "deepseek": os.getenv("DEEPSEEK_API_KEY"),
            "fireworks_ai": os.getenv("FIREWORKS_AI_API_KEY"),
            "clarifai": os.getenv("CLARIFAI_API_KEY"),
            "vllm": os.getenv("VLLM_API_KEY"),
            "infinity": os.getenv("INFINITY_API_KEY"),
            "xinference": os.getenv("XINFERENCE_API_KEY"),
            "cloudflare_workers": os.getenv("CLOUDFLARE_WORKERS_API_KEY"),
            "deepinfra": os.getenv("DEEPINFRA_API_KEY"),
            "ai21": os.getenv("AI21_API_KEY"),
            "nlp_cloud": os.getenv("NLPCLOUD_API_KEY"),
            "replicate": os.getenv("REPLICATE_API_KEY"),
            "voyage": os.getenv("VOYAGEAI_API_KEY"),
            "jina": os.getenv("JINA_AI_API_KEY"),
            "aleph_alpha": os.getenv("ALEPH_ALPHA_API_KEY"),
            "baseten": os.getenv("BASETEN_API_KEY"),
            "openrouter": os.getenv("OPENROUTER_API_KEY"),
            "sambanova": os.getenv("SAMBANOVA_API_KEY"),
            "petals": os.getenv("PETALS_API_KEY"),
        }
        
        # Optionally, log warnings for missing keys
        for provider, key in self.provider_keys.items():
            if not key:
                logging.warning(f"{provider.upper()} API key not found")

        litellm.success_callback=["helicone"]
        
    def _select_api_key(self, model: str, model_type: str) -> str:
        """
        Select and return the proper API key based on substrings within the model string.
        Falls back to the OPENROUTER_API_KEY if no specific provider matches.
        """
        # Mapping of model prefixes (or substrings) to provider key names
        providers_map = {
            "openai/": "openai",
            "azure_openai/": "azure_openai",
            "azure_ai/": "azure_ai",
            "aiml/": "aiml",
            "vertex/": "vertex",
            "together_ai/": "together_ai",
            "anthropic/": "anthropic",
            "aws_sagemaker/": "aws_sagemaker",
            "aws_bedrock/": "aws_bedrock",
            "mistral/": "mistral",
            "codestral/": "codestral",
            "cohere/": "cohere",
            "anyscale/": "anyscale",
            "huggingface/": "huggingface",
            "databricks/": "databricks",
            "deepgram/": "deepgram",
            "watsonx/": "watsonx",
            "predibase/": "predibase",
            "nvidia/": "nvidia",
            "xai/": "xai",
            "lm_studio/": "lm_studio",
            "cerebras/": "cerebras",
            "volcano/": "volcano",
            "triton/": "triton",
            "ollama/": "ollama",
            "perplexity/": "perplexity",
            "friendliai/": "friendliai",
            "galadriel/": "galadriel",
            "topaz/": "topaz",
            "groq/": "groq",
            "github/": "github",
            "deepseek/": "deepseek",
            "fireworks_ai/": "fireworks_ai",
            "clarifai/": "clarifai",
            "vllm/": "vllm",
            "infinity/": "infinity",
            "xinference/": "xinference",
            "cloudflare_workers/": "cloudflare_workers",
            "deepinfra/": "deepinfra",
            "ai21/": "ai21",
            "nlp_cloud/": "nlp_cloud",
            "replicate/": "replicate",
            "voyage/": "voyage",
            "jina/": "jina",
            "aleph_alpha/": "aleph_alpha",
            "baseten/": "baseten",
            "sambanova/": "sambanova",
            "petals/": "petals",
            "openrouter/": "openrouter",
        }
    
        # Iterate over the mapping and select a key if the model string matches the provider prefix
        for prefix, key_name in providers_map.items():
            if model.startswith(prefix) or prefix[:-1] in model.lower():
                selected_key = self.provider_keys.get(key_name)
                if selected_key:
                    return selected_key
                else:
                    logging.error(f"{key_name.upper()} API key not found for model {model}")
                    raise ValueError(f"{key_name.upper()} API key not found")
    
        # Fallback to OPENROUTER_API_KEY if nothing else matches
        fallback = self.provider_keys.get("openrouter")
        if fallback:
            return fallback
        raise ValueError("No valid API key found for model.")

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
        
        logging.info(f"Using {model_type} model: {model}")
        try:
            api_key = self._select_api_key(model, model_type)
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
            logging.error(f"System message length: {len(system_message)}")
            logging.error(f"User message length: {len(user_message)}")
            return json.dumps({
                "error": str(e),
                "model": model,
                "model_type": model_type
            })
