import pytest
from unittest.mock import patch, mock_open
from pathlib import Path
from github_token import GitHubTokenManager

@pytest.fixture
def token_manager():
    """Create a token manager instance for testing."""
    return GitHubTokenManager()

def test_init_with_env_token():
    """Test initialization with token in environment."""
    with patch.dict('os.environ', {'GITHUB_TOKEN': 'test_token'}):
        manager = GitHubTokenManager()
        assert manager.token == 'test_token'

def test_init_with_env_file():
    """Test initialization with token in .env file."""
    mock_env_content = 'GITHUB_TOKEN=test_token_from_file\n'
    with patch.dict('os.environ', {}, clear=True), \
         patch('pathlib.Path.home', return_value=Path('/mock_home')), \
         patch('pathlib.Path.exists', return_value=True), \
         patch('builtins.open', mock_open(read_data=mock_env_content)):
        manager = GitHubTokenManager()
        assert manager.token == 'test_token_from_file'

def test_init_without_token():
    """Test initialization without any token available."""
    with patch.dict('os.environ', {}, clear=True), \
         patch('pathlib.Path.home', return_value=Path('/mock_home')), \
         patch('pathlib.Path.exists', return_value=False):
        manager = GitHubTokenManager()
        assert manager.token is None

def test_get_token():
    """Test getting the token."""
    with patch.dict('os.environ', {'GITHUB_TOKEN': 'test_token'}):
        manager = GitHubTokenManager()
        assert manager.get_token() == 'test_token'

def test_set_token_success():
    """Test successfully setting a new token."""
    mock_env_path = Path('/mock_home/.env')
    with patch('pathlib.Path.home', return_value=Path('/mock_home')), \
         patch('builtins.open', mock_open()) as mock_file:
        manager = GitHubTokenManager()
        result = manager.set_token('new_test_token')
        assert result is True
        assert manager.token == 'new_test_token'
        mock_file.assert_called_once_with(mock_env_path, 'a')
        mock_file().write.assert_called_once_with('\nGITHUB_TOKEN=new_test_token\n')

def test_set_token_failure():
    """Test failure when setting a token."""
    with patch('pathlib.Path.home', side_effect=Exception('Mock error')):
        manager = GitHubTokenManager()
        result = manager.set_token('new_test_token')
        assert result is False

def test_load_token_with_invalid_env_file():
    """Test loading token with corrupted or invalid .env file."""
    with patch.dict('os.environ', {}, clear=True), \
         patch('pathlib.Path.home', return_value=Path('/mock_home')), \
         patch('pathlib.Path.exists', return_value=True), \
         patch('builtins.open', side_effect=Exception('Mock file error')):
        manager = GitHubTokenManager()
        assert manager.token is None

def test_set_token_with_empty_token():
    """Test setting an empty token."""
    manager = GitHubTokenManager()
    result = manager.set_token('')
    assert result is False

def test_set_token_with_none():
    """Test setting None as token."""
    manager = GitHubTokenManager()
    result = manager.set_token(None)
    assert result is False

def test_load_token_with_malformed_env_file():
    """Test loading token from malformed .env file."""
    mock_env_content = 'MALFORMED_CONTENT\nGITHUB_TOKEN\nNO_VALUE='
    with patch.dict('os.environ', {}, clear=True), \
         patch('pathlib.Path.home', return_value=Path('/mock_home')), \
         patch('pathlib.Path.exists', return_value=True), \
         patch('builtins.open', mock_open(read_data=mock_env_content)):
        manager = GitHubTokenManager()
        assert manager.token is None
