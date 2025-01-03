import sqlite3
from pathlib import Path
import json
from datetime import datetime
from typing import Dict, List, Optional

DATABASE_PATH = Path("tasks.db")

def init_db():
    # ... (init_db function remains the same)

def save_agent(agent_id: str, agent_data: Dict) -> bool:
    # ... (save_agent function remains the same)

def get_agent(agent_id: str) -> Optional[Dict]:
    # ... (get_agent function remains the same)

def get_all_agents() -> Dict[str, Dict]:
    # ... (get_all_agents function remains the same)

def delete_agent(agent_id: str) -> bool:
    # ... (delete_agent function remains the same)

def save_task(task_data: Dict) -> int:
    # ... (save_task function remains the same)

def get_all_tasks() -> List[Dict]:
    # ... (get_all_tasks function remains the same)

def get_config(key: str) -> Optional[str]:
    # ... (get_config function remains the same)

def save_config(key: str, value: str) -> bool:
    # ... (save_config function remains the same)

def get_model_config() -> Optional[Dict]:
    # ... (get_model_config function remains the same)

def save_agent_actions(agent_id: str, action_history: List[str]) -> bool:
    """Saves the agent's action history to the database."""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO agent_actions (agent_id, action_history)
                VALUES (?, ?)
            """, (agent_id, json.dumps(action_history)))
            conn.commit()
            return True
    except Exception as e:
        print(f"Error saving agent actions: {e}")
        return False

def load_agent_actions(agent_id: str) -> Optional[List[str]]:
    """Loads the agent's action history from the database."""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT action_history FROM agent_actions WHERE agent_id = ?", (agent_id,))
            row = cursor.fetchone()
            if row:
                return json.loads(row[0])
            return None
    except Exception as e:
        print(f"Error loading agent actions: {e}")
        return None

# Initialize the database when this module is imported
init_db()
