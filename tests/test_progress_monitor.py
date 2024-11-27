"""
Tests for the Progress Monitor module
"""
import pytest
from datetime import datetime, timedelta
from app.monitoring.progress_monitor import ProgressMonitor, AgentMetrics, TaskMetrics

@pytest.fixture
def progress_monitor():
    """Fixture to create a fresh ProgressMonitor instance for each test"""
    return ProgressMonitor()

def test_register_agent(progress_monitor):
    """Test registering a new agent"""
    metrics = progress_monitor.register_agent("test-agent")
    assert isinstance(metrics, AgentMetrics)
    assert metrics.agent_id == "test-agent"
    assert metrics.tasks_completed == 0
    assert metrics.tasks_failed == 0

def test_register_duplicate_agent(progress_monitor):
    """Test registering an agent with duplicate ID"""
    progress_monitor.register_agent("test-agent")
    with pytest.raises(ValueError, match="Agent test-agent is already registered"):
        progress_monitor.register_agent("test-agent")

def test_start_task(progress_monitor):
    """Test starting a new task"""
    progress_monitor.register_agent("test-agent")
    metrics = progress_monitor.start_task("test-agent", "task-1")
    
    assert isinstance(metrics, TaskMetrics)
    assert metrics.task_id == "task-1"
    assert metrics.status == "in_progress"
    assert isinstance(metrics.start_time, datetime)

def test_start_task_unregistered_agent(progress_monitor):
    """Test starting a task for unregistered agent"""
    with pytest.raises(ValueError, match="Agent unknown-agent is not registered"):
        progress_monitor.start_task("unknown-agent", "task-1")

def test_update_task_metrics(progress_monitor):
    """Test updating task metrics"""
    progress_monitor.register_agent("test-agent")
    progress_monitor.start_task("test-agent", "task-1")
    
    metrics = progress_monitor.update_task_metrics(
        "test-agent",
        "task-1",
        code_changes=5,
        tests_added=2,
        tests_passing=10,
        tests_failing=1
    )
    
    assert metrics.code_changes == 5
    assert metrics.tests_added == 2
    assert metrics.tests_passing == 10
    assert metrics.tests_failing == 1

def test_complete_task_success(progress_monitor):
    """Test completing a task successfully"""
    progress_monitor.register_agent("test-agent")
    progress_monitor.start_task("test-agent", "task-1")
    
    metrics = progress_monitor.complete_task("test-agent", "task-1", success=True)
    
    assert metrics.status == "completed"
    assert isinstance(metrics.end_time, datetime)
    assert metrics.error_message is None
    
    agent_metrics = progress_monitor.get_agent_metrics("test-agent")
    assert agent_metrics.tasks_completed == 1
    assert agent_metrics.tasks_failed == 0
    assert agent_metrics.success_rate == 1.0

def test_complete_task_failure(progress_monitor):
    """Test completing a task with failure"""
    progress_monitor.register_agent("test-agent")
    progress_monitor.start_task("test-agent", "task-1")
    
    error_msg = "Test failure"
    metrics = progress_monitor.complete_task("test-agent", "task-1", success=False, error=error_msg)
    
    assert metrics.status == "failed"
    assert isinstance(metrics.end_time, datetime)
    assert metrics.error_message == error_msg
    
    agent_metrics = progress_monitor.get_agent_metrics("test-agent")
    assert agent_metrics.tasks_completed == 0
    assert agent_metrics.tasks_failed == 1
    assert agent_metrics.success_rate == 0.0

def test_get_project_metrics(progress_monitor):
    """Test getting overall project metrics"""
    # Register and complete tasks for multiple agents
    for agent_id in ["agent-1", "agent-2"]:
        progress_monitor.register_agent(agent_id)
        
        # Complete two tasks successfully
        for task_id in [f"{agent_id}-task-1", f"{agent_id}-task-2"]:
            progress_monitor.start_task(agent_id, task_id)
            progress_monitor.update_task_metrics(agent_id, task_id, code_changes=5, tests_added=2)
            progress_monitor.complete_task(agent_id, task_id, success=True)
        
        # Complete one task with failure
        fail_task_id = f"{agent_id}-task-3"
        progress_monitor.start_task(agent_id, fail_task_id)
        progress_monitor.complete_task(agent_id, fail_task_id, success=False, error="Test error")
    
    metrics = progress_monitor.get_project_metrics()
    
    assert metrics["total_agents"] == 2
    assert metrics["total_tasks_completed"] == 4
    assert metrics["total_tasks_failed"] == 2
    assert metrics["total_code_changes"] == 20  # 4 successful tasks * 5 changes
    assert metrics["total_tests_added"] == 8    # 4 successful tasks * 2 tests
    assert metrics["overall_success_rate"] == 0.6666666666666666  # 4 succeeded / 6 total
    assert isinstance(metrics["project_runtime"], float)

def test_get_agent_metrics_unregistered(progress_monitor):
    """Test getting metrics for unregistered agent"""
    with pytest.raises(ValueError, match="Agent unknown-agent is not registered"):
        progress_monitor.get_agent_metrics("unknown-agent")

def test_multiple_tasks_success_rate(progress_monitor):
    """Test success rate calculation with multiple tasks"""
    progress_monitor.register_agent("test-agent")
    
    # Complete 3 successful tasks and 2 failed tasks
    for i in range(5):
        task_id = f"task-{i}"
        progress_monitor.start_task("test-agent", task_id)
        success = i < 3  # First 3 tasks succeed, last 2 fail
        progress_monitor.complete_task("test-agent", task_id, success=success)
    
    agent_metrics = progress_monitor.get_agent_metrics("test-agent")
    assert agent_metrics.tasks_completed == 3
    assert agent_metrics.tasks_failed == 2
    assert agent_metrics.success_rate == 0.6  # 3 succeeded / 5 total