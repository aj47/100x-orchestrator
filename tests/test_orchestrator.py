import pytest
import sys
from pathlib import Path
import os
import subprocess
import json
from unittest.mock import patch, MagicMock

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent.parent))

from orchestrator import (
    initialiseCodingAgent,
    load_tasks,
    save_tasks,
    delete_agent,
    cloneRepository,
    create_pull_request,
    get_github_token
)

# Mock functions for testing
@patch('orchestrator.initialiseCodingAgent')
@patch('orchestrator.save_tasks')
@patch('orchestrator.load_tasks')
def test_load_tasks_exception(mock_load_tasks, mock_save_tasks, mock_initialiseCodingAgent, temp_config_file):
    """Test load_tasks exception handling."""
    mock_load_tasks.side_effect = FileNotFoundError
    tasks_data = load_tasks()
    assert tasks_data == {
        "tasks": [],
        "agents": {},
        "repository_url": ""
    }

@patch('orchestrator.initialiseCodingAgent')
@patch('orchestrator.save_tasks')
@patch('orchestrator.load_tasks')
def test_save_tasks_exception(mock_load_tasks, mock_save_tasks, mock_initialiseCodingAgent, temp_config_file):
    """Test save_tasks exception handling."""
    mock_save_tasks.side_effect = IOError
    tasks_data = {"tasks": [], "agents": {}}
    with pytest.raises(IOError):
        save_tasks(tasks_data)

@patch('orchestrator.subprocess.run')
def test_clone_repository_exception(mock_subprocess_run):
    """Test cloneRepository exception handling."""
    mock_subprocess_run.side_effect = subprocess.CalledProcessError(1, 'git clone')
    result = cloneRepository('test_url')
    assert result is False

@patch('orchestrator.Github')
def test_create_pull_request_exception(mock_github):
    """Test create_pull_request exception handling."""
    mock_github.return_value.get_repo.return_value.create_pull.side_effect = Exception("GitHub API error")
    result = create_pull_request('test_agent_id', 'test_branch', {'title': 'Test PR'})
    assert result is None

@patch('orchestrator.os.environ')
def test_get_github_token_exception(mock_os_environ):
    """Test get_github_token exception handling."""
    mock_os_environ.__getitem__.side_effect = KeyError("GITHUB_TOKEN")
    token = get_github_token()
    assert token is None

@patch('orchestrator.AgentSession.start')
def test_initialiseCodingAgent_exception(mock_agent_session_start, temp_workspace):
    """Test initialiseCodingAgent exception handling."""
    mock_agent_session_start.return_value = False
    result = initialiseCodingAgent(repository_url="test_url", task_description="test_task")
    assert result is None

@patch('orchestrator.AgentSession')
def test_initialiseCodingAgent_clone_exception(mock_agent_session):
    """Test initialiseCodingAgent exception handling during cloning."""
    mock_agent_session.return_value.start.return_value = True
    mock_agent_session.return_value.send_message.return_value = True
    with patch('orchestrator.cloneRepository') as mock_clone:
        mock_clone.return_value = False
        result = initialiseCodingAgent(repository_url="test_url", task_description="test_task")
        assert result is None

@patch('orchestrator.AgentSession')
def test_initialiseCodingAgent_start_exception(mock_agent_session):
    """Test initialiseCodingAgent exception handling during session start."""
    mock_agent_session.return_value.start.side_effect = Exception("Session start failed")
    result = initialiseCodingAgent(repository_url="test_url", task_description="test_task")
    assert result is None

@patch('orchestrator.load_tasks')
def test_delete_agent_exception(mock_load_tasks):
    """Test delete_agent exception handling."""
    mock_load_tasks.side_effect = Exception("Error loading tasks")
    with pytest.raises(Exception):
        delete_agent('test_agent_id')

@patch('orchestrator.load_tasks')
def test_delete_agent_not_found(mock_load_tasks):
    """Test delete_agent when agent is not found."""
    mock_load_tasks.return_value = {'agents': {}}
    result = delete_agent('test_agent_id')
    assert result is False

@patch('orchestrator.update_agent_output')
def test_main_loop_exception(mock_update_agent_output):
    """Test main_loop exception handling."""
    mock_update_agent_output.side_effect = Exception("Error updating agent output")
    with patch('orchestrator.sleep') as mock_sleep:
        with pytest.raises(Exception):
            main_loop()

@patch('orchestrator.LiteLLMClient.chat_completion')
def test_main_loop_litellm_exception(mock_chat_completion):
    """Test main_loop exception handling for LiteLLM errors."""
    mock_chat_completion.side_effect = Exception("LiteLLM error")
    with patch('orchestrator.sleep') as mock_sleep:
        with pytest.raises(Exception):
            main_loop()

@patch('orchestrator.PromptProcessor.process_response')
def test_main_loop_prompt_processor_exception(mock_process_response):
    """Test main_loop exception handling for PromptProcessor errors."""
    mock_process_response.side_effect = Exception("PromptProcessor error")
    with patch('orchestrator.sleep') as mock_sleep:
        with pytest.raises(Exception):
            main_loop()

@patch('orchestrator.create_pull_request')
def test_main_loop_create_pr_exception(mock_create_pull_request):
    """Test main_loop exception handling for PR creation errors."""
    mock_create_pull_request.side_effect = Exception("PR creation error")
    with patch('orchestrator.sleep') as mock_sleep:
        with pytest.raises(Exception):
            main_loop()

@patch('orchestrator.AgentSession.send_message')
def test_main_loop_send_message_exception(mock_send_message):
    """Test main_loop exception handling for message sending errors."""
    mock_send_message.side_effect = Exception("Message sending error")
    with patch('orchestrator.sleep') as mock_sleep:
        with pytest.raises(Exception):
            main_loop()

def test_agent_session_read_output_exception():
    """Test AgentSession._read_output exception handling."""
    with patch('agent_session.logging.info') as mock_log:
        with patch('agent_session.time.sleep') as mock_sleep:
            with patch('agent_session.subprocess.Popen') as mock_popen:
                mock_popen.return_value.stdout = MagicMock()
                mock_popen.return_value.stderr = MagicMock()
                mock_popen.return_value.poll.return_value = None
                mock_popen.return_value.stdout.readline.side_effect = Exception("Readline error")
                session = AgentSession("test_path", "test_task")
                session._read_output(session.process.stdout, "stdout")
                mock_log.assert_any_call(f"[Session {session.session_id}] Error reading from stdout: Readline error")

def test_agent_session_send_message_exception():
    """Test AgentSession.send_message exception handling."""
    with patch('agent_session.logging.info') as mock_log:
        with patch('agent_session.subprocess.Popen') as mock_popen:
            mock_popen.return_value.stdin = MagicMock()
            mock_popen.return_value.poll.return_value = None
            mock_popen.return_value.stdin.write.side_effect = BrokenPipeError("Broken pipe")
            session = AgentSession("test_path", "test_task")
            result = session.send_message("test message")
            assert result is False
            mock_log.assert_any_call(f"[Session {session.session_id}] Pipe error sending message: Broken pipe")

def test_agent_session_is_ready_exception():
    """Test AgentSession.is_ready exception handling."""
    with patch('agent_session.logging.info') as mock_log:
        with patch('agent_session.time.sleep') as mock_sleep:
            session = AgentSession("test_path", "test_task")
            session.get_output = MagicMock(side_effect=Exception("Get output error"))
            result = session.is_ready()
            assert result is False
            mock_log.assert_any_call(f"[Session {session.session_id}] Error in readiness check: Get output error")

def test_agent_session_cleanup_exception():
    """Test AgentSession.cleanup exception handling."""
    with patch('agent_session.logging.info') as mock_log:
        with patch('agent_session.subprocess.Popen') as mock_popen:
            mock_popen.return_value.terminate.side_effect = Exception("Terminate error")
            session = AgentSession("test_path", "test_task")
            session.cleanup()
            mock_log.assert_any_call(f"[Session {session.session_id}] Error during cleanup: Terminate error")

from orchestrator import main_loop
@pytest.mark.asyncio
async def test_main_loop_handles_exceptions():
    """Test that the main loop gracefully handles exceptions."""
    with patch('orchestrator.sleep') as mock_sleep:
        with patch('orchestrator.load_tasks') as mock_load_tasks:
            mock_load_tasks.side_effect = Exception("Simulated load_tasks error")
            with pytest.raises(Exception) as excinfo:
                main_loop()
            assert "Simulated load_tasks error" in str(excinfo.value)
            mock_sleep.assert_called_once()

