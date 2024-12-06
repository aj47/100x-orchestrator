
import sys
from pathlib import Path
import pytest
from snapshottest import TestCase

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent.parent))

from app import app

def test_basic_elements(capsys):  # Add capsys fixture to capture output
    client = app.test_client()
    response = client.get('/')
    response_text = response.data.decode('utf-8')
    
    # Print what we're testing
    print("\nChecking response text for elements...")
    
    # Check for 'Task Description' in placeholder
    placeholder_text = 'Describe the task for the agent...'
    if placeholder_text in response_text:
        print(f"Found placeholder: {placeholder_text}")
    else:
        print("Placeholder not found")
    
    # Check for basic elements
    elements = [
        'Git Repository URL',
        'Tasks',
        'Create New Agents',
        '100x Orchestrator',
        'Number of Agents per Task'
    ]
    
    for element in elements:
        if element in response_text:
            print(f"Found element: {element}")
        else:
            print(f"Missing element: {element}")
    
    # Force output to be shown
    captured = capsys.readouterr()
    print(captured.out)
