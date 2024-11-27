"""
Git Manager module for handling version control operations
"""
from pathlib import Path
import asyncio
import logging
from typing import Optional, List
from git import Repo, GitCommandError
from git.remote import Remote

logger = logging.getLogger(__name__)

class GitManager:
    """Manages Git operations for agent workspaces"""

    def __init__(self, workspace_root: str):
        """
        Initialize GitManager
        
        Args:
            workspace_root: Root directory for all agent workspaces
        """
        self.workspace_root = Path(workspace_root)
        self.workspace_root.mkdir(parents=True, exist_ok=True)
        self._locks = {}

    async def clone_repository(self, agent_id: str, repo_url: str) -> Path:
        """
        Clone a repository for an agent
        
        Args:
            agent_id: Unique identifier for the agent
            repo_url: URL of the repository to clone
        
        Returns:
            Path: Path to the cloned repository
        """
        workspace_path = self.workspace_root / agent_id
        if workspace_path.exists():
            raise ValueError(f"Workspace for agent {agent_id} already exists")

        try:
            repo = Repo.clone_from(repo_url, workspace_path)
            logger.info(f"Successfully cloned repository for agent {agent_id}")
            return workspace_path
        except GitCommandError as e:
            logger.error(f"Failed to clone repository for agent {agent_id}: {e}")
            raise

    async def create_branch(self, agent_id: str, branch_name: str) -> str:
        """
        Create a new branch in the agent's repository
        
        Args:
            agent_id: Identifier of the agent
            branch_name: Name of the branch to create
        
        Returns:
            str: Name of the created branch
        """
        workspace_path = self.workspace_root / agent_id
        if not workspace_path.exists():
            raise ValueError(f"Workspace for agent {agent_id} does not exist")

        try:
            repo = Repo(workspace_path)
            current = repo.create_head(branch_name)
            current.checkout()
            logger.info(f"Created and checked out branch {branch_name} for agent {agent_id}")
            return branch_name
        except GitCommandError as e:
            logger.error(f"Failed to create branch for agent {agent_id}: {e}")
            raise

    async def commit_changes(self, agent_id: str, message: str) -> str:
        """
        Commit changes in the agent's workspace
        
        Args:
            agent_id: Identifier of the agent
            message: Commit message
        
        Returns:
            str: Hash of the commit
        """
        workspace_path = self.workspace_root / agent_id
        if not workspace_path.exists():
            raise ValueError(f"Workspace for agent {agent_id} does not exist")

        try:
            repo = Repo(workspace_path)
            repo.git.add(A=True)
            commit = repo.index.commit(message)
            logger.info(f"Committed changes for agent {agent_id}: {message}")
            return commit.hexsha
        except GitCommandError as e:
            logger.error(f"Failed to commit changes for agent {agent_id}: {e}")
            raise

    async def push_changes(self, agent_id: str, branch_name: Optional[str] = None) -> bool:
        """
        Push changes to remote repository
        
        Args:
            agent_id: Identifier of the agent
            branch_name: Optional branch name to push (defaults to current branch)
        
        Returns:
            bool: True if push was successful
        """
        workspace_path = self.workspace_root / agent_id
        if not workspace_path.exists():
            raise ValueError(f"Workspace for agent {agent_id} does not exist")

        try:
            repo = Repo(workspace_path)
            if branch_name:
                repo.git.push('origin', branch_name)
            else:
                repo.git.push()
            logger.info(f"Pushed changes for agent {agent_id}")
            return True
        except GitCommandError as e:
            logger.error(f"Failed to push changes for agent {agent_id}: {e}")
            raise

    async def merge_branch(self, agent_id: str, source_branch: str, target_branch: str = "main") -> bool:
        """
        Merge source branch into target branch
        
        Args:
            agent_id: Identifier of the agent
            source_branch: Branch to merge from
            target_branch: Branch to merge into (defaults to main)
        
        Returns:
            bool: True if merge was successful
        """
        workspace_path = self.workspace_root / agent_id
        if not workspace_path.exists():
            raise ValueError(f"Workspace for agent {agent_id} does not exist")

        try:
            repo = Repo(workspace_path)
            repo.git.checkout(target_branch)
            repo.git.merge(source_branch)
            logger.info(f"Merged {source_branch} into {target_branch} for agent {agent_id}")
            return True
        except GitCommandError as e:
            logger.error(f"Failed to merge branches for agent {agent_id}: {e}")
            raise

    def get_current_branch(self, agent_id: str) -> str:
        """
        Get the current branch name for an agent's repository
        
        Args:
            agent_id: Identifier of the agent
        
        Returns:
            str: Name of the current branch
        """
        workspace_path = self.workspace_root / agent_id
        if not workspace_path.exists():
            raise ValueError(f"Workspace for agent {agent_id} does not exist")

        repo = Repo(workspace_path)
        return repo.active_branch.name

    def list_branches(self, agent_id: str) -> List[str]:
        """
        List all branches in an agent's repository
        
        Args:
            agent_id: Identifier of the agent
        
        Returns:
            List[str]: List of branch names
        """
        workspace_path = self.workspace_root / agent_id
        if not workspace_path.exists():
            raise ValueError(f"Workspace for agent {agent_id} does not exist")

        repo = Repo(workspace_path)
        return [branch.name for branch in repo.branches]