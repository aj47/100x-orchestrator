import os, json, traceback, subprocess, sys, uuid
from prompts import PROMPT_AIDER
from litellm_client import LiteLLMClient
from prompt_processor import PromptProcessor
from pathlib import Path
import shutil
import tempfile
from time import sleep
import datetime
import logging
from github import Github
from dotenv import load_dotenv

# Import the new AgentSession class
from agent_session import AgentSession, normalize_path

# Configuration
DEFAULT_AGENTS_PER_TASK = 2
CONFIG_FILE = Path("tasks/tasks.json")

# Ensure tasks directory exists
CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
tools, available_functions = [], {}
MAX_TOOL_OUTPUT_LENGTH = 5000  # Adjust as needed
CHECK_INTERVAL = 5  # Reduced to 30 seconds for more frequent updates

# Global dictionaries to store sessions and processors
aider_sessions = {}
prompt_processors = {}

def load_tasks():
    """Load config from tasks.json."""
    try:
        with open(CONFIG_FILE, 'r') as f:
            data = json.load(f)

            # Ensure data has the correct structure
            if not isinstance(data, dict):
                logging.warning("tasks.json has incorrect structure, resetting to default")
                return {"tasks": [], "agents": {}, "repository_url": ""}

            # Ensure required keys exist
            data.setdefault('tasks', [])
            data.setdefault('agents', {})
            data.setdefault('repository_url', '')

            # Normalize paths in loaded data
            if isinstance(data.get('agents'), dict):
                for agent_id, agent_data in data['agents'].items():
                    if isinstance(agent_data, dict):
                        if 'workspace' in agent_data:
                            agent_data['workspace'] = normalize_path(agent_data['workspace'])
                        if 'repo_path' in agent_data:
                            agent_data['repo_path'] = normalize_path(agent_data['repo_path'])
            else:
                logging.warning("Agents data is not a dictionary, resetting to empty dict")
                data['agents'] = {}

            return data
    except FileNotFoundError:
        logging.info("tasks.json not found, creating default")
        return {"tasks": [], "agents": {}, "repository_url": ""}
    except json.JSONDecodeError:
        logging.error("Error decoding tasks.json", exc_info=True)
        return {"tasks": [], "agents": {}, "repository_url": ""}

# ... (rest of orchestrator.py remains the same)
