import json
from typing import Dict, List, Union, Optional
from pathlib import Path

CONFIG_FILE = Path("tasks/tasks.json")

# Ensure tasks directory exists
CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)

def load_tasks() -> Dict[str, Union[List, Dict, str]]:
    """
    Load tasks configuration from JSON file with proper acceptance criteria structure.
    
    Returns:
        Dict containing tasks, agents, repository URL, and acceptance criteria
    """
    try:
        with open(CONFIG_FILE, 'r') as f:
            data = json.load(f)
            
            # Ensure data has the correct structure
            if not isinstance(data, dict):
                data = {
                    "tasks": [],
                    "agents": {},
                    "repository_url": "",
                    "acceptance_criteria": ""
                }
            
            # Ensure required keys exist with proper structure
            data.setdefault('tasks', [])
            data.setdefault('agents', {})
            data.setdefault('repository_url', '')
            
            # Initialize acceptance criteria as a single string if not present
            if 'acceptance_criteria' not in data:
                data['acceptance_criteria'] = ""
            elif not isinstance(data['acceptance_criteria'], str):
                # Convert structured criteria to a single string
                data['acceptance_criteria'] = json.dumps(data['acceptance_criteria'])
            
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        # Initialize with default structure if file not found or JSON error
        return {
            "tasks": [],
            "agents": {},
            "repository_url": "",
            "acceptance_criteria": {
                "code_quality": [],
                "testing": [],
                "architecture": []
            }
        }

def save_tasks(tasks_data: Dict[str, Union[List, Dict, str]]) -> None:
    """
    Save tasks configuration to JSON file, preserving acceptance criteria structure.
    
    Args:
        tasks_data: Dictionary containing tasks configuration
    """
    # Create a copy of the data to avoid modifying the original
    data_to_save = {
        "tasks": tasks_data.get("tasks", []),
        "agents": {},
        "repository_url": tasks_data.get("repository_url", ""),
        "acceptance_criteria": tasks_data.get("acceptance_criteria", "")
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
            'last_action': agent_data.get('last_action', ''),
            'acceptance_criteria': agent_data.get('acceptance_criteria', 
                tasks_data.get('acceptance_criteria', "")
            )
        }
    
    with open(CONFIG_FILE, 'w') as f:
        json.dump(data_to_save, f, indent=4)
