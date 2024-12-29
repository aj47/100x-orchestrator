import pytest
import json
from unittest.mock import patch, MagicMock
from app import app, initialiseCodingAgent, load_tasks, save_tasks, delete_agent
from flask import Flask, request, jsonify
import sqlite3
from pathlib import Path
import os
import datetime

# Mock the database interactions
@pytest.fixture
def mock_db_connection():
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    return mock_conn

# Mock initialiseCodingAgent
@pytest.fixture
def mock_initialiseCodingAgent():
    return MagicMock(return_value=['agent1', 'agent2'])

# Mock load_tasks and save_tasks
@pytest.fixture
def mock_load_tasks():
    return MagicMock(return_value={'agents': {}, 'tasks': []})

@pytest.fixture
def mock_save_tasks():
    return MagicMock()

# Test Client
@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

# Test create_agent route
def test_create_agent_success(client, mock_initialiseCodingAgent, mock_load_tasks, mock_save_tasks, monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "test_token")
    data = {
        'repo_url': 'https://github.com/test/repo',
        'tasks': [{'title': 'Task 1', 'description': 'Description 1'}],
        'num_agents': 2,
        'aider_commands': ['command1', 'command2']
    }
    response = client.post('/create_agent', data=json.dumps(data), content_type='application/json')
    assert response.status_code == 200
    assert json.loads(response.data)['success'] is True
    mock_initialiseCodingAgent.assert_called_once()
    mock_save_tasks.assert_called_once()

def test_create_agent_missing_fields(client, mock_initialiseCodingAgent, mock_load_tasks, mock_save_tasks):
    response = client.post('/create_agent', data=json.dumps({}), content_type='application/json')
    assert response.status_code == 400
    assert json.loads(response.data)['error'] == 'Repository URL and tasks are required'
    mock_initialiseCodingAgent.assert_not_called()
    mock_save_tasks.assert_not_called()

def test_create_agent_missing_github_token(client, mock_initialiseCodingAgent, mock_load_tasks, mock_save_tasks):
    data = {
        'repo_url': 'https://github.com/test/repo',
        'tasks': [{'title': 'Task 1', 'description': 'Description 1'}],
        'num_agents': 2,
        'aider_commands': ['command1', 'command2']
    }
    response = client.post('/create_agent', data=json.dumps(data), content_type='application/json')
    assert response.status_code == 400
    assert json.loads(response.data)['error'] == 'GitHub token is required'
    mock_initialiseCodingAgent.assert_not_called()
    mock_save_tasks.assert_not_called()

def test_create_agent_initialiseCodingAgent_failure(client, mock_initialiseCodingAgent, mock_load_tasks, mock_save_tasks, monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "test_token")
    mock_initialiseCodingAgent.side_effect = Exception("Failed to initialize")
    data = {
        'repo_url': 'https://github.com/test/repo',
        'tasks': [{'title': 'Task 1', 'description': 'Description 1'}],
        'num_agents': 2,
        'aider_commands': ['command1', 'command2']
    }
    response = client.post('/create_agent', data=json.dumps(data), content_type='application/json')
    assert response.status_code == 500
    assert json.loads(response.data)['success'] is False
    mock_initialiseCodingAgent.assert_called_once()
    mock_save_tasks.assert_not_called()


# Test get_model_config route
def test_get_model_config_success(client, mock_db_connection):
    mock_cursor = mock_db_connection.cursor.return_value
    mock_cursor.fetchone.return_value = {
        'orchestrator_model': 'model1',
        'aider_model': 'model2',
        'agent_model': 'model3'
    }
    response = client.get('/config/models')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert data['config']['orchestrator_model'] == 'model1'
    assert data['config']['aider_model'] == 'model2'
    assert data['config']['agent_model'] == 'model3'

def test_get_model_config_no_config(client, mock_db_connection):
    mock_cursor = mock_db_connection.cursor.return_value
    mock_cursor.fetchone.return_value = None
    response = client.get('/config/models')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    assert data['config']['orchestrator_model'] == 'openrouter/google/gemini-flash-1.5'
    assert data['config']['aider_model'] == 'anthropic/claude-3-haiku'
    assert data['config']['agent_model'] == 'meta-llama/llama-3-70b'

def test_get_model_config_db_error(client, mock_db_connection):
    mock_db_connection.cursor.side_effect = sqlite3.Error("Database error")
    response = client.get('/config/models')
    assert response.status_code == 500
    assert json.loads(response.data)['success'] is False

def test_update_model_config_success(client, mock_db_connection):
    data = {
        'orchestrator_model': 'new_model1',
        'aider_model': 'new_model2',
        'agent_model': 'new_model3'
    }
    response = client.post('/config/models', data=json.dumps(data), content_type='application/json')
    assert response.status_code == 200
    assert json.loads(response.data)['success'] is True
    mock_db_connection.cursor.return_value.execute.assert_called_once()
    mock_db_connection.commit.assert_called_once()

def test_update_model_config_missing_fields(client, mock_db_connection):
    data = {
        'orchestrator_model': 'new_model1',
        'aider_model': 'new_model2'
    }
    response = client.post('/config/models', data=json.dumps(data), content_type='application/json')
    assert response.status_code == 400
    assert json.loads(response.data)['success'] is False

def test_update_model_config_db_error(client, mock_db_connection):
    mock_db_connection.cursor.side_effect = sqlite3.Error("Database error")
    data = {
        'orchestrator_model': 'new_model1',
        'aider_model': 'new_model2',
        'agent_model': 'new_model3'
    }
    response = client.post('/config/models', data=json.dumps(data), content_type='application/json')
    assert response.status_code == 500
    assert json.loads(response.data)['success'] is False

