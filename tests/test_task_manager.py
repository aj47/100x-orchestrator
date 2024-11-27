"""
Tests for the Task Manager module
"""
import pytest
from datetime import datetime, timedelta
from app.tasks.task_manager import TaskManager, Task, TaskStatus, TaskPriority

@pytest.fixture
def task_manager():
    """Fixture to create a fresh TaskManager instance for each test"""
    return TaskManager()

def test_create_task(task_manager):
    """Test creating a new task"""
    task = task_manager.create_task(
        title="Test Task",
        description="Test Description",
        priority=TaskPriority.HIGH
    )
    
    assert isinstance(task, Task)
    assert task.title == "Test Task"
    assert task.description == "Test Description"
    assert task.priority == TaskPriority.HIGH
    assert task.status == TaskStatus.PENDING
    assert isinstance(task.created_at, datetime)

def test_create_task_with_dependencies(task_manager):
    """Test creating a task with dependencies"""
    # Create dependency task first
    dep_task = task_manager.create_task(
        title="Dependency Task",
        description="Must be completed first"
    )
    
    # Create dependent task
    task = task_manager.create_task(
        title="Dependent Task",
        description="Depends on another task",
        dependencies={dep_task.task_id}
    )
    
    assert task.status == TaskStatus.BLOCKED
    assert dep_task.task_id in task.dependencies

def test_assign_task(task_manager):
    """Test assigning a task to an agent"""
    task = task_manager.create_task(
        title="Test Task",
        description="Test Description"
    )
    
    updated_task = task_manager.assign_task(task.task_id, "agent-1")
    assert updated_task.assigned_agent == "agent-1"
    assert updated_task.status == TaskStatus.ASSIGNED

def test_assign_nonexistent_task(task_manager):
    """Test assigning a nonexistent task"""
    with pytest.raises(ValueError, match="Task .* not found"):
        task_manager.assign_task("nonexistent-task", "agent-1")

def test_start_task(task_manager):
    """Test starting a task"""
    task = task_manager.create_task(
        title="Test Task",
        description="Test Description"
    )
    task_manager.assign_task(task.task_id, "agent-1")
    
    started_task = task_manager.start_task(task.task_id)
    assert started_task.status == TaskStatus.IN_PROGRESS
    assert isinstance(started_task.started_at, datetime)

def test_start_unassigned_task(task_manager):
    """Test starting an unassigned task"""
    task = task_manager.create_task(
        title="Test Task",
        description="Test Description"
    )
    
    with pytest.raises(ValueError, match="Task .* cannot be started"):
        task_manager.start_task(task.task_id)

def test_complete_task_success(task_manager):
    """Test completing a task successfully"""
    task = task_manager.create_task(
        title="Test Task",
        description="Test Description"
    )
    task_manager.assign_task(task.task_id, "agent-1")
    task_manager.start_task(task.task_id)
    
    completed_task = task_manager.complete_task(task.task_id, success=True)
    assert completed_task.status == TaskStatus.COMPLETED
    assert isinstance(completed_task.completed_at, datetime)
    assert isinstance(completed_task.actual_duration, int)

def test_complete_task_failure(task_manager):
    """Test completing a task with failure"""
    task = task_manager.create_task(
        title="Test Task",
        description="Test Description"
    )
    task_manager.assign_task(task.task_id, "agent-1")
    task_manager.start_task(task.task_id)
    
    failed_task = task_manager.complete_task(
        task.task_id,
        success=False,
        error="Test failure"
    )
    assert failed_task.status == TaskStatus.FAILED
    assert failed_task.error_message == "Test failure"

def test_unblock_dependent_tasks(task_manager):
    """Test unblocking dependent tasks"""
    # Create dependency task
    dep_task = task_manager.create_task(
        title="Dependency Task",
        description="Must be completed first"
    )
    
    # Create dependent task
    dependent_task = task_manager.create_task(
        title="Dependent Task",
        description="Depends on another task",
        dependencies={dep_task.task_id}
    )
    
    # Complete dependency task
    task_manager.assign_task(dep_task.task_id, "agent-1")
    task_manager.start_task(dep_task.task_id)
    task_manager.complete_task(dep_task.task_id, success=True)
    
    # Check if dependent task is unblocked
    unblocked_task = task_manager.get_task(dependent_task.task_id)
    assert unblocked_task.status == TaskStatus.PENDING

def test_get_agent_tasks(task_manager):
    """Test getting tasks assigned to an agent"""
    # Create and assign multiple tasks
    task1 = task_manager.create_task(title="Task 1", description="First task")
    task2 = task_manager.create_task(title="Task 2", description="Second task")
    
    task_manager.assign_task(task1.task_id, "agent-1")
    task_manager.assign_task(task2.task_id, "agent-1")
    
    agent_tasks = task_manager.get_agent_tasks("agent-1")
    assert len(agent_tasks) == 2
    assert all(task.assigned_agent == "agent-1" for task in agent_tasks)

def test_get_available_tasks(task_manager):
    """Test getting available tasks"""
    # Create tasks with different statuses
    task1 = task_manager.create_task(title="Task 1", description="Pending task")
    task2 = task_manager.create_task(title="Task 2", description="Assigned task")
    task_manager.assign_task(task2.task_id, "agent-1")
    
    available_tasks = task_manager.get_available_tasks()
    assert len(available_tasks) == 1
    assert available_tasks[0].task_id == task1.task_id

def test_get_blocked_tasks(task_manager):
    """Test getting blocked tasks"""
    # Create dependency chain
    task1 = task_manager.create_task(title="Task 1", description="First task")
    task2 = task_manager.create_task(
        title="Task 2",
        description="Dependent task",
        dependencies={task1.task_id}
    )
    
    blocked_tasks = task_manager.get_blocked_tasks()
    assert len(blocked_tasks) == 1
    assert blocked_tasks[0].task_id == task2.task_id

def test_get_task_dependencies(task_manager):
    """Test getting task dependencies"""
    # Create dependency chain
    task1 = task_manager.create_task(title="Task 1", description="First task")
    task2 = task_manager.create_task(
        title="Task 2",
        description="Dependent task",
        dependencies={task1.task_id}
    )
    
    dependencies = task_manager.get_task_dependencies(task2.task_id)
    assert len(dependencies) == 1
    assert dependencies[0].task_id == task1.task_id