import pytest
from unittest.mock import patch, MagicMock
from app import app
import json

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_update_model_config(client, mock_db):
    new_config = {
        'provider': 'huggingface',
        'api_key_source': 'env:HUGGINGFACE_API_KEY'
    }
    response = client.post('/config/models', json={'model_config': new_config})
    assert response.status_code == 200
    assert json.loads(response.data)['message'] == 'Model config updated successfully'

@patch('orchestrator.initialiseCodingAgent', return_value=['test_agent'])
def test_create_agent_custom_provider(mock_init_agent, client, mock_db, mock_env_vars):
    mock_env_vars({"HUGGINGFACE_API_KEY": "test"})
    response = client.post('/create_agent',
                           headers={'X-GitHub-Token': 'test_token'},
                           json={
                               'repo_url': 'test_repo',
                               'tasks': [{'title': 'test', 'description': 'test'}],
                               'model_config': {
                                   'provider': 'huggingface',
                                   'api_key_source': 'env:HUGGINGFACE_API_KEY'
                               }
                           })
    assert response.status_code == 200
    assert json.loads(response.data)['success'] is True
    mock_init_agent.assert_called_once()

@patch('orchestrator.initialiseCodingAgent', return_value=['test_agent'])
def test_create_agent_file_api_key(mock_init_agent, client, mock_db, mock_api_key_file, mock_env_vars):
    response = client.post('/create_agent',
                           headers={'X-GitHub-Token': 'test_token'},
                           json={
                               'repo_url': 'test_repo',
                               'tasks': [{'title': 'test', 'description': 'test'}],
                               'model_config': {
                                   'provider': 'openai',
                                   'api_key_source': f'file:{mock_api_key_file}'
                               }
                           })
    assert response.status_code == 200
    assert json.loads(response.data)['success'] is True
    mock_init_agent.assert_called_once()

