import os
import sys
import pytest
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

@pytest.fixture
def temp_workspace():
    """Create a temporary workspace for testing."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        old_cwd = os.getcwd()
        os.chdir(tmpdir)
        yield tmpdir
        os.chdir(old_cwd)

@pytest.fixture
def mock_github_token():
    """Mock GitHub token for testing."""
    return "mock_github_token_12345"

@pytest.fixture
def mock_litellm_api_key():
    """Mock LiteLLM API key for testing."""
    return "mock_litellm_api_key_12345"
