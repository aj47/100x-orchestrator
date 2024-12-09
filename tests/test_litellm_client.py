import pytest
import os
from pathlib import Path
from dotenv import load_dotenv
from litellm import completion
from litellm_client import LiteLLMClient

# Mock the litellm.completion function
def mock_completion(*args, **kwargs):
    mock_response = {
        "choices": [
            {
                "message": {
                    "content": '{"progress": "Task initiated", "thought": "Starting the process", "action": "/instruct Next step", "future": "Expect progress soon"}'
                }
            }
        ]
    }
    return mock_response

@pytest.fixture
def mock_env(monkeypatch):
    """Mock environment variables for testing."""
    monkeypatch.setenv("OPENROUTER_API_KEY", "test_api_key")
    
@pytest.fixture
def mock_litellm(monkeypatch):
    """Mock the litellm.completion function."""
    monkeypatch.setattr("litellm.completion", mock_completion)

def test_litellm_client_initialization(mock_env):
    """Test LiteLLMClient initialization."""
    client = LiteLLMClient()
    assert client is not None
    assert client.api_key == "test_api_key"

def test_chat_completion(mock_litellm):
    """Test chat completion method with a mock response."""
    client = LiteLLMClient()
    system_message = "You are a helpful coding assistant."
    user_message = "Write a simple Python function to calculate factorial."
    response = client.chat_completion(system_message=system_message, user_message=user_message)
    assert response == '{"progress": "Task initiated", "thought": "Starting the process", "action": "/instruct Next step", "future": "Expect progress soon"}'

def test_chat_completion_error(monkeypatch):
    """Test chat completion method handling errors."""
    monkeypatch.setattr("litellm.completion", lambda *args, **kwargs: None)
    client = LiteLLMClient()
    system_message = "You are a helpful coding assistant."
    user_message = "Write a simple Python function to calculate factorial."
    response = client.chat_completion(system_message=system_message, user_message=user_message)
    assert "Error generating summary" in response

def test_litellm_client_missing_api_key(monkeypatch):
    """Test LiteLLMClient initialization with missing API key."""
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(ValueError):
        LiteLLMClient()

