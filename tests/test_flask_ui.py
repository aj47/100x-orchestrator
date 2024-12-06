import pytest
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent.parent))

from app import app

def test_index_route():
    """Test the index route of the Flask application."""
    client = app.test_client()
    
    # Test GET request to index route
    response = client.get('/')
    
    # Check response status code
    assert response.status_code == 200, "Index route should return 200 OK"
    
    # Check response content type
    assert 'text/html' in response.content_type, "Response should be HTML"
    
    # Optional: Check for specific content in the response
    assert b'100x Orchestrator' in response.data, "Page should contain project title"
    assert b'Create AI Agents' in response.data, "Page should have a create agents section"

def test_index_route_content():
    """Verify key elements are present in the index route."""
    client = app.test_client()
    
    response = client.get('/')
    response_text = response.data.decode('utf-8')
    
    # Check for key UI elements
    assert 'Repository URL' in response_text, "Should have repository URL input"
    assert 'Task Description' in response_text, "Should have task description input"
    assert 'Number of Agents' in response_text, "Should have number of agents input"
    assert 'Create Agents' in response_text, "Should have a create agents button"
