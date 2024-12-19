import json
import logging
from pathlib import Path

CONFIG_FILE = Path("tasks/tasks.json")

# Ensure tasks directory exists
CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)

def load_tasks():
    """Load config from tasks.json."""
    try:
        with open(CONFIG_FILE, 'r') as f:
            data = json.load(f)
            
            # Ensure data has the correct structure
            if not isinstance(data, dict):
                logging.warning("tasks.json has incorrect structure, resetting to default")
                data = {
                    "tasks": [],
                    "agents": {},
                    "repository_url": ""
                }
            
            # Ensure required keys exist
            data.setdefault('tasks', [])
            data.setdefault('agents', {})
            data.setdefault('repository_url', '')
            
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
                'workspace': agent_data.get('workspace'),
                'repo_path': agent_data.get('repo_path'),
                'task': agent_data.get('task'),
                'status': agent_data.get('status'),
                'created_at': agent_data.get('created_at'),
                'last_updated': agent_data.get('last_updated'),
                'aider_output': agent_data.get('aider_output', ''),
                'progress': agent_data.get('progress', ''),
                'thought': agent_data.get('thought', ''),
                'progress_history': agent_data.get('progress_history', []),
                'thought_history': agent_data.get('thought_history', []),
                'future': agent_data.get('future', ''),
                'last_action': agent_data.get('last_action', '')
            }
        
        logging.debug(f"Saving tasks data")
        with open(CONFIG_FILE, 'w') as f:
            json.dump(data_to_save, f, indent=4)
        logging.info("Successfully saved tasks data")
    except Exception as e:
        logging.error(f"Error saving tasks: {e}", exc_info=True)
