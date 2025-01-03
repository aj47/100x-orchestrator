import sqlite3
from pathlib import Path
import json
from datetime import datetime
from typing import Dict, List, Optional

DATABASE_PATH = Path("tasks.db")

def init_db():
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agents (
                    agent_id TEXT PRIMARY KEY,
                    agent_data TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_data TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS config (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_actions (
                    agent_id TEXT,
                    action_history TEXT,
                    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
                )
            """)
            conn.commit()
    except Exception as e:
        print(f"Error initializing database: {e}")

def save_agent(agent_id: str, agent_data: Dict) -> bool:
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO agents (agent_id, agent_data)
                VALUES (?, ?)
            """, (agent_id, json.dumps(agent_data)))
            conn.commit()
            return True
    except Exception as e:
        print(f"Error saving agent: {e}")
        return False

def get_agent(agent_id: str) -> Optional[Dict]:
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT agent_data FROM agents WHERE agent_id = ?", (agent_id,))
            row = cursor.fetchone()
            if row:
                return json.loads(row[0])
            return None
    except Exception as e:
        print(f"Error getting agent: {e}")
        return None

def get_all_agents() -> Dict[str, Dict]:
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT agent_id, agent_data FROM agents")
            rows = cursor.fetchall()
            agents = {}
            for row in rows:
                agents[row[0]] = json.loads(row[1])
            return agents
    except Exception as e:
        print(f"Error getting all agents: {e}")
        return {}

def delete_agent(agent_id: str) -> bool:
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM agents WHERE agent_id = ?", (agent_id,))
            conn.commit()
            return True
    except Exception as e:
        print(f"Error deleting agent: {e}")
        return False

def save_task(task_data: Dict) -> int:
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO tasks (task_data)
                VALUES (?)
            """, (json.dumps(task_data),))
            conn.commit()
            return cursor.lastrowid
    except Exception as e:
        print(f"Error saving task: {e}")
        return -1

def get_all_tasks() -> List[Dict]:
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT task_data FROM tasks")
            rows = cursor.fetchall()
            tasks = []
            for row in rows:
                tasks.append(json.loads(row[0]))
            return tasks
    except Exception as e:
        print(f"Error getting all tasks: {e}")
        return []

def get_config(key: str) -> Optional[str]:
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM config WHERE key = ?", (key,))
            row = cursor.fetchone()
            if row:
                return row[0]
            return None
    except Exception as e:
        print(f"Error getting config: {e}")
        return None

def save_config(key: str, value: str) -> bool:
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO config (key, value)
                VALUES (?, ?)
            """, (key, value))
            conn.commit()
            return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False

def get_model_config() -> Optional[Dict]:
    try:
        config_str = get_config('model_config')
        if config_str:
            return json.loads(config_str)
        return None
    except Exception as e:
        print(f"Error getting model config: {e}")
        return None

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
