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
import threading # Import threading module

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
agent_completion_events = {} # Dictionary to track agent completion events

def load_tasks():
    """Load config from tasks.json."""
    try:
        with open(CONFIG_FILE, 'r') as f:
            data = json.load(f)
            
            # Ensure data has the correct structure and required keys
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
                data['agents'] = {} # Reset to empty dict if not a dictionary
                
            return data
    except FileNotFoundError:
        return {"tasks": [], "agents": {}, "repository_url": ""} # Return default if file not found
    except json.JSONDecodeError:
        logging.error("Error decoding tasks.json", exc_info=True)
        return {"tasks": [], "agents": {}, "repository_url": ""} # Return default on decode error

def save_tasks(tasks_data):
    """Save tasks to tasks.json."""
    try:
        data_to_save = {
            "tasks": tasks_data.get("tasks", []),
            "agents": {},
            "repository_url": tasks_data.get("repository_url", "")
        }
        
        for agent_id, agent_data in tasks_data.get("agents", {}).items():
            repo_path = normalize_path(agent_data.get('repo_path'))
            data_to_save["agents"][agent_id] = {
                'workspace': normalize_path(agent_data.get('workspace')),
                'repo_path': repo_path,
                'task': agent_data.get('task'),
                'status': agent_data.get('status'),
                'created_at': agent_data.get('created_at'),
                'last_updated': agent_data.get('last_updated'),
                'aider_output': agent_data.get('aider_output', ''),
                'last_critique': agent_data.get('last_critique'),
                'progress': agent_data.get('progress', ''),
                'thought': agent_data.get('thought', ''),
                'progress_history': agent_data.get('progress_history', []),
                'thought_history': agent_data.get('thought_history', []),
                'future': agent_data.get('future', ''),
                'last_action': agent_data.get('last_action', ''),
                'pr_url': agent_data.get('pr_url', None) # Include pr_url
            }
        
        with open(CONFIG_FILE, 'w') as f:
            json.dump(data_to_save, f, indent=4)
    except Exception as e:
        logging.error(f"Error saving tasks: {e}", exc_info=True)

def delete_agent(agent_id):
    """Delete a specific agent and clean up its workspace."""
    try:
        logging.info(f"Deleting agent {agent_id}")
        tasks_data = load_tasks()
        if agent_id in tasks_data['agents']:
            agent_data = tasks_data['agents'][agent_id]
            if agent_id in aider_sessions:
                aider_sessions[agent_id].cleanup()
                del aider_sessions[agent_id]
            workspace = agent_data.get('workspace')
            if workspace and os.path.exists(workspace):
                try:
                    shutil.rmtree(workspace)
                except Exception as e:
                    logging.error(f"Could not remove workspace: {e}", exc_info=True)
            del tasks_data['agents'][agent_id]
            save_tasks(tasks_data)
            logging.info(f"Agent {agent_id} deleted")
            return True
        else:
            logging.warning(f"No agent found with ID {agent_id}")
            return False
    except Exception as e:
        logging.error(f"Error deleting agent: {e}", exc_info=True)
        return False

def cloneRepository(repository_url: str) -> bool:
    """Clone a Git repository."""
    try:
        logging.info(f"Cloning repository from {repository_url}")
        subprocess.check_call(["git", "clone", repository_url])
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Error cloning repository: {e}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error cloning repository: {e}")
        return False

def initialiseCodingAgent(repository_url: str = None, task_description: str = None, num_agents: int = None, aider_commands: str = None):
    """Initialise coding agents with configurable agent count."""
    logging.info("Starting agent initialization")
    num_agents = num_agents or DEFAULT_AGENTS_PER_TASK
    if not task_description:
        logging.error("No task description provided")
        return None
    created_agent_ids = []
    try:
        tasks_data = load_tasks()
        agent_config = tasks_data.get('config', {}).get('agent_session', {})
        for i in range(num_agents):
            agent_id = str(uuid.uuid4())
            agent_workspace = Path(tempfile.mkdtemp(prefix=f"agent_{agent_id}_")).resolve()
            workspace_dirs = {
                "src": agent_workspace / "src",
                "tests": agent_workspace / "tests", 
                "docs": agent_workspace / "docs", 
                "config": agent_workspace / "config", 
                "repo": agent_workspace / "repo"
            }
            for dir_path in workspace_dirs.values():
                dir_path.mkdir(parents=True, exist_ok=True)
            task_file = agent_workspace / "current_task.txt"
            task_file.write_text(task_description)
            original_dir = Path.cwd()
            repo_dir = None
            full_repo_path = None
            try:
                os.chdir(workspace_dirs["repo"])
                if not repository_url:
                    logging.error("No repository URL provided")
                    shutil.rmtree(agent_workspace)
                    continue
                repo_name = repository_url.rstrip('/').split('/')[-1]
                if repo_name.endswith('.git'):
                    repo_name = repo_name[:-4]
                if not cloneRepository(repository_url):
                    logging.error("Failed to clone repository")
                    shutil.rmtree(agent_workspace)
                    continue
                if not os.path.exists(repo_name) or not os.path.isdir(os.path.join(repo_name, '.git')):
                    logging.error(f"Repo dir {repo_name} not found or not a git repository")
                    shutil.rmtree(agent_workspace)
                    continue
                repo_dir = repo_name
                full_repo_path = workspace_dirs["repo"] / repo_dir
                full_repo_path = full_repo_path.resolve()
                os.chdir(full_repo_path)
                branch_name = f"agent-{agent_id[:8]}"
                try:
                    subprocess.check_call(f"git checkout -b {branch_name}", shell=True)
                except subprocess.CalledProcessError:
                    logging.error("Failed to create new branch", exc_info=True)
                    shutil.rmtree(agent_workspace)
                    continue
                aider_session = AgentSession(str(full_repo_path), task_description, agent_config, aider_commands=aider_commands)
                prompt_processor = PromptProcessor()
                if not aider_session.start():
                    logging.error("Failed to start aider session")
                    shutil.rmtree(agent_workspace)
                    continue
                aider_sessions[agent_id] = aider_session
                prompt_processors[agent_id] = prompt_processor
                agent_completion_events[agent_id] = threading.Event() # Initialize completion event
            finally:
                os.chdir(original_dir)
            tasks_data['agents'][agent_id] = {
                'workspace': normalize_path(agent_workspace),
                'repo_path': normalize_path(full_repo_path) if full_repo_path else None,
                'task': task_description,
                'status': 'pending',
                'created_at': datetime.datetime.now().isoformat(),
                'last_updated': datetime.datetime.now().isoformat(),
                'aider_output': '',
                'progress': '',
                'thought': '',
                'progress_history': [],
                'thought_history': [],
                'future': '',
                'last_action': '',
                'pr_url': None # Initialize pr_url
            }
            tasks_data['repository_url'] = repository_url
            save_tasks(tasks_data)
            created_agent_ids.append(agent_id)
        return created_agent_ids
    except Exception as e:
        logging.error(f"Error initializing coding agents: {e}", exc_info=True)

