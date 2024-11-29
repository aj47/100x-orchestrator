import os, json, traceback, subprocess, sys, uuid
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
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('aider_debug.log'),
        logging.StreamHandler()
    ]
)

# ANSI escape codes for color and formatting
class Colors:
    HEADER = '\033[95m'; OKBLUE = '\033[94m'; OKCYAN = '\033[96m'; OKGREEN = '\033[92m'
    WARNING = '\033[93m'; FAIL = '\033[91m'; ENDC = '\033[0m'; BOLD = '\033[1m'; UNDERLINE = '\033[4m'

# Configuration
DEFAULT_AGENTS_PER_TASK = 2
MODEL_NAME = os.environ.get('LITELLM_MODEL', 'anthropic/claude-3-5-sonnet-20240620')
CONFIG_FILE = Path("config.json")
tools, available_functions = [], {}
MAX_TOOL_OUTPUT_LENGTH = 5000  # Adjust as needed
CHECK_INTERVAL = 5  # Reduced to 30 seconds for more frequent updates

# Global dictionary to store aider sessions
aider_sessions = {}

def normalize_path(path_str):
    """Normalize a path string to absolute path with forward slashes."""
    if not path_str:
        return None
    try:
        # Convert to Path object and resolve to absolute path
        path = Path(path_str).resolve()
        # Convert to string with forward slashes
        normalized = str(path).replace('\\', '/')
        # Log both the input and output paths
        logging.debug(f"Path normalization: {path_str} -> {normalized}")
        return normalized
    except Exception as e:
        logging.error(f"Error normalizing path {path_str}: {e}")
        return None

def validate_agent_paths(agent_id, workspace_path):
    """Validate that an agent's paths match the given workspace path."""
    try:
        tasks_data = load_tasks()
        agent_data = tasks_data['agents'].get(agent_id)
        
        if not agent_data:
            logging.error(f"No agent found with ID {agent_id}")
            return False
            
        # Normalize all paths for comparison
        workspace_path = normalize_path(workspace_path)
        agent_workspace = normalize_path(agent_data.get('workspace'))
        agent_repo_path = normalize_path(agent_data.get('repo_path'))
        
        logging.info(f"Validating paths for agent {agent_id}:")
        logging.info(f"  Workspace path: {workspace_path}")
        logging.info(f"  Agent workspace: {agent_workspace}")
        logging.info(f"  Agent repo path: {agent_repo_path}")
        
        # Check if paths match
        matches_workspace = workspace_path == agent_workspace
        matches_repo = workspace_path == agent_repo_path
        
        logging.info(f"Path validation results for agent {agent_id}:")
        logging.info(f"  Matches workspace: {matches_workspace}")
        logging.info(f"  Matches repo path: {matches_repo}")
        
        return matches_workspace or matches_repo
        
    except Exception as e:
        logging.error(f"Error validating agent paths: {e}", exc_info=True)
        return False

class AiderSession:
    def __init__(self, workspace_path, task):
        self.workspace_path = normalize_path(workspace_path)
        self.task = task
        self.output_buffer = io.StringIO()
        self.process = None
        self.output_queue = queue.Queue()
        self._stop_event = threading.Event()
        self.session_id = str(uuid.uuid4())[:8]  # For logging
        logging.info(f"[Session {self.session_id}] Initialized with workspace: {self.workspace_path}")
        
        # Validate paths immediately
        for agent_id in aider_sessions:
            if validate_agent_paths(agent_id, self.workspace_path):
                logging.info(f"[Session {self.session_id}] Successfully validated paths for agent {agent_id}")
            else:
                logging.warning(f"[Session {self.session_id}] Path validation failed for agent {agent_id}")

    def start(self):
        """Start the aider session"""
        try:
            logging.info(f"[Session {self.session_id}] Starting aider session in workspace: {self.workspace_path}")
            
            # Create startupinfo to hide console window
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            # Start aider process with unbuffered output
            # cmd = f'aider --mini --message "{self.task}"'
            cmd = f'aider --version'
            logging.info(f"[Session {self.session_id}] Executing command: {cmd}")
            
            # Set up environment with forced unbuffering
            env = os.environ.copy()
            env['PYTHONUNBUFFERED'] = '1'
            env['PYTHONIOENCODING'] = 'utf-8'
            
            self.process = subprocess.Popen(
                cmd,
                shell=True,
                cwd=str(Path(self.workspace_path).resolve()),  # Ensure absolute path
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                startupinfo=startupinfo,
                text=True,
                bufsize=1,  # Line buffered
                universal_newlines=True,
                env=env
            )
            
            logging.info(f"[Session {self.session_id}] Process started with PID: {self.process.pid}")
            logging.info(f"[Session {self.session_id}] Working directory: {self.workspace_path}")

            # Start output reading threads
            stdout_thread = threading.Thread(
                target=self._read_output, 
                args=(self.process.stdout, "stdout"), 
                daemon=True,
                name=f"stdout-{self.session_id}"
            )
            stderr_thread = threading.Thread(
                target=self._read_output, 
                args=(self.process.stderr, "stderr"), 
                daemon=True,
                name=f"stderr-{self.session_id}"
            )
            process_thread = threading.Thread(
                target=self._process_output, 
                daemon=True,
                name=f"process-{self.session_id}"
            )
            
            stdout_thread.start()
            stderr_thread.start()
            process_thread.start()
            
            logging.info(f"[Session {self.session_id}] Started output processing threads")

            # Verify threads are running
            for thread in [stdout_thread, stderr_thread, process_thread]:
                if not thread.is_alive():
                    logging.error(f"[Session {self.session_id}] Thread {thread.name} failed to start")
                    return False
                logging.info(f"[Session {self.session_id}] Thread {thread.name} is running")

            return True
        except Exception as e:
            logging.error(f"[Session {self.session_id}] Failed to start aider session: {e}", exc_info=True)
            return False

    def _read_output(self, pipe, pipe_name):
        """Read output from a pipe and put it in the queue"""
        try:
            logging.info(f"[Session {self.session_id}] Started reading from {pipe_name}")
            for line in iter(pipe.readline, ''):
                if self._stop_event.is_set():
                    break
                logging.debug(f"[Session {self.session_id}] {pipe_name} received: {line.strip()}")
                self.output_queue.put(line)
                # Flush the pipe to ensure we get output immediately
                pipe.flush()
        except Exception as e:
            logging.error(f"[Session {self.session_id}] Error reading from {pipe_name}: {e}", exc_info=True)
        finally:
            try:
                pipe.close()
                logging.info(f"[Session {self.session_id}] Closed {pipe_name} pipe")
            except Exception as e:
                logging.error(f"[Session {self.session_id}] Error closing {pipe_name} pipe: {e}", exc_info=True)

    def _process_output(self):
        """Process output from the queue and write to buffer"""
        logging.info(f"[Session {self.session_id}] Started output processing thread")
        buffer_update_count = 0
        
        while not self._stop_event.is_set():
            try:
                # Reduced timeout for more frequent updates
                try:
                    line = self.output_queue.get(timeout=0.05)
                except queue.Empty:
                    continue
                
                # Lock for thread safety when updating buffer
                with threading.Lock():
                    self.output_buffer.seek(0, 2)  # Seek to end
                    self.output_buffer.write(line)
                    buffer_update_count += 1
                    
                    # Log buffer status
                    current_content = self.output_buffer.getvalue()
                    logging.debug(f"[Session {self.session_id}] Buffer update #{buffer_update_count}")
                    logging.debug(f"[Session {self.session_id}] Current buffer length: {len(current_content)}")
                    logging.debug(f"[Session {self.session_id}] Last line added: {line.strip()}")
                    
                    # Update tasks.json every 5 buffer updates or if line contains important content
                    if buffer_update_count % 5 == 0 or any(keyword in line for keyword in ['Error:', 'Warning:', 'Success:']):
                        self._update_output_in_tasks()
                        logging.debug(f"[Session {self.session_id}] Forced tasks.json update after {buffer_update_count} updates")
                
            except Exception as e:
                logging.error(f"[Session {self.session_id}] Error processing output: {e}", exc_info=True)
                # Don't break on error, try to continue processing
                continue

    def _update_output_in_tasks(self):
        """Update the output in tasks.json"""
        try:
            tasks_data = load_tasks()
            updated = False
            current_output = self.get_output()
            
            # Log the output being saved
            logging.debug(f"[Session {self.session_id}] Attempting to save output (length: {len(current_output)})")
            logging.debug(f"[Session {self.session_id}] Current workspace path: {self.workspace_path}")
            
            # Normalize current workspace path
            current_workspace = normalize_path(self.workspace_path)
            
            # First try to find agent by matching session ID with agent ID
            matching_agent_id = None
            for agent_id, session in aider_sessions.items():
                if session.session_id == self.session_id:
                    matching_agent_id = agent_id
                    break
            
            if matching_agent_id:
                logging.debug(f"[Session {self.session_id}] Found matching agent by session ID: {matching_agent_id}")
                agent_data = tasks_data['agents'].get(matching_agent_id)
                if agent_data:
                    # Update the repo_path if it's not set
                    if not agent_data.get('repo_path'):
                        agent_data['repo_path'] = current_workspace
                        logging.info(f"[Session {self.session_id}] Updated repo_path for agent {matching_agent_id}")
                    
                    # Update output
                    if current_output != agent_data.get('aider_output', ''):
                        agent_data['aider_output'] = current_output
                        agent_data['last_updated'] = datetime.datetime.now().isoformat()
                        updated = True
                        logging.info(f"[Session {self.session_id}] Updated output for agent {matching_agent_id}")
            else:
                # Fall back to path matching if session ID matching fails
                for agent_id, agent_data in tasks_data['agents'].items():
                    # Normalize agent paths
                    agent_workspace = normalize_path(agent_data.get('workspace'))
                    agent_repo_path = normalize_path(agent_data.get('repo_path'))
                    
                    # Log comparison details
                    logging.debug(f"[Session {self.session_id}] Comparing paths for agent {agent_id}:")
                    logging.debug(f"Current workspace: {current_workspace}")
                    logging.debug(f"Agent workspace: {agent_workspace}")
                    logging.debug(f"Agent repo_path: {agent_repo_path}")
                    
                    # Update repo_path if it matches workspace but repo_path isn't set
                    if current_workspace == agent_workspace and not agent_repo_path:
                        agent_data['repo_path'] = current_workspace
                        logging.info(f"[Session {self.session_id}] Updated repo_path for agent {agent_id}")
                    
                    # Check if either path matches
                    if current_workspace in [agent_workspace, agent_repo_path]:
                        logging.debug(f"[Session {self.session_id}] Found matching agent: {agent_id}")
                        
                        # Only update if output has changed
                        if current_output != agent_data.get('aider_output', ''):
                            agent_data['aider_output'] = current_output
                            agent_data['last_updated'] = datetime.datetime.now().isoformat()
                            updated = True
                            logging.info(f"[Session {self.session_id}] Updated output for agent {agent_id}")
                        break
            
            if updated:
                save_tasks(tasks_data)
                logging.info(f"[Session {self.session_id}] Saved updated output to tasks.json")
            else:
                logging.warning(f"[Session {self.session_id}] No matching agent found for workspace {current_workspace}")
                # Log all workspace paths for debugging
                logging.debug("Available agent paths:")
                for aid, adata in tasks_data['agents'].items():
                    logging.debug(f"Agent {aid}:")
                    logging.debug(f"  workspace: {normalize_path(adata.get('workspace'))}")
                    logging.debug(f"  repo_path: {normalize_path(adata.get('repo_path'))}")
                    
        except Exception as e:
            logging.error(f"[Session {self.session_id}] Error updating output in tasks: {e}", exc_info=True)

    def get_output(self):
        """Get the current output buffer contents"""
        try:
            # Save current position
            pos = self.output_buffer.tell()
            # Go to beginning
            self.output_buffer.seek(0)
            # Read all content
            output = self.output_buffer.read()
            # Restore position
            self.output_buffer.seek(pos)
            
            logging.debug(f"[Session {self.session_id}] Retrieved output (length: {len(output)})")
            logging.debug(f"[Session {self.session_id}] Output preview: {output[:200]}...")  # Log preview of output
            return output
        except Exception as e:
            logging.error(f"[Session {self.session_id}] Error getting output: {e}", exc_info=True)
            return ""

    def cleanup(self):
        """Clean up the aider session"""
        try:
            logging.info(f"[Session {self.session_id}] Starting cleanup")
            self._stop_event.set()
            if self.process:
                logging.info(f"[Session {self.session_id}] Terminating process {self.process.pid}")
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                    logging.info(f"[Session {self.session_id}] Process terminated successfully")
                except subprocess.TimeoutExpired:
                    logging.warning(f"[Session {self.session_id}] Process did not terminate, forcing kill")
                    self.process.kill()
            logging.info(f"[Session {self.session_id}] Cleanup completed")
        except Exception as e:
            logging.error(f"[Session {self.session_id}] Error during cleanup: {e}", exc_info=True)

def load_tasks():
    """Load config from config.json."""
    try:
        with open(CONFIG_FILE, 'r') as f:
            data = json.load(f)
            if 'repository_url' not in data:
                data['repository_url'] = ""
                
            # Normalize paths in loaded data
            for agent_id, agent_data in data.get('agents', {}).items():
                if 'workspace' in agent_data:
                    agent_data['workspace'] = normalize_path(agent_data['workspace'])
                if 'repo_path' in agent_data:
                    agent_data['repo_path'] = normalize_path(agent_data['repo_path'])
                    
                # Log the normalized paths
                logging.debug(f"Loaded agent {agent_id} with normalized paths:")
                logging.debug(f"  workspace: {agent_data.get('workspace')}")
                logging.debug(f"  repo_path: {agent_data.get('repo_path')}")
                
            logging.debug(f"Loaded tasks data: {json.dumps(data, indent=2)}")
            return data
    except FileNotFoundError:
        logging.info("tasks.json not found, creating new data structure")
        return {
            "tasks": [],
            "agents": {},
            "repository_url": ""
        }
    except json.JSONDecodeError:
        logging.error("Error decoding tasks.json", exc_info=True)
        return {
            "tasks": [],
            "agents": {},
            "repository_url": ""
        }

def save_tasks(tasks_data):
    """Save tasks to tasks.json."""
    try:
        # Create a copy of the data to avoid modifying the original
        data_to_save = {
            "tasks": tasks_data.get("tasks", []),
            "agents": {},
            "repository_url": tasks_data.get("repository_url", "")
        }
        
        # Copy agent data without the session object and normalize paths
        for agent_id, agent_data in tasks_data.get("agents", {}).items():
            data_to_save["agents"][agent_id] = {
                'workspace': normalize_path(agent_data.get('workspace')),
                'repo_path': normalize_path(agent_data.get('repo_path')),
                'task': agent_data.get('task'),
                'status': agent_data.get('status'),
                'created_at': agent_data.get('created_at'),
                'last_updated': agent_data.get('last_updated'),
                'aider_output': agent_data.get('aider_output', ''),
                'last_critique': agent_data.get('last_critique')
            }
            
            # Log the normalized paths
            logging.debug(f"Saving agent {agent_id} with normalized paths:")
            logging.debug(f"  workspace: {data_to_save['agents'][agent_id]['workspace']}")
            logging.debug(f"  repo_path: {data_to_save['agents'][agent_id]['repo_path']}")
        
        logging.debug(f"Saving tasks data: {json.dumps(data_to_save, indent=2)}")
        with open(CONFIG_FILE, 'w') as f:
            json.dump(data_to_save, f, indent=4)
        logging.info("Successfully saved tasks data")
    except Exception as e:
        logging.error(f"Error saving tasks: {e}", exc_info=True)

def delete_agent(agent_id):
    """Delete a specific agent and clean up its workspace."""
    try:
        logging.info(f"Attempting to delete agent {agent_id}")
        tasks_data = load_tasks()
        
        # Find and remove the agent
        if agent_id in tasks_data['agents']:
            agent_data = tasks_data['agents'][agent_id]
            logging.info(f"Found agent {agent_id} in tasks data")
            
            # Cleanup aider session if it exists
            if agent_id in aider_sessions:
                logging.info(f"Cleaning up aider session for agent {agent_id}")
                aider_sessions[agent_id].cleanup()
                del aider_sessions[agent_id]
            
            # Remove workspace directory if it exists
            workspace = agent_data.get('workspace')
            if workspace and os.path.exists(workspace):
                try:
                    shutil.rmtree(workspace)
                    logging.info(f"Removed workspace for agent {agent_id}: {workspace}")
                except Exception as e:
                    logging.error(f"Could not remove workspace: {e}", exc_info=True)
            
            # Remove agent from tasks data
            del tasks_data['agents'][agent_id]
            save_tasks(tasks_data)
            
            logging.info(f"Successfully deleted agent {agent_id}")
            return True
        else:
            logging.warning(f"No agent found with ID {agent_id}")
            return False
    except Exception as e:
        logging.error(f"Error deleting agent: {e}", exc_info=True)
        return False

def initialiseCodingAgent(repository_url: str = None, task_description: str = None, num_agents: int = None):
    """Initialise coding agents with configurable agent count."""
    logging.info("Starting agent initialization")
    logging.debug(f"Parameters: repo_url={repository_url}, task={task_description}, num_agents={num_agents}")
    
    # Use provided num_agents or get default from config
    num_agents = num_agents or DEFAULT_AGENTS_PER_TASK
    
    # Validate input
    if not task_description:
        logging.error("No task description provided")
        return None
    
    # Track created agent IDs
    created_agent_ids = []
    
    try:
        # Load tasks data to get repository URL
        tasks_data = load_tasks()
        if repository_url:
            tasks_data['repository_url'] = repository_url
            save_tasks(tasks_data)
            logging.info(f"Updated repository URL: {repository_url}")
        else:
            repository_url = tasks_data.get('repository_url')
            logging.info(f"Using existing repository URL: {repository_url}")
        
        for i in range(num_agents):
            logging.info(f"Creating agent {i+1} of {num_agents}")
            
            # Generate unique agent ID
            agent_id = str(uuid.uuid4())
            logging.info(f"Generated agent ID: {agent_id}")
            
            # Create temporary workspace directory with absolute path
            agent_workspace = Path(tempfile.mkdtemp(prefix=f"agent_{agent_id}_")).resolve()
            logging.info(f"Created workspace at: {agent_workspace}")
            
            # Create standard directory structure
            workspace_dirs = {
                "src": agent_workspace / "src",
                "tests": agent_workspace / "tests", 
                "docs": agent_workspace / "docs", 
                "config": agent_workspace / "config", 
                "repo": agent_workspace / "repo"
            }
            
            # Create all directories
            for dir_path in workspace_dirs.values():
                dir_path.mkdir(parents=True, exist_ok=True)
            logging.info("Created workspace directory structure")
                
            # Create task file in agent workspace
            task_file = agent_workspace / "current_task.txt"
            task_file.write_text(task_description)
            logging.info("Created task file")
            
            # Store current directory
            original_dir = Path.cwd()
            repo_dir = None
            full_repo_path = None
            
            try:
                # Clone repository into repo subdirectory
                os.chdir(workspace_dirs["repo"])
                if not repository_url:
                    logging.error("No repository URL provided")
                    shutil.rmtree(agent_workspace)
                    continue
                
                logging.info(f"Cloning repository: {repository_url}")
                if not cloneRepository(repository_url):
                    logging.error("Failed to clone repository")
                    shutil.rmtree(agent_workspace)
                    continue
                
                # Get the cloned repository directory name
                repo_dirs = [d for d in os.listdir('.') if os.path.isdir(d) and not d.startswith('.')]
                if not repo_dirs:
                    logging.error("No repository directory found after cloning")
                    shutil.rmtree(agent_workspace)
                    continue
                
                repo_dir = repo_dirs[0]
                full_repo_path = workspace_dirs["repo"] / repo_dir
                full_repo_path = full_repo_path.resolve()  # Get absolute path
                logging.info(f"Repository cloned to: {full_repo_path}")
                
                # Change to the cloned repository directory
                os.chdir(full_repo_path)
                
                # Create and checkout new branch
                branch_name = f"agent-{agent_id[:8]}"
                try:
                    subprocess.check_call(f"git checkout -b {branch_name}", shell=True)
                    logging.info(f"Created and checked out branch: {branch_name}")
                except subprocess.CalledProcessError:
                    logging.error("Failed to create new branch", exc_info=True)
                    shutil.rmtree(agent_workspace)
                    continue

                # Initialize aider session with absolute path
                logging.info("Initializing aider session")
                aider_session = AiderSession(str(full_repo_path), task_description)
                if not aider_session.start():
                    logging.error("Failed to start aider session")
                    shutil.rmtree(agent_workspace)
                    continue

                # Store session in global dictionary
                aider_sessions[agent_id] = aider_session
                logging.info("Aider session started successfully")

            finally:
                # Always return to original directory
                os.chdir(original_dir)
            
            # Update tasks.json with new agent using absolute paths
            tasks_data['agents'][agent_id] = {
                'workspace': normalize_path(agent_workspace),
                'repo_path': normalize_path(full_repo_path) if full_repo_path else None,
                'task': task_description,
                'status': 'pending',
                'created_at': datetime.datetime.now().isoformat(),
                'last_updated': datetime.datetime.now().isoformat(),
                'aider_output': ''  # Initialize empty output
            }
            save_tasks(tasks_data)
            
            logging.info(f"Successfully initialized agent {agent_id}")
            created_agent_ids.append(agent_id)
        
        return created_agent_ids if created_agent_ids else None
        
    except Exception as e:
        logging.error(f"Error initializing coding agents: {e}", exc_info=True)
        return None

def cloneRepository(repository_url: str) -> bool:
    """Clone git repository using subprocess.check_call."""
    try:
        if not repository_url:
            logging.error("No repository URL provided")
            return False
        logging.info(f"Cloning repository: {repository_url}")
        subprocess.check_call(f"git clone {repository_url}", shell=True)
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Git clone failed with exit code {e.returncode}", exc_info=True)
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
            
        # Update aider output if session exists
        if agent_id in aider_sessions:
            output = aider_sessions[agent_id].get_output()
            agent_data['aider_output'] = output
            agent_data['last_updated'] = datetime.datetime.now().isoformat()
            logging.debug(f"Updated aider output (length: {len(output)})")
            save_tasks(tasks_data)
            return True
        
        return False
    
    except Exception as e:
        logging.error(f"Error updating agent output: {e}", exc_info=True)
        return False

def main_loop():
    """Main orchestration loop to manage agents."""
    logging.info("Starting main orchestration loop")
    while True:
        try:
            # Load current tasks and agents
            tasks_data = load_tasks()
            
            # Update each agent's output
            for agent_id in list(tasks_data['agents'].keys()):
                logging.info(f"Checking agent {agent_id}")
                update_agent_output(agent_id)
            
            # Wait before next check
            logging.info(f"Waiting {CHECK_INTERVAL} seconds before next check")
            sleep(CHECK_INTERVAL)
        
        except Exception as e:
            logging.error(f"Error in main loop: {e}", exc_info=True)
            sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    logging.info("Starting orchestrator")
    main_loop()
