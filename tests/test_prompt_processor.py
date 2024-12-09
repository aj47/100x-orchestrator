import pytest
import json
from prompt_processor import PromptProcessor, AgentResponse

def test_process_response_valid():
    """Test processing a valid JSON response."""
    processor = PromptProcessor()
    valid_response = {
        "progress": "Progress update",
        "thought": "Rationale",
        "action": "/instruct write a function",
        "future": "Future prediction"
    }
    action = processor.process_response("agent1", json.dumps(valid_response))
    assert action == "write a function"
    assert len(processor.response_history["agent1"]) == 1
    assert processor.agent_states["agent1"]["last_action"] == "/instruct write a function"

def test_process_response_invalid():
    """Test processing an invalid JSON response."""
    processor = PromptProcessor()
    invalid_response = "invalid json"
    action = processor.process_response("agent1", invalid_response)
    assert action is None
    assert "agent1" not in processor.response_history

def test_process_response_missing_fields():
    """Test processing a response with missing fields."""
    processor = PromptProcessor()
    missing_fields_response = {"progress": "Progress update", "thought": "Rationale", "future": "Future prediction"}
    action = processor.process_response("agent1", json.dumps(missing_fields_response))
    assert action is None
    assert "agent1" not in processor.response_history

def test_process_response_finish():
    """Test processing a response with the '/finish' action."""
    processor = PromptProcessor()
    finish_response = {
        "progress": "Progress update",
        "thought": "Rationale",
        "action": "/finish",
        "future": "Future prediction"
    }
    # Mocking the LiteLLMClient and its methods for testing purposes
    from unittest.mock import patch
    from litellm_client import LiteLLMClient
    from prompts import PROMPT_PR
    
    mock_pr_info = {
        "title": "Test PR",
        "description": "Test description",
        "labels": ["test"],
        "reviewers": ["reviewer1"]
    }
    
    with patch.object(LiteLLMClient, 'chat_completion', return_value=json.dumps(mock_pr_info)):
        action = processor.process_response("agent1", json.dumps(finish_response))
        assert action == "/finish"
        assert processor.agent_states["agent1"]["status"] == "creating_pr"
        assert processor.agent_states["agent1"]["pr_info"] == mock_pr_info

def test_get_agent_state():
    """Test getting the agent state."""
    processor = PromptProcessor()
    state = processor.get_agent_state("agent1")
    assert state == {
        'progress': 'Not started',
        'thought': 'Initializing...',
        'future': 'Waiting to begin',
        'last_action': None
    }

def test_get_response_history():
    """Test getting the response history."""
    processor = PromptProcessor()
    history = processor.get_response_history("agent1")
    assert history == []

