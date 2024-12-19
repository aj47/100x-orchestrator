import os, json, traceback, subprocess, sys, uuid
from prompts import PROMPT_AIDER
from litellm_client import LiteLLMClient
from prompt_processor import PromptProcessor
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
from github import Github
from dotenv import load_dotenv

# Import the new AgentSession class
from agent_session import AgentSession, normalize_path



# Configuration
DEFAULT_AGENTS_PER_TASK = 2
MODEL_NAME = os.environ.get('LITELLM_MODEL', 'anthropic/claude-3-5-sonnet-20240620')
CONFIG_FILE = Path("tasks/tasks.json")
CRITIQUE_MODEL = "gpt-3.5-turbo" #Critique agent model
MAX_CRITIQUE_ITERATIONS = 3

# Ensure tasks directory exists
CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
tools, available_functions = [], {}
MAX_TOOL_OUTPUT_LENGTH = 5000  # Adjust as needed
CHECK_INTERVAL = 5  # Reduced to 30 seconds for more frequent updates

# Global dictionaries to store sessions and processors
aider_sessions = {}
prompt_processors = {}

# ... (rest of the code remains the same) ...

def critique_submission(agent_id, code_submission, acceptance_criteria, session_context):
    """Critique the agent's code submission."""
    try:
        litellm_client = LiteLLMClient()
        prompt = f"""You are a code critique expert. Your task is to evaluate the validity of a code submission against a set of acceptance criteria.

**Acceptance Criteria:**
{json.dumps(acceptance_criteria, indent=2)}

**Session Context:**
{session_context}

**Code Submission:**
