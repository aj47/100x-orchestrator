import os, json, subprocess, sys, uuid
from time import sleep
import threading
import datetime
import io
import logging
from pathlib import Path
import time
from logging_config import configure_logging

configure_logging()

def normalize_path(path_str):
    if not path_str:
        return None
    try:
        path = Path(path_str).resolve()
        return str(path).replace('\\', '/')
    except Exception:
        return None

class AgentSession:
    def __init__(self, workspace_path, task, config=None, aider_commands=None):
        self.workspace_path = normalize_path(workspace_path)
        self.task = task
        self.aider_commands = aider_commands
        self.output_buffer = io.StringIO()
        self.process = None
        self._stop_event = threading.Event()
        self.session_id = str(uuid.uuid4())[:8]
        self._buffer_lock = threading.Lock()
        self.aider_commands = aider_commands
        
        default_config = {
            'stability_duration': 10,
            'output_buffer_max_length': 10000
        }
        self.config = {**default_config, **(config or {})}

    def start(self) -> bool:
        try:
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
            
            if self.aider_commands:
                cmd.extend(self.aider_commands.split())
            
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

            for thread in [stdout_thread, stderr_thread]:
                if not thread.is_alive():
                    return False

            return True
        except Exception:
            return False

    def _read_output(self, pipe, pipe_name):
        try:
            message_buffer = []
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
                    "python.exe -m pip install --upgrade --upgrade-strategy only-if-needed aider-chat"
                    "Aider v",
                    "Model:",
                    "Git repo:",
                    "Repo-map:",
                    "cmd.exe?",
                    "Use /help"
                ]):
                    continue
                
                if line.strip():
                    log_time = datetime.datetime.now().isoformat()
                    message_buffer.append(line.strip())
                    
                    if '>' in line or '?' in line:
                        if message_buffer:
                            message_buffer = []
                
                with self._buffer_lock:
                    self.output_buffer.seek(0, 2)
                    self.output_buffer.write(line)
                    
                pipe.flush()
                
        except Exception:
            pass

    def get_output(self):
        try:
            pos = self.output_buffer.tell()
            self.output_buffer.seek(0)
            output = self.output_buffer.read()
            self.output_buffer.seek(pos)
            
            return output
        except Exception:
            return None

    def _echo_message(self, message: str) -> None:
        try:
            echo_line = self._format_output_line(f"{message}")
            echo_line = echo_line.replace('class="output-line"', 'class="output-line user-message"')
            
            with threading.Lock():
                self.output_buffer.seek(0, 2)
                self.output_buffer.write(echo_line)
                
        except Exception:
            pass

    def is_ready(self) -> bool:
        try:
            stability_duration = self.config['stability_duration']
            
            initial_output = self.get_output()
            
            start_time = time.time()
            while time.time() - start_time < stability_duration:
                time.sleep(1)
                
                current_output = self.get_output()
                
                if current_output != initial_output:
                    return False
            
            return True
        
        except Exception:
            return False

    def send_message(self, message: str, timeout: int = 10) -> bool:
        try:
            if not self.process or self.process.poll() is not None:
                if self.start():
                    pass
                else:
                    return False
            
            sanitized_message = message.replace('"', '\\"')
            
            try:
                self.process.stdin.write(sanitized_message + "\n")
                self.process.stdin.flush()
                return True
            except (BrokenPipeError, IOError):
                return False
        
        except Exception:
            return False

    def _format_output_line(self, line: str) -> str:
        if not line.strip():
            return ''
            
        formatted_line = (
            line.replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('\n', '<br>')
                .replace(' ', '&nbsp;')
        )
        
        if line.startswith('>'):
            return f'<div class="output-line agent-response">{formatted_line}</div>'
        elif line.startswith('?'):
            return f'<div class="output-line agent-question">{formatted_line}</div>'
        elif 'Error:' in line:
            return f'<div class="output-line error-message">{formatted_line}</div>'
        else:
            return f'<div class="output-line">{formatted_line}</div>'

    def cleanup(self) -> None:
        try:
            self._stop_event.set()
            if self.process:
                try:
                    if self.process.stdin:
                        self.process.stdin.close()
                except Exception:
                    pass
                
                try:
                    self.process.terminate()
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                
                try:
                    if self.process.stdout:
                        self.process.stdout.close()
                    if self.process.stderr:
                        self.process.stderr.close()
                except Exception:
                    pass
            
        except Exception:
            pass
