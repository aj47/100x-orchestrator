import sys
from pathlib import Path
import pytest
from snapshottest import TestCase

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent.parent))

from app import app

class TestFlaskUINew(TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_index_route_content_new(self):
        """Verify key elements are present in the index route."""
        response = self.client.get('/')
        response_text = response.data.decode('utf-8')
        
        # Print response text for debugging
        print("\nResponse text contains:")
        
        # Key UI elements to check
        expected_elements = [
            'Git Repository URL',  # Label for repo URL input
            'Tasks',              # Label for tasks section
            'Create New Agents',  # Card title
            '100x Orchestrator',  # Main heading
            'Number of Agents per Task',  # Label for agent count input
            'Describe the task for the agent...'  # Task input placeholder
        ]
        
        # Check each element and print whether it's found
        for element in expected_elements:
            found = element in response_text
            print(f"- {element}: {'Found' if found else 'Not found'}")
            assert found, f"Should have {element}"
