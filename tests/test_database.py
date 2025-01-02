import pytest
import sqlite3
from pathlib import Path
from datetime import datetime
import json
from database import (
    init_db, save_agent, get_agent, get_all_agents,
    delete_agent, save_task, get_all_tasks,
    get_config, save_config, get_model_config
)

@pytest.fixture
def test_db_path(tmp_path):
    """Create a temporary database path for testing."""
    db_path = tmp_path / "test_tasks.db"
    # Temporarily override the DATABASE_PATH
    import database
    original_path = database.DATABASE_PATH
    database.DATABASE_PATH = db_path
    yield db_path
    # Reset the DATABASE_PATH
    database.DATABASE_PATH = original_path

@pytest.fixture
def initialized_db(test_db_path):
    """Initialize the test database."""
    init_db()
    return test_db_path

@pytest.fixture
def sample_agent_data():
    """Create sample agent data for testing."""
    return {
        'workspace': '/test/workspace',
        'repo_path': '/test/repo',
        'task': 'Test task',
        'status': 'running',
        'progress_history': ['Started task'],
        'thought_history': ['Initial thought'],
        'agent_type': 'test_agent'
    }

def test_init_db(test_db_path):
    """Test database initialization."""
    init_db()
    assert test_db_path.exists()
    
    # Verify tables were created
    with sqlite3.connect(test_db_path) as conn:
        cursor = conn.cursor()
        
        # Check if all tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
        expected_tables = {'model_config', 'agents', 'tasks', 'config'}
        assert expected_tables.issubset(tables)
        
        # Verify default model config was created
        cursor.execute("SELECT COUNT(*) FROM model_config")
        assert cursor.fetchone()[0] == 1

def test_init_db_error(test_db_path, monkeypatch):
    """Test database initialization with error."""
    def mock_connect(*args, **kwargs):
        raise sqlite3.Error("Mock DB Error")
    
    monkeypatch.setattr(sqlite3, "connect", mock_connect)
    with pytest.raises(Exception):
        init_db()

def test_save_and_get_agent(initialized_db, sample_agent_data):
    """Test saving and retrieving an agent."""
    agent_id = "test_agent_1"
    
    # Test saving
    assert save_agent(agent_id, sample_agent_data) is True
    
    # Test retrieving
    agent = get_agent(agent_id)
    assert agent is not None
    assert agent['id'] == agent_id
    assert agent['workspace'] == sample_agent_data['workspace']
    assert agent['repo_path'] == sample_agent_data['repo_path']
    assert agent['task'] == sample_agent_data['task']
    assert agent['status'] == sample_agent_data['status']
    assert agent['progress_history'] == sample_agent_data['progress_history']
    assert agent['thought_history'] == sample_agent_data['thought_history']

def test_save_agent_error(initialized_db, sample_agent_data, monkeypatch):
    """Test saving agent with database error."""
    def mock_connect(*args, **kwargs):
        raise sqlite3.Error("Mock DB Error")
    
    monkeypatch.setattr(sqlite3, "connect", mock_connect)
    assert save_agent("test_agent", sample_agent_data) is False

def test_get_agent_error(initialized_db, monkeypatch):
    """Test getting agent with database error."""
    def mock_connect(*args, **kwargs):
        raise sqlite3.Error("Mock DB Error")
    
    monkeypatch.setattr(sqlite3, "connect", mock_connect)
    assert get_agent("test_agent") is None

def test_get_all_agents(initialized_db, sample_agent_data):
    """Test retrieving all agents."""
    # Save multiple agents
    agent_ids = ["test_agent_1", "test_agent_2"]
    for agent_id in agent_ids:
        save_agent(agent_id, sample_agent_data)
    
    # Get all agents
    agents = get_all_agents()
    assert len(agents) == 2
    assert all(aid in agents for aid in agent_ids)

def test_get_all_agents_error(initialized_db, monkeypatch):
    """Test getting all agents with database error."""
    def mock_connect(*args, **kwargs):
        raise sqlite3.Error("Mock DB Error")
    
    monkeypatch.setattr(sqlite3, "connect", mock_connect)
    assert get_all_agents() == {}

def test_delete_agent(initialized_db, sample_agent_data):
    """Test deleting an agent."""
    agent_id = "test_agent_1"
    
    # Save and verify agent exists
    save_agent(agent_id, sample_agent_data)
    assert get_agent(agent_id) is not None
    
    # Delete and verify agent is gone
    assert delete_agent(agent_id) is True
    assert get_agent(agent_id) is None

def test_delete_nonexistent_agent(initialized_db):
    """Test deleting a non-existent agent."""
    assert delete_agent("nonexistent_agent") is False

def test_delete_agent_error(initialized_db, monkeypatch):
    """Test deleting agent with database error."""
    def mock_connect(*args, **kwargs):
        raise sqlite3.Error("Mock DB Error")
    
    monkeypatch.setattr(sqlite3, "connect", mock_connect)
    assert delete_agent("test_agent") is False

def test_save_and_get_tasks(initialized_db):
    """Test saving and retrieving tasks."""
    task_data = {
        'title': 'Test Task',
        'description': 'Test Description'
    }
    
    # Save task and verify ID
    task_id = save_task(task_data)
    assert task_id > 0
    
    # Get all tasks and verify
    tasks = get_all_tasks()
    assert len(tasks) == 1
    assert tasks[0]['title'] == task_data['title']
    assert tasks[0]['description'] == task_data['description']

def test_save_task_error(initialized_db, monkeypatch):
    """Test saving task with database error."""
    def mock_connect(*args, **kwargs):
        raise sqlite3.Error("Mock DB Error")
    
    monkeypatch.setattr(sqlite3, "connect", mock_connect)
    assert save_task({'title': 'Test', 'description': 'Test'}) == -1

def test_get_all_tasks_error(initialized_db, monkeypatch):
    """Test getting all tasks with database error."""
    def mock_connect(*args, **kwargs):
        raise sqlite3.Error("Mock DB Error")
    
    monkeypatch.setattr(sqlite3, "connect", mock_connect)
    assert get_all_tasks() == []

def test_config_operations(initialized_db):
    """Test config save and retrieve operations."""
    # Test saving config
    assert save_config('test_key', 'test_value') is True
    
    # Test retrieving config
    value = get_config('test_key')
    assert value == 'test_value'
    
    # Test non-existent config
    assert get_config('non_existent') is None

def test_save_config_error(initialized_db, monkeypatch):
    """Test saving config with database error."""
    def mock_connect(*args, **kwargs):
        raise sqlite3.Error("Mock DB Error")
    
    monkeypatch.setattr(sqlite3, "connect", mock_connect)
    assert save_config('test_key', 'test_value') is False

def test_get_config_error(initialized_db, monkeypatch):
    """Test getting config with database error."""
    def mock_connect(*args, **kwargs):
        raise sqlite3.Error("Mock DB Error")
    
    monkeypatch.setattr(sqlite3, "connect", mock_connect)
    assert get_config('test_key') is None

def test_get_model_config(initialized_db):
    """Test retrieving model configuration."""
    config = get_model_config()
    assert config is not None
    assert 'orchestrator_model' in config
    assert 'aider_model' in config
    assert 'agent_model' in config
    assert config['orchestrator_model'] == 'openrouter/google/gemini-flash-1.5'

def test_get_model_config_error(initialized_db, monkeypatch):
    """Test getting model config with database error."""
    def mock_connect(*args, **kwargs):
        raise sqlite3.Error("Mock DB Error")
    
    monkeypatch.setattr(sqlite3, "connect", mock_connect)
    assert get_model_config() is None