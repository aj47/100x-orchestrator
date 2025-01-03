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
    create_pull_request, # Added create_pull_request to imports
    get_github_token
)
from agent_session import AgentSession # Added import statement

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
