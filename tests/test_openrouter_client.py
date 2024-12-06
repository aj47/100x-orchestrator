import pytest
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent.parent))

from litellm_client import LiteLLMClient

def test_litellm_client_initialization():
    """Test LiteLLMClient initialization."""
    client = LiteLLMClient()
    assert client is not None

def test_chat_completion():
    """Test chat completion method."""
    client = LiteLLMClient()
    
    system_message = "You are a helpful coding assistant."
    user_message = "Write a simple Python function to calculate factorial."
    
    try:
        response = client.chat_completion(
            system_message=system_message, 
            user_message=user_message
        )
        assert response is not None
        assert isinstance(response, str)
    except Exception as e:
        pytest.fail(f"Chat completion failed: {e}")
