import pytest
import sys
from pathlib import Path
import os
import subprocess
import json
from unittest.mock import patch, MagicMock

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent.parent))

from orchestrator import (
    initialiseCodingAgent,
    load_tasks,
    save_tasks,
    delete_agent,
    cloneRepository,
    get_github_token,
    update_agent_output,
    main_loop
)
from pull_request import PullRequestManager
from agent_session import AgentSession # Added import statement

# Mock functions for testing
@patch('orchestrator.get_all_tasks')
@patch('orchestrator.get_all_agents')
@patch('orchestrator.get_config')
def test_load_tasks(mock_get_config, mock_get_agents, mock_get_tasks):
    """Test load_tasks normal operation."""
    mock_get_tasks.return_value = []
    mock_get_agents.return_value = {}
    mock_get_config.return_value = 'https://github.com/test/repo'
    
    tasks_data = load_tasks()
    assert tasks_data == {
        "tasks": [],
        "agents": {},
        "repository_url": 'https://github.com/test/repo'
    }

@patch('orchestrator.subprocess.run')
def test_clone_repository_exception(mock_subprocess_run):
    """Test cloneRepository exception handling."""
    mock_subprocess_run.side_effect = subprocess.CalledProcessError(1, 'git clone')
    result = cloneRepository('test_url')
    assert result is False


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

@patch('orchestrator.save_config')
@patch('orchestrator.save_agent')
def test_save_tasks(mock_save_agent, mock_save_config):
    """Test save_tasks normal operation."""
    tasks_data = {
        'repository_url': 'https://github.com/test/repo',
        'agents': {
            'agent1': {'status': 'pending'}
        }
    }
    save_tasks(tasks_data)
    mock_save_config.assert_called_once_with('repository_url', 'https://github.com/test/repo')
    mock_save_agent.assert_called_once_with('agent1', {'status': 'pending'})

@patch('orchestrator.subprocess.run')
def test_clone_repository_success(mock_subprocess_run):
    """Test successful repository cloning."""
    mock_subprocess_run.return_value = MagicMock(returncode=0)
    result = cloneRepository('https://github.com/test/repo')
    assert result is True
    mock_subprocess_run.assert_called_once()

@patch('orchestrator.Github')
@patch('orchestrator.load_dotenv')
def test_get_github_token_success(mock_load_dotenv, mock_github):
    """Test successful GitHub token retrieval."""
    with patch.dict('os.environ', {'GITHUB_TOKEN': 'test_token'}):
        mock_github.return_value.get_user.return_value.login = 'test_user'
        token = get_github_token()
        assert token == 'test_token'

@patch('orchestrator.AgentSession')
@patch('orchestrator.tempfile.mkdtemp')
@patch('orchestrator.cloneRepository')
@patch('orchestrator.os.path.exists')
@patch('orchestrator.os.path.isdir')
@patch('orchestrator.subprocess.check_call')
@patch('orchestrator.os.chdir')  # Add this to mock directory changes
def test_initialiseCodingAgent_success(
    mock_chdir,
    mock_check_call,
    mock_isdir,
    mock_exists,
    mock_clone,
    mock_mkdtemp,
    mock_agent_session
):
    """Test successful agent initialization."""
    # Setup mocks
    mock_mkdtemp.return_value = '/tmp/test_dir'
    mock_clone.return_value = True
    mock_agent_session.return_value.start.return_value = True
    mock_exists.return_value = True
    mock_isdir.return_value = True
    mock_check_call.return_value = 0
    mock_chdir.return_value = None  # Mock successful directory change

    # Mock database operations
    with patch('orchestrator.save_tasks') as mock_save_tasks:
        with patch('orchestrator.get_config') as mock_get_config:
            mock_get_config.return_value = None  # Mock no existing config
            result = initialiseCodingAgent(
                repository_url="https://github.com/test/repo",
                task_description="test task",
                num_agents=1
            )
            
            assert result is not None
            assert len(result) == 1
            assert isinstance(result[0], str)
            mock_clone.assert_called_once()
            mock_check_call.assert_called()
            mock_save_tasks.assert_called()

@patch('orchestrator.load_tasks')
@patch('orchestrator.db_delete_agent')
@patch('orchestrator.os.path.exists')
def test_delete_agent_success(mock_exists, mock_db_delete, mock_load_tasks):
    """Test successful agent deletion."""
    # Setup
    mock_exists.return_value = True
    mock_load_tasks.return_value = {
        'agents': {
            'test_agent': {
                'workspace': '/tmp/test_workspace'
            }
        }
    }
    mock_db_delete.return_value = True
    
    with patch('orchestrator.shutil.rmtree') as mock_rmtree:
        result = delete_agent('test_agent')
        assert result is True
        mock_rmtree.assert_called_once_with('/tmp/test_workspace')

@patch('orchestrator.load_tasks')
def test_update_agent_output_success(mock_load_tasks):
    """Test successful agent output update."""
    mock_load_tasks.return_value = {
        'agents': {
            'test_agent': {
                'status': 'pending'
            }
        }
    }
    
    with patch.dict('orchestrator.aider_sessions', {
        'test_agent': MagicMock(get_output=lambda: 'test output')
    }):
        result = update_agent_output('test_agent')
        assert result is True

@patch('orchestrator.load_tasks')
def test_update_agent_output_no_agent(mock_load_tasks):
    """Test agent output update with non-existent agent."""
    mock_load_tasks.return_value = {'agents': {}}
    result = update_agent_output('non_existent_agent')
    assert result is False
