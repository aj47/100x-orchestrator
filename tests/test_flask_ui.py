import sys
from pathlib import Path
import pytest
from snapshottest import TestCase

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent.parent))

from app import app

class TestFlaskUI(TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_index_route(self):
        """Test the index route of the Flask application."""
        response = self.client.get('/')
        
        # Check response status code
        assert response.status_code == 200, "Index route should return 200 OK"
        
        # Check response content type
        assert 'text/html' in response.content_type, "Response should be HTML"
        
        # Use snapshot testing for the full response
        self.assertMatchSnapshot(response.data.decode('utf-8'))

    def test_index_route_content(self):
        """Verify key elements are present in the index route."""
        response = self.client.get('/')
        response_text = response.data.decode('utf-8')
        
        # Key UI elements to check
        expected_elements = [
            'Repository URL', 
            'Task Description', 
            'Number of Agents', 
            'Create Agents',
            '100x Orchestrator'
        ]
        
        # Check that all expected elements are in the response
        for element in expected_elements:
            assert element in response_text, f"Should have {element}"
        
        # Also use snapshot for content verification
        self.assertMatchSnapshot(response_text)
