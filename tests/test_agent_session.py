import pytest
import os
import tempfile
from agent_session import AgentSession, normalize_path
import time
import logging

# Configure logging for testing
logging.basicConfig(level=logging.DEBUG)

def test_normalize_path():
    """Test path normalization."""
    assert normalize_path("/tmp/test") == "/tmp/test"
    assert normalize_path("C:\\tmp\\test") == "C:/tmp/test"
    assert normalize_path(None) is None
    assert normalize_path("") is None

@pytest.mark.parametrize("aider_commands", [None, "--custom-command"])
def test_agent_session_start(aider_commands):
    """Test starting an agent session."""
    with tempfile.TemporaryDirectory() as tmpdir:
        session = AgentSession(tmpdir, "test task", aider_commands=aider_commands)
        assert session.start() == True
        assert session.process is not None
        session.cleanup()

def test_agent_session_send_message():
    """Test sending a message to the agent session."""
    with tempfile.TemporaryDirectory() as tmpdir:
        session = AgentSession(tmpdir, "test task")
        session.start()
        assert session.send_message("test message") == True
        session.cleanup()

def test_agent_session_get_output():
    """Test getting the output from the agent session."""
    with tempfile.TemporaryDirectory() as tmpdir:
        session = AgentSession(tmpdir, "test task")
        session.start()
        session.send_message("test message")
        time.sleep(2) #Allow time for output
        output = session.get_output()
        assert "test message" in output
        session.cleanup()

def test_agent_session_is_ready():
    """Test checking if the agent session is ready."""
    with tempfile.TemporaryDirectory() as tmpdir:
        session = AgentSession(tmpdir, "test task")
        session.start()
        time.sleep(15) #Allow time for stability check
        assert session.is_ready() == True
        session.cleanup()

def test_agent_session_cleanup():
    """Test cleaning up the agent session."""
    with tempfile.TemporaryDirectory() as tmpdir:
        session = AgentSession(tmpdir, "test task")
        session.start()
        session.cleanup()
        assert session.process is None

