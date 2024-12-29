import sqlite3
from pathlib import Path
import json
from datetime import datetime
from typing import Dict, List, Optional

DATABASE_PATH = Path("tasks.db")

def init_db():
    """Initialize the SQLite database with required tables."""
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()
        
        # Create model_config table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS model_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                orchestrator_model TEXT NOT NULL DEFAULT 'openrouter/google/gemini-flash-1.5',
                aider_model TEXT NOT NULL DEFAULT 'openrouter/google/gemini-flash-1.5',
                agent_model TEXT NOT NULL DEFAULT 'openrouter/google/gemini-flash-1.5',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # Create agents table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agents (
                id TEXT PRIMARY KEY,
                workspace TEXT NOT NULL,
                repo_path TEXT,
                task TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                last_updated TEXT NOT NULL,
                aider_output TEXT,
                last_critique TEXT,
                progress TEXT,
                thought TEXT,
                progress_history TEXT,
                thought_history TEXT,
                future TEXT,
                last_action TEXT,
                pr_url TEXT
            )
        """)
        
        # Create tasks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        
        # Create config table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS config (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        
        conn.commit()

def save_agent(agent_id: str, agent_data: Dict) -> bool:
    """Save or update an agent in the database."""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            
            # Convert lists to JSON strings
            progress_history = json.dumps(agent_data.get('progress_history', []))
            thought_history = json.dumps(agent_data.get('thought_history', []))
            
            cursor.execute("""
                INSERT OR REPLACE INTO agents VALUES (
                    :id, :workspace, :repo_path, :task, :status, :created_at, 
                    :last_updated, :aider_output, :last_critique, :progress, 
                    :thought, :progress_history, :thought_history, :future, 
                    :last_action, :pr_url
                )
            """, {
                'id': agent_id,
                'workspace': agent_data.get('workspace'),
                'repo_path': agent_data.get('repo_path'),
                'task': agent_data.get('task'),
                'status': agent_data.get('status', 'pending'),
                'created_at': agent_data.get('created_at', datetime.now().isoformat()),
                'last_updated': agent_data.get('last_updated', datetime.now().isoformat()),
                'aider_output': agent_data.get('aider_output', ''),
                'last_critique': agent_data.get('last_critique', ''),
                'progress': agent_data.get('progress', ''),
                'thought': agent_data.get('thought', ''),
                'progress_history': progress_history,
                'thought_history': thought_history,
                'future': agent_data.get('future', ''),
                'last_action': agent_data.get('last_action', ''),
                'pr_url': agent_data.get('pr_url', '')
            })
            conn.commit()
            return True
    except Exception as e:
        print(f"Error saving agent: {e}")
        return False

def get_agent(agent_id: str) -> Optional[Dict]:
    """Get an agent by ID."""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM agents WHERE id = ?", (agent_id,))
            row = cursor.fetchone()
            if row:
                agent_data = dict(row)
                # Convert JSON strings back to lists
                agent_data['progress_history'] = json.loads(agent_data['progress_history'])
                agent_data['thought_history'] = json.loads(agent_data['thought_history'])
                return agent_data
            return None
    except Exception as e:
        print(f"Error getting agent: {e}")
        return None

def get_all_agents() -> Dict[str, Dict]:
    """Get all agents."""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM agents")
            rows = cursor.fetchall()
            agents = {}
            for row in rows:
                agent_data = dict(row)
                # Convert JSON strings back to lists
                agent_data['progress_history'] = json.loads(agent_data['progress_history'])
                agent_data['thought_history'] = json.loads(agent_data['thought_history'])
                agents[agent_data['id']] = agent_data
            return agents
    except Exception as e:
        print(f"Error getting all agents: {e}")
        return {}

def delete_agent(agent_id: str) -> bool:
    """Delete an agent from the database."""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM agents WHERE id = ?", (agent_id,))
            conn.commit()
            return cursor.rowcount > 0
    except Exception as e:
        print(f"Error deleting agent: {e}")
        return False

def save_task(task_data: Dict) -> int:
    """Save a task to the database."""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO tasks (title, description, created_at)
                VALUES (:title, :description, :created_at)
            """, {
                'title': task_data.get('title'),
                'description': task_data.get('description'),
                'created_at': datetime.now().isoformat()
            })
            conn.commit()
            return cursor.lastrowid
    except Exception as e:
        print(f"Error saving task: {e}")
        return -1

def get_all_tasks() -> List[Dict]:
    """Get all tasks."""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks")
            return [dict(row) for row in cursor.fetchall()]
    except Exception as e:
        print(f"Error getting tasks: {e}")
        return []

def get_config(key: str) -> Optional[str]:
    """Get a config value."""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM config WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row[0] if row else None
    except Exception as e:
        print(f"Error getting config: {e}")
        return None

def save_config(key: str, value: str) -> bool:
    """Save a config value."""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO config (key, value)
                VALUES (:key, :value)
            """, {'key': key, 'value': value})
            conn.commit()
            return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False

def get_model_config() -> Optional[Dict]:
    """Get the current model configuration."""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM model_config ORDER BY id DESC LIMIT 1")
            config = cursor.fetchone()
            return dict(config) if config else None
    except Exception as e:
        print(f"Error getting model config: {e}")
        return None

# Initialize the database when this module is imported
init_db()
