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
                'pr_url': agent_data.get('pr_url') # Include pr_url
            }
        
        with open(CONFIG_FILE, 'w') as f:
            json.dump(data_to_save, f, indent=4)
        logging.info("tasks data saved")
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
                    logging.info(f"Removed workspace for agent {agent_id}")
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
                logging.info(f"Cloning {repository_url}")
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
                    logging.info(f"Created branch {branch_name}")
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
        return None

def get_github_token():
    """Get GitHub token from environment"""
    load_dotenv()
    token = os.getenv('GITHUB_TOKEN')
    if not token:
        logging.error("No GitHub token found in environment")
        return None
    try:
        g = Github(token)
        g.get_user().login
        return token
    except Exception as e:
        logging.error(f"Invalid GitHub token: {e}")
        return None

def create_pull_request(agent_id, branch_name, pr_info):
    """Create a pull request for the agent's changes"""
    try:
        token = get_github_token()
        if not token:
            return None
        g = Github(token)
        tasks_data = load_tasks()
        repo_url = tasks_data.get('repository_url', '')
        if not repo_url:
            logging.error("No repository URL found")
            return None
        agent_data = tasks_data['agents'].get(agent_id)
        if not agent_data:
            logging.error(f"No agent data found for {agent_id}")
            return None
        repo_path = agent_data.get('repo_path')
        if not repo_path:
            logging.error("No repo path found for agent")
            return None
        repo_parts = repo_url.rstrip('/').split('/')
        repo_name = '/'.join(repo_parts[-2:]).replace('.git', '')
        current_dir = os.getcwd()
        try:
            os.chdir(repo_path)
            subprocess.run(["git", "config", "user.name", "GitHub Actions"], check=True)
            subprocess.run(["git", "config", "user.email", "actions@github.com"], check=True)
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(["git", "commit", "-m", f"Changes by Agent {agent_id}"], check=False)
            remote_url = f"https://x-access-token:{token}@github.com/{repo_name}.git"
            subprocess.run(["git", "remote", "set-url", "origin", remote_url], check=True)
            subprocess.run(["git", "push", "-u", "origin", branch_name], check=True)
        finally:
            os.chdir(current_dir)
        repo = g.get_repo(repo_name)
        pr = repo.create_pull(
            title=pr_info.get('title', f'Changes by Agent {agent_id}'),
            body=pr_info.get('description', 'Automated changes'),
            head=branch_name,
            base='main'
        )
        pr_url = pr.html_url
        if pr_info.get('labels'):
            pr.add_to_labels(*pr_info['labels'])
        if pr_info.get('reviewers'):
            pr.create_review_request(reviewers=pr_info['reviewers'])
        return pr_url
    except Exception as e:
        logging.error(f"Error creating pull request: {e}")
        return None

def cloneRepository(repository_url: str) -> bool:
    """Clone git repository using subprocess.check_call."""
    try:
        if not repository_url:
            logging.error("No repository URL provided")
            return False
        logging.info(f"Cloning {repository_url}")
        result = subprocess.run(
            f"git clone --quiet {repository_url}",
            shell=True,
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            logging.error(f"Git clone failed: {result.stderr}")
            return False
        return True
    except subprocess.SubprocessError as e:
        logging.error(f"Git clone failed: {str(e)}", exc_info=True)
        return False
    except Exception as e:
        logging.error(f"Unexpected error during clone: {str(e)}", exc_info=True)
        return False

def update_agent_output(agent_id):
    """Update the output for a specific agent."""
    try:
        logging.info(f"Updating output for agent {agent_id}")
        tasks_data = load_tasks()
        agent_data = tasks_data['agents'].get(agent_id)
        if not agent_data:
            logging.error(f"No agent found with ID {agent_id}")
            return False
        if agent_id in aider_sessions:
            output = aider_sessions[agent_id].get_output()
            agent_data['aider_output'] = output
            agent_data['last_updated'] = datetime.datetime.now().isoformat()
            save_tasks(tasks_data)
            return True
        return False
    except Exception as e:
        logging.error(f"Error updating agent output: {e}", exc_info=True)
        return False

def main_loop():
    """Main orchestration loop to manage agents."""
    logging.info("Starting main loop")
    while True:
        try:
            tasks_data = load_tasks()
            for agent_id in list(tasks_data['agents'].keys()):
                logging.info(f"Checking agent {agent_id}")
                update_agent_output(agent_id)
                if agent_id in aider_sessions:
                    agent_session: AgentSession = aider_sessions[agent_id]
                    if agent_session.is_ready():
                        session_logs = agent_session.get_output()
                        try:
                            litellm_client = LiteLLMClient()
                            #if session_logs is empty or only newlines. replace it with "*aider started*"
                            if not session_logs or session_logs.isspace():
                                session_logs = "*aider started*"
                            follow_up_message = litellm_client.chat_completion(
                                PROMPT_AIDER(agent_session.task),
                                session_logs
                            )
                            if agent_id in tasks_data['agents']:
                                try:
                                    follow_up_data = json.loads(follow_up_message)
                                    current_time = datetime.datetime.now().isoformat()
                                    if 'progress_history' not in tasks_data['agents'][agent_id]:
                                        tasks_data['agents'][agent_id]['progress_history'] = []
                                    if 'thought_history' not in tasks_data['agents'][agent_id]:
                                        tasks_data['agents'][agent_id]['thought_history'] = []
                                    if follow_up_data.get('progress'):
                                        tasks_data['agents'][agent_id]['progress'] = follow_up_data['progress']
                                        tasks_data['agents'][agent_id]['progress_history'].append({
                                            'timestamp': current_time,
                                            'content': follow_up_data['progress']
                                        })
                                    if follow_up_data.get('thought'):
                                        tasks_data['agents'][agent_id]['thought'] = follow_up_data['thought']
                                        tasks_data['agents'][agent_id]['thought_history'].append({
                                            'timestamp': current_time,
                                            'content': follow_up_data['thought']
                                        })
                                    tasks_data['agents'][agent_id].update({
                                        'future': follow_up_data.get('future', ''),
                                        'last_action': follow_up_data.get('action', ''),
                                        'last_updated': current_time
                                    })
                                    save_tasks(tasks_data)
                                except json.JSONDecodeError:
                                    logging.error(f"Invalid JSON in follow_up_message: {follow_up_message}")
                            if agent_id