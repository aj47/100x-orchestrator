import pytest
import os
from orchestrator import initialiseCodingAgent, delete_agent, load_tasks, save_tasks, normalize_path
from pathlib import Path
import tempfile
import shutil
import json
from unittest.mock import patch
import logging

# Configure logging for testing
logging.basicConfig(level=logging.DEBUG)

# Mock functions for testing
@patch('orchestrator.cloneRepository', return_value=True)
@patch('orchestrator.create_pull_request', return_value=None)
@patch('orchestrator.get_github_token', return_value="test_token")
def test_initialiseCodingAgent_success(mock_get_github_token, mock_create_pull_request, mock_cloneRepository):
    """Test successful initialization of coding agents."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_url = "https://github.com/test/repo.git"
        task_description = "Test task description"
        agent_ids = initialiseCodingAgent(repository_url=repo_url, task_description=task_description)
        assert agent_ids is not None
        assert len(agent_ids) > 0
        # Clean up created agents
        tasks_data = load_tasks()
        for agent_id in agent_ids:
            delete_agent(agent_id)

@patch('orchestrator.cloneRepository', return_value=False)
def test_initialiseCodingAgent_failure(mock_cloneRepository):
    """Test initialization failure due to repository cloning."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_url = "https://github.com/test/repo.git"
        task_description = "Test task description"
        agent_ids = initialiseCodingAgent(repository_url=repo_url, task_description=task_description)
        assert agent_ids is None

def test_delete_agent():
    """Test deleting an agent."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a dummy agent entry in tasks.json
        tasks_data = load_tasks()
        agent_id = "test_agent_id"
        tasks_data["agents"][agent_id] = {"workspace": tmpdir}
        save_tasks(tasks_data)
        
        assert delete_agent(agent_id) == True
        # Verify agent is removed
        tasks_data = load_tasks()
        assert agent_id not in tasks_data["agents"]

def test_load_tasks_empty():
    """Test loading tasks from an empty tasks.json."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = Path(tmpdir) / "tasks.json"
        config_file.touch()
        tasks_data = load_tasks()
        assert tasks_data == {"tasks": [], "agents": {}, "repository_url": ""}

def test_load_tasks_valid():
    """Test loading tasks from a valid tasks.json."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = Path(tmpdir) / "tasks.json"
        valid_data = {"tasks": ["task1"], "agents": {"agent1": {"workspace": tmpdir}}, "repository_url": "test_url"}
        with open(config_file, "w") as f:
            json.dump(valid_data, f)
        tasks_data = load_tasks()
        assert tasks_data == valid_data

def test_save_tasks():
    """Test saving tasks to tasks.json."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_file = Path(tmpdir) / "tasks.json"
        tasks_data = {"tasks": ["task1"], "agents": {"agent1": {"workspace": tmpdir}}, "repository_url": "test_url"}
        save_tasks(tasks_data)
        with open(config_file, "r") as f:
            loaded_data = json.load(f)
        assert loaded_data == tasks_data

def test_normalize_path_orchestrator():
    """Test path normalization in orchestrator."""
    test_path = "/tmp/test/path"
    normalized_path = normalize_path(test_path)
    assert normalized_path == test_path

