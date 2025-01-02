import pytest
import json
import os
from unittest.mock import patch, MagicMock
from pathlib import Path
from litellm_client import LiteLLMClient

@pytest.fixture
def mock_env_file(tmp_path):
    """Create a temporary .env file with test credentials."""
    env_content = "OPENROUTER_API_KEY=test_key_123"
    env_file = tmp_path / ".env"
    env_file.write_text(env_content)
    
    # Mock Path.home() to return our temp directory
    with patch('pathlib.Path.home', return_value=tmp_path):
        yield env_file

@pytest.fixture
def mock_model_config():
    """Mock the database.get_model_config function."""
    return {
        'orchestrator_model': 'openrouter/google/gemini-flash-1.5',
        'aider_model': 'openrouter/google/gemini-flash-1.5',
        'agent_model': 'openrouter/google/gemini-flash-1.5'
    }

@pytest.fixture
def mock_env_vars():
    """Mock environment variables."""
    with patch.dict(os.environ, {'OPENROUTER_API_KEY': 'test_key_123'}):
        yield

@pytest.fixture
def client(mock_env_vars):
    """Create a LiteLLMClient instance with mocked environment."""
    return LiteLLMClient()

def test_init_with_env_file(mock_env_file, mock_env_vars):
    """Test client initialization with .env file."""
    client = LiteLLMClient()
    assert client.api_key == "test_key_123"

def test_init_without_env_file():
    """Test client initialization without .env file."""
    with patch.dict(os.environ, clear=True):
        with patch('pathlib.Path.home', return_value=Path('/nonexistent')):
            with pytest.raises(ValueError, match="OPENROUTER_API_KEY not found"):
                LiteLLMClient()

@patch('litellm_client.completion')
@patch('database.get_model_config')
def test_chat_completion_success(mock_get_config, mock_completion, client, mock_model_config):
    """Test successful chat completion."""
    # Mock the model config
    mock_get_config.return_value = mock_model_config
    
    # Mock the completion response
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content='{"result": "test response"}'))
    ]
    mock_completion.return_value = mock_response
    
    # Test the chat completion
    result = client.chat_completion(
        system_message="system test",
        user_message="user test",
        model_type="orchestrator"
    )
    
    # Verify the result
    assert json.loads(result)["result"] == "test response"

@patch('litellm_client.completion')
@patch('database.get_model_config')
def test_chat_completion_with_markdown(mock_get_config, mock_completion, client, mock_model_config):
    """Test chat completion with markdown code blocks in response."""
    mock_get_config.return_value = mock_model_config
    
    # Test with ```json block
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content='```json\n{"result": "test"}\n```'))
    ]
    mock_completion.return_value = mock_response
    
    result = client.chat_completion(
        system_message="test",
        user_message="test"
    )
    assert json.loads(result)["result"] == "test"

@patch('litellm_client.completion')
@patch('database.get_model_config')
def test_chat_completion_error(mock_get_config, mock_completion, client, mock_model_config):
    """Test chat completion with error."""
    mock_get_config.return_value = mock_model_config
    mock_completion.side_effect = Exception("Test error")
    
    result = client.chat_completion(
        system_message="test",
        user_message="test",
        model_type="orchestrator"
    )
    
    error_response = json.loads(result)
    assert "error" in error_response
    assert error_response["error"] == "Test error"
    assert error_response["model"] == mock_model_config["orchestrator_model"]
    assert error_response["model_type"] == "orchestrator"

@patch('litellm_client.completion')
@patch('database.get_model_config')
def test_chat_completion_without_config(mock_get_config, mock_completion, client):
    """Test chat completion when no model config is available."""
    # Mock no config available
    mock_get_config.return_value = None
    
    # Mock successful completion
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content='{"result": "test"}'))
    ]
    mock_completion.return_value = mock_response
    
    result = client.chat_completion(
        system_message="test",
        user_message="test",
        model_type="orchestrator"
    )
    
    # Verify default model was used
    mock_completion.assert_called_once()
    call_args = mock_completion.call_args[1]
    assert call_args["model"] == "openrouter/google/gemini-flash-1.5"
    assert json.loads(result)["result"] == "test"

@patch('litellm_client.completion')
@patch('database.get_model_config')
def test_chat_completion_with_non_json_response(mock_get_config, mock_completion, client, mock_model_config):
    """Test chat completion with non-JSON response."""
    mock_get_config.return_value = mock_model_config

    # Mock response with non-JSON content
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content='This is not JSON'))
    ]
    mock_completion.return_value = mock_response

    result = client.chat_completion(
        system_message="test",
        user_message="test",
        model_type="orchestrator"
    )

    # The result should be a JSON string containing an error message
    assert isinstance(result, str)
    try:
        error_response = json.loads(result)
        assert "error" in error_response
    except json.JSONDecodeError:
        pytest.fail("Result should be valid JSON")
