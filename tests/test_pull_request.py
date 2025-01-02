import json
import pytest
from unittest.mock import patch, MagicMock
from pull_request import PullRequestManager
from github import Auth

@pytest.fixture
def pr_manager():
    return PullRequestManager()

@pytest.fixture
def mock_github():
    return MagicMock()

@pytest.fixture
def mock_repo():
    repo = MagicMock()
    repo.get_pulls.return_value = MagicMock(totalCount=0)
    return repo

@pytest.fixture
def mock_pr():
    return MagicMock()

@pytest.fixture
def mock_token():
    return MagicMock()

def test_init(pr_manager):
    """Test initialization."""
    assert isinstance(pr_manager, PullRequestManager)
    assert pr_manager.token_manager is not None
    assert pr_manager.litellm_client is not None

def test_generate_pr_info_success(pr_manager):
    """Test successful PR info generation."""
    mock_pr_info = {
        'title': 'Test PR',
        'description': 'Test description',
        'labels': ['test'],
        'reviewers': ['reviewer1']
    }

    with patch.object(pr_manager.litellm_client, 'chat_completion',
                     return_value=json.dumps(mock_pr_info)):
        result = pr_manager.generate_pr_info('test_agent', 'test history')
        assert result == mock_pr_info

def test_generate_pr_info_failure(pr_manager):
    """Test PR info generation failure."""
    with patch.object(pr_manager.litellm_client, 'chat_completion',
                     side_effect=Exception('Test error')):
        result = pr_manager.generate_pr_info('test_agent', 'test history')
        assert result is None

def test_create_pull_request_no_token(pr_manager):
    """Test when no token is available."""
    with patch.object(pr_manager.token_manager, 'get_token', return_value=None):
        result = pr_manager.create_pull_request('test_agent', 'test-branch', {})
        assert result is None

def test_create_pull_request_no_repo_url(pr_manager):
    """Test when no repository URL is available."""
    with patch('orchestrator.load_tasks', return_value={}), \
         patch.object(pr_manager.token_manager, 'get_token', return_value='test_token'):
        result = pr_manager.create_pull_request('test_agent', 'test-branch', {})
        assert result is None

def test_create_pull_request_no_agent_data(pr_manager):
    """Test when no agent data is available."""
    with patch('orchestrator.load_tasks', return_value={
        'repository_url': 'https://github.com/test/repo',
        'agents': {}
    }), patch.object(pr_manager.token_manager, 'get_token', return_value='test_token'):
        result = pr_manager.create_pull_request('test_agent', 'test-branch', {})
        assert result is None

def test_create_pull_request_no_repo_path(pr_manager):
    """Test when no repository path is available."""
    with patch('orchestrator.load_tasks', return_value={
        'repository_url': 'https://github.com/test/repo',
        'agents': {'test_agent': {}}
    }), patch.object(pr_manager.token_manager, 'get_token', return_value='test_token'):
        result = pr_manager.create_pull_request('test_agent', 'test-branch', {})
        assert result is None

def test_create_pull_request_git_error(pr_manager, mock_github, mock_repo):
    """Test when git operations fail."""
    with patch('github.Github', return_value=mock_github), \
         patch('github.Auth.Token', return_value=MagicMock()), \
         patch('orchestrator.load_tasks', return_value={
             'repository_url': 'https://github.com/test/repo',
             'agents': {
                 'test_agent': {'repo_path': '/test/path'}
             }
         }), \
         patch('subprocess.run', side_effect=Exception('Git error')), \
         patch('os.chdir'):

        # Configure mock_github to return mock_repo
        mock_github.get_repo.return_value = mock_repo

        result = pr_manager.create_pull_request('test_agent', 'test-branch', {})
        assert result is None

def test_create_pull_request_github_error(pr_manager, mock_github):
    """Test when GitHub operations fail."""
    mock_github.get_repo.side_effect = Exception('GitHub error')

    with patch('github.Github', return_value=mock_github), \
         patch('github.Auth.Token', return_value=MagicMock()), \
         patch('orchestrator.load_tasks', return_value={
             'repository_url': 'https://github.com/test/repo',
             'agents': {
                 'test_agent': {'repo_path': '/test/path'}
             }
         }), \
         patch('subprocess.run'), \
         patch('os.chdir'):

        result = pr_manager.create_pull_request('test_agent', 'test-branch', {})
        assert result is None