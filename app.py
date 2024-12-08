import eventlet
# Monkey patch before importing other modules for async I/O
eventlet.monkey_patch()

import os
import json
import threading
import datetime
import uuid
import shutil
import tempfile
import subprocess
import sys
import time
import io
import logging
import traceback
import stat
from pathlib import Path
from dotenv import load_dotenv

from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
from shutil import which

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

BASE_DIR = Path(__file__).parent.resolve()
TASKS_DIR = BASE_DIR / "tasks"
CONFIG_FILE = TASKS_DIR / "tasks.json"
thread_lock = threading.Lock()

CHECK_INTERVAL = 5
NO_OUTPUT_TIMEOUT = 60

aider_sessions = {}

REQUIRED_ENV_VARS = ['OPENAI_API_KEY']
DEFAULT_HOST = os.getenv('HOST', '127.0.0.1')
DEFAULT_PORT = int(os.getenv('PORT', 5000))

env_issues = []
for var in REQUIRED_ENV_VARS:
    if not os.getenv(var):
        env_issues.append(f"Missing required environment variable: {var}")

aider_in_path = bool(which("aider"))
if not aider_in_path:
    env_issues.append("`aider` not found in PATH. Please ensure aider is installed and in PATH.")

def ensure_tasks_file():
    """Ensure the tasks.json file exists with base structure."""
    TASKS_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_FILE.exists():
        data = {"tasks": [], "agents": {}, "repository_url": ""}
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)

def load_tasks():
    """Load tasks and agents data from tasks.json, returning a dictionary."""
    ensure_tasks_file()
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if 'repository_url' not in data:
                data['repository_url'] = ""
            return data
    except Exception:
        return {"tasks": [], "agents": {}, "repository_url": ""}

def save_tasks(data):
    """Save tasks and agent data to tasks.json file."""
    ensure_tasks_file()
    final_data = {
        "tasks": data.get("tasks", []),
        "agents": {},
        "repository_url": data.get("repository_url", "")
    }
    # Save minimal agent info
    for agent_id, agent_data in data.get("agents", {}).items():
        final_data["agents"][agent_id] = {
            'workspace': agent_data.get('workspace'),
            'repo_path': agent_data.get('repo_path'),
            'task': agent_data.get('task'),
            'status': agent_data.get('status'),
            'created_at': agent_data.get('created_at'),
            'last_updated': agent_data.get('last_updated'),
            'aider_output': agent_data.get('aider_output', ''),
            'last_critique': agent_data.get('last_critique'),
            'session_id': agent_data.get('session_id'),
            'last_error': agent_data.get('last_error')
        }
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, indent=4)
    logging.info("Tasks saved successfully.")

def normalize_path(path_str):
    """Safely resolve and return the absolute path, or None if invalid."""
    if not path_str:
        return None
    try:
        path = Path(path_str).resolve()
        return str(path)
    except:
        return None

def make_writable(path: str):
    """Remove read-only attributes from all files and dirs inside 'path'."""
    for root, dirs, files in os.walk(path):
        for d in dirs:
            dpath = os.path.join(root, d)
            os.chmod(dpath, stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)
        for f in files:
            fpath = os.path.join(root, f)
            os.chmod(fpath, stat.S_IWRITE | stat.S_IREAD)

def cleanup_workspace(workspace_path, max_retries=5):
    """
    Attempt to clean up the agent workspace, retrying multiple times if 
    file locks occur. Make files writable before removal.
    """
    if not workspace_path:
        return True
    logging.info(f"Attempting to clean up workspace: {workspace_path}")
    for attempt in range(max_retries):
        try:
            if os.path.exists(workspace_path):
                make_writable(workspace_path)
                shutil.rmtree(workspace_path, ignore_errors=False)
            if not os.path.exists(workspace_path):
                logging.info(f"Workspace {workspace_path} removed successfully.")
                return True
            logging.warning(f"Workspace still exists after attempt {attempt+1}, retrying...")
            # Exponential backoff for retries
            time.sleep(2 ** attempt)
        except Exception as e:
            logging.warning(f"Cleanup attempt {attempt+1} failed: {e}")
            time.sleep(2 ** attempt)
    logging.error(f"Failed to cleanup workspace after {max_retries} attempts.")
    return False

def handle_agent_error(agent_id, error_msg, log_output=None):
    """Handle errors by updating agent status, logging, and cleaning up workspace."""
    logging.error(f"Agent {agent_id} error: {error_msg}")
    if log_output:
        logging.error(f"Captured output:\n{log_output}")
    tasks_data = load_tasks()
    if agent_id in tasks_data['agents']:
        changed = False
        if tasks_data['agents'][agent_id]['status'] != 'error':
            tasks_data['agents'][agent_id]['status'] = 'error'
            changed = True
        if tasks_data['agents'][agent_id].get('last_error') != error_msg:
            tasks_data['agents'][agent_id]['last_error'] = error_msg
            changed = True
        workspace = tasks_data['agents'][agent_id].get('workspace')
        if workspace and os.path.exists(workspace):
            # Ensure session is stopped
            if agent_id in aider_sessions:
                aider_sessions[agent_id].cleanup()
            cleanup_workspace(workspace)
            tasks_data['agents'][agent_id]['workspace'] = None
            changed = True
        if changed:
            save_tasks(tasks_data)

        # Notify frontend
        socketio.emit('agent_error', {
            'error': error_msg,
            'agent_id': agent_id,
            'timestamp': datetime.datetime.now().isoformat()
        }, namespace='/')
        socketio.emit('agent_status_update', {
            'agent_id': agent_id,
            'status': 'error',
            'state_info': {},
            'last_updated': datetime.datetime.now().isoformat()
        }, namespace='/')

def initialise_orchestrator(tasks_data):
    """Ensure the orchestrator agent exists to represent top-level management."""
    if 'orchestrator' not in tasks_data['agents']:
        tasks_data['agents']['orchestrator'] = {
            'task': 'Master Orchestrator Agent: Manages and monitors other agents.',
            'status': 'completed',
            'created_at': datetime.datetime.now().isoformat(),
            'last_updated': datetime.datetime.now().isoformat(),
            'aider_output': '',
            'last_critique': None,
            'session_id': None,
            'workspace': None,
            'repo_path': None,
            'last_error': None
        }
        save_tasks(tasks_data)
        logging.info("Orchestrator agent initialized.")

def mark_abandoned_agents(tasks_data):
    """
    Mark agents with no active sessions and not completed/error as abandoned.
    This runs periodically before rendering the agent view.
    """
    changed = False
    for agent_id, agent in tasks_data.get('agents', {}).items():
        if agent_id == 'orchestrator':
            continue
        status = agent.get('status', 'pending')
        if status not in ['completed', 'error', 'abandoned']:
            session_active = any(sid_agent_id == agent_id and session.stream_status['stream_active']
                                 for sid_agent_id, session in aider_sessions.items())
            if not session_active:
                agent['status'] = 'abandoned'
                if not agent.get('last_error'):
                    agent['last_error'] = "No active session found and agent produced no output."
                logging.warning(f"Agent {agent_id} marked as abandoned.")
                changed = True
    if changed:
        save_tasks(tasks_data)

def cloneRepository(repository_url: str) -> bool:
    """Clone the repository from the given URL. Return True if successful."""
    if not repository_url:
        return False
    try:
        subprocess.check_call(["git", "clone", repository_url], shell=False)
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to clone repository: {e}")
        return False
    except Exception as e:
        logging.error(f"Exception cloning repository: {e}")
        return False

def update_agent_output(agent_id):
    """Update the agent's recorded output if it has changed."""
    tasks_data = load_tasks()
    agent_data = tasks_data['agents'].get(agent_id)
    if not agent_data:
        return False
    if agent_id in aider_sessions:
        output = aider_sessions[agent_id].get_output()
        if agent_data.get('aider_output') != output:
            agent_data['aider_output'] = output
            agent_data['last_updated'] = datetime.datetime.now().isoformat()
            save_tasks(tasks_data)
        return True
    return False

def delete_agent(agent_id):
    """Delete an agent, cleaning up workspace and session."""
    logging.info(f"Attempting to delete agent {agent_id}")
    tasks_data = load_tasks()
    if agent_id in tasks_data['agents']:
        if agent_id == 'orchestrator':
            return False
        if agent_id in aider_sessions:
            aider_sessions[agent_id].cleanup()
            del aider_sessions[agent_id]
        workspace = tasks_data['agents'][agent_id].get('workspace')
        if workspace and os.path.exists(workspace):
            cleanup_workspace(workspace)
        del tasks_data['agents'][agent_id]
        save_tasks(tasks_data)
        logging.info(f"Agent {agent_id} deleted successfully.")
        return True
    logging.warning(f"Agent {agent_id} not found.")
    return False

def check_aider_availability():
    """Check if 'aider' is available in PATH."""
    if not aider_in_path:
        logging.error("`aider` is not available in PATH.")
        return False
    try:
        version_out = subprocess.check_output(["aider", "--version"], text=True)
        logging.info(f"aider version: {version_out.strip()}")
        return True
    except Exception as e:
        logging.error(f"Failed to run `aider --version`: {e}")
        return False

def gather_repo_files(repo_path):
    """Gather a limited set of repo files (up to 20) to pass to aider."""
    repo_path = Path(repo_path).resolve()
    patterns = ["*.html", "*.py", "*.js", "*.css"]
    files = []
    for pattern in patterns:
        for f in repo_path.rglob(pattern):
            if repo_path in f.resolve().parents:
                files.append(f)
    return [str(f.relative_to(repo_path)) for f in files[:20]]

def initialiseCodingAgent(repository_url: str = None, task_description: str = None, num_agents: int = None):
    """
    Initialize one or more coding agents for a given repository and task.
    Returns a list of created agent IDs or None if failed.
    """
    if not task_description:
        logging.error("No task description provided.")
        return None
    if env_issues:
        logging.error("Environment issues prevent starting agents: " + "; ".join(env_issues))
        return None
    if not check_aider_availability():
        logging.error("Aider not available or not functioning. Cannot initialize agents.")
        return None

    created_agent_ids = []
    tasks_data = load_tasks()
    if repository_url:
        tasks_data['repository_url'] = repository_url
        save_tasks(tasks_data)
    else:
        repository_url = tasks_data.get('repository_url')

    initialise_orchestrator(tasks_data)
    num_agents = num_agents or 1

    for i in range(num_agents):
        current_agent_id = str(uuid.uuid4())
        logging.info(f"Initializing agent {current_agent_id} for task: {task_description}")
        tasks_data = load_tasks()
        tasks_data['agents'][current_agent_id] = {
            'task': task_description,
            'status': 'initializing',
            'created_at': datetime.datetime.now().isoformat(),
            'last_updated': datetime.datetime.now().isoformat(),
            'aider_output': '',
            'session_id': None,
            'last_error': None,
            'workspace': None,
            'repo_path': None,
            'last_critique': None
        }
        save_tasks(tasks_data)

        current_workspace = None
        original_cwd = os.getcwd()
        try:
            current_workspace = Path(tempfile.mkdtemp(prefix=f"agent_{current_agent_id}_", dir=str(BASE_DIR))).resolve()
            logging.info(f"Created workspace: {current_workspace} for agent {current_agent_id}")

            for d in ["src", "tests", "docs", "config", "repo"]:
                (current_workspace / d).mkdir(parents=True, exist_ok=True)

            tasks_data = load_tasks()
            tasks_data['agents'][current_agent_id]['workspace'] = str(current_workspace)
            tasks_data['agents'][current_agent_id]['repo_path'] = None
            save_tasks(tasks_data)

            # Write the current task to a file
            task_file = current_workspace / "current_task.txt"
            task_file.write_text(task_description, encoding='utf-8')

            agent_repo_path = current_workspace / "repo"
            os.chdir(agent_repo_path)
            logging.info(f"Cloning repository: {repository_url}")
            repo_success = False
            for attempt in range(3):
                if repository_url and cloneRepository(repository_url):
                    repo_success = True
                    break
                time.sleep(1)
            if not repo_success:
                raise Exception("Failed to clone repository")

            repo_dirs = [d for d in os.listdir('.') if os.path.isdir(d) and not d.startswith('.')]
            if not repo_dirs:
                raise Exception("No repository directory found after cloning.")
            repo_dir = repo_dirs[0]
            full_repo_path = (agent_repo_path / repo_dir).resolve()

            tasks_data = load_tasks()
            tasks_data['agents'][current_agent_id]['repo_path'] = str(full_repo_path)
            save_tasks(tasks_data)

            os.chdir(full_repo_path)
            branch_name = f"agent-{current_agent_id[:8]}"
            try:
                subprocess.check_call(["git", "checkout", "-b", branch_name], shell=False)
            except subprocess.CalledProcessError as e:
                raise Exception(f"Failed to create and checkout branch: {e}")

            repo_files = gather_repo_files(str(full_repo_path))

            aider_session = AiderSession(str(full_repo_path), task_description, current_agent_id, repo_files=repo_files)
            if not aider_session.start():
                raise Exception("Failed to start aider session.")

            tasks_data = load_tasks()
            tasks_data['agents'][current_agent_id]['session_id'] = aider_session.session_id
            tasks_data['agents'][current_agent_id]['status'] = 'pending'
            save_tasks(tasks_data)
            aider_sessions[current_agent_id] = aider_session
            logging.info(f"Agent {current_agent_id} created and session started successfully.")

            created_agent_ids.append(current_agent_id)

        except Exception as e:
            error_msg = f"Error initializing agent {current_agent_id}: {e}"
            logging.error(error_msg)
            handle_agent_error(current_agent_id, str(e))
            continue
        finally:
            os.chdir(original_cwd)

    return created_agent_ids if created_agent_ids else None

class AiderSession:
    """
    Represents an aider session for a single agent. Handles process start, 
    output reading, status updates, and cleanup.
    """
    def __init__(self, workspace_path, task, agent_id, repo_files=None):
        self.agent_id = agent_id
        self.workspace_path = normalize_path(workspace_path)
        self.task = task
        self.output_buffer = io.StringIO()
        self.process = None
        self._stop_event = threading.Event()
        self.session_id = str(uuid.uuid4())[:8]
        self._buffer_lock = threading.Lock()
        self.stream_status = {
            'last_output_time': time.time(),
            'output_count': 0,
            'stream_active': True,
            'conversation_phase': 'starting',
            'last_error': None,
            'command_complete': False
        }
        self.json_signals = []
        self.completed = False
        self.errored = False
        self.lock_file = Path(self.workspace_path) / "session.lock"
        self.repo_files = repo_files or []
        self.line_queue = eventlet.queue.Queue()
        logging.info(f"[{self.agent_id}] AiderSession initialized. Workspace: {self.workspace_path}, Task: {self.task}")

    def start(self):
        """Start the aider process and begin reading output."""
        if self.lock_file.exists():
            self.fail_with_error("Session lock file already exists.")
            return False
        try:
            self.lock_file.touch(exist_ok=False)
        except Exception as e:
            self.fail_with_error(f"Failed to create lock file: {e}")
            return False

        python_exe = sys.executable
        env = os.environ.copy()
        env.update({
            'PYTHONUNBUFFERED': '1',
            'PYTHONIOENCODING': 'utf-8',
            'TERM': 'dumb',
            'FORCE_COLOR': '0',
            'NO_COLOR': '1',
            'PROMPT_TOOLKIT_NO_CPR': '1',
        })

        cmd = [
            python_exe,
            '-u',
            '-m', 'aider',
            '--mini',
            '--no-git',
            '--no-pretty',
            '--yes-always',
            '--no-auto-commits',
            '--map-tokens', '2046',
            '--message', self.task
        ]

        for f in self.repo_files:
            cmd.extend(['--file', f])

        logging.info(f"[{self.agent_id}] Starting aider session with command: {' '.join(cmd)}")
        try:
            self.process = subprocess.Popen(
                cmd,
                cwd=self.workspace_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE,
                text=True,
                universal_newlines=True,
                bufsize=1,
                env=env,
                encoding='utf-8',
                errors='replace'
            )
        except Exception:
            self.fail_with_error("Failed to start aider process:\n" + traceback.format_exc())
            self.unlock_workspace()
            return False

        if self.process.poll() is not None:
            self.fail_with_error("Aider process ended immediately. Check 'aider' installation and PATH.")
            self.unlock_workspace()
            return False

        output_thread = threading.Thread(target=self._read_output, args=(self.process.stdout,), daemon=True)
        output_thread.start()
        monitor_thread = threading.Thread(target=self._monitor_process, daemon=True)
        monitor_thread.start()

        # Background task to emit queued lines
        socketio.start_background_task(self._emit_queued_lines)

        logging.info(f"[{self.agent_id}] Aider session started successfully, session_id={self.session_id}")
        return True

    def fail_with_error(self, message):
        """Handle a session error."""
        logging.error(f"[{self.agent_id}] {message}")
        self.stream_status['last_error'] = message
        self.stream_status['stream_active'] = False
        self.errored = True
        self.stream_status['conversation_phase'] = 'error'
        self._emit_status()
        handle_agent_error(self.agent_id, message, log_output=self.get_output())
        self.unlock_workspace()

    def _monitor_process(self):
        """Monitor the aider process and update status on completion or error."""
        self.process.wait()
        exit_code = self.process.returncode
        if exit_code != 0 and not self.completed and not self.errored:
            error_msg = f"Process exited with code {exit_code}"
            logging.error(f"[{self.agent_id}] {error_msg}")
            self.fail_with_error(error_msg)
        else:
            if not self.completed and not self.errored:
                logging.info(f"[{self.agent_id}] Process completed successfully.")
                self.completed = True
                self.stream_status['command_complete'] = True
                self.stream_status['conversation_phase'] = 'completed'
                self.stream_status['stream_active'] = False
                self._emit_status()
                self.unlock_workspace()

    def _read_output(self, pipe):
        """Read the output from the aider process and enqueue lines for emission."""
        try:
            while not self._stop_event.is_set():
                line = pipe.readline()
                if line == '' and self.process.poll() is not None:
                    logging.info(f"[{self.agent_id}] Process ended during output reading.")
                    break
                if line:
                    self.line_queue.put(line)
                    self.stream_status['last_output_time'] = time.time()
                    self.stream_status['output_count'] += 1
        except Exception:
            self.fail_with_error("Error reading output:\n" + traceback.format_exc())

    def cleanup(self):
        """Cleanup session: stop event, terminate process, unlock workspace."""
        logging.info(f"[{self.agent_id}] Cleaning up session.")
        self._stop_event.set()
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
                logging.info(f"[{self.agent_id}] Process terminated cleanly.")
            except:
                logging.warning(f"[{self.agent_id}] Process did not terminate, forcing kill.")
                self.process.kill()
        self.unlock_workspace()

    def _emit_queued_lines(self):
        """Continuously emit queued output lines to the frontend."""
        while not self._stop_event.is_set():
            try:
                lines = []
                while not self.line_queue.empty():
                    line = self.line_queue.get_nowait()
                    line = line.rstrip('\n')
                    with self._buffer_lock:
                        self.output_buffer.write(line + "\n")
                    lines.append(line)
                if lines:
                    current_time = datetime.datetime.now().isoformat()
                    for ln in lines:
                        socketio.emit('agent_output_update', {
                            'agent_id': self.agent_id,
                            'new_output': ln,
                            'timestamp': current_time
                        }, namespace='/')
                    self._emit_status()
                eventlet.sleep(0.5)
            except Exception as e:
                logging.error(f"[{self.agent_id}] Error in _emit_queued_lines: {e}")
                eventlet.sleep(1)

    def _emit_status(self):
        """Emit the agent's status to the frontend and save any updates."""
        tasks_data = load_tasks()
        if self.agent_id in tasks_data['agents']:
            current_time = datetime.datetime.now().isoformat()
            if self.errored:
                status = 'error'
            elif self.completed:
                status = 'completed'
            else:
                status = 'in_progress' if self.stream_status.get('stream_active') else 'stalled'

            changed = False
            old_status = tasks_data['agents'][self.agent_id].get('status')
            if old_status != status:
                tasks_data['agents'][self.agent_id]['status'] = status
                changed = True
            old_output = tasks_data['agents'][self.agent_id].get('aider_output', '')
            new_output = self.get_output()
            if old_output != new_output:
                tasks_data['agents'][self.agent_id]['aider_output'] = new_output
                tasks_data['agents'][self.agent_id]['last_updated'] = current_time
                changed = True
            if not tasks_data['agents'][self.agent_id].get('last_error') and self.stream_status.get('last_error'):
                tasks_data['agents'][self.agent_id]['last_error'] = self.stream_status.get('last_error')
                changed = True
            if changed:
                save_tasks(tasks_data)

            socketio.emit('agent_status_update', {
                'agent_id': self.agent_id,
                'status': status,
                'state_info': self.stream_status,
                'last_updated': current_time
            }, namespace='/')

    def get_output(self):
        """Return the entire output buffer."""
        with self._buffer_lock:
            return self.output_buffer.getvalue()

    def unlock_workspace(self):
        """Ensure the lock file is removed and the process is no longer running."""
        # Make sure process is terminated
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
                logging.info(f"[{self.agent_id}] Process terminated cleanly.")
            except:
                logging.warning(f"[{self.agent_id}] Forcing kill of process.")
                self.process.kill()
        if self.lock_file.exists():
            try:
                self.lock_file.unlink()
                logging.info(f"[{self.agent_id}] Lock file removed successfully.")
            except Exception as e:
                logging.warning(f"[{self.agent_id}] Failed to remove lock file: {e}")

def main_loop():
    """
    Main orchestration loop: periodically checks agents for stalls and updates outputs.
    This runs in a background thread.
    """
    logging.info("Starting main orchestration loop.")
    while True:
        try:
            tasks_data = load_tasks()
            for agent_id in list(tasks_data['agents'].keys()):
                if agent_id in aider_sessions:
                    with thread_lock:
                        update_agent_output(agent_id)
                        session = aider_sessions[agent_id]
                        if session.stream_status['stream_active']:
                            since_last_output = time.time() - session.stream_status['last_output_time']
                            if since_last_output > NO_OUTPUT_TIMEOUT and not session.completed and not session.errored:
                                stall_msg = f"No output for {NO_OUTPUT_TIMEOUT} seconds (stalled)"
                                logging.warning(f"Agent {agent_id} stalled: {stall_msg}")
                                session.fail_with_error(stall_msg)
            time.sleep(CHECK_INTERVAL)
        except Exception:
            logging.error("Error in main loop:\n" + traceback.format_exc())
            time.sleep(CHECK_INTERVAL)

@app.route('/')
def index():
    return render_template('index.html', missing_vars=env_issues)

@app.route('/tasks/tasks.json')
def serve_tasks_json():
    ensure_tasks_file()
    return send_from_directory(str(TASKS_DIR), 'tasks.json')

@app.route('/agents')
def agent_view():
    tasks_data = load_tasks()
    initialise_orchestrator(tasks_data)
    mark_abandoned_agents(tasks_data)
    agents = tasks_data.get('agents', {})
    # Debug URLs for direct inspection
    for agent_id, agent in agents.items():
        if 'files' not in agent:
            agent['files'] = []
        agent['debug_urls'] = {
            'info': f'/debug/agent/{agent_id}',
            'validate': f'/debug/validate_paths/{agent_id}'
        }
    logging.info(f"Rendering agent_view with {len(agents)} agents: {list(agents.keys())}")
    return render_template('agents.html', agents=agents)

@app.route('/create_agent', methods=['POST'])
def create_agent_endpoint():
    try:
        data = request.get_json()
        repo_url = data.get('repo_url')
        tasks = data.get('tasks', [])
        num_agents = data.get('num_agents', 1)
        if not repo_url or not tasks:
            return jsonify({'error': 'Repository URL and tasks are required'}), 400
        if isinstance(tasks, str):
            tasks = [tasks]

        if env_issues:
            return jsonify({'success': False, 'error': 'Environment issues: ' + '; '.join(env_issues)}), 500

        tasks_data = load_tasks()
        all_created_agents = []
        for task_description in tasks:
            os.environ['REPOSITORY_URL'] = repo_url
            agent_ids = initialiseCodingAgent(repository_url=repo_url, task_description=task_description, num_agents=num_agents)
            if agent_ids:
                all_created_agents.extend(agent_ids)
                tasks_data = load_tasks()
                if task_description not in tasks_data['tasks']:
                    tasks_data['tasks'].append(task_description)
                tasks_data['repository_url'] = repo_url
                save_tasks(tasks_data)
            else:
                return jsonify({'success': False, 'error': 'Failed to create any agents'}), 500

        def check_and_start_main_loop():
            # Start the main orchestration loop if not already started
            for thread in threading.enumerate():
                if thread.name == 'OrchestratorMainLoop':
                    return
            loop_thread = threading.Thread(target=main_loop, name='OrchestratorMainLoop', daemon=True)
            loop_thread.start()

        check_and_start_main_loop()

        test_data = load_tasks()
        logging.info(f"After create_agent_endpoint, tasks.json agents: {list(test_data.get('agents', {}).keys())}")

        return jsonify({
            'success': True,
            'agent_ids': all_created_agents,
            'message': f'Agents {", ".join(all_created_agents)} created successfully'
        }), 200
    except Exception as e:
        logging.error("Error creating agent:\n" + traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/delete_agent/<agent_id>', methods=['DELETE'])
def remove_agent_endpoint(agent_id):
    try:
        if agent_id == 'orchestrator':
            return jsonify({'success': False, 'error': 'Cannot delete the orchestrator agent'}), 400
        result = delete_agent(agent_id)
        if result:
            return jsonify({'success': True, 'message': f'Agent {agent_id} deleted successfully'})
        else:
            return jsonify({'success': False, 'error': f'Agent {agent_id} not found'}), 404
    except Exception as e:
        logging.error("Error deleting agent:\n" + traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/debug/agent/<agent_id>')
def debug_agent(agent_id):
    try:
        tasks_data = load_tasks()
        agent_data = tasks_data['agents'].get(agent_id)
        if not agent_data:
            return jsonify({'error': f'Agent {agent_id} not found'}), 404
        workspace_path = normalize_path(agent_data.get('workspace'))
        repo_path = normalize_path(agent_data.get('repo_path'))
        aider_session = aider_sessions.get(agent_id)
        aider_workspace = normalize_path(aider_session.workspace_path) if aider_session else None
        debug_info = {
            'agent_id': agent_id,
            'paths': {
                'workspace': {
                    'raw': agent_data.get('workspace'),
                    'normalized': workspace_path,
                    'exists': os.path.exists(workspace_path) if workspace_path else False
                },
                'repo_path': {
                    'raw': agent_data.get('repo_path'),
                    'normalized': repo_path,
                    'exists': os.path.exists(repo_path) if repo_path else False
                },
                'aider_workspace': {
                    'raw': aider_workspace,
                    'exists': os.path.exists(aider_workspace) if aider_workspace else False
                }
            },
            'aider_session': {
                'exists': aider_session is not None,
                'output_buffer_length': len(aider_session.get_output()) if aider_session else 0,
                'session_id': aider_session.session_id if aider_session else None
            },
            'agent_data': {
                'status': agent_data.get('status'),
                'created_at': agent_data.get('created_at'),
                'last_updated': agent_data.get('last_updated'),
                'aider_output_length': len(agent_data.get('aider_output', '')),
                'task': agent_data.get('task'),
                'last_error': agent_data.get('last_error')
            }
        }
        return jsonify(debug_info)
    except Exception as e:
        logging.error("Error in debug_agent:\n" + traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/debug/validate_paths/<agent_id>')
def debug_validate_paths(agent_id):
    try:
        tasks_data = load_tasks()
        agent_data = tasks_data['agents'].get(agent_id)
        if not agent_data:
            return jsonify({'error': f'Agent {agent_id} not found'}), 404
        aider_session = aider_sessions.get(agent_id)
        validation_results = {
            'agent_id': agent_id,
            'paths': {
                'workspace': {
                    'raw': agent_data.get('workspace'),
                    'normalized': normalize_path(agent_data.get('workspace'))
                },
                'repo_path': {
                    'raw': agent_data.get('repo_path'),
                    'normalized': normalize_path(agent_data.get('repo_path'))
                },
                'aider_workspace': {
                    'raw': aider_session.workspace_path if aider_session else None,
                    'normalized': normalize_path(aider_session.workspace_path) if aider_session else None
                }
            },
            'validation': {
                'has_aider_session': aider_session is not None
            }
        }
        return jsonify(validation_results)
    except Exception as e:
        logging.error("Error in debug_validate_paths:\n" + traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@socketio.on('request_agent_data', namespace='/')
def handle_agent_data_request(data):
    try:
        agent_id = data.get('agent_id')
        if not agent_id or agent_id == 'orchestrator':
            return
        tasks_data = load_tasks()
        agent_data = tasks_data['agents'].get(agent_id)
        if not agent_data:
            return
        if agent_id in aider_sessions:
            with thread_lock:
                current_output = aider_sessions[agent_id].get_output()
                if current_output:
                    current_time = datetime.datetime.now().isoformat()
                    if agent_data['aider_output'] != current_output:
                        agent_data['aider_output'] = current_output
                        agent_data['last_updated'] = current_time
                        save_tasks(tasks_data)
                    emit('agent_output_update', {
                        'agent_id': agent_id,
                        'new_output': current_output,
                        'timestamp': current_time
                    }, namespace='/')
                    emit('agent_status_update', {
                        'agent_id': agent_id,
                        'status': agent_data['status'],
                        'last_updated': current_time,
                        'state_info': aider_sessions[agent_id].stream_status
                    }, namespace='/')
        else:
            # No session found for this agent
            status = agent_data.get('status', 'pending')
            if status not in ['completed', 'error', 'abandoned']:
                agent_data['status'] = 'abandoned'
                if not agent_data.get('last_error'):
                    agent_data['last_error'] = "No session found for this agent. It is now abandoned."
                save_tasks(tasks_data)
                emit('agent_error', {
                    'error': agent_data['last_error'],
                    'timestamp': datetime.datetime.now().isoformat()
                }, namespace='/')
                emit('agent_status_update', {
                    'agent_id': agent_id,
                    'status': 'abandoned',
                    'last_updated': datetime.datetime.now().isoformat(),
                    'state_info': {}
                }, namespace='/')
            else:
                emit('agent_error', {
                    'error': f"No session found for agent {agent_id}, current status: {status}.",
                    'timestamp': datetime.datetime.now().isoformat()
                }, namespace='/')
    except Exception as e:
        logging.error("Error in handle_agent_data_request:\n" + traceback.format_exc())
        emit('agent_error', {'error': str(e), 'timestamp': datetime.datetime.now().isoformat()}, namespace='/')

@socketio.on('request_agent_output', namespace='/')
def handle_request_agent_output(data):
    try:
        agent_id = data.get('agent_id')
        if not agent_id or agent_id == 'orchestrator':
            return
        tasks_data = load_tasks()
        agent_data = tasks_data['agents'].get(agent_id)
        if not agent_data:
            emit('agent_error', {'error': f"Agent {agent_id} not found"}, namespace='/')
            return
        if agent_id in aider_sessions:
            with thread_lock:
                output = aider_sessions[agent_id].get_output()
                emit('agent_output_update', {
                    'agent_id': agent_id,
                    'new_output': output,
                    'timestamp': datetime.datetime.now().isoformat(),
                }, namespace='/')
                return
        status = agent_data.get('status', 'pending')
        if status not in ['completed', 'error', 'abandoned']:
            agent_data['status'] = 'abandoned'
            agent_data['last_error'] = "No session found for this agent. It is now abandoned."
            save_tasks(tasks_data)
            emit('agent_error', {
                'error': agent_data['last_error'],
                'timestamp': datetime.datetime.now().isoformat()
            }, namespace='/')
            emit('agent_status_update', {
                'agent_id': agent_id,
                'status': 'abandoned',
                'state_info': {},
                'last_updated': datetime.datetime.now().isoformat()
            }, namespace='/')
        else:
            emit('agent_error', {
                'error': f"No session found for agent {agent_id}. It's already {status}.",
                'timestamp': datetime.datetime.now().isoformat()
            }, namespace='/')
    except Exception as e:
        logging.error("Error in handle_request_agent_output:\n" + traceback.format_exc())
        emit('agent_error', {'error': str(e)}, namespace='/')

if __name__ == '__main__':
    if env_issues:
        logging.error(" ".join(env_issues))
    logging.info(f"Starting server on http://{DEFAULT_HOST}:{DEFAULT_PORT}")
    socketio.run(app, debug=True, host=DEFAULT_HOST, port=DEFAULT_PORT)
