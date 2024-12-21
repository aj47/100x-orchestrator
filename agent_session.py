import os, json, traceback, subprocess, sys, uuid
from time import sleep
import threading
import datetime
import queue
import io
import logging
from pathlib import Path
import time
import re

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

class AgentSession:
    def __init__(self, workspace_path, task, config_path='config.json', aider_commands=None):
        self.workspace_path = normalize_path(workspace_path)
        self.task = task
        self.aider_commands = aider_commands # Store aider commands
        self.output_buffer = io.StringIO()
        self.process = None
        self._stop_event = threading.Event()
        self.session_id = str(uuid.uuid4())[:8]  # For logging
        self._buffer_lock = threading.Lock()  # Add lock for thread-safe buffer access
        self.aider_commands = aider_commands
        
        # Load configuration with defaults and error handling
        self.config = self._load_config(config_path)
        
        logging.info(f"[Session {self.session_id}] Initialized with workspace: {self.workspace_path}")
        logging.info(f"[Session {self.session_id}] Configuration: {self.config}")

    def _load_config(self, config_path):
        """Load configuration from JSON file with defaults and error handling."""
        default_config = {
            'model': 'openrouter/google/gemini-flash-1.5',
            'stability_duration': 10,
            'output_buffer_max_length': 10000,
            'prompts': {}
        }
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                # Validate config and merge with defaults
                return {**default_config, **config}
        except FileNotFoundError:
            logging.warning(f"Config file '{config_path}' not found. Using default configuration.")
            return default_config
        except json.JSONDecodeError as e:
            logging.error(f"Error decoding config file '{config_path}': {e}. Using default configuration.")
            return default_config

    def start(self) -> bool:
        """
        Start the aider session.
        
        Returns:
            bool: True if session started successfully, False otherwise
        """
        try:
            logging.info(f"[Session {self.session_id}] Starting aider session in workspace: {self.workspace_path}")
            
            # Set up environment with forced unbuffering
            env = os.environ.copy()
            env['PYTHONUNBUFFERED'] = '1'
            env['PYTHONIOENCODING'] = 'utf-8'
            
            # Create startupinfo to hide console window
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            # Start aider process with unbuffered output and console mode
            cmd = [
                'aider',
                '--map-tokens', '1024',
                '--no-show-model-warnings',
                '--yes',
                '--model', self.config['model'], # Load model from config
                '--no-pretty',
            ]
            if self.aider_commands:
                cmd.extend(self.aider_commands.split())
            
            # Add custom commands if provided
            if self.aider_commands:
                cmd.extend(self.aider_commands.split())
            logging.info(f"[Session {self.session_id}] Executing command: {' '.join(cmd)}")
            
            self.process = subprocess.Popen(
                cmd,
                shell=True,
                cwd=str(Path(self.workspace_path).resolve()),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                startupinfo=startupinfo,
                text=True,
                bufsize=1,  # Line buffered
                universal_newlines=True,
                env=env,
                creationflags=subprocess.CREATE_NO_WINDOW  # Prevent console window
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
            
            stdout_thread.start()
            stderr_thread.start()

            # Wait briefly for startup
            time.sleep(2)
            
            logging.info(f"[Session {self.session_id}] Started output processing threads")

            # Verify threads are running
            for thread in [stdout_thread, stderr_thread]:
                if not thread.is_alive():
                    logging.error(f"[Session {self.session_id}] Thread {thread.name} failed to start")
                    return False
                logging.info(f"[Session {self.session_id}] Thread {thread.name} is running")

            return True
        except Exception as e:
            logging.error(f"[Session {self.session_id}] Failed to start aider session: {e}", exc_info=True)
            return False

    def _read_output(self, pipe, pipe_name):
        # ... (rest of the _read_output method remains unchanged) ...
    def get_output(self):
        # ... (rest of the get_output method remains unchanged) ...

    def _echo_message(self, message: str) -> None:
        # ... (rest of the _echo_message method remains unchanged) ...

    def is_ready(self) -> bool:
        # ... (rest of the is_ready method remains unchanged) ...

    def send_message(self, message: str, timeout: int = 10) -> bool:
        # ... (rest of the send_message method remains unchanged) ...

    def _format_output_line(self, line: str) -> str:
        # ... (rest of the _format_output_line method remains unchanged) ...

    def cleanup(self) -> None:
        # ... (rest of the cleanup method remains unchanged) ...
