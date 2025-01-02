import pytest
from datetime import datetime
import json
from unittest.mock import patch, MagicMock
from prompt_processor import PromptProcessor, AgentResponse

@pytest.fixture
def processor():
    """Create a prompt processor instance for testing."""
    return PromptProcessor()

def test_agent_response_creation():
    """Test creating an AgentResponse object."""
    response = AgentResponse(
        progress="Test progress",
        thought="Test thought",
        action="Test action",
        future="Test future"
    )
    assert response.progress == "Test progress"
    assert response.thought == "Test thought"
    assert response.action == "Test action"
    assert response.future == "Test future"
    assert isinstance(response.timestamp, datetime)

def test_process_valid_response(processor):
    """Test processing a valid JSON response."""
    test_response = json.dumps({
        'progress': 'Test progress',
        'thought': 'Test thought',
        'action': 'Test action',
        'future': 'Test future'
    })
    
    result = processor.process_response('test_agent', test_response)
    assert result == 'Test action'
    
    # Check state was updated
    state = processor.get_agent_state('test_agent')
    assert state['progress'] == 'Test progress'
    assert state['thought'] == 'Test thought'
    assert state['future'] == 'Test future'
    assert state['last_action'] == 'Test action'

def test_process_finish_action(processor):
    """Test processing a /finish action."""
    test_response = json.dumps({
        'progress': 'Completed task',
        'thought': 'Ready to create PR',
        'action': '/finish',
        'future': 'None'
    })
    
    mock_pr_info = {
        'title': 'Test PR',
        'body': 'Test PR body'
    }
    
    with patch('pull_request.PullRequestManager') as mock_pr_manager:
        mock_pr_manager.return_value.generate_pr_info.return_value = mock_pr_info
        result = processor.process_response('test_agent', test_response)
        
        assert result == '/finish'
        state = processor.get_agent_state('test_agent')
        assert state['pr_info'] == mock_pr_info
        assert state['status'] == 'creating_pr'

def test_process_instruct_action(processor):
    """Test processing an /instruct action."""
    test_response = json.dumps({
        'progress': 'In progress',
        'thought': 'Need to modify code',
        'action': '/instruct modify this file',
        'future': 'Will continue after modification'
    })
    
    result = processor.process_response('test_agent', test_response)
    assert result == 'modify this file'

def test_process_invalid_json(processor):
    """Test processing invalid JSON."""
    result = processor.process_response('test_agent', 'invalid json')
    assert result is None

def test_process_missing_fields(processor):
    """Test processing JSON with missing required fields."""
    test_response = json.dumps({
        'progress': 'Test progress',
        'thought': 'Test thought'
        # Missing action and future
    })
    
    result = processor.process_response('test_agent', test_response)
    assert result is None

def test_process_response_exception(processor):
    """Test processing response with unexpected exception."""
    with patch('json.loads', side_effect=Exception('Unexpected error')):
        result = processor.process_response('test_agent', '{}')
        assert result is None

def test_get_agent_state_existing(processor):
    """Test getting state for an existing agent."""
    # First process a response to create state
    test_response = json.dumps({
        'progress': 'Test progress',
        'thought': 'Test thought',
        'action': 'Test action',
        'future': 'Test future'
    })
    processor.process_response('test_agent', test_response)
    
    state = processor.get_agent_state('test_agent')
    assert state['progress'] == 'Test progress'
    assert state['thought'] == 'Test thought'
    assert state['future'] == 'Test future'
    assert state['last_action'] == 'Test action'

def test_get_agent_state_nonexistent(processor):
    """Test getting state for a non-existent agent."""
    state = processor.get_agent_state('nonexistent_agent')
    assert state['progress'] == 'Not started'
    assert state['thought'] == 'Initializing...'
    assert state['future'] == 'Waiting to begin'
    assert state['last_action'] is None

def test_get_response_history(processor):
    """Test getting response history."""
    # Process multiple responses
    responses = [
        {
            'progress': f'Progress {i}',
            'thought': f'Thought {i}',
            'action': f'Action {i}',
            'future': f'Future {i}'
        } for i in range(3)
    ]
    
    for response in responses:
        processor.process_response('test_agent', json.dumps(response))
    
    history = processor.get_response_history('test_agent')
    assert len(history) == 3
    for i, response in enumerate(history):
        assert response.progress == f'Progress {i}'
        assert response.thought == f'Thought {i}'
        assert response.action == f'Action {i}'
        assert response.future == f'Future {i}'

def test_get_response_history_nonexistent(processor):
    """Test getting response history for non-existent agent."""
    history = processor.get_response_history('nonexistent_agent')
    assert history == []

def test_response_history_limit(processor):
    """Test that response history is limited to 100 entries."""
    # Create 110 responses
    responses = [
        {
            'progress': f'Progress {i}',
            'thought': f'Thought {i}',
            'action': f'Action {i}',
            'future': f'Future {i}'
        } for i in range(110)
    ]
    
    for response in responses:
        processor.process_response('test_agent', json.dumps(response))
    
    history = processor.get_response_history('test_agent')
    assert len(history) == 100
    # Should have the last 100 responses (10-109)
    assert history[0].progress == 'Progress 10'
    assert history[-1].progress == 'Progress 109'