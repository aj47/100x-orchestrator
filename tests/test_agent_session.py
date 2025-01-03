import pytest
from unittest.mock import patch, MagicMock, call
import subprocess
import threading
import io
from pathlib import Path
from agent_session import AgentSession, normalize_path

def test_normalize_path():
    """Test path normalization function."""
    # Test with valid path
    test_path = "test/path"
    normalized = normalize_path(test_path)
    assert isinstance(normalized, str)
    assert '\\' not in normalized
    
    # Test with None
    assert normalize_path(None) is None
    
    # Test with invalid path that raises an exception
    with patch('pathlib.Path.resolve', side_effect=Exception("Invalid path")):
        assert normalize_path('invalid/path') is None

@pytest.fixture
def mock_process():
    """Create a mock subprocess."""
    process = MagicMock()
    process.poll.return_value = None
    process.stdout = MagicMock()
    process.stderr = MagicMock()
    process.stdin = MagicMock()
    return process

@pytest.fixture
def agent_session():
    """Create an agent session for testing."""
    return AgentSession(
        workspace_path="test/workspace",
        task="Test task",
        config={
            'stability_duration': 1,
            'output_buffer_max_length': 1000
        }
    )

@patch('subprocess.Popen')
@patch('database.get_model_config')
def test_agent_session_start(mock_get_config, mock_popen, agent_session, mock_process):
    """Test starting an agent session."""
    mock_get_config.return_value = {'aider_model': 'test-model'}
    mock_popen.return_value = mock_process
    
    result = agent_session.start()
    assert result is True
    mock_popen.assert_called_once()
    
    # Test with failed process creation
    mock_popen.side_effect = Exception("Failed to start process")
    result = agent_session.start()
    assert result is False

def test_agent_session_get_output(agent_session):
    """Test getting output from agent session."""
    test_output = "Test output"
    agent_session.output_buffer = io.StringIO(test_output)
    
    output = agent_session.get_output()
    assert output == test_output
    
    # Test with buffer error
    agent_session.output_buffer = None
    assert agent_session.get_output() is None

@patch('subprocess.Popen')
def test_agent_session_send_message(mock_popen, agent_session, mock_process):
    """Test sending messages to agent session."""
    mock_popen.return_value = mock_process
    agent_session.process = mock_process
    
    # Test successful message send
    result = agent_session.send_message("Test message", "test_action") # Added agent_action
    assert result is True
    agent_session.process.stdin.write.assert_called_once_with("Test message\n")
    
    # Test with broken pipe
    agent_session.process.stdin.write.side_effect = BrokenPipeError()
    result = agent_session.send_message("Test message", "test_action") # Added agent_action
    assert result is False
    
    # Test with no process
    agent_session.process = None
    result = agent_session.send_message("Test message", "test_action") # Added agent_action
    assert result is False

def test_agent_session_is_ready(agent_session):
    """Test checking if agent session is ready."""
    # Test with empty output
    agent_session.output_buffer = io.StringIO()
    assert agent_session.is_ready() is True
    
    # Test with stable output
    agent_session.output_buffer = io.StringIO("Stable output")
    assert agent_session.is_ready() is True
    
    # Test with error
    agent_session.get_output = MagicMock(side_effect=Exception())
    assert agent_session.is_ready() is False

def test_format_output_line(agent_session):
    """Test output line formatting."""
    # Test agent response
    line = "> Agent response"
    formatted = agent_session._format_output_line(line)
    assert 'class="output-line agent-response"' in formatted
    
    # Test agent question
    line = "? Agent question"
    formatted = agent_session._format_output_line(line)
    assert 'class="output-line agent-question"' in formatted
    
    # Test error message
    line = "Error: Something went wrong"
    formatted = agent_session._format_output_line(line)
    assert 'class="output-line error-message"' in formatted
    
    # Test normal output
    line = "Normal output"
    formatted = agent_session._format_output_line(line)
    assert 'class="output-line"' in formatted
    
    # Test empty line
    assert agent_session._format_output_line('') == ''

@patch('subprocess.Popen')
def test_agent_session_cleanup(mock_popen, agent_session, mock_process):
    """Test agent session cleanup."""
    mock_popen.return_value = mock_process
    agent_session.process = mock_process
    
    agent_session.cleanup()
    assert agent_session._stop_event.is_set()
    mock_process.terminate.assert_called_once()
    
    # Test cleanup with process kill
    mock_process.wait.side_effect = subprocess.TimeoutExpired(cmd="test", timeout=5)
    agent_session.cleanup()
    mock_process.kill.assert_called_once()
    
    # Test cleanup with no process
    agent_session.process = None
    agent_session.cleanup()  # Should not raise any exception

@patch('subprocess.Popen')
def test_read_output(mock_popen, agent_session, mock_process):
    """Test reading output from process pipes."""
    mock_popen.return_value = mock_process
    agent_session.process = mock_process
    
    # Setup mock pipe
    mock_pipe = MagicMock()
    mock_pipe.readline.side_effect = [
        "Normal output\n",
        "Error: test error\n",
        "> Agent response\n",
        "Can't initialize prompt toolkit\n",  # Should be filtered
        ""  # EOF
    ]
    
    # Start reading output
    agent_session._read_output(mock_pipe, "stdout")
    
    # Verify output was written to buffer
    output = agent_session.get_output()
    assert "Normal output" in output
    assert "Error: test error" in output
    assert "> Agent response" in output
    assert "Can't initialize prompt toolkit" not in output

def test_echo_message(agent_session):
    """Test echoing messages to output buffer."""
    test_message = "Test echo message"
    agent_session._echo_message(test_message)
    
    output = agent_session.get_output()
    # Check for HTML-escaped version of the message
    assert "Test&nbsp;echo&nbsp;message" in output
    assert 'class="output-line user-message"' in output
    
    # Test with error
    agent_session.output_buffer = None
    agent_session._echo_message(test_message)  # Should not raise exception

