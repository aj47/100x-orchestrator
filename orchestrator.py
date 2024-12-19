import os, json, traceback, subprocess, sys, uuid
from prompts import PROMPT_AIDER
from litellm_client import LiteLLMClient
from prompt_processor import PromptProcessor
from task_manager import load_tasks, save_tasks
from pathlib import Path
import shutil
import tempfile
from time import sleep
from litellm import completion
import threading
import datetime
import queue
import io
import errno
from github import Github
from dotenv import load_dotenv
from agent_session import AgentSession, normalize_path

DEFAULT_AGENTS_PER_TASK = 2
MODEL_NAME = os.environ.get('LITELLM_MODEL', 'anthropic/claude-3-5-sonnet-20240620')
CONFIG_FILE = Path("tasks/tasks.json")

CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
tools, available_functions = [], {}
MAX_TOOL_OUTPUT_LENGTH = 5000
CHECK_INTERVAL = 5

aider_sessions = {}
prompt_processors = {}

def delete_agent(agent_id):
    try:
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
                except Exception:
                    pass
            
            del tasks_data['agents'][agent_id]
            save_tasks(tasks_data)
            
            return True
        else:
            return False
    except Exception:
        return False

def initialiseCodingAgent(repository_url: str = None, task_description: str = None, num_agents: int = None, aider_commands: str = None):
    num_agents = num_agents or DEFAULT_AGENTS_PER_TASK
    
    if not task_description:
        return None
    
    created_agent_ids = []
    
    try:
        tasks_data = load_tasks()
        agent_config = tasks_data.get('config', {}).get('agent_session', {})
        
        # Get the structured acceptance criteria
        acceptance_criteria = tasks_data.get('acceptance_criteria', {
            "code_quality": [],
            "testing": [],
            "architecture": []
        })
        
        for _ in range(num_agents):
            agent_id = str(uuid.uuid4())
            agent_workspace = Path(tempfile.mkdtemp(prefix=f"agent_{agent_id}_")).resolve()

            # Define standard directories within the workspace
            workspace_dirs = {
                "src": agent_workspace / "src",
                "tests": agent_workspace / "tests",
                "docs": agent_workspace / "docs",
                "config": agent_workspace / "config",
                "repo": agent_workspace / "repo"
            }

            # Create directories
            for dir_path in workspace_dirs.values():
                dir_path.mkdir(parents=True, exist_ok=True)

            # Write the task description to a file in the workspace
            task_file = agent_workspace / "current_task.txt"
            task_file.write_text(task_description)

            original_dir = Path.cwd()
            repo_dir = None
            full_repo_path = None

            try:
                # Change to the repository directory within the workspace
                os.chdir(workspace_dirs["repo"])

                # Clone the repository if URL is provided
                if not repository_url:
                    logging.error("Repository URL is required for cloning.")
                    shutil.rmtree(agent_workspace)
                    continue

                repo_name = repository_url.rstrip('/').split('/')[-1]
                if repo_name.endswith('.git'):
                    repo_name = repo_name[:-4]

                if not cloneRepository(repository_url):
                    logging.error(f"Failed to clone repository: {repository_url}")
                    shutil.rmtree(agent_workspace)
                    continue

                # Check if repository was cloned successfully
                if not os.path.exists(repo_name) or not os.path.isdir(os.path.join(repo_name, '.git')):
                    logging.error(f"Repository directory '{repo_name}' not found or not a git repository.")
                    shutil.rmtree(agent_workspace)
                    continue

                repo_dir = repo_name
                full_repo_path = (workspace_dirs["repo"] / repo_dir).resolve()

                # Change to the cloned repository directory
                os.chdir(full_repo_path)

                # Create a new branch for the agent
                branch_name = f"agent-{agent_id[:8]}"
                try:
                    subprocess.check_call(f"git checkout -b {branch_name}", shell=True)
                except subprocess.CalledProcessError:
                    logging.error(f"Failed to create branch '{branch_name}'.")
                    shutil.rmtree(agent_workspace)
                    continue

                # Initialize an Aider session
                aider_session = AgentSession(str(full_repo_path), task_description, agent_config, aider_commands=aider_commands)
                prompt_processor = PromptProcessor()

                # Start the Aider session
                if not aider_session.start():
                    logging.error("Failed to start Aider session.")
                    shutil.rmtree(agent_workspace)
                    continue

                # Store the Aider session and prompt processor
                aider_sessions[agent_id] = aider_session
                prompt_processors[agent_id] = prompt_processor

            finally:
                # Change back to the original directory
                os.chdir(original_dir)

            # Store agent data
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
                'acceptance_criteria': acceptance_criteria
            }
            tasks_data['repository_url'] = repository_url
            save_tasks(tasks_data)

            created_agent_ids.append(agent_id)

        return created_agent_ids if created_agent_ids else None

    except Exception as e:
        logging.error(f"An error occurred during agent initialization: {e}")
        traceback.print_exc()
        return None

                repo_name = repository_url.rstrip('/').split('/')[-1]
                if repo_name.endswith('.git'):
                    repo_name = repo_name[:-4]
                
                if not cloneRepository(repository_url):
                    shutil.rmtree(agent_workspace)
                    continue
                
                if not os.path.exists(repo_name) or not os.path.isdir(os.path.join(repo_name, '.git')):
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
                    shutil.rmtree(agent_workspace)
                    continue

                aider_session = AgentSession(str(full_repo_path), task_description, agent_config, aider_commands=aider_commands)
                prompt_processor = PromptProcessor()
                
                if not aider_session.start():
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
                'acceptance_criteria': acceptance_criteria  # Use structured format
            }
            tasks_data['repository_url'] = repository_url
            save_tasks(tasks_data)
            
            created_agent_ids.append(agent_id)
        
        return created_agent_ids if created_agent_ids else None
        
    except Exception:
        return None

def get_github_token():
    load_dotenv()
    token = os.getenv('GITHUB_TOKEN')
    
    if not token:
        return None
        
    try:
        g = Github(token)
        g.get_user().login
        return token
    except Exception:
        return None

def create_pull_request(agent_id, branch_name, pr_info):
    try:
        token = get_github_token()
        if not token:
            return None
            
        g = Github(token)
        
        tasks_data = load_tasks()
        repo_url = tasks_data.get('repository_url', '')
        if not repo_url:
            return None

        agent_data = tasks_data['agents'].get(agent_id)
        if not agent_data:
            return None

        repo_path = agent_data.get('repo_path')
        if not repo_path:
            return None
            
        repo_parts = repo_url.rstrip('/').split('/')
        repo_name = '/'.join(repo_parts[-2:]).replace('.git', '')
        
        current_dir = os.getcwd()
        try:
            os.chdir(repo_path)
            subprocess.run(["git", "config", "user.name", "GitHub Actions"], check=True)
            subprocess.run(["git", "config", "user.email", "actions@github.com"], check=True)
            
            subprocess.run(["git", "add", "."], check=True)
            
            # Include acceptance criteria status in commit message
            commit_msg = f"Changes by Agent {agent_id}\n\nAcceptance Criteria Status:\n"
            criteria = agent_data.get('acceptance_criteria', {})
            for category, items in criteria.items():
                commit_msg += f"\n{category.replace('_', ' ').title()}:\n"
                for item in items:
                    commit_msg += f"- {item}\n"
            
            subprocess.run(["git", "commit", "-m", commit_msg], check=False)
            
            remote_url = f"https://x-access-token:{token}@github.com/{repo_name}.git"
            subprocess.run(["git", "remote", "set-url", "origin", remote_url], check=True)
            
            subprocess.run(["git", "push", "-u", "origin", branch_name], check=True)
        finally:
            os.chdir(current_dir)

        repo = g.get_repo(repo_name)
        
        # Include acceptance criteria in PR description
        pr_description = pr_info.get('description', 'Automated changes') + "\n\n## Acceptance Criteria Status\n"
        for category, items in criteria.items():
            pr_description += f"\n### {category.replace('_', ' ').title()}\n"
            for item in items:
                pr_description += f"- [ ] {item}\n"
        
        pr = repo.create_pull(
            title=pr_info.get('title', f'Changes by Agent {agent_id}'),
            body=pr_description,
            head=branch_name,
            base='main'
        )
        
        if pr_info.get('labels'):
            pr.add_to_labels(*pr_info['labels'])
        
        if pr_info.get('reviewers'):
            pr.create_review_request(reviewers=pr_info['reviewers'])
        
        return pr
        
    except Exception:
        return None

def cloneRepository(repository_url: str) -> bool:
    try:
        if not repository_url:
            return False
            
        result = subprocess.run(
            f"git clone --quiet {repository_url}",
            shell=True,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            return False
            
        return True
        
    except subprocess.SubprocessError:
        return False
    except Exception:
        return False

def update_agent_output(agent_id):
    try:
        tasks_data = load_tasks()
        agent_data = tasks_data['agents'].get(agent_id)
        
        if not agent_data:
            return False
            
        if agent_id in aider_sessions:
            output = aider_sessions[agent_id].get_output()
            agent_data['aider_output'] = output
            agent_data['last_updated'] = datetime.datetime.now().isoformat()
            save_tasks(tasks_data)
            return True
        
        return False
    
    except Exception:
        return False

def main_loop():
    while True:
        try:
            tasks_data = load_tasks()
                
            for agent_id in list(tasks_data['agents'].keys()):
                update_agent_output(agent_id)
                    
                if agent_id in aider_sessions:
                    agent_session: AgentSession = aider_sessions[agent_id]
                        
                    if agent_session.is_ready():
                        session_logs = agent_session.get_output()
                            
                        try:
                            litellm_client = LiteLLMClient()
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
                                    pass
                            
                            if agent_id in prompt_processors:
                                processor = prompt_processors[agent_id]
                                acceptance_criteria = tasks_data['agents'][agent_id].get('acceptance_criteria', {
                                    "code_quality": [],
                                    "testing": [],
                                    "architecture": []
                                })
                                action = processor.process_response(
                                    agent_id, 
                                    follow_up_message, 
                                    json.dumps(acceptance_criteria)  # Convert structured criteria to JSON string
                                )
                                
                                if agent_id in aider_sessions:
                                    action_message = f'<div class="output-line agent-action"><strong>[AGENT ACTION]:</strong> {action}</div>'
                                    aider_sessions[agent_id].output_buffer.write(action_message)
                                
                                if action == "/finish":
                                    pr_info = processor.get_agent_state(agent_id).get('pr_info')
                                    if pr_info:
                                        try:
                                            branch_name = f"agent-{agent_id[:8]}"
                                            pr = create_pull_request(agent_id, branch_name, pr_info)
                                            if pr:
                                                tasks_data['agents'][agent_id]['pr_url'] = pr.html_url
                                                tasks_data['agents'][agent_id]['status'] = 'completed'
                                                save_tasks(tasks_data)
                                        except Exception:
                                            pass
                                elif action:
                                    if agent_session.send_message(action):
                                        pass
                                        
                        except Exception:
                            pass
                
            sleep(CHECK_INTERVAL)
            
        except Exception:
            sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main_loop()
