import pytest
import os
from unittest.mock import patch, MagicMock
from agent_session import AgentSession
import time
import io

# Mock subprocess.Popen to avoid actually launching a process
@patch('subprocess.Popen')
def test_agent_session_start_success(mock_popen):
    mock_process = MagicMock()
    mock_process.stdout = io.StringIO()
    mock_process.stderr = io.StringIO()
    mock_process.poll.return_value = None  # Simulate a running process
    mock_popen.return_value = mock_process

    session = AgentSession(workspace_path="/tmp", task="test_task")
    assert session.start()
    mock_popen.assert_called_once()


@patch('subprocess.Popen')
def test_agent_session_start_failure(mock_popen):
    mock_popen.side_effect = OSError("Failed to start process")
    session = AgentSession(workspace_path="/tmp", task="test_task")
    assert not session.start()


def test_agent_session_get_output():
    session = AgentSession(workspace_path="/tmp", task="test_task")
    session.output_buffer.write("Test output")
    assert session.get_output() == "Test output"


@patch('agent_session.AgentSession.start')
def test_agent_session_send_message_success(mock_start):
    mock_start.return_value = True
    mock_process = MagicMock()
    mock_process.stdin = MagicMock()
    session = AgentSession(workspace_path="/tmp", task="test_task")
    session.process = mock_process
    assert session.send_message("Test message")
    mock_process.stdin.write.assert_called_once_with("Test message\n")


@patch('agent_session.AgentSession.start')
def test_agent_session_send_message_failure(mock_start):
    mock_start.return_value = True
    mock_process = MagicMock()
    mock_process.stdin = MagicMock()
    mock_process.stdin.write.side_effect = BrokenPipeError("Broken pipe")
    session = AgentSession(workspace_path="/tmp", task="test_task")
    session.process = mock_process
    assert not session.send_message("Test message")


@patch('agent_session.AgentSession.start')
def test_agent_session_is_ready_true(mock_start):
    mock_start.return_value = True
    session = AgentSession(workspace_path="/tmp", task="test_task")
    session.output_buffer = io.StringIO("Initial output")
    assert session.is_ready()


@patch('agent_session.AgentSession.start')
def test_agent_session_is_ready_false(mock_start):
    mock_start.return_value = True
    session = AgentSession(workspace_path="/tmp", task="test_task")
    session.output_buffer = io.StringIO("Initial output")
    session.config['stability_duration'] = 0.1
    session.output_buffer.write("New output")
    time.sleep(0.2)
    assert not session.is_ready()

