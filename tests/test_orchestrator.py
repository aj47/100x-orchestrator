"""
Tests for the main Orchestrator module
"""
import pytest
from pathlib import Path
import tempfile
import shutil
from unittest.mock import Mock, patch
from app.orchestrator import Orchestrator
from app.tasks.task_manager import TaskPriority, TaskStatus

@pytest.fixture
def temp_workspace():
    """Fixture to create a temporary workspace directory"""
    workspace_dir = tempfile.mkdtemp()
    yield workspace_dir
    shutil.rmtree(workspace_dir)

@pytest.fixture
async def orchestrator(temp_workspace):
    """Fixture to create an Orchestrator instance with temporary workspace"""
    with patch('app.config.settings.ConfigManager.load_config') as mock_load_config:
        # Mock configuration
        mock_config = Mock()
        mock_config.workspace_root = Path(temp_workspace)
        mock_config.source_url = "https://github.com/test/repo"
        mock_config.git_config = {
            "commit_prefix": "[AI]",
            "auto_merge": True,
            "require_tests": False
        }
        mock_load_config.return_value = mock_config
        
        orchestrator = Orchestrator()
        yield orchestrator

@pytest.mark.asyncio
async def test_initialize_project(orchestrator):
    """Test project initialization"""
    test_url = "https://github.com/test/new-repo"
    
    with patch('app.vcs.git_manager.GitManager.clone_repository') as mock_clone:
        await orchestrator.initialize_project(test_url)
        mock_clone.assert_called_once_with("main", test_url)

@pytest.mark.asyncio
async def test_initialize_project_no_url(orchestrator):
    """Test project initialization without URL"""
    orchestrator.config.source_url = None
    with pytest.raises(ValueError, match="No source URL provided"):
        await orchestrator.initialize_project()

@pytest.mark.asyncio
async def test_start_agent(orchestrator):
    """Test starting a new agent"""
    agent_id = "test-agent"
    
    with patch('app.vcs.git_manager.GitManager.clone_repository') as mock_clone, \
         patch('app.vcs.git_manager.GitManager.create_branch') as mock_create_branch, \
         patch('app.agents.manager.AgentManager.start_agent') as mock_start_agent, \
         patch('app.monitoring.progress_monitor.ProgressMonitor.register_agent') as mock_register:
        
        await orchestrator.start_agent(agent_id)
        
        mock_clone.assert_called_once()
        mock_create_branch.assert_called_once()
        mock_start_agent.assert_called_once()
        mock_register.assert_called_once_with(agent_id)

@pytest.mark.asyncio
async def test_stop_agent(orchestrator):
    """Test stopping an agent"""
    agent_id = "test-agent"
    
    with patch('app.agents.manager.AgentManager.stop_agent') as mock_stop_agent, \
         patch('app.tasks.task_manager.TaskManager.get_agent_tasks') as mock_get_tasks:
        
        # Mock an in-progress task
        mock_task = Mock()
        mock_task.status = TaskStatus.IN_PROGRESS
        mock_task.task_id = "task-1"
        mock_get_tasks.return_value = [mock_task]
        
        await orchestrator.stop_agent(agent_id)
        
        mock_stop_agent.assert_called_once_with(agent_id)

@pytest.mark.asyncio
async def test_create_task(orchestrator):
    """Test creating a new task"""
    title = "Test Task"
    description = "Test Description"
    
    task = await orchestrator.create_task(
        title=title,
        description=description,
        priority=TaskPriority.HIGH
    )
    
    assert task.title == title
    assert task.description == description
    assert task.priority == TaskPriority.HIGH

@pytest.mark.asyncio
async def test_create_and_assign_task(orchestrator):
    """Test creating and assigning a task"""
    agent_id = "test-agent"
    
    with patch('app.monitoring.progress_monitor.ProgressMonitor.start_task') as mock_start_monitoring:
        task = await orchestrator.create_task(
            title="Test Task",
            description="Test Description",
            assigned_agent=agent_id
        )
        
        assert task.assigned_agent == agent_id
        mock_start_monitoring.assert_called_once()

@pytest.mark.asyncio
async def test_complete_task(orchestrator):
    """Test completing a task"""
    task = await orchestrator.create_task(
        title="Test Task",
        description="Test Description"
    )
    
    with patch('app.monitoring.progress_monitor.ProgressMonitor.complete_task') as mock_complete_monitoring:
        completed_task = await orchestrator.complete_task(task.task_id, success=True)
        assert completed_task.status == TaskStatus.COMPLETED

@pytest.mark.asyncio
async def test_get_project_status(orchestrator):
    """Test getting project status"""
    status = await orchestrator.get_project_status()
    
    assert "config" in status
    assert "agents" in status
    assert "tasks" in status
    assert "metrics" in status

@pytest.mark.asyncio
async def test_sync_agent_changes(orchestrator):
    """Test syncing agent changes"""
    agent_id = "test-agent"
    
    with patch('app.vcs.git_manager.GitManager.commit_changes') as mock_commit, \
         patch('app.vcs.git_manager.GitManager.push_changes') as mock_push, \
         patch('app.vcs.git_manager.GitManager.get_current_branch') as mock_get_branch, \
         patch('app.vcs.git_manager.GitManager.merge_branch') as mock_merge:
        
        mock_get_branch.return_value = "feature/test"
        success = await orchestrator.sync_agent_changes(agent_id)
        
        assert success is True
        mock_commit.assert_called_once()
        mock_push.assert_called_once()
        mock_merge.assert_called_once()

@pytest.mark.asyncio
async def test_sync_agent_changes_failure(orchestrator):
    """Test syncing agent changes with failure"""
    agent_id = "test-agent"
    
    with patch('app.vcs.git_manager.GitManager.commit_changes') as mock_commit:
        mock_commit.side_effect = Exception("Test error")
        success = await orchestrator.sync_agent_changes(agent_id)
        
        assert success is False

@pytest.mark.asyncio
async def test_run_tests(orchestrator):
    """Test running tests"""
    agent_id = "test-agent"
    result = await orchestrator._run_tests(agent_id)
    assert result is True  # Currently always returns True as it's not implemented