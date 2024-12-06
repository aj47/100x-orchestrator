import sys
from pathlib import Path
import pytest

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent.parent))

from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_index_route_basic(client):
    """Test basic functionality of the index route."""
    response = client.get('/')
    assert response.status_code == 200
    assert 'text/html' in response.content_type

def test_index_route_elements(client):
    """Test that all required elements are present in the index route."""
    response = client.get('/')
    content = response.data.decode('utf-8')
    
    # Print what we're checking for debugging
    print("\nChecking for elements in the page:")
    
    elements = {
        'Git Repository URL': 'repository URL input',
        'Tasks': 'tasks section',
        'Create New Agents': 'create agents heading',
        '100x Orchestrator': 'main heading',
        'Number of Agents per Task': 'agents count input',
        'Describe the task for the agent...': 'task input placeholder'
    }
    
    for text, description in elements.items():
        found = text in content
        print(f"- {description}: {'Found' if found else 'Not found'}")
        assert found, f"Missing {description}: '{text}'"

def test_index_route_snapshot(client, snapshot):
    """Test the index route using snapshot testing."""
    response = client.get('/')
    assert response.status_code == 200
    snapshot.assert_match(response.data.decode('utf-8'), 'index_page_content')
