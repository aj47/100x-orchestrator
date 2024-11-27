"""
Agent Manager module for handling agent lifecycle and operations
"""
from typing import Dict, Optional
from pydantic import BaseModel
import asyncio
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class AgentStatus(BaseModel):
    """Model representing the current status of an agent"""
    agent_id: str
    status: str  # "initializing", "running", "stopped", "error"
    started_at: datetime
    last_updated: datetime
    current_task: Optional[str] = None
    resource_usage: Optional[Dict] = None
    error_message: Optional[str] = None

class AgentManager:
    """Manages the lifecycle and operations of AI coding agents"""
    
    def __init__(self):
        self._agents: Dict[str, AgentStatus] = {}
        self._locks: Dict[str, asyncio.Lock] = {}

    async def start_agent(self, agent_id: str, config: dict) -> AgentStatus:
        """
        Initialize and start a new agent
        
        Args:
            agent_id: Unique identifier for the agent
            config: Configuration dictionary for the agent
        
        Returns:
            AgentStatus: The status of the newly created agent
        """
        if agent_id in self._agents:
            raise ValueError(f"Agent {agent_id} already exists")

        self._locks[agent_id] = asyncio.Lock()
        
        now = datetime.utcnow()
        status = AgentStatus(
            agent_id=agent_id,
            status="initializing",
            started_at=now,
            last_updated=now
        )
        
        try:
            # TODO: Implement actual agent initialization logic
            status.status = "running"
            self._agents[agent_id] = status
            logger.info(f"Agent {agent_id} started successfully")
            return status
        except Exception as e:
            status.status = "error"
            status.error_message = str(e)
            logger.error(f"Failed to start agent {agent_id}: {e}")
            raise

    async def stop_agent(self, agent_id: str) -> AgentStatus:
        """
        Stop an active agent
        
        Args:
            agent_id: Identifier of the agent to stop
        
        Returns:
            AgentStatus: The final status of the stopped agent
        """
        if agent_id not in self._agents:
            raise ValueError(f"Agent {agent_id} not found")

        async with self._locks[agent_id]:
            status = self._agents[agent_id]
            try:
                # TODO: Implement actual agent shutdown logic
                status.status = "stopped"
                status.last_updated = datetime.utcnow()
                logger.info(f"Agent {agent_id} stopped successfully")
                return status
            except Exception as e:
                status.status = "error"
                status.error_message = str(e)
                logger.error(f"Failed to stop agent {agent_id}: {e}")
                raise

    async def get_status(self, agent_id: str) -> AgentStatus:
        """
        Get the current status of an agent
        
        Args:
            agent_id: Identifier of the agent
        
        Returns:
            AgentStatus: Current status of the agent
        """
        if agent_id not in self._agents:
            raise ValueError(f"Agent {agent_id} not found")
        
        return self._agents[agent_id]

    async def update_config(self, agent_id: str, config: dict) -> AgentStatus:
        """
        Update the configuration of an active agent
        
        Args:
            agent_id: Identifier of the agent
            config: New configuration dictionary
        
        Returns:
            AgentStatus: Updated status of the agent
        """
        if agent_id not in self._agents:
            raise ValueError(f"Agent {agent_id} not found")

        async with self._locks[agent_id]:
            status = self._agents[agent_id]
            try:
                # TODO: Implement configuration update logic
                status.last_updated = datetime.utcnow()
                logger.info(f"Agent {agent_id} configuration updated")
                return status
            except Exception as e:
                status.status = "error"
                status.error_message = str(e)
                logger.error(f"Failed to update agent {agent_id} configuration: {e}")
                raise

    def list_agents(self) -> Dict[str, AgentStatus]:
        """
        Get a list of all active agents and their statuses
        
        Returns:
            Dict[str, AgentStatus]: Dictionary of agent IDs to their current status
        """
        return self._agents.copy()