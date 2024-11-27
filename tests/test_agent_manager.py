"""
Tests for the Agent Manager module
"""
import pytest
from datetime import datetime
from app.agents.manager import AgentManager, AgentStatus

@pytest.fixture
async def agent_manager():
    """Fixture to create a fresh AgentManager instance for each test"""
    return AgentManager()

@pytest.mark.asyncio
async def test_start_agent(agent_manager):
    """Test starting a new agent"""
    config = {"repository_url": "https://github.com/test/repo"}
    status = await agent_manager.start_agent("test-agent", config)
    
    assert isinstance(status, AgentStatus)
    assert status.agent_id == "test-agent"
    assert status.status == "running"
    assert isinstance(status.started_at, datetime)
    assert isinstance(status.last_updated, datetime)

@pytest.mark.asyncio
async def test_start_duplicate_agent(agent_manager):
    """Test starting an agent with an ID that already exists"""
    config = {"repository_url": "https://github.com/test/repo"}
    await agent_manager.start_agent("test-agent", config)
    
    with pytest.raises(ValueError, match="Agent test-agent already exists"):
        await agent_manager.start_agent("test-agent", config)

@pytest.mark.asyncio
async def test_stop_agent(agent_manager):
    """Test stopping an agent"""
    config = {"repository_url": "https://github.com/test/repo"}
    await agent_manager.start_agent("test-agent", config)
    
    status = await agent_manager.stop_agent("test-agent")
    assert status.status == "stopped"
    assert isinstance(status.last_updated, datetime)

@pytest.mark.asyncio
async def test_stop_nonexistent_agent(agent_manager):
    """Test stopping an agent that doesn't exist"""
    with pytest.raises(ValueError, match="Agent nonexistent-agent not found"):
        await agent_manager.stop_agent("nonexistent-agent")

@pytest.mark.asyncio
async def test_get_agent_status(agent_manager):
    """Test getting agent status"""
    config = {"repository_url": "https://github.com/test/repo"}
    await agent_manager.start_agent("test-agent", config)
    
    status = await agent_manager.get_status("test-agent")
    assert isinstance(status, AgentStatus)
    assert status.agent_id == "test-agent"
    assert status.status == "running"

@pytest.mark.asyncio
async def test_update_agent_config(agent_manager):
    """Test updating agent configuration"""
    initial_config = {"repository_url": "https://github.com/test/repo"}
    await agent_manager.start_agent("test-agent", initial_config)
    
    new_config = {"repository_url": "https://github.com/test/new-repo"}
    status = await agent_manager.update_config("test-agent", new_config)
    
    assert isinstance(status, AgentStatus)
    assert status.agent_id == "test-agent"
    assert isinstance(status.last_updated, datetime)

@pytest.mark.asyncio
async def test_list_agents(agent_manager):
    """Test listing all agents"""
    config1 = {"repository_url": "https://github.com/test/repo1"}
    config2 = {"repository_url": "https://github.com/test/repo2"}
    
    await agent_manager.start_agent("agent1", config1)
    await agent_manager.start_agent("agent2", config2)
    
    agents = agent_manager.list_agents()
    assert len(agents) == 2
    assert "agent1" in agents
    assert "agent2" in agents
    assert all(isinstance(status, AgentStatus) for status in agents.values())