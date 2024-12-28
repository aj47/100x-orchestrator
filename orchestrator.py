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
from flask_socketio import emit

# Import the new AgentSession class
from agent_session import AgentSession, normalize_path

from database import (
    save_agent, get_agent, get_all_agents, delete_agent as db_delete_agent,
    save_task, get_all_tasks, save_config, get_config
)

# Configuration
DEFAULT_AGENTS_PER_TASK = 2
tools, available_functions = [], {}
MAX_TOOL_OUTPUT_LENGTH = 5000  # Adjust as needed
CHECK_INTERVAL = 5  # Reduced to 30 seconds for more frequent updates

# Global dictionaries to store sessions and processors
aider_sessions = {}
prompt_processors = {}

# ... (rest of the code remains the same until cloneRepository function)

def cloneRepository(repository_url: str, agent_id: str) -> bool:
    """Clone git repository using subprocess and emit progress updates."""
    try:
        if not repository_url:
            logging.error("No repository URL provided")
            return False
        logging.info(f"Cloning {repository_url} for agent {agent_id}")
        process = subprocess.Popen(
            f"git clone --quiet {repository_url}",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        while process.poll() is None:
            # Emit progress updates (replace with actual progress calculation if possible)
            emit('clone_progress', {'agent_id': agent_id, 'progress': 50}, namespace='/agent')
            sleep(2)
        
        stdout, stderr = process.communicate()
        if process.returncode != 0:
            logging.error(f"Git clone failed for agent {agent_id}: {stderr.decode()}")
            emit('clone_error', {'agent_id': agent_id, 'error': stderr.decode()}, namespace='/agent')
            return False
        return True
    except subprocess.SubprocessError as e:
        logging.error(f"Git clone failed for agent {agent_id}: {str(e)}", exc_info=True)
        emit('clone_error', {'agent_id': agent_id, 'error': str(e)}, namespace='/agent')
        return False
    except Exception as e:
        logging.error(f"Unexpected error during clone for agent {agent_id}: {str(e)}", exc_info=True)
        emit('clone_error', {'agent_id': agent_id, 'error': str(e)}, namespace='/agent')
        return False

# ... (rest of the orchestrator.py code remains the same)
