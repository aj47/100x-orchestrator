import pytest
import sys
from pathlib import Path
import os
import subprocess
import json
from unittest.mock import patch, MagicMock
from unittest import mock

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent.parent))

from orchestrator import (
    initialiseCodingAgent,
    load_tasks,
    save_tasks,
    delete_agent,
    cloneRepository,
    create_pull_request,
    get_github_token,
    update_agent_output
)
from agent_session import AgentSession

# Mock functions for testing
@patch('orchestrator.initialiseCodingAgent')
@patch('orchestrator.save_tasks')
@patch('orchestrator.load_tasks')
def test_load_tasks_exception(mock_load_tasks, mock_save_tasks, mock_initialiseCodingAgent, temp_config_file):
    """Test load_tasks exception handling."""
    mock_load_tasks.side_effect = FileNotFoundError
    tasks_data = load_tasks()
    assert tasks_data == {
        "tasks": [],
        "agents": {},
        "repository_url": ""
    }

@patch('orchestrator.subprocess.run')
def test_clone_repository_exception(mock_subprocess_run):
    """Test cloneRepository exception handling."""
    mock_subprocess_run.side_effect = subprocess.CalledProcessError(1, 'git clone')
    result = cloneRepository('test_url')
    assert result is False

@patch('orchestrator.Github')
def test_create_pull_request_exception(mock_github):
    """Test create_pull_request exception handling."""
    mock_github.return_value.get_repo.return_value.create_pull.side_effect = Exception("GitHub API error")
    result = create_pull_request('test_agent_id', 'test_branch', {'title': 'Test PR'})
    assert result is None

@patch('orchestrator.os.environ')
def test_get_github_token_exception(mock_os_environ):
    """Test get_github_token exception handling."""
    mock_os_environ.__getitem__.side_effect = KeyError("GITHUB_TOKEN")
    token = get_github_token()
    assert token is None

@patch('orchestrator.AgentSession.start')
def test_initialiseCodingAgent_exception(mock_agent_session_start, temp_workspace):
    """Test initialiseCodingAgent exception handling."""
    mock_agent_session_start.return_value = False
    result = initialiseCodingAgent(repository_url="test_url", task_description="test_task")
    assert result is None

@patch('orchestrator.AgentSession')
def test_initialiseCodingAgent_clone_exception(mock_agent_session):
    """Test initialiseCodingAgent exception handling during cloning."""
    mock_agent_session.return_value.start.return_value = True
    mock_agent_session.return_value.send_message.return_value = True
    with patch('orchestrator.cloneRepository') as mock_clone:
        mock_clone.return_value = False
        result = initialiseCodingAgent(repository_url="test_url", task_description="test_task")
        assert result is None

@patch('orchestrator.AgentSession')
def test_initialiseCodingAgent_start_exception(mock_agent_session):
    """Test initialiseCodingAgent exception handling during session start."""
    mock_agent_session.return_value.start.side_effect = Exception("Session start failed")
    result = initialiseCodingAgent(repository_url="test_url", task_description="test_task")
    assert result is None

@patch('orchestrator.load_tasks')
def test_delete_agent_not_found(mock_load_tasks):
    """Test delete_agent when agent is not found."""
    mock_load_tasks.return_value = {'agents': {}}
    result = delete_agent('test_agent_id')
    assert result is False

@patch('orchestrator.save_agent')
@patch('orchestrator.db_delete_agent')
@patch('orchestrator.shutil.rmtree')
def test_delete_agent_success(mock_rmtree, mock_db_delete_agent, mock_save_agent, temp_workspace):
    """Test successful agent deletion."""
    mock_db_delete_agent.return_value = True
    mock_rmtree.return_value = None
    mock_save_agent.return_value = True
    result = delete_agent('test_agent_id')
    assert result is True

@patch('orchestrator.save_agent')
@patch('orchestrator.db_delete_agent')
@patch('orchestrator.shutil.rmtree')
def test_delete_agent_rmtree_failure(mock_rmtree, mock_db_delete_agent, mock_save_agent, temp_workspace):
    """Test agent deletion with rmtree failure."""
    mock_db_delete_agent.return_value = True
    mock_rmtree.side_effect = OSError("Permission denied")
    mock_save_agent.return_value = True
    result = delete_agent('test_agent_id')
    assert result is True #Should still return True even if rmtree fails

@patch('orchestrator.save_agent')
@patch('orchestrator.db_delete_agent')
def test_delete_agent_db_failure(mock_db_delete_agent, mock_save_agent, temp_workspace):
    """Test agent deletion with database failure."""
    mock_db_delete_agent.return_value = False
    mock_save_agent.return_value = True
    result = delete_agent('test_agent_id')
    assert result is False

@patch('orchestrator.subprocess.run')
def test_clone_repository_network_error(mock_subprocess_run):
    """Test cloneRepository with simulated network error."""
    mock_subprocess_run.side_effect = subprocess.CalledProcessError(128, 'git clone', stderr='Network error')
    result = cloneRepository('test_url')
    assert result is False

@patch('orchestrator.subprocess.run')
def test_clone_repository_invalid_url(mock_subprocess_run):
    """Test cloneRepository with invalid URL."""
    mock_subprocess_run.side_effect = subprocess.CalledProcessError(128, 'git clone', stderr='Invalid URL')
    result = cloneRepository('invalid_url')
    assert result is False

@patch('orchestrator.Github')
def test_create_pull_request_api_error(mock_github):
    """Test create_pull_request with GitHub API error."""
    mock_github.return_value.get_repo.return_value.create_pull.side_effect = Exception("GitHub API error")
    result = create_pull_request('test_agent_id', 'test_branch', {'title': 'Test PR'})
    assert result is None

@patch('orchestrator.Github')
def test_create_pull_request_pr_exists(mock_github):
    """Test create_pull_request when PR already exists."""
    mock_github.return_value.get_repo.return_value.get_pulls.return_value.totalCount = 1
    result = create_pull_request('test_agent_id', 'test_branch', {'title': 'Test PR'})
    assert result is not None

@patch('orchestrator.Github')
def test_create_pull_request_missing_repo_url(mock_github):
    """Test create_pull_request with missing repository URL."""
    with patch('orchestrator.load_tasks') as mock_load_tasks:
        mock_load_tasks.return_value = {'repository_url': ''}
        result = create_pull_request('test_agent_id', 'test_branch', {'title': 'Test PR'})
        assert result is None

@patch('orchestrator.Github')
def test_create_pull_request_invalid_branch(mock_github):
    """Test create_pull_request with invalid branch name."""
    with patch('orchestrator.subprocess.run') as mock_subprocess:
        mock_subprocess.side_effect = subprocess.CalledProcessError(1, 'git push', stderr='Invalid branch name')
        result = create_pull_request('test_agent_id', 'invalid/branch', {'title': 'Test PR'})
        assert result is None

@patch('orchestrator.Github')
def test_create_pull_request_missing_pr_info(mock_github):
    """Test create_pull_request with missing pr_info."""
    result = create_pull_request('test_agent_id', 'test_branch', {})
    assert result is not None #Should still create a PR, even if pr_info is empty

@patch('orchestrator.Github')
def test_create_pull_request_reviewers_not_collaborators(mock_github):
    """Test create_pull_request with reviewers who are not collaborators."""
    mock_github.return_value.get_repo.return_value.get_collaborators.return_value = []
    result = create_pull_request('test_agent_id', 'test_branch', {'reviewers': ['non_collaborator']})
    assert result is not None #Should still create a PR, even if reviewers are not collaborators

@patch('orchestrator.load_tasks')
def test_update_agent_output_success(mock_load_tasks):
    """Test successful update of agent output."""
    mock_load_tasks.return_value = {'agents': {'test_agent_id': {'aider_output': ''}}}
    with patch('orchestrator.AgentSession.get_output') as mock_get_output:
        mock_get_output.return_value = 'Test output'
        result = update_agent_output('test_agent_id')
        assert result is True

@patch('orchestrator.load_tasks')
def test_update_agent_output_agent_not_found(mock_load_tasks):
    """Test update_agent_output when agent is not found."""
    mock_load_tasks.return_value = {'agents': {}}
    result = update_agent_output('test_agent_id')
    assert result is False

@patch('orchestrator.load_tasks')
def test_update_agent_output_session_not_found(mock_load_tasks):
    """Test update_agent_output when session is not found."""
    mock_load_tasks.return_value = {'agents': {'test_agent_id': {'aider_output': ''}}}
    result = update_agent_output('test_agent_id')
    assert result is True #Should return True even if session is not found

@patch('orchestrator.os.environ.get')
def test_get_github_token_success(mock_os_environ_get):
    """Test successful retrieval of GitHub token."""
    mock_os_environ_get.return_value = 'test_token'
    with patch('orchestrator.Github') as mock_github:
        mock_github.return_value.get_user.return_value.login = 'test_user'
        token = get_github_token()
        assert token == 'test_token'

@patch('orchestrator.os.environ.get')
def test_get_github_token_invalid_token(mock_os_environ_get):
    """Test retrieval of invalid GitHub token."""
    mock_os_environ_get.return_value = 'invalid_token'
    with patch('orchestrator.Github') as mock_github:
        mock_github.side_effect = Exception("Invalid token")
        token = get_github_token()
        assert token is None

@patch('orchestrator.load_tasks')
def test_save_tasks_exception(mock_load_tasks, temp_config_file):
    """Test save_tasks exception handling."""
    mock_load_tasks.return_value = {'agents': {'test_agent_id': {'workspace': 'test_workspace'}}}
    with patch('orchestrator.save_agent') as mock_save_agent:
        mock_save_agent.side_effect = Exception("Database error")
        save_tasks({'agents': {'test_agent_id': {'workspace': 'test_workspace'}}})
        mock_save_agent.assert_called_once()

@patch('orchestrator.load_tasks')
def test_save_tasks_empty_agents(mock_load_tasks, temp_config_file):
    """Test save_tasks with empty agents."""
    mock_load_tasks.return_value = {'agents': {}}
    save_tasks({'agents': {}})
    #No assertion needed, as this should run without error

@patch('orchestrator.load_tasks')
def test_save_tasks_repository_url(mock_load_tasks, temp_config_file):
    """Test save_tasks with repository URL."""
    mock_load_tasks.return_value = {'agents': {}}
    save_tasks({'repository_url': 'test_url'})
    #No assertion needed, as this should run without error

@patch('orchestrator.get_all_tasks')
@patch('orchestrator.get_all_agents')
@patch('orchestrator.get_config')
def test_load_tasks_empty_database(mock_get_config, mock_get_all_agents, mock_get_all_tasks):
    """Test load_tasks with empty database."""
    mock_get_config.return_value = None
    mock_get_all_agents.return_value = {}
    mock_get_all_tasks.return_value = []
    tasks_data = load_tasks()
    assert tasks_data == {
        "tasks": [],
        "agents": {},
        "repository_url": ""
    }

@patch('orchestrator.get_all_tasks')
@patch('orchestrator.get_all_agents')
@patch('orchestrator.get_config')
def test_load_tasks_populated_database(mock_get_config, mock_get_all_agents, mock_get_all_tasks):
    """Test load_tasks with populated database."""
    mock_get_config.return_value = "test_repo_url"
    mock_get_all_agents.return_value = {"agent1": {"workspace": "path/to/workspace"}}
    mock_get_all_tasks.return_value = [{"task": "test_task"}]
    tasks_data = load_tasks()
    assert tasks_data == {
        "tasks": [{"task": "test_task"}],
        "agents": {"agent1": {"workspace": "path/to/workspace"}},
        "repository_url": "test_repo_url"
    }

# Add tests for main_loop (this will require significant mocking)
# ... (Add tests for main_loop here, mocking relevant functions) ...

@pytest.fixture
def temp_config_file(tmp_path):
    config_file = tmp_path / "config.json"
    config_file.write_text('{}')
    return config_file

@pytest.fixture
def temp_workspace(tmp_path):
    workspace_dir = tmp_path / "workspace"
    workspace_dir.mkdir()
    return workspace_dir
