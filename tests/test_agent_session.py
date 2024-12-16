import pytest
from unittest.mock import patch, MagicMock
from agent_session import AgentSession
import io
import os
import tempfile
import time

# Example test cases for AgentSession
def test_agent_session_initialization():
    # Create a temporary directory for the workspace
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_path = temp_dir
        session = AgentSession(workspace_path, "test task")
        assert session.workspace_path == workspace_path
        assert session.task == "test task"
        assert session.output_buffer is not None
        assert session.process is None
        assert session.session_id is not None

@patch('subprocess.Popen')
def test_agent_session_start_success(mock_popen):
    # Create a temporary directory for the workspace
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_path = temp_dir
        mock_process = MagicMock()
        mock_process.stdout = io.StringIO()
        mock_process.stderr = io.StringIO()
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process
        session = AgentSession(workspace_path, "test task")
        assert session.start()
        mock_popen.assert_called_once()

@patch('subprocess.Popen')
def test_agent_session_start_failure(mock_popen):
    mock_popen.side_effect = OSError("Failed to start process")
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_path = temp_dir
        session = AgentSession(workspace_path, "test task")
        assert not session.start()
        mock_popen.assert_called_once()

@patch('agent_session.AgentSession.is_ready', return_value=True)
def test_agent_session_send_message_success(mock_is_ready):
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_path = temp_dir
        session = AgentSession(workspace_path, "test task")
        # Mock the process and stdin for testing
        session.process = MagicMock()
        session.process.stdin = io.StringIO()
        assert session.send_message("test message")
        mock_is_ready.assert_called_once()

@patch('agent_session.AgentSession.is_ready', return_value=False)
def test_agent_session_send_message_failure(mock_is_ready):
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_path = temp_dir
        session = AgentSession(workspace_path, "test task")
        # Mock the process and stdin for testing
        session.process = MagicMock()
        session.process.stdin = io.StringIO()
        assert not session.send_message("test message")
        mock_is_ready.assert_called_once()

def test_agent_session_get_output():
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_path = temp_dir
        session = AgentSession(workspace_path, "test task")
        session.output_buffer.write("test output")
        assert session.get_output() == "test output"

@patch('subprocess.Popen')
def test_agent_session_cleanup(mock_popen):
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace_path = temp_dir
        mock_process = MagicMock()
        mock_popen.return_value = mock_process
        session = AgentSession(workspace_path, "test task")
        session.start()
        session.cleanup()
        mock_process.terminate.assert_called_once()
        mock_process.wait.assert_called_once()

def test_normalize_path():
    # Test with valid path
    normalized_path = normalize_path("/tmp/test/path")
    assert normalized_path == "/tmp/test/path"

    # Test with path containing backslashes
    normalized_path = normalize_path("C:\\tmp\\test\\path")
    assert normalized_path == "/tmp/test/path"

    # Test with empty path
    normalized_path = normalize_path("")
    assert normalized_path is None

    # Test with invalid path
    normalized_path = normalize_path("invalid/path")
    assert normalized_path is None

