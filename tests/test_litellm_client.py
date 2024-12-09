import pytest
import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from litellm_client import LiteLLMClient

# Load environment variables for testing
env_path = Path.home() / '.env'
load_dotenv(env_path)

OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')

# Skip tests if API key is not set
pytestmark = pytest.mark.skipif(not OPENROUTER_API_KEY, reason="OPENROUTER_API_KEY not found")


def test_litellm_client_initialization():
    """Test LiteLLMClient initialization."""
    client = LiteLLMClient()
    assert client is not None
    assert client.api_key == OPENROUTER_API_KEY

def test_chat_completion_success():
    """Test chat completion method with a successful response."""
    client = LiteLLMClient()
    system_message = "You are a helpful coding assistant."
    user_message = "Write a simple Python function to calculate factorial."
    response = client.chat_completion(system_message=system_message, user_message=user_message)
    assert response is not None
    assert isinstance(response, str)
    assert "def factorial" in response #Check for expected content

def test_chat_completion_failure():
    """Test chat completion method with a failure (e.g., invalid API key)."""
    client = LiteLLMClient()
    client.api_key = "invalid-api-key" #Simulate failure
    system_message = "You are a helpful coding assistant."
    user_message = "Write a simple Python function to calculate factorial."
    with pytest.raises(Exception) as e:
        client.chat_completion(system_message=system_message, user_message=user_message)
    assert "Error getting session summary" in str(e.value) #Check for expected error message


