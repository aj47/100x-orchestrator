"""
Tests for the Configuration Manager module
"""
import pytest
from pathlib import Path
import json
import tempfile
from app.config.settings import ConfigManager, AgentConfig, ProjectConfig

@pytest.fixture
def temp_config_file():
    """Fixture to create a temporary configuration file"""
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
        # Create default config
        default_config = {
            "project_name": "test-project",
            "project_root": str(Path.cwd()),
            "source_type": "github",
            "max_agents": 5,
            "workspace_root": str(Path("workspaces")),
            "default_agent_config": {
                "agent_id": "default",
                "branch_prefix": "agent",
                "resource_limits": {
                    "cpu": 1.0,
                    "memory": "512M",
                    "timeout": 3600
                }
            },
            "agents": {},
            "git_config": {
                "commit_prefix": "[AI]",
                "auto_merge": True,
                "require_tests": True
            }
        }
        tmp.write(json.dumps(default_config).encode())
        tmp.flush()
        yield Path(tmp.name)
        try:
            Path(tmp.name).unlink(missing_ok=True)
        except PermissionError:
            pass  # Ignore permission errors during cleanup

@pytest.fixture
def config_manager(temp_config_file):
    """Fixture to create a ConfigManager instance with temporary config file"""
    return ConfigManager(config_path=temp_config_file)

def test_create_default_config(config_manager):
    """Test creation of default configuration"""
    config = config_manager.load_config()
    
    assert isinstance(config, ProjectConfig)
    assert config.project_name == "test-project"
    assert isinstance(config.project_root, Path)
    assert isinstance(config.default_agent_config, AgentConfig)
    assert config.default_agent_config.agent_id == "default"

def test_save_and_load_config(config_manager, temp_config_file):
    """Test saving and loading configuration"""
    # Get default config and modify it
    config = config_manager.load_config()
    config.project_name = "updated-project"
    config_manager.save_config()
    
    # Create new config manager and load config
    new_manager = ConfigManager(config_path=temp_config_file)
    loaded_config = new_manager.load_config()
    
    assert loaded_config.project_name == "updated-project"
    assert loaded_config.project_root == config.project_root

def test_get_agent_config_new(config_manager):
    """Test getting configuration for a new agent"""
    agent_config = config_manager.get_agent_config("test-agent")
    
    assert isinstance(agent_config, AgentConfig)
    assert agent_config.agent_id == "test-agent"
    assert agent_config.branch_prefix == "agent"
    assert "cpu" in agent_config.resource_limits

def test_get_agent_config_existing(config_manager):
    """Test getting configuration for an existing agent"""
    # Create agent config first
    first_config = config_manager.get_agent_config("test-agent")
    first_config.branch_prefix = "custom-prefix"
    config_manager.update_agent_config("test-agent", {"branch_prefix": "custom-prefix"})
    
    # Get it again
    second_config = config_manager.get_agent_config("test-agent")
    assert second_config.branch_prefix == "custom-prefix"

def test_update_agent_config(config_manager):
    """Test updating agent configuration"""
    agent_id = "test-agent"
    updates = {
        "branch_prefix": "feature",
        "resource_limits": {"cpu": 2.0, "memory": "1G"},
        "test_framework": "unittest"
    }
    
    config = config_manager.update_agent_config(agent_id, updates)
    
    assert config.branch_prefix == "feature"
    assert config.resource_limits["cpu"] == 2.0
    assert config.resource_limits["memory"] == "1G"
    assert config.test_framework == "unittest"

def test_list_agents(config_manager):
    """Test listing configured agents"""
    # Create some agent configs
    config_manager.get_agent_config("agent1")
    config_manager.get_agent_config("agent2")
    
    agents = config_manager.list_agents()
    assert len(agents) == 2
    assert "agent1" in agents
    assert "agent2" in agents

def test_remove_agent(config_manager):
    """Test removing agent configuration"""
    # Create agent config
    config_manager.get_agent_config("test-agent")
    assert "test-agent" in config_manager.list_agents()
    
    # Remove it
    config_manager.remove_agent("test-agent")
    assert "test-agent" not in config_manager.list_agents()

def test_update_project_config(config_manager):
    """Test updating project configuration"""
    updates = {
        "project_name": "updated-project",
        "max_agents": 10,
        "git_config": {"auto_merge": False}
    }
    
    config = config_manager.update_project_config(updates)
    
    assert config.project_name == "updated-project"
    assert config.max_agents == 10
    assert config.git_config["auto_merge"] is False

def test_invalid_config_file(temp_config_file):
    """Test handling of invalid configuration file"""
    # Write invalid JSON
    temp_config_file.write_text("invalid json content")
    
    config_manager = ConfigManager(config_path=temp_config_file)
    with pytest.raises(Exception):
        config_manager.load_config()

def test_config_file_permissions(temp_config_file):
    """Test handling of configuration file permissions"""
    config_manager = ConfigManager(config_path=temp_config_file)
    config = config_manager.load_config()
    
    # Verify config can be saved
    config.project_name = "test-permissions"
    config_manager.save_config()
    
    # Verify changes were saved
    new_manager = ConfigManager(config_path=temp_config_file)
    loaded_config = new_manager.load_config()
    assert loaded_config.project_name == "test-permissions"
