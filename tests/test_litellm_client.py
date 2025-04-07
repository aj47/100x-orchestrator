import pytest
from litellm_client import LiteLLMClient
from unittest.mock import patch

def test_litellm_client_init_default():
    client = LiteLLMClient()
    assert client.provider == "openai"
    assert client.api_key_source == "OPENAI_API_KEY"

def test_litellm_client_init_custom(mock_env_vars):
    mock_env_vars({"CUSTOM_API_KEY": "test"})
    client = LiteLLMClient(provider="custom", api_key_source="env:CUSTOM_API_KEY")
    assert client.provider == "custom"
    assert client.api_key_source == "env:CUSTOM_API_KEY"
    assert client.api_key == "test"

def test_litellm_client_missing_api_key(mock_env_vars):
    client = LiteLLMClient(api_key_source="env:MISSING_KEY")
    assert client.api_key is None

def test_litellm_client_invalid_api_key_source(mock_env_vars):
    with pytest.raises(KeyError):
        LiteLLMClient(api_key_source="invalid_source")

def test_litellm_client_chat_completion_success(mock_completion, mock_db):
    with patch('litellm_client.completion', mock_completion):
        client = LiteLLMClient()
        result = client.chat_completion(system_message="test", user_message="test")
        assert result == '{"result": "test"}'

def test_litellm_client_chat_completion_error(mock_db):
    mock_completion = MagicMock(side_effect=Exception("Test Error"))
    with patch('litellm_client.completion', mock_completion):
        client = LiteLLMClient()
        result = client.chat_completion(system_message="test", user_message="test")
        assert result is None

def test_litellm_client_chat_completion_provider(mock_completion, mock_db):
    mock_completion.return_value = {'choices': [{'message': {'content': '{"result": "huggingface"}'}}]}
    with patch('litellm_client.completion', mock_completion):
        client = LiteLLMClient(provider="huggingface")
        result = client.chat_completion(system_message="test", user_message="test")
        assert result == '{"result": "huggingface"}'
        mock_completion.assert_called_once_with(model='gpt-3.5-turbo', messages=[{'role': 'system', 'content': 'test'}, {'role': 'user', 'content': 'test'}], api_key=client.api_key, provider='huggingface')

def test_litellm_client_api_key_file(mock_api_key_file, mock_env_vars):
    client = LiteLLMClient(api_key_source=f"file:{mock_api_key_file}")
    assert client.api_key == "mock_api_key_from_file"

