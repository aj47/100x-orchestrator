"""
Settings manager for handling application configuration
"""
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class AgentConfig(BaseModel):
    """Configuration settings for an individual agent"""
    agent_id: str
    repository_url: Optional[str] = None
    local_path: Optional[str] = None
    branch_prefix: str = "agent"
    resource_limits: Dict[str, Any] = Field(default_factory=lambda: {
        "cpu": 1.0,
        "memory": "512M",
        "timeout": 3600
    })
    environment_vars: Dict[str, str] = Field(default_factory=dict)
    test_framework: str = "pytest"
    code_style: Dict[str, Any] = Field(default_factory=lambda: {
        "formatter": "black",
        "line_length": 88,
        "use_types": True
    })

class ProjectConfig(BaseModel):
    """Configuration settings for the entire project"""
    project_name: str
    project_root: Path
    source_type: str = "github"  # "github" or "local"
    source_url: Optional[str] = None
    max_agents: int = 5
    workspace_root: Path = Path("workspaces")
    default_agent_config: AgentConfig
    agents: Dict[str, AgentConfig] = Field(default_factory=dict)
    git_config: Dict[str, Any] = Field(default_factory=lambda: {
        "commit_prefix": "[AI]",
        "auto_merge": True,
        "require_tests": True
    })
    monitoring_config: Dict[str, Any] = Field(default_factory=lambda: {
        "metrics_interval": 60,
        "save_history": True,
        "history_path": "metrics_history"
    })

class ConfigManager:
    """Manages configuration settings for the orchestrator"""

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize ConfigManager
        
        Args:
            config_path: Path to configuration file (optional)
        """
        self.config_path = config_path or Path("config.json")
        self._config: Optional[ProjectConfig] = None

    def load_config(self) -> ProjectConfig:
        """
        Load configuration from file
        
        Returns:
            ProjectConfig: Loaded project configuration
        """
        if self._config is not None:
            return self._config

        try:
            if self.config_path.exists():
                config_data = json.loads(self.config_path.read_text())
                self._config = ProjectConfig(**config_data)
                logger.info(f"Loaded configuration from {self.config_path}")
            else:
                logger.warning(f"Configuration file {self.config_path} not found")
                self._config = self._create_default_config()
                self.save_config()
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            raise

        return self._config

    def save_config(self) -> None:
        """Save current configuration to file"""
        if self._config is None:
            raise ValueError("No configuration loaded")

        try:
            config_data = self._config.model_dump(mode='json')
            self.config_path.write_text(json.dumps(config_data, indent=2))
            logger.info(f"Saved configuration to {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            raise

    def _create_default_config(self) -> ProjectConfig:
        """
        Create default configuration
        
        Returns:
            ProjectConfig: Default project configuration
        """
        default_agent = AgentConfig(
            agent_id="default",
            branch_prefix="agent"
        )

        return ProjectConfig(
            project_name="ai-orchestrator",
            project_root=Path.cwd(),
            default_agent_config=default_agent
        )

    def get_agent_config(self, agent_id: str) -> AgentConfig:
        """
        Get configuration for specific agent
        
        Args:
            agent_id: Identifier of the agent
        
        Returns:
            AgentConfig: Agent configuration
        """
        config = self.load_config()
        if agent_id not in config.agents:
            # Create new agent config based on default
            agent_config = AgentConfig(
                **config.default_agent_config.model_dump(exclude={'agent_id'}),
                agent_id=agent_id
            )
            config.agents[agent_id] = agent_config
            self.save_config()
        
        return config.agents[agent_id]

    def update_agent_config(self, agent_id: str, updates: Dict[str, Any]) -> AgentConfig:
        """
        Update configuration for specific agent
        
        Args:
            agent_id: Identifier of the agent
            updates: Dictionary of configuration updates
        
        Returns:
            AgentConfig: Updated agent configuration
        """
        config = self.load_config()
        agent_config = self.get_agent_config(agent_id)
        
        # Update configuration
        for key, value in updates.items():
            if hasattr(agent_config, key):
                setattr(agent_config, key, value)
        
        config.agents[agent_id] = agent_config
        self.save_config()
        return agent_config

    def list_agents(self) -> List[str]:
        """
        Get list of configured agents
        
        Returns:
            List[str]: List of agent IDs
        """
        config = self.load_config()
        return list(config.agents.keys())

    def remove_agent(self, agent_id: str) -> None:
        """
        Remove agent configuration
        
        Args:
            agent_id: Identifier of the agent to remove
        """
        config = self.load_config()
        if agent_id in config.agents:
            del config.agents[agent_id]
            self.save_config()
            logger.info(f"Removed configuration for agent {agent_id}")
        else:
            logger.warning(f"Agent {agent_id} not found in configuration")

    def update_project_config(self, updates: Dict[str, Any]) -> ProjectConfig:
        """
        Update project configuration
        
        Args:
            updates: Dictionary of configuration updates
        
        Returns:
            ProjectConfig: Updated project configuration
        """
        config = self.load_config()
        
        # Update configuration
        for key, value in updates.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        self.save_config()
        return config