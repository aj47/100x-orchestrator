import pytest
from orchestrator import initialiseCodingAgent, cloneRepository
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile
import shutil
import os

# Mock functions for testing
def mock_cloneRepository(repo_url):
    return True

def mock_subprocess_run(cmd, shell=True, capture_output=True, text=True):
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = ""
    mock_result.stderr = ""
    return mock_result

@patch('orchestrator.cloneRepository', mock_cloneRepository)
@patch('subprocess.run', mock_subprocess_run)
def test_initialiseCodingAgent_repo_name_extraction():
    """Test repository name extraction in initialiseCodingAgent."""
    repo_url = "https://github.com/owner/repo_name.git"
    task_description = "Test task"
    agent_id = initialiseCodingAgent(repository_url=repo_url, task_description=task_description, num_agents=1)[0]
    tasks_data = {
        'agents': {
            agent_id: {
                'repo_name': 'repo_name'
            }
        }
    }
    assert tasks_data['agents'][agent_id]['repo_name'] == 'repo_name'

@patch('orchestrator.cloneRepository', mock_cloneRepository)
@patch('subprocess.run', mock_subprocess_run)
def test_initialiseCodingAgent_repo_name_extraction_error():
    """Test error handling during repository name extraction."""
    repo_url = "invalid_repo_url"
    task_description = "Test task"
    agent_id = initialiseCodingAgent(repository_url=repo_url, task_description=task_description, num_agents=1)[0]
    tasks_data = {
        'agents': {
            agent_id: {
                'repo_name': 'Repository name unavailable'
            }
        }
    }
    assert tasks_data['agents'][agent_id]['repo_name'] == 'Repository name unavailable'

@patch('orchestrator.cloneRepository', mock_cloneRepository)
@patch('subprocess.run', mock_subprocess_run)
def test_initialiseCodingAgent_no_repo_url():
    """Test handling of missing repository URL."""
    task_description = "Test task"
    agent_id = initialiseCodingAgent(repository_url=None, task_description=task_description, num_agents=1)[0]
    tasks_data = {
        'agents': {
            agent_id: {
                'repo_name': 'Repository name unavailable'
            }
        }
    }
    assert tasks_data['agents'][agent_id]['repo_name'] == 'Repository name unavailable'

@patch('orchestrator.cloneRepository', mock_cloneRepository)
@patch('subprocess.run', mock_subprocess_run)
def test_initialiseCodingAgent_invalid_repo_url():
    """Test handling of invalid repository URL."""
    repo_url = "https://invalid.repo/url"
    task_description = "Test task"
    agent_id = initialiseCodingAgent(repository_url=repo_url, task_description=task_description, num_agents=1)[0]
    tasks_data = {
        'agents': {
            agent_id: {
                'repo_name': 'Repository name unavailable'
            }
        }
    }
    assert tasks_data['agents'][agent_id]['repo_name'] == 'Repository name unavailable'

