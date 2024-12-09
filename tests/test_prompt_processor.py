import pytest
import json
from prompt_processor import PromptProcessor, AgentResponse
from datetime import datetime, timedelta

def test_prompt_processor_initialization():
    """Test PromptProcessor initialization."""
    processor = PromptProcessor()
    assert processor.agent_states == {}
    assert processor.response_history == {}

def test_prompt_processor_process_response():
    """Test PromptProcessor process_response method."""
    processor = PromptProcessor()
    response = '{"progress": "Task initiated", "thought": "Starting the process", "action": "/instruct Next step", "future": "Expect progress soon"}'
    action = processor.process_response("test_agent", response)
    assert action == "Next step"
    assert processor.agent_states["test_agent"]['last_action'] == "/instruct Next step"

def test_prompt_processor_process_response_finish():
    """Test PromptProcessor process_response method with /finish action."""
    processor = PromptProcessor()
    response = '{"progress": "Task completed", "thought": "All done", "action": "/finish", "future": "No further steps"}'
    action = processor.process_response("test_agent", response)
    assert action == "/finish"
    assert "pr_info" in processor.agent_states["test_agent"]

def test_prompt_processor_process_response_invalid_json():
    """Test PromptProcessor process_response method with invalid JSON."""
    processor = PromptProcessor()
    response = "invalid json"
    action = processor.process_response("test_agent", response)
    assert action is None

def test_prompt_processor_process_response_missing_fields():
    """Test PromptProcessor process_response method with missing fields."""
    processor = PromptProcessor()
    response = '{"progress": "Task initiated", "thought": "Starting the process", "future": "Expect progress soon"}'
    action = processor.process_response("test_agent", response)
    assert action is None

def test_prompt_processor_get_agent_state():
    """Test PromptProcessor get_agent_state method."""
    processor = PromptProcessor()
    processor.agent_states["test_agent"] = {"progress": "In progress"}
    assert processor.get_agent_state("test_agent") == {"progress": "In progress"}

def test_prompt_processor_get_response_history():
    """Test PromptProcessor get_response_history method."""
    processor = PromptProcessor()
    response = AgentResponse(progress="Step 1", thought="Thinking...", action="/instruct next", future="Step 2")
    processor.response_history["test_agent"] = [response]
    assert processor.get_response_history("test_agent") == [response]

def test_agent_response_timestamp():
    """Test AgentResponse timestamp."""
    response = AgentResponse(progress="Step 1", thought="Thinking...", action="/instruct next", future="Step 2")
    assert isinstance(response.timestamp, datetime)
    
    # Check that the timestamp is within a reasonable tolerance of the current time
    now = datetime.now()
    assert now - timedelta(seconds=1) < response.timestamp < now + timedelta(seconds=1)

