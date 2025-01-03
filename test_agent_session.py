import pytest
import os
from agent_session import AgentSession
import time
import io

# Mock the subprocess module to avoid actually running the aider command
class MockPopen:
    def __init__(self, *args, **kwargs):
        self.stdout = io.StringIO()
        self.stderr = io.StringIO()
        self.stdin = io.StringIO()
        self.returncode = 0

    def poll(self):
        return self.returncode

    def communicate(self):
        return self.stdout.getvalue(), self.stderr.getvalue()

    def terminate(self):
        self.returncode = 1

    def kill(self):
        self.returncode = -1

    def stdin(self):
        return self.stdin

    def wait(self, timeout=None):
        return self.returncode

def mock_get_model_config():
    return {'aider_model': 'mocked_model'}

# Mock the subprocess module
import subprocess
original_popen = subprocess.Popen
subprocess.Popen = MockPopen

# Mock the database function
from unittest.mock import patch
@patch('agent_session.get_model_config', side_effect=mock_get_model_config)
def test_agent_session_start(mock_get_model_config):
    session = AgentSession(workspace_path="/tmp", task="test_task")
    assert session.start() == True

@patch('agent_session.get_model_config', side_effect=mock_get_model_config)
def test_agent_session_send_message(mock_get_model_config):
    session = AgentSession(workspace_path="/tmp", task="test_task")
    session.start()
    assert session.send_message("test message") == True

@patch('agent_session.get_model_config', side_effect=mock_get_model_config)
def test_agent_session_get_output(mock_get_model_config):
    session = AgentSession(workspace_path="/tmp", task="test_task")
    session.start()
    session.send_message("test message")
    output = session.get_output()
    assert "test message" in output

@patch('agent_session.get_model_config', side_effect=mock_get_model_config)
def test_agent_session_is_ready(mock_get_model_config):
    session = AgentSession(workspace_path="/tmp", task="test_task")
    session.start()
    time.sleep(1) # Give some time for the mock process to "run"
    assert session.is_ready() == True

@patch('agent_session.get_model_config', side_effect=mock_get_model_config)
def test_agent_session_cleanup(mock_get_model_config):
    session = AgentSession(workspace_path="/tmp", task="test_task")
    session.start()
    session.cleanup()
    assert session.process.poll() != 0

# Restore the original subprocess.Popen
subprocess.Popen = original_popen
