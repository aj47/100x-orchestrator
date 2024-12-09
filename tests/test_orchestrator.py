import pytest
import os
from unittest.mock import patch, MagicMock
from orchestrator import (
    initialiseCodingAgent,
    load_tasks,
    save_tasks,
    delete_agent,
    main_loop,
    get_github_token,
    create_pull_request,
    cloneRepository,
    update_agent_output
)
from pathlib import Path
import tempfile
import shutil
import logging
from agent_session import AgentSession

# Configure logging for testing
logging.basicConfig(level=logging.INFO)

@pytest.fixture
def mock_env(monkeypatch):
    """Mock environment variables for testing."""
    monkeypatch.setenv("GITHUB_TOKEN", "test_github_token")
    monkeypatch.setenv("LITELLM_MODEL", "test_model")

@pytest.fixture
def mock_github(monkeypatch):
    """Mock the Github library for testing."""
    mock_github_class = MagicMock()
    mock_github_class.get_repo.return_value = MagicMock(
        create_pull=MagicMock(return_value=MagicMock(html_url="test_pr_url"))
    )
    mock_github_class.get_user.return_value = MagicMock(login="test_user")
    monkeypatch.setattr("orchestrator.Github", mock_github_class)

@pytest.fixture
def mock_subprocess(monkeypatch):
    """Mock subprocess for testing."""
    mock_subprocess_class = MagicMock()
    mock_subprocess_class.run.return_value = MagicMock(returncode=0)
    monkeypatch.setattr("subprocess.run", mock_subprocess_class.run)

@pytest.fixture
def mock_litellm(monkeypatch):
    """Mock the litellm library for testing."""
    mock_litellm_class = MagicMock()
    mock_litellm_class.chat_completion.return_value = '{"progress": "Task initiated", "thought": "Starting the process", "action": "/instruct Next step", "future": "Expect progress soon"}'
    monkeypatch.setattr("orchestrator.LiteLLMClient", mock_litellm_class)

@pytest.fixture
def mock_agent_session(monkeypatch):
    """Mock the AgentSession class for testing."""
    mock_agent_session_class = MagicMock(spec=AgentSession)
    mock_agent_session_class.start.return_value = True
    mock_agent_session_class.is_ready.return_value = True
    mock_agent_session_class.get_output.return_value = ""
    mock_agent_session_class.send_message.return_value = True
    mock_agent_session_class.cleanup.return_value = None
    monkeypatch.setattr("orchestrator.AgentSession", mock_agent_session_class)

@pytest.fixture
def temp_config_file():
    """Create a temporary tasks.json file."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        json.dump({"tasks": [], "agents": {}, "repository_url": ""}, f)
        yield f.name
    os.remove(f.name)

def test_load_tasks(temp_config_file):
    """Test loading tasks from tasks.json."""
    tasks_data = load_tasks()
    assert tasks_data == {"tasks": [], "agents": {}, "repository_url": ""}

def test_save_tasks(temp_config_file):
    """Test saving tasks to tasks.json."""
    tasks_data = {"tasks": ["test_task"], "agents": {"test_agent": {}}, "repository_url": "test_url"}
    save_tasks(tasks_data)
    with open(temp_config_file, "r") as f:
        loaded_data = json.load(f)
    assert loaded_data == {"tasks": ["test_task"], "agents": {"test_agent": {}}, "repository_url": "test_url"}

def test_delete_agent(temp_config_file, mock_agent_session):
    """Test deleting an agent."""
    tasks_data = {"tasks": [], "agents": {"test_agent": {"workspace": "/tmp/test"}}, "repository_url": ""}
    save_tasks(tasks_data)
    assert delete_agent("test_agent")
    with open(temp_config_file, "r") as f:
        loaded_data = json.load(f)
    assert loaded_data["agents"] == {}

def test_initialiseCodingAgent(mock_subprocess, mock_litellm, mock_agent_session):
    """Test initializing coding agents."""
    agent_ids = initialiseCodingAgent(repository_url="test_url", task_description="test_task", num_agents=1)
    assert len(agent_ids) == 1

def test_get_github_token(mock_env):
    """Test getting the GitHub token."""
    token = get_github_token()
    assert token == "test_github_token"

def test_create_pull_request(mock_github, mock_subprocess):
    """Test creating a pull request."""
    pr = create_pull_request("test_agent", "test_branch", {"title": "test_title", "description": "test_description"})
    assert pr.html_url == "test_pr_url"

def test_cloneRepository(mock_subprocess):
    """Test cloning a repository."""
    assert cloneRepository("test_url")

def test_update_agent_output(mock_agent_session):
    """Test updating agent output."""
    assert update_agent_output("test_agent")

@pytest.mark.asyncio
async def test_main_loop(mock_agent_session, mock_litellm):
    """Test the main loop (partial, as it's an infinite loop)."""
    with patch('orchestrator.sleep') as mock_sleep:
        main_loop()
        mock_sleep.assert_called()

