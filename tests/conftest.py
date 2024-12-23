import pytest
from pathlib import Path
import tempfile
import json

@pytest.fixture
def temp_config_file():
    """Fixture that creates a temporary config file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        test_config = {
            "repository_url": "https://github.com/test/repo",
            "current_task": "test task",
            "default_agents_per_task": 2
        }
        json.dump(test_config, f)
        config_path = f.name
    
    yield config_path
    Path(config_path).unlink()  # Cleanup after test

@pytest.fixture
def temp_workspace():
    """Fixture that creates a temporary workspace directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)
