import os
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile

@pytest.fixture
def mock_env_vars(monkeypatch):
    """Fixture to mock environment variables."""
    with patch.dict(os.environ, clear=True):
        yield monkeypatch.setenv

@pytest.fixture
def mock_api_key_file(tmp_path):
    """Fixture to create a temporary API key file."""
    api_key_file = tmp_path / "api_key.txt"
    api_key_file.write_text("mock_api_key_from_file")
    yield str(api_key_file)

@pytest.fixture
def mock_completion():
    """Fixture to mock litellm.completion."""
    mock_completion = MagicMock()
    mock_completion.return_value = {
        'choices': [{'message': {'content': '{"result": "test"}'}}]
    }
    return mock_completion

@pytest.fixture
def mock_db_config():
    """Fixture for a mock database configuration."""
    return {
        'model_config': {
            'provider': 'openai',
            'api_key_source': 'env:OPENAI_API_KEY'
        }
    }

@pytest.fixture
def mock_db(monkeypatch, mock_db_config):
    """Fixture to mock database interactions."""
    with patch('database.get_model_config', return_value=mock_db_config['model_config']):
        yield

