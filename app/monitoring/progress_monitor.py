"""
Progress Monitor module for tracking and evaluating agent performance
"""
from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

class TaskMetrics(BaseModel):
    """Metrics for a single task"""
    task_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str  # "in_progress", "completed", "failed"
    code_changes: int = 0
    tests_added: int = 0
    tests_passing: int = 0
    tests_failing: int = 0
    error_message: Optional[str] = None

class AgentMetrics(BaseModel):
    """Metrics for an individual agent"""
    agent_id: str
    tasks_completed: int = 0
    tasks_failed: int = 0
    total_code_changes: int = 0
    total_tests_added: int = 0
    success_rate: float = 0.0
    current_task: Optional[str] = None
    tasks: Dict[str, TaskMetrics] = {}

class ProgressMonitor:
    """Monitors and evaluates agent progress and performance"""

    def __init__(self):
        self._agent_metrics: Dict[str, AgentMetrics] = {}
        self._project_start_time = datetime.utcnow()

    def register_agent(self, agent_id: str) -> AgentMetrics:
        """
        Register a new agent for monitoring
        
        Args:
            agent_id: Unique identifier for the agent
        
        Returns:
            AgentMetrics: Initial metrics for the agent
        """
        if agent_id in self._agent_metrics:
            raise ValueError(f"Agent {agent_id} is already registered")
        
        metrics = AgentMetrics(agent_id=agent_id)
        self._agent_metrics[agent_id] = metrics
        logger.info(f"Registered agent {agent_id} for monitoring")
        return metrics

    def start_task(self, agent_id: str, task_id: str) -> TaskMetrics:
        """
        Start monitoring a new task for an agent
        
        Args:
            agent_id: Identifier of the agent
            task_id: Identifier for the new task
        
        Returns:
            TaskMetrics: Initial metrics for the task
        """
        if agent_id not in self._agent_metrics:
            raise ValueError(f"Agent {agent_id} is not registered")
        
        agent_metrics = self._agent_metrics[agent_id]
        if task_id in agent_metrics.tasks:
            raise ValueError(f"Task {task_id} is already started for agent {agent_id}")
        
        task_metrics = TaskMetrics(
            task_id=task_id,
            start_time=datetime.utcnow(),
            status="in_progress"
        )
        agent_metrics.tasks[task_id] = task_metrics
        agent_metrics.current_task = task_id
        
        logger.info(f"Started monitoring task {task_id} for agent {agent_id}")
        return task_metrics

    def update_task_metrics(
        self,
        agent_id: str,
        task_id: str,
        code_changes: int = 0,
        tests_added: int = 0,
        tests_passing: int = 0,
        tests_failing: int = 0
    ) -> TaskMetrics:
        """
        Update metrics for a task
        
        Args:
            agent_id: Identifier of the agent
            task_id: Identifier of the task
            code_changes: Number of code changes made
            tests_added: Number of new tests added
            tests_passing: Number of passing tests
            tests_failing: Number of failing tests
        
        Returns:
            TaskMetrics: Updated metrics for the task
        """
        if agent_id not in self._agent_metrics:
            raise ValueError(f"Agent {agent_id} is not registered")
        
        agent_metrics = self._agent_metrics[agent_id]
        if task_id not in agent_metrics.tasks:
            raise ValueError(f"Task {task_id} not found for agent {agent_id}")
        
        task_metrics = agent_metrics.tasks[task_id]
        task_metrics.code_changes += code_changes
        task_metrics.tests_added += tests_added
        task_metrics.tests_passing = tests_passing
        task_metrics.tests_failing = tests_failing
        
        # Update agent-level metrics
        agent_metrics.total_code_changes += code_changes
        agent_metrics.total_tests_added += tests_added
        
        logger.info(f"Updated metrics for task {task_id} of agent {agent_id}")
        return task_metrics

    def complete_task(self, agent_id: str, task_id: str, success: bool = True, error: str = None) -> TaskMetrics:
        """
        Mark a task as completed
        
        Args:
            agent_id: Identifier of the agent
            task_id: Identifier of the task
            success: Whether the task was successful
            error: Error message if task failed
        
        Returns:
            TaskMetrics: Final metrics for the task
        """
        if agent_id not in self._agent_metrics:
            raise ValueError(f"Agent {agent_id} is not registered")
        
        agent_metrics = self._agent_metrics[agent_id]
        if task_id not in agent_metrics.tasks:
            raise ValueError(f"Task {task_id} not found for agent {agent_id}")
        
        task_metrics = agent_metrics.tasks[task_id]
        task_metrics.end_time = datetime.utcnow()
        task_metrics.status = "completed" if success else "failed"
        task_metrics.error_message = error
        
        # Update agent-level metrics
        if success:
            agent_metrics.tasks_completed += 1
        else:
            agent_metrics.tasks_failed += 1
        
        total_tasks = agent_metrics.tasks_completed + agent_metrics.tasks_failed
        agent_metrics.success_rate = agent_metrics.tasks_completed / total_tasks if total_tasks > 0 else 0.0
        agent_metrics.current_task = None
        
        logger.info(f"Completed task {task_id} for agent {agent_id} with status: {'success' if success else 'failed'}")
        return task_metrics

    def get_agent_metrics(self, agent_id: str) -> AgentMetrics:
        """
        Get current metrics for an agent
        
        Args:
            agent_id: Identifier of the agent
        
        Returns:
            AgentMetrics: Current metrics for the agent
        """
        if agent_id not in self._agent_metrics:
            raise ValueError(f"Agent {agent_id} is not registered")
        
        return self._agent_metrics[agent_id]

    def get_project_metrics(self) -> Dict:
        """
        Get overall project metrics
        
        Returns:
            Dict: Project-level metrics
        """
        total_tasks_completed = 0
        total_tasks_failed = 0
        total_code_changes = 0
        total_tests_added = 0
        overall_success_rate = 0.0
        
        for agent_metrics in self._agent_metrics.values():
            total_tasks_completed += agent_metrics.tasks_completed
            total_tasks_failed += agent_metrics.tasks_failed
            total_code_changes += agent_metrics.total_code_changes
            total_tests_added += agent_metrics.total_tests_added
        
        total_tasks = total_tasks_completed + total_tasks_failed
        if total_tasks > 0:
            overall_success_rate = total_tasks_completed / total_tasks
        
        return {
            "total_agents": len(self._agent_metrics),
            "total_tasks_completed": total_tasks_completed,
            "total_tasks_failed": total_tasks_failed,
            "total_code_changes": total_code_changes,
            "total_tests_added": total_tests_added,
            "overall_success_rate": overall_success_rate,
            "project_runtime": (datetime.utcnow() - self._project_start_time).total_seconds()
        }