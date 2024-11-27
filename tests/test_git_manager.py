"""
Tests for the Git Manager module
"""
import pytest
from pathlib import Path
import tempfile
import shutil
from git import Repo
from app.vcs.git_manager import GitManager

@pytest.fixture
def temp_workspace():
    """Fixture to create a temporary workspace directory"""
    workspace_dir = tempfile.mkdtemp()
    yield workspace_dir
    shutil.rmtree(workspace_dir)

@pytest.fixture
def temp_repo():
    """Fixture to create a temporary Git repository"""
    repo_dir = tempfile.mkdtemp()
    repo = Repo.init(repo_dir)
    
    # Create an initial commit
    Path(repo_dir, "README.md").write_text("# Test Repository")
    repo.index.add(["README.md"])
    repo.index.commit("Initial commit")
    
    yield repo_dir
    shutil.rmtree(repo_dir)

@pytest.fixture
def git_manager(temp_workspace):
    """Fixture to create a GitManager instance"""
    return GitManager(temp_workspace)

@pytest.mark.asyncio
async def test_clone_repository(git_manager, temp_repo):
    """Test cloning a repository"""
    agent_id = "test-agent"
    workspace_path = await git_manager.clone_repository(agent_id, temp_repo)
    
    assert workspace_path.exists()
    assert workspace_path.name == agent_id
    assert (workspace_path / ".git").is_dir()
    assert (workspace_path / "README.md").is_file()

@pytest.mark.asyncio
async def test_clone_repository_duplicate(git_manager, temp_repo):
    """Test cloning a repository with duplicate agent ID"""
    agent_id = "test-agent"
    await git_manager.clone_repository(agent_id, temp_repo)
    
    with pytest.raises(ValueError, match=f"Workspace for agent {agent_id} already exists"):
        await git_manager.clone_repository(agent_id, temp_repo)

@pytest.mark.asyncio
async def test_create_branch(git_manager, temp_repo):
    """Test creating a new branch"""
    agent_id = "test-agent"
    await git_manager.clone_repository(agent_id, temp_repo)
    
    branch_name = "feature/test"
    result = await git_manager.create_branch(agent_id, branch_name)
    
    assert result == branch_name
    assert git_manager.get_current_branch(agent_id) == branch_name

@pytest.mark.asyncio
async def test_commit_changes(git_manager, temp_repo):
    """Test committing changes"""
    agent_id = "test-agent"
    workspace_path = await git_manager.clone_repository(agent_id, temp_repo)
    
    # Make some changes
    test_file = workspace_path / "test.txt"
    test_file.write_text("test content")
    
    commit_hash = await git_manager.commit_changes(agent_id, "Add test file")
    assert len(commit_hash) == 40  # SHA-1 hash length

@pytest.mark.asyncio
async def test_list_branches(git_manager, temp_repo):
    """Test listing branches"""
    agent_id = "test-agent"
    await git_manager.clone_repository(agent_id, temp_repo)
    await git_manager.create_branch(agent_id, "feature/test1")
    await git_manager.create_branch(agent_id, "feature/test2")
    
    branches = git_manager.list_branches(agent_id)
    assert len(branches) >= 3  # main + 2 feature branches
    assert "feature/test1" in branches
    assert "feature/test2" in branches

@pytest.mark.asyncio
async def test_merge_branch(git_manager, temp_repo):
    """Test merging branches"""
    agent_id = "test-agent"
    workspace_path = await git_manager.clone_repository(agent_id, temp_repo)
    
    # Create and modify a feature branch
    await git_manager.create_branch(agent_id, "feature/test")
    test_file = workspace_path / "test.txt"
    test_file.write_text("test content")
    await git_manager.commit_changes(agent_id, "Add test file")
    
    # Merge back to main
    result = await git_manager.merge_branch(agent_id, "feature/test", "main")
    assert result is True

@pytest.mark.asyncio
async def test_get_current_branch(git_manager, temp_repo):
    """Test getting current branch"""
    agent_id = "test-agent"
    await git_manager.clone_repository(agent_id, temp_repo)
    
    # Initially should be on main/master branch
    current_branch = git_manager.get_current_branch(agent_id)
    assert current_branch in ["main", "master"]
    
    # Switch to new branch
    await git_manager.create_branch(agent_id, "feature/test")
    current_branch = git_manager.get_current_branch(agent_id)
    assert current_branch == "feature/test"