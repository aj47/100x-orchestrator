"""
Main orchestrator module that coordinates all components
"""
from typing import Dict, List, Optional
from pathlib import Path
import logging
import asyncio

from .agents.manager import AgentManager
from .vcs.git_manager import GitManager
from .tasks.task_manager import TaskManager, Task, TaskStatus, TaskPriority
from .monitoring.progress_monitor import ProgressMonitor
from .config.settings import ConfigManager, ProjectConfig

logger = logging.getLogger(__name__)

class Orchestrator:
    """Main orchestrator class that coordinates AI coding agents"""

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the orchestrator
        
        Args:
            config_path: Optional path to configuration file
        """
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.load_config()
        
        # Initialize components
        self.agent_manager = AgentManager()
        self.git_manager = GitManager(self.config.workspace_root)
        self.task_manager = TaskManager()
        self.progress_monitor = ProgressMonitor()

    async def initialize_project(self, source_url: Optional[str] = None) -> None:
        """
        Initialize project from source
        
        Args:
            source_url: Optional URL to source repository
        """
        if source_url:
            self.config.source_url = source_url
            self.config_manager.update_project_config({"source_url": source_url})
        
        if not self.config.source_url:
            raise ValueError("No source URL provided")
        
        logger.info(f"Initializing project from {self.config.source_url}")
        # Clone main repository
        await self.git_manager.clone_repository("main", self.config.source_url)

    async def start_agent(self, agent_id: str, config: Optional[Dict] = None) -> None:
        """
        Start a new AI coding agent
        
        Args:
            agent_id: Identifier for the new agent
            config: Optional configuration overrides
        """
        if config:
            agent_config = self.config_manager.update_agent_config(agent_id, config)
        else:
            agent_config = self.config_manager.get_agent_config(agent_id)
        
        # Initialize agent workspace
        if self.config.source_url:
            await self.git_manager.clone_repository(agent_id, self.config.source_url)
            await self.git_manager.create_branch(
                agent_id,
                f"{agent_config.branch_prefix}/{agent_id}"
            )
        
        # Register agent with managers
        await self.agent_manager.start_agent(agent_id, agent_config.model_dump())
        self.progress_monitor.register_agent(agent_id)
        
        logger.info(f"Started agent {agent_id}")

    async def stop_agent(self, agent_id: str) -> None:
        """
        Stop an AI coding agent
        
        Args:
            agent_id: Identifier of the agent to stop
        """
        # Complete any ongoing tasks
        agent_tasks = self.task_manager.get_agent_tasks(agent_id)
        for task in agent_tasks:
            if task.status == TaskStatus.IN_PROGRESS:
                await self.task_manager.complete_task(
                    task.task_id,
                    success=False,
                    error="Agent stopped"
                )
        
        # Stop the agent
        await self.agent_manager.stop_agent(agent_id)
        logger.info(f"Stopped agent {agent_id}")

    async def create_task(
        self,
        title: str,
        description: str,
        priority: TaskPriority = TaskPriority.MEDIUM,
        dependencies: Optional[List[str]] = None,
        assigned_agent: Optional[str] = None
    ) -> Task:
        """
        Create a new task
        
        Args:
            title: Title of the task
            description: Detailed description
            priority: Task priority
            dependencies: Optional list of dependency task IDs
            assigned_agent: Optional agent to assign the task to
        
        Returns:
            Task: Created task
        """
        task = self.task_manager.create_task(
            title=title,
            description=description,
            priority=priority,
            dependencies=set(dependencies) if dependencies else None
        )
        
        if assigned_agent:
            self.task_manager.assign_task(task.task_id, assigned_agent)
            # Start monitoring the task
            self.progress_monitor.start_task(assigned_agent, task.task_id)
        
        logger.info(f"Created task {task.task_id}: {title}")
        return task

    async def assign_task(self, task_id: str, agent_id: str) -> Task:
        """
        Assign a task to an agent
        
        Args:
            task_id: ID of the task to assign
            agent_id: ID of the agent to assign to
        
        Returns:
            Task: Updated task
        """
        task = self.task_manager.assign_task(task_id, agent_id)
        self.progress_monitor.start_task(agent_id, task_id)
        logger.info(f"Assigned task {task_id} to agent {agent_id}")
        return task

    async def complete_task(
        self,
        task_id: str,
        success: bool = True,
        error: Optional[str] = None
    ) -> Task:
        """
        Mark a task as completed
        
        Args:
            task_id: ID of the task to complete
            success: Whether the task was successful
            error: Optional error message
        
        Returns:
            Task: Updated task
        """
        task = self.task_manager.get_task(task_id)
        if task.assigned_agent:
            # Update progress monitoring
            self.progress_monitor.complete_task(
                task.assigned_agent,
                task_id,
                success,
                error
            )
        
        completed_task = self.task_manager.complete_task(task_id, success, error)
        logger.info(f"Completed task {task_id} with status: {'success' if success else 'failed'}")
        return completed_task

    async def get_project_status(self) -> Dict:
        """
        Get overall project status
        
        Returns:
            Dict: Project status information
        """
        return {
            "config": self.config.model_dump(),
            "agents": {
                agent_id: self.progress_monitor.get_agent_metrics(agent_id)
                for agent_id in self.config_manager.list_agents()
            },
            "tasks": {
                "available": len(self.task_manager.get_available_tasks()),
                "blocked": len(self.task_manager.get_blocked_tasks())
            },
            "metrics": self.progress_monitor.get_project_metrics()
        }

    async def sync_agent_changes(self, agent_id: str) -> bool:
        """
        Sync changes from an agent's workspace
        
        Args:
            agent_id: ID of the agent
        
        Returns:
            bool: True if sync was successful
        """
        try:
            # Commit any pending changes
            await self.git_manager.commit_changes(
                agent_id,
                f"{self.config.git_config['commit_prefix']} Sync changes from agent {agent_id}"
            )
            
            # Push changes to remote
            await self.git_manager.push_changes(agent_id)
            
            # If auto-merge is enabled and all tests pass
            if (
                self.config.git_config["auto_merge"]
                and (not self.config.git_config["require_tests"]
                     or await self._run_tests(agent_id))
            ):
                current_branch = self.git_manager.get_current_branch(agent_id)
                await self.git_manager.merge_branch(agent_id, current_branch)
            
            logger.info(f"Successfully synced changes from agent {agent_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to sync changes from agent {agent_id}: {e}")
            return False

    async def _run_tests(self, agent_id: str) -> bool:
        """
        Run tests in agent's workspace
        
        Args:
            agent_id: ID of the agent
        
        Returns:
            bool: True if all tests pass
        """
        # TODO: Implement test running logic
        return True