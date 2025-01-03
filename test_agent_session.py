import pytest
import os
import tempfile
import shutil
from agent_session import AgentSession
from unittest.mock import patch, MagicMock

# Replace with your actual aider command if it's not on the PATH
AIDER_COMMAND = "aider"  

@pytest.fixture
def temp_workspace():
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@patch('subprocess.Popen')
def test_agent_session_start_success(mock_popen, temp_workspace):
    mock_process = MagicMock()
    mock_process.stdout = MagicMock()
    mock_process.stderr = MagicMock()
    mock_process.poll.return_value = None
    mock_popen.return_value = mock_process
    session = AgentSession(workspace_path=temp_workspace, task="test task")
    assert session.start()
    mock_popen.assert_called_once()

@patch('subprocess.Popen')
def test_agent_session_start_failure(mock_popen, temp_workspace):
    mock_popen.side_effect = OSError("Failed to start process")
    session = AgentSession(workspace_path=temp_workspace, task="test task")
    assert not session.start()

@patch('subprocess.Popen')
def test_agent_session_send_message_success(mock_popen, temp_workspace):
    mock_process = MagicMock()
    mock_process.stdin = MagicMock()
    mock_process.stdout = MagicMock()
    mock_process.stderr = MagicMock()
    mock_process.poll.return_value = None
    mock_popen.return_value = mock_process
    session = AgentSession(workspace_path=temp_workspace, task="test task")
    session.start()
    assert session.send_message("test message")
    mock_process.stdin.write.assert_called_once_with("test message\n")

@patch('subprocess.Popen')
def test_agent_session_send_message_failure(mock_popen, temp_workspace):
    mock_process = MagicMock()
    mock_process.stdin = MagicMock()
    mock_process.stdin.write.side_effect = BrokenPipeError("Broken pipe")
    mock_process.stdout = MagicMock()
    mock_process.stderr = MagicMock()
    mock_process.poll.return_value = None
    mock_popen.return_value = mock_process
    session = AgentSession(workspace_path=temp_workspace, task="test task")
    session.start()
    assert not session.send_message("test message")

@patch('subprocess.Popen')
def test_agent_session_get_output(mock_popen, temp_workspace):
    mock_process = MagicMock()
    mock_process.stdout = MagicMock()
    mock_process.stderr = MagicMock()
    mock_process.poll.return_value = None
    mock_popen.return_value = mock_process
    session = AgentSession(workspace_path=temp_workspace, task="test task")
    session.start()
    session._read_output(mock_process.stdout, "stdout")
    output = session.get_output()
    assert isinstance(output, str)

@patch('subprocess.Popen')
def test_agent_session_cleanup(mock_popen, temp_workspace):
    mock_process = MagicMock()
    mock_process.stdout = MagicMock()
    mock_process.stderr = MagicMock()
    mock_process.poll.return_value = None
    mock_popen.return_value = mock_process
    session = AgentSession(workspace_path=temp_workspace, task="test task")
    session.start()
    session.cleanup()
    mock_process.terminate.assert_called_once()
    mock_process.kill.assert_not_called()

@patch('subprocess.Popen')
def test_agent_session_cleanup_timeout(mock_popen, temp_workspace):
    mock_process = MagicMock()
    mock_process.stdout = MagicMock()
    mock_process.stderr = MagicMock()
    mock_process.poll.return_value = None
    mock_process.wait.side_effect = subprocess.TimeoutExpired("", 5)
    mock_popen.return_value = mock_process
    session = AgentSession(workspace_path=temp_workspace, task="test task")
    session.start()
    session.cleanup()
    mock_process.terminate.assert_called_once()
    mock_process.kill.assert_called_once()

@patch('subprocess.Popen')
def test_agent_session_send_message_timeout(mock_popen, temp_workspace):
    mock_process = MagicMock()
    mock_process.stdin = MagicMock()
    mock_process.stdout = MagicMock()
    mock_process.stderr = MagicMock()
    mock_process.poll.return_value = None
    mock_popen.return_value = mock_process
    session = AgentSession(workspace_path=temp_workspace, task="test task")
    session.start()
    with pytest.raises(Exception):
        session.send_message("test message", timeout=0)

