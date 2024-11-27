"""
Task Manager module for handling task lifecycle and dependencies
"""
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Set
from pydantic import BaseModel
import logging
from uuid import uuid4

logger = logging.getLogger(__name__)

class TaskStatus(str, Enum):
    """Enumeration of possible task statuses"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"

class TaskPriority(int, Enum):
    """Enumeration of task priorities"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

class Task(BaseModel):
    """Model representing a task"""
    task_id: str
    title: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    assigned_agent: Optional[str] = None
    dependencies: Set[str] = set()
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_duration: Optional[int] = None  # in seconds
    actual_duration: Optional[int] = None
    error_message: Optional[str] = None
    metadata: Dict = {}

class TaskManager:
    """Manages task lifecycle and dependencies"""

    def __init__(self):
        self._tasks: Dict[str, Task] = {}
        self._agent_tasks: Dict[str, Set[str]] = {}  # agent_id -> set of task_ids

    def create_task(
        self,
        title: str,
        description: str,
        priority: TaskPriority = TaskPriority.MEDIUM,
        dependencies: Optional[Set[str]] = None,
        estimated_duration: Optional[int] = None,
        metadata: Optional[Dict] = None
    ) -> Task:
        """
        Create a new task
        
        Args:
            title: Title of the task
            description: Detailed description of the task
            priority: Priority level of the task
            dependencies: Set of task IDs this task depends on
            estimated_duration: Estimated duration in seconds
            metadata: Additional task metadata
        
        Returns:
            Task: Created task
        """
        task_id = str(uuid4())
        task = Task(
            task_id=task_id,
            title=title,
            description=description,
            priority=priority,
            dependencies=dependencies or set(),
            created_at=datetime.utcnow(),
            estimated_duration=estimated_duration,
            metadata=metadata or {}
        )
        
        # Check if task is blocked by dependencies
        if task.dependencies and any(
            dep_id not in self._tasks or self._tasks[dep_id].status != TaskStatus.COMPLETED
            for dep_id in task.dependencies
        ):
            task.status = TaskStatus.BLOCKED
        
        self._tasks[task_id] = task
        logger.info(f"Created task {task_id}: {title}")
        return task

    def assign_task(self, task_id: str, agent_id: str) -> Task:
        """
        Assign a task to an agent
        
        Args:
            task_id: ID of the task to assign
            agent_id: ID of the agent to assign the task to
        
        Returns:
            Task: Updated task
        """
        if task_id not in self._tasks:
            raise ValueError(f"Task {task_id} not found")
        
        task = self._tasks[task_id]
        if task.status not in [TaskStatus.PENDING, TaskStatus.BLOCKED]:
            raise ValueError(f"Task {task_id} cannot be assigned (status: {task.status})")
        
        # Initialize agent's task set if needed
        if agent_id not in self._agent_tasks:
            self._agent_tasks[agent_id] = set()
        
        task.assigned_agent = agent_id
        task.status = TaskStatus.ASSIGNED
        self._agent_tasks[agent_id].add(task_id)
        
        logger.info(f"Assigned task {task_id} to agent {agent_id}")
        return task

    def start_task(self, task_id: str) -> Task:
        """
        Mark a task as started
        
        Args:
            task_id: ID of the task to start
        
        Returns:
            Task: Updated task
        """
        if task_id not in self._tasks:
            raise ValueError(f"Task {task_id} not found")
        
        task = self._tasks[task_id]
        if task.status != TaskStatus.ASSIGNED:
            raise ValueError(f"Task {task_id} cannot be started (status: {task.status})")
        
        # Check dependencies
        if task.dependencies and any(
            self._tasks[dep_id].status != TaskStatus.COMPLETED
            for dep_id in task.dependencies
        ):
            task.status = TaskStatus.BLOCKED
            raise ValueError(f"Task {task_id} is blocked by incomplete dependencies")
        
        task.status = TaskStatus.IN_PROGRESS
        task.started_at = datetime.utcnow()
        
        logger.info(f"Started task {task_id}")
        return task

    def complete_task(self, task_id: str, success: bool = True, error: str = None) -> Task:
        """
        Mark a task as completed
        
        Args:
            task_id: ID of the task to complete
            success: Whether the task completed successfully
            error: Error message if task failed
        
        Returns:
            Task: Updated task
        """
        if task_id not in self._tasks:
            raise ValueError(f"Task {task_id} not found")
        
        task = self._tasks[task_id]
        if task.status != TaskStatus.IN_PROGRESS:
            raise ValueError(f"Task {task_id} cannot be completed (status: {task.status})")
        
        task.completed_at = datetime.utcnow()
        if task.started_at:
            task.actual_duration = int((task.completed_at - task.started_at).total_seconds())
        
        if success:
            task.status = TaskStatus.COMPLETED
            # Unblock dependent tasks
            self._unblock_dependent_tasks(task_id)
        else:
            task.status = TaskStatus.FAILED
            task.error_message = error
        
        # Remove task from agent's task set
        if task.assigned_agent and task.assigned_agent in self._agent_tasks:
            self._agent_tasks[task.assigned_agent].remove(task_id)
        
        logger.info(f"Completed task {task_id} with status: {'success' if success else 'failed'}")
        return task

    def _unblock_dependent_tasks(self, completed_task_id: str) -> None:
        """
        Unblock tasks that depend on the completed task
        
        Args:
            completed_task_id: ID of the completed task
        """
        for task in self._tasks.values():
            if (
                task.status == TaskStatus.BLOCKED
                and completed_task_id in task.dependencies
                and all(
                    self._tasks[dep_id].status == TaskStatus.COMPLETED
                    for dep_id in task.dependencies
                )
            ):
                task.status = TaskStatus.PENDING
                logger.info(f"Unblocked task {task.task_id}")

    def get_task(self, task_id: str) -> Task:
        """
        Get a task by ID
        
        Args:
            task_id: ID of the task
        
        Returns:
            Task: Retrieved task
        """
        if task_id not in self._tasks:
            raise ValueError(f"Task {task_id} not found")
        return self._tasks[task_id]

    def get_agent_tasks(self, agent_id: str) -> List[Task]:
        """
        Get all tasks assigned to an agent
        
        Args:
            agent_id: ID of the agent
        
        Returns:
            List[Task]: List of tasks assigned to the agent
        """
        if agent_id not in self._agent_tasks:
            return []
        return [self._tasks[task_id] for task_id in self._agent_tasks[agent_id]]

    def get_available_tasks(self) -> List[Task]:
        """
        Get all available tasks that can be assigned
        
        Returns:
            List[Task]: List of available tasks
        """
        return [
            task for task in self._tasks.values()
            if task.status == TaskStatus.PENDING
        ]

    def get_blocked_tasks(self) -> List[Task]:
        """
        Get all blocked tasks
        
        Returns:
            List[Task]: List of blocked tasks
        """
        return [
            task for task in self._tasks.values()
            if task.status == TaskStatus.BLOCKED
        ]

    def get_task_dependencies(self, task_id: str) -> List[Task]:
        """
        Get all dependencies for a task
        
        Args:
            task_id: ID of the task
        
        Returns:
            List[Task]: List of dependency tasks
        """
        if task_id not in self._tasks:
            raise ValueError(f"Task {task_id} not found")
        
        task = self._tasks[task_id]
        return [self._tasks[dep_id] for dep_id in task.dependencies]