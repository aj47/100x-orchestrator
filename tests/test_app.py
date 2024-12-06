import pytest
import json
from pathlib import Path
import os
from app import app
import threading
from unittest.mock import patch, MagicMock

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
def mock_tasks_file(tmp_path):
    # Create a temporary tasks.json file
    tasks_file = tmp_path / "tasks" / "tasks.json"
    tasks_file.parent.mkdir(parents=True, exist_ok=True)
    default_data = {
        "tasks": [],
        "agents": {},
        "repository_url": "",
        "config": {
            "agent_session": {}
        }
    }
    tasks_file.write_text(json.dumps(default_data))
    return tasks_file

def test_index_route(client):
    """Test the index route returns the index template"""
    response = client.get('/')
    assert response.status_code == 200
    assert b'<!DOCTYPE html>' in response.data

def test_serve_tasks_json(client, tmp_path):
    """Test serving tasks.json file"""
    with patch('app.Path') as mock_path:
        mock_path.return_value = tmp_path / "tasks" / "tasks.json"
        response = client.get('/tasks/tasks.json')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "tasks" in data
        assert "agents" in data
        assert "repository_url" in data
        assert "config" in data

def test_agent_view(client):
    """Test the agent view route"""
    mock_tasks_data = {
        "agents": {
            "agent1": {
                "task": "test task",
                "status": "pending",
                "aider_output": "",
                "last_updated": None
            }
        }
    }
    
    with patch('app.load_tasks', return_value=mock_tasks_data):
        response = client.get('/agents')
        assert response.status_code == 200
        assert b'agent1' in response.data

def test_create_agent_missing_data(client):
    """Test create_agent route with missing data"""
    response = client.post('/create_agent', 
                         json={},
                         content_type='application/json')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data

def test_create_agent_success(client):
    """Test successful agent creation"""
    mock_agent_ids = ['test_agent_1']
    
    with patch('app.initialiseCodingAgent', return_value=mock_agent_ids), \
         patch('app.load_tasks', return_value={'tasks': [], 'agents': {}}), \
         patch('app.save_tasks'):
        
        response = client.post('/create_agent',
                             json={
                                 'repo_url': 'https://github.com/test/repo',
                                 'tasks': ['Test task']
                             },
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'test_agent_1' in data['agent_ids']

def test_delete_agent_success(client):
    """Test successful agent deletion"""
    agent_id = 'test_agent'
    mock_tasks_data = {
        'agents': {
            agent_id: {
                'task': 'test task'
            }
        }
    }
    
    with patch('app.load_tasks', return_value=mock_tasks_data), \
         patch('app.delete_agent', return_value=True), \
         patch('app.save_tasks'):
        
        response = client.delete(f'/delete_agent/{agent_id}')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True

def test_delete_agent_not_found(client):
    """Test deleting non-existent agent"""
    with patch('app.load_tasks', return_value={'agents': {}}):
        response = client.delete('/delete_agent/nonexistent')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['success'] is False

def test_debug_agent_info(client):
    """Test debug endpoint for agent info"""
    agent_id = 'test_agent'
    mock_tasks_data = {
        'agents': {
            agent_id: {
                'workspace': '/test/workspace',
                'repo_path': '/test/repo',
                'status': 'active',
                'created_at': '2023-01-01',
                'last_updated': '2023-01-02',
                'aider_output': 'test output',
                'task': 'test task'
            }
        }
    }
    
    with patch('app.load_tasks', return_value=mock_tasks_data), \
         patch('app.aider_sessions', {}):
        
        response = client.get(f'/debug/agent/{agent_id}')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['agent_id'] == agent_id
        assert 'paths' in data
        assert 'agent_data' in data

def test_debug_validate_paths(client):
    """Test debug endpoint for path validation"""
    agent_id = 'test_agent'
    mock_tasks_data = {
        'agents': {
            agent_id: {
                'workspace': '/test/workspace',
                'repo_path': '/test/repo'
            }
        }
    }
    
    with patch('app.load_tasks', return_value=mock_tasks_data), \
         patch('app.aider_sessions', {}):
        
        response = client.get(f'/debug/validate_paths/{agent_id}')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['agent_id'] == agent_id
        assert 'paths' in data
        assert 'validation' in data
