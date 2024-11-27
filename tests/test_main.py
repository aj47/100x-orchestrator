"""
Tests for the main FastAPI application
"""
from fastapi.testclient import TestClient
import pytest
from app.main import app

client = TestClient(app)

def test_root_endpoint():
    """Test the root endpoint returns correct status"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "status": "active",
        "service": "100x-orchestrator"
    }

def test_start_agent():
    """Test starting a new agent"""
    test_config = {
        "agent_id": "test-agent-1",
        "repository_url": "https://github.com/test/repo",
        "resource_allocation": {"cpu": 1, "memory": "512M"}
    }
    response = client.post("/agents/start", json=test_config)
    assert response.status_code == 200
    assert response.json()["agent_id"] == "test-agent-1"
    assert response.json()["status"] == "initialized"

def test_stop_agent():
    """Test stopping an agent"""
    response = client.post("/agents/test-agent-1/stop")
    assert response.status_code == 200
    assert response.json()["status"] == "terminated"
    assert response.json()["agent_id"] == "test-agent-1"

def test_get_agent_status():
    """Test getting agent status"""
    response = client.get("/agents/test-agent-1/status")
    assert response.status_code == 200
    assert "agent_id" in response.json()
    assert "status" in response.json()

def test_update_agent_config():
    """Test updating agent configuration"""
    test_config = {
        "agent_id": "test-agent-1",
        "resource_allocation": {"cpu": 2, "memory": "1G"}
    }
    response = client.put("/agents/test-agent-1/config", json=test_config)
    assert response.status_code == 200
    assert response.json()["status"] == "updated"
    assert response.json()["agent_id"] == "test-agent-1"