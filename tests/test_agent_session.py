import pytest
from unittest.mock import patch, MagicMock
from agent_session import AgentSession, normalize_path
import logging
import io
import time
import threading
import subprocess

# Configure logging for testing
logging.basicConfig(level=logging.INFO)

@pytest.fixture
def mock_subprocess(monkeypatch):
    """Mock subprocess for testing."""
    mock_process = MagicMock()
    mock_process.stdout = io.StringIO()
    mock_process.stderr = io.StringIO()
    mock_process.stdin = MagicMock()
    mock_process.poll.return_value = None
    mock_process.terminate.return_value = None
    mock_process.kill.return_value = None
    mock_process.wait.return_value = 0
    mock_subprocess_class = MagicMock(return_value=mock_process)
    monkeypatch.setattr("subprocess.Popen", mock_subprocess_class)
    yield mock_process

def test_normalize_path():
    """Test path normalization."""
    assert normalize_path("/tmp/test") == "/tmp/test"
    assert normalize_path("C:\\tmp\\test") == "C:/tmp/test"
    assert normalize_path(None) is None
    assert normalize_path("") is None

def test_agent_session_initialization():
    """Test AgentSession initialization."""
    session = AgentSession("/tmp/test", "test_task")
    assert session.workspace_path == "/tmp/test"
    assert session.task == "test_task"
    assert isinstance(session.output_buffer, io.StringIO)

@patch('agent_session.AgentSession._read_output')
def test_agent_session_start(mock_read_output, mock_subprocess):
    """Test AgentSession start method."""
    session = AgentSession("/tmp/test", "test_task")
    assert session.start()
    mock_read_output.assert_called()

@patch('agent_session.AgentSession._read_output')
def test_agent_session_start_failure(mock_read_output, mock_subprocess):
    """Test AgentSession start method failure."""
    mock_subprocess.side_effect = subprocess.CalledProcessError(1, "command")
    session = AgentSession("/tmp/test", "test_task")
    assert not session.start()

def test_agent_session_get_output(mock_subprocess):
    """Test AgentSession get_output method."""
    session = AgentSession("/tmp/test", "test_task")
    session.start()
    session.output_buffer.write("test output")
    assert session.get_output() == "test output"

@patch('agent_session.AgentSession._echo_message')
def test_agent_session_send_message(mock_echo_message, mock_subprocess):
    """Test AgentSession send_message method."""
    session = AgentSession("/tmp/test", "test_task")
    session.start()
    assert session.send_message("test message")
    mock_echo_message.assert_called_with("test message")

def test_agent_session_is_ready(mock_subprocess):
    """Test AgentSession is_ready method."""
    session = AgentSession("/tmp/test", "test_task")
    session.start()
    # Simulate stable output
    time.sleep(1)
    assert session.is_ready()

def test_agent_session_cleanup(mock_subprocess):
    """Test AgentSession cleanup method."""
    session = AgentSession("/tmp/test", "test_task")
    session.start()
    session.cleanup()
    assert session.process.terminate.called

def test_agent_session_format_output_line():
    """Test AgentSession _format_output_line method."""
    session = AgentSession("/tmp/test", "test_task")
    assert session._format_output_line("> test output") == '<div class="output-line agent-response">&gt;&nbsp;test&nbsp;output</div>'
    assert session._format_output_line("? test question") == '<div class="output-line agent-question">?&nbsp;test&nbsp;question</div>'
    assert session._format_output_line("Error: test error") == '<div class="output-line error-message">Error:&nbsp;test&nbsp;error</div>'
    assert session._format_output_line("test output") == '<div class="output-line">test&nbsp;output</div>'

