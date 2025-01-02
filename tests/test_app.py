import pytest
import json
from unittest.mock import patch, MagicMock
from app import app
import sqlite3
from pathlib import Path

@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def mock_db():
    """Create a temporary test database."""
    db_path = Path("test_tasks.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create necessary tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS model_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            orchestrator_model TEXT,
            aider_model TEXT,
            agent_model TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    """)
    conn.commit()
    conn.close()
    
    yield db_path
    
    # Cleanup
    if db_path.exists():
        db_path.unlink()

def test_index(client):
    """Test the index route."""
    response = client.get('/')
    assert response.status_code == 200

@patch('app.load_tasks')
def test_serve_tasks_json(mock_load_tasks, client):
    """Test serving tasks JSON."""
    mock_data = {
        'tasks': [],
        'agents': {},
        'repository_url': ''
    }
    mock_load_tasks.return_value = mock_data
    
    response = client.get('/tasks/tasks.json')
    assert response.status_code == 200
    assert response.json == mock_data

@patch('app.load_tasks')
@patch('app.save_tasks')
def test_agent_view(mock_save_tasks, mock_load_tasks, client):
    """Test the agent view route."""
    mock_data = {
        'agents': {
            'agent1': {
                'status': 'pending'
            }
        }
    }
    mock_load_tasks.return_value = mock_data
    
    response = client.get('/agents')
    assert response.status_code == 200

@patch('app.initialiseCodingAgent')
def test_create_agent_success(mock_init_agent, client):
    """Test successful agent creation."""
    # Setup mocks
    mock_token_manager = MagicMock()
    mock_token_manager.return_value.set_token.return_value = True
    mock_init_agent.return_value = ['test_agent_id']
    
    # Test data
    test_data = {
        'repo_url': 'https://github.com/test/repo',
        'tasks': [{'title': 'Test Task', 'description': 'Test Description'}],
        'num_agents': 1
    }
    
    # Make request
    with patch('github_token.GitHubTokenManager', return_value=mock_token_manager):
        response = client.post('/create_agent',
                             headers={'X-GitHub-Token': 'test_token'},
                             json=test_data)
        
        assert response.status_code == 200
        assert response.json['success'] is True
        assert 'test_agent_id' in response.json['agent_ids']

@patch('app.initialiseCodingAgent')
def test_create_agent_missing_token(mock_init_agent, client):
    """Test agent creation without GitHub token."""
    test_data = {
        'repo_url': 'https://github.com/test/repo',
        'tasks': [{'title': 'Test Task', 'description': 'Test Description'}]
    }
    
    response = client.post('/create_agent', json=test_data)
    assert response.status_code == 400
    assert 'GitHub token is required' in response.json['error']

def test_update_model_config(client, mock_db):
    """Test updating model configuration."""
    with patch('app.DATABASE_PATH', mock_db):
        test_config = {
            'orchestrator_model': 'test_model1',
            'aider_model': 'test_model2',
            'agent_model': 'test_model3'
        }
        
        response = client.post('/config/models', json=test_config)
        assert response.status_code == 200
        assert response.json['success'] is True

def test_get_model_config(client, mock_db):
    """Test getting model configuration."""
    with patch('app.DATABASE_PATH', mock_db):
        response = client.get('/config/models')
        assert response.status_code == 200
        assert response.json['success'] is True
        assert 'config' in response.json

def test_config_view(client):
    """Test the configuration view route."""
    response = client.get('/config')
    assert response.status_code == 200

@patch('app.delete_agent')
@patch('app.load_tasks')
@patch('app.save_tasks')
def test_delete_agent_success(mock_save_tasks, mock_load_tasks, mock_delete_agent, client):
    """Test successful agent deletion."""
    mock_load_tasks.return_value = {
        'agents': {
            'test_agent': {'status': 'pending'}
        }
    }
    mock_delete_agent.return_value = True
    
    response = client.delete('/delete_agent/test_agent')
    assert response.status_code == 200
    assert response.json['success'] is True

@patch('app.delete_agent')
@patch('app.load_tasks')
def test_delete_agent_not_found(mock_load_tasks, mock_delete_agent, client):
    """Test deleting non-existent agent."""
    mock_load_tasks.return_value = {'agents': {}}
    
    response = client.delete('/delete_agent/nonexistent')
    assert response.status_code == 404
    assert response.json['success'] is False

# Add error case tests
@patch('app.initialiseCodingAgent')
def test_create_agent_failure(mock_init_agent, client):
    """Test agent creation failure."""
    mock_token_manager = MagicMock()
    mock_token_manager.return_value.set_token.return_value = True
    mock_init_agent.return_value = None
    
    test_data = {
        'repo_url': 'https://github.com/test/repo',
        'tasks': [{'title': 'Test Task', 'description': 'Test Description'}],
        'num_agents': 1
    }
    
    with patch('github_token.GitHubTokenManager', return_value=mock_token_manager):
        response = client.post('/create_agent',
                             headers={'X-GitHub-Token': 'test_token'},
                             json=test_data)
        
        assert response.status_code == 500
        assert response.json['success'] is False

@patch('app.load_tasks')
def test_agent_view_with_missing_fields(mock_load_tasks, client):
    """Test agent view with missing fields in agent data."""
    mock_data = {
        'agents': {
            'agent1': {}  # Missing all fields
        }
    }
    mock_load_tasks.return_value = mock_data
    
    response = client.get('/agents')
    assert response.status_code == 200