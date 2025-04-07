import pytest
import sqlite3
from pathlib import Path
from database import get_model_config, save_config
from unittest.mock import patch, MagicMock

@pytest.fixture
def db_path(tmp_path):
    db_path = tmp_path / "test.db"
    yield db_path
    if db_path.exists():
        db_path.unlink()

def test_get_model_config_success(db_path, monkeypatch):
    # Mock the database connection to return a sample config
    mock_config = {'provider': 'openai', 'api_key_source': 'env:OPENAI_API_KEY'}
    with patch('sqlite3.connect', return_value=MagicMock(row_factory=sqlite3.Row, cursor=MagicMock(fetchone=MagicMock(return_value=mock_config)))):
        config = get_model_config()
        assert config == mock_config

def test_get_model_config_empty(db_path, monkeypatch):
    # Mock the database connection to return no config
    with patch('sqlite3.connect', return_value=MagicMock(row_factory=sqlite3.Row, cursor=MagicMock(fetchone=MagicMock(return_value=None)))):
        config = get_model_config()
        assert config is None

def test_get_model_config_error(db_path, monkeypatch):
    # Mock the database connection to raise an error
    with patch('sqlite3.connect', side_effect=sqlite3.Error):
        config = get_model_config()
        assert config is None

def test_save_config_success(db_path, monkeypatch):
    config = {'provider': 'huggingface', 'api_key_source': 'env:HUGGINGFACE_API_KEY'}
    with patch('sqlite3.connect') as mock_connect:
        assert save_config('model_config', config) is True
        mock_connect.assert_called_once()
        mock_cursor = mock_connect.return_value.cursor.return_value
        mock_cursor.execute.assert_called_once()
        mock_connect.return_value.commit.assert_called_once()

def test_save_config_error(db_path, monkeypatch):
    config = {'provider': 'huggingface', 'api_key_source': 'env:HUGGINGFACE_API_KEY'}
    with patch('sqlite3.connect', side_effect=sqlite3.Error):
        assert save_config('model_config', config) is False

