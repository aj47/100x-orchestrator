import pytest
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent.parent))

from openrouter_client import OpenRouterClient

def test_openrouter_client_initialization():
    """Test OpenRouterClient initialization."""
    client = OpenRouterClient()
    assert client is not None

def test_chat_completion():
    """Test chat completion method."""
    client = OpenRouterClient()
    
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
