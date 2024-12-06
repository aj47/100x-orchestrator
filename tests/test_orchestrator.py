import os
import pytest
import sys
from pathlib import Path
import tempfile
import requests

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent.parent))

from orchestrator import AiderSession, cloneRepository, initialiseCodingAgent
from app import app

def test_aider_session_initialization(tmp_path):
    """Test AiderSession initialization."""
    workspace = str(tmp_path / "test_workspace")
    session = AiderSession(workspace, "test task")
    assert session.workspace_path == workspace
    assert session.task == "test task"
    assert session.process is None
    assert not session._stop_event.is_set()

def test_initialize_coding_agent():
    """Test initializing a coding agent."""
    test_repo = "https://github.com/example/test-repo"
    test_task = "Create a simple README"
    
    try:
        agent = initialiseCodingAgent(repository_url=test_repo, task_description=test_task)
        assert agent is not None
    except Exception as e:
        pytest.fail(f"Failed to initialize coding agent: {e}")

def test_flask_app_routes():
    """Test basic Flask app routes."""
    client = app.test_client()
    
    # Test index route
    response = client.get('/')
    assert response.status_code == 200
    
    # Test create_agent route
    test_payload = {
        'repo_url': 'https://github.com/example/test-repo',
        'tasks': ['Create a simple README'],
        'num_agents': 1
    }
    response = client.post('/create_agent', json=test_payload)
    assert response.status_code in [200, 201]

def test_logging_and_error_handling():
    """Test logging and error handling."""
    # Temporarily redirect logging to capture output
    import logging
    log_capture = []
    
    class LogCapture(logging.Handler):
        def emit(self, record):
            log_capture.append(record.getMessage())
    
    logger = logging.getLogger('test_logger')
    handler = LogCapture()
    logger.addHandler(handler)
    
    # Simulate an action that might log something
    try:
        initialiseCodingAgent(repository_url=None, task_description=None)
    except Exception:
        pass
    
    # Check that logs were generated
    assert len(log_capture) > 0

@pytest.mark.skip(reason="Requires network access and git installation")
def test_clone_repository():
    """Test repository cloning functionality."""
    # Skip this test as it requires network access
    pass
