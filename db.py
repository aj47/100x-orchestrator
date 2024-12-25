import sqlite3
from pathlib import Path
import logging

DATABASE_PATH = Path("tasks/agents.db")

def init_db():
    """Initialize the database and create the agents table if it doesn't exist."""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agents (
                    agent_id TEXT PRIMARY KEY,
                    workspace TEXT,
                    repo_path TEXT,
                    task TEXT,
                    status TEXT,
                    created_at TEXT,
                    last_updated TEXT,
                    aider_output TEXT,
                    progress TEXT,
                    thought TEXT,
                    progress_history TEXT,
                    thought_history TEXT,
                    future TEXT,
                    last_action TEXT,
                    pr_url TEXT
                )
            """)
            conn.commit()
        logging.info("Database initialized successfully.")
    except Exception as e:
        logging.error(f"Error initializing database: {e}", exc_info=True)

def create_agent(agent_data):
    """Create a new agent in the database."""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO agents (
                    agent_id, workspace, repo_path, task, status, created_at, last_updated,
                    aider_output, progress, thought, progress_history, thought_history,
                    future, last_action, pr_url
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                agent_data['agent_id'], agent_data['workspace'], agent_data['repo_path'],
                agent_data['task'], agent_data['status'], agent_data['created_at'],
                agent_data['last_updated'], agent_data['aider_output'],
                agent_data['progress'], agent_data['thought'],
                agent_data.get('progress_history', ''), agent_data.get('thought_history', ''),
                agent_data['future'], agent_data['last_action'], agent_data.get('pr_url', '')
            ))
            conn.commit()
        logging.info(f"Agent {agent_data['agent_id']} created successfully.")
    except Exception as e:
        logging.error(f"Error creating agent: {e}", exc_info=True)

def get_agent(agent_id):
    """Retrieve an agent from the database by agent_id."""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM agents WHERE agent_id = ?", (agent_id,))
            agent = cursor.fetchone()
            if agent:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, agent))
            else:
                return None
    except Exception as e:
        logging.error(f"Error retrieving agent {agent_id}: {e}", exc_info=True)
        return None

def update_agent(agent_id, updates):
    """Update an agent's data in the database."""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            set_clause = ', '.join([f"{key} = ?" for key in updates])
            values = list(updates.values())
            values.append(agent_id)
            cursor.execute(f"UPDATE agents SET {set_clause} WHERE agent_id = ?", tuple(values))
            conn.commit()
        logging.info(f"Agent {agent_id} updated successfully.")
    except Exception as e:
        logging.error(f"Error updating agent {agent_id}: {e}", exc_info=True)

def delete_agent(agent_id):
    """Delete an agent from the database."""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM agents WHERE agent_id = ?", (agent_id,))
            conn.commit()
        logging.info(f"Agent {agent_id} deleted successfully.")
    except Exception as e:
        logging.error(f"Error deleting agent {agent_id}: {e}", exc_info=True)

def get_all_agents():
    """Retrieve all agents from the database."""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM agents")
            agents = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, agent)) for agent in agents]
    except Exception as e:
        logging.error(f"Error retrieving all agents: {e}", exc_info=True)
        return []
