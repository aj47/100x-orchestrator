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
        path = Path(path_str).resolve()
        normalized = str(path).replace('\\', '/')
        logging.debug(f"Path normalization: {path_str} -> {normalized}")
        return normalized
    except Exception as e:
        logging.error(f"Error normalizing path {path_str}: {e}")
        return None

class AgentSession:
    def __init__(self, workspace_path, task, config=None, aider_commands=None):
        self.workspace_path = normalize_path(workspace_path)
        self.task = task
        self.aider_commands = aider_commands
        self.output_queue = queue.Queue() # Use a queue for thread-safe output
        self.process = None
        self._stop_event = threading.Event()
        self.session_id = str(uuid.uuid4())[:8]
        self.aider_commands = aider_commands

        # Load configuration with defaults from a dictionary (easily replaceable with file loading)
        default_config = {
            'stability_duration': 10,
            'output_buffer_max_length': 10000,
            'log_level': logging.INFO
        }
        self.config = {**default_config, **(config or {})}
        logging.basicConfig(level=self.config['log_level']) # Set log level from config

        logging.info(f"[Session {self.session_id}] Initialized with workspace: {self.workspace_path}")
        logging.info(f"[Session {self.session_id}] Configuration: {self.config}")

    def start(self) -> bool:
        try:
            logging.info(f"[Session {self.session_id}] Starting aider session in workspace: {self.workspace_path}")
            env = os.environ.copy()
            env['PYTHONUNBUFFERED'] = '1'
            env['PYTHONIOENCODING'] = 'utf-8'
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            cmd = [
                'aider',
                '--map-tokens', '1024',
                '--no-show-model-warnings',
                '--yes',
                '--model', 'openrouter/google/gemini-flash-1.5',
                '--no-pretty',
            ]
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
                bufsize=1,
                universal_newlines=True,
                env=env,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            logging.info(f"[Session {self.session_id}] Process started with PID: {self.process.pid}")
            logging.info(f"[Session {self.session_id}] Working directory: {self.workspace_path}")

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
            time.sleep(2)
            logging.info(f"[Session {self.session_id}] Started output processing threads")
            return True
        except Exception as e:
            logging.error(f"[Session {self.session_id}] Failed to start aider session: {e}", exc_info=True)
            return False

    def _read_output(self, pipe, pipe_name):
        try:
            logging.info(f"[Session {self.session_id}] Started reading from {pipe_name}")
            while not self._stop_event.is_set() and self.process and self.process.poll() is None:
                line = pipe.readline()
                if not line:
                    sleep(0.1)
                    continue
                if any(msg in line for msg in [
                    "Can't initialize prompt toolkit",
                    "Newer aider version",
                    "Run this command to update:",
                    "python.exe -m pip install aider",
                    "cmd.exe?",
                    "Aider v",
                    "Model:",
                    "Git repo:",
                    "Repo-map:",
                    "Use /help"
                ]):
                    continue
                if line.strip():
                    log_time = datetime.datetime.now().isoformat()
                    logging.info(f"[Session {self.session_id}] {pipe_name} ({log_time}): {line.strip()}")
                    self.output_queue.put(line) # Put line in queue
                pipe.flush()
            logging.info(f"[Session {self.session_id}] {pipe_name} reader stopping - process terminated: {self.process.poll() if self.process else 'No process'}")
        except Exception as e:
            logging.error(f"[Session {self.session_id}] Error reading from {pipe_name}: {e}", exc_info=True)

    def get_output(self):
        output = ""
        while not self.output_queue.empty():
            output += self.output_queue.get()
        return output

    def send_message(self, message: str, timeout: int = 10) -> bool:
        try:
            if not self.process or self.process.poll() is not None:
                logging.error(f"[Session {self.session_id}] Cannot send message: Process is not running")
                if self.start():
                    logging.info(f"[Session {self.session_id}] Process restarted successfully")
                else:
                    logging.error(f"[Session {self.session_id}] Failed to restart the process")
                    return False
            logging.info(f"[Session {self.session_id}] 🔵 SENDING MESSAGE TO AIDER:")
            for line in message.split('\n'):
                logging.info(f"[Session {self.session_id}] 📤 {line}")
            sanitized_message = message.replace('"', '\\"')
            self.process.stdin.write(sanitized_message + "\n")
            self.process.stdin.flush()
            logging.debug(f"[Session {self.session_id}] Message sent to Aider successfully")
            return True
        except (BrokenPipeError, IOError) as pipe_error:
            logging.error(f"[Session {self.session_id}] Pipe error sending message: {pipe_error}")
            return False
        except Exception as e:
            logging.error(f"[Session {self.session_id}] Error sending message: {e}", exc_info=True)
            return False

    def is_ready(self) -> bool:
        try:
            stability_duration = self.config['stability_duration']
            start_time = time.time()
            while time.time() - start_time < stability_duration:
                time.sleep(1)
                # More sophisticated readiness check could be implemented here
                # For example, check for a specific "ready" message from the aider process
                if not self.output_queue.empty():
                    return True # Assume ready if there's output
            return True # Assume ready after timeout
        except Exception as e:
            logging.error(f"[Session {self.session_id}] Error in readiness check: {e}", exc_info=True)
            return False

    def cleanup(self) -> None:
        try:
            logging.info(f"[Session {self.session_id}] Starting cleanup")
            self._stop_event.set()
            if self.process:
                logging.info(f"[Session {self.session_id}] Terminating process {self.process.pid}")
                try:
                    if self.process.stdin:
                        self.process.stdin.close()
                except Exception as stdin_close_error:
                    logging.warning(f"[Session {self.session_id}] Error closing stdin: {stdin_close_error}")
                try:
                    self.process.terminate()
                    self.process.wait(timeout=5)
                    logging.info(f"[Session {self.session_id}] Process terminated successfully")
                except subprocess.TimeoutExpired:
                    logging.warning(f"[Session {self.session_id}] Process did not terminate, forcing kill")
                    self.process.kill()
                try:
                    if self.process.stdout:
                        self.process.stdout.close()
                    if self.process.stderr:
                        self.process.stderr.close()
                except Exception as pipe_close_error:
                    logging.warning(f"[Session {self.session_id}] Error closing pipes: {pipe_close_error}")
            logging.info(f"[Session {self.session_id}] Cleanup completed")
        except Exception as e:
            logging.error(f"[Session {self.session_id}] Error during cleanup: {e}", exc_info=True)

