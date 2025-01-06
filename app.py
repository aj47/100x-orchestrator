import logging
import sqlite3
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.serving import WSGIRequestHandler

# Database configuration
DATABASE_PATH = Path("tasks.db")

# Custom log filter to suppress specific log messages
class TasksJsonLogFilter(logging.Filter):
    def filter(self, record):
        # Suppress log messages for tasks.json requests
        return not ('/tasks/tasks.json' in record.getMessage())
from orchestrator import (
    initialiseCodingAgent, 
    main_loop, 
    load_tasks, 
    save_tasks, 
    delete_agent,
    aider_sessions  # Add this import
)
import os
import threading
import json
from pathlib import Path
import datetime

app = Flask(__name__)

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

# Add filter to suppress tasks.json log messages
for handler in logging.getLogger().handlers:
    handler.addFilter(TasksJsonLogFilter())

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/tasks/tasks.json')
def serve_tasks_json():
    """Serve tasks data in JSON format from database."""
    tasks_data = load_tasks()
    return jsonify(tasks_data)

@app.route('/agents')
def agent_view():
    """Render the agent view with all agent details."""
    tasks_data = load_tasks()
    agents = tasks_data.get('agents', {})
    
    # Calculate time until next check (reduced to 30 seconds for more frequent updates)
    now = datetime.datetime.now()
    next_check = now + datetime.timedelta(seconds=30)
    
    # Ensure basic agent data exists and add new fields if missing
    for agent_id, agent in list(agents.items()):
        # Ensure basic fields exist
        agent.setdefault('aider_output', '')
        agent.setdefault('last_updated', None)
        
        # Add new fields for progress tracking
        agent.setdefault('progress', '')
        agent.setdefault('thought', '')
        agent.setdefault('future', '')
        agent.setdefault('last_action', '')
    
    # Save updated tasks data
    save_tasks(tasks_data)
    
    return render_template('agent_view.html', 
                           agents=agents)

@app.route('/create_agent', methods=['POST'])
def create_agent():
    try:
        data = request.get_json()
        repo_url = data.get('repo_url')
        tasks = data.get('tasks', [])
        num_agents = data.get('num_agents', 1)  # Default to 1 if not specified
        aider_commands = data.get('aider_commands') # Get aider commands
        github_token = request.headers.get('X-GitHub-Token')
        if not github_token:
            return jsonify({'error': 'GitHub token is required'}), 400

        # Save token using manager
        from github_token import GitHubTokenManager
        token_manager = GitHubTokenManager()
        if not token_manager.set_token(github_token):
            return jsonify({'error': 'Failed to save GitHub token'}), 500
        
        # Enhanced logging for debugging
        app.logger.info(f"Received create_agent request: {data}")
        
        if not repo_url or not tasks:
            app.logger.error("Missing repository URL or tasks")
            return jsonify({'error': 'Repository URL and tasks are required'}), 400
        
        # Ensure tasks is a list
        if isinstance(tasks, str):
            tasks = [tasks]
        
        # Load existing tasks
        tasks_data = load_tasks()
        
        # Initialize agents for each task
        created_agents = []
        for task_description in tasks:
            # Set environment variable for repo URL
            os.environ['REPOSITORY_URL'] = repo_url
            
            app.logger.info(f"Attempting to initialize agent for task: {task_description}")
            
            # Initialize agent with specified number of agents per task
            try:
                # task_text = f"{task_description['title']}\n\nDetails:\n{task_description['description']}"
                task_text = task_description['title']
                if (task_description['description']):
                    task_text += f"\n\n{task_description['description']}"
                agent_ids = initialiseCodingAgent(
                    repository_url=repo_url, 
                    task_description=task_text,
                    num_agents=num_agents,
                    aider_commands=aider_commands # Pass aider commands
                )
                
                if agent_ids:
                    created_agents.extend(agent_ids)
                    # Add task to tasks list if not already present
                    if task_description not in tasks_data['tasks']:
                        tasks_data['tasks'].append(task_description)
                else:
                    app.logger.warning(f"Failed to create agents for task: {task_description}")
            except Exception as task_error:
                app.logger.error(f"Error initializing agent for task {task_description}: {task_error}", exc_info=True)
        
        # Start main loop in a separate thread if not already running
        def check_and_start_main_loop():
            # Check if main loop thread is already running
            for thread in threading.enumerate():
                if thread.name == 'OrchestratorMainLoop':
                    return
            
            # Start main loop if not running
            thread = threading.Thread(target=main_loop, name='OrchestratorMainLoop')
            thread.daemon = True
            thread.start()
        
        check_and_start_main_loop()
        
        if created_agents:
            app.logger.info(f"Successfully created agents: {created_agents}")
            return jsonify({
                'success': True,
                'agent_ids': created_agents,
                'message': f'Agents {", ".join(created_agents)} created successfully'
            })
        else:
            app.logger.error("Failed to create any agents")
            return jsonify({
                'success': False,
                'error': 'Failed to create any agents'
            }), 500
            
    except Exception as e:
        # Log the full exception details
        app.logger.error(f"Unexpected error in create_agent: {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/config/models', methods=['POST'])
def update_model_config():
    """Update the model configuration for orchestrator, aider and agent."""
    try:
        data = request.get_json()
        required_fields = ['orchestrator_model', 'aider_model', 'agent_model']
        
        if not all(field in data for field in required_fields):
            return jsonify({
                'success': False,
                'error': 'Missing required fields. Need orchestrator_model, aider_model, and agent_model'
            }), 400
        
        # Get existing config to preserve aider_prompt_suffix if not provided
        existing_config = get_model_config()
        aider_prompt_suffix = data.get('aider_prompt_suffix', existing_config.get('aider_prompt_suffix', ''))
        
        # Save to database
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.cursor()
            # Delete any existing config
            cursor.execute("DELETE FROM model_config")
            # Insert new config
            cursor.execute("""
                INSERT INTO model_config (
                    orchestrator_model, aider_model, agent_model, 
                    aider_prompt_suffix, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                data['orchestrator_model'],
                data['aider_model'],
                data['agent_model'],
                aider_prompt_suffix,
                datetime.datetime.now().isoformat(),
                datetime.datetime.now().isoformat()
            ))
            conn.commit()
            
        return jsonify({
            'success': True,
            'message': 'Model configuration updated successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/config/models', methods=['GET'])
def get_model_config():
    """Get the current model configuration."""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM model_config ORDER BY id DESC LIMIT 1")
            config = cursor.fetchone()
            
            if config:
                config_dict = dict(config)
                # Ensure all required fields are present
                required_fields = ['orchestrator_model', 'aider_model', 'agent_model']
                for field in required_fields:
                    if field not in config_dict:
                        config_dict[field] = {
                            'orchestrator_model': 'openrouter/google/gemini-flash-1.5',
                            'aider_model': 'openrouter/google/gemini-flash-1.5',
                            'agent_model': 'openrouter/google/gemini-flash-1.5'
                        }[field]
                return jsonify({
                    'success': True,
                    'config': config_dict
                })
            else:
                # Return default values if no config exists
                return jsonify({
                    'success': True,
                    'config': {
                        'orchestrator_model': 'openrouter/google/gemini-flash-1.5',
                        'aider_model': 'openrouter/google/gemini-flash-1.5',
                        'agent_model': 'openrouter/google/gemini-flash-1.5'
                    }
                })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/config')
def config_view():
    """Render the configuration view."""
    return render_template('config_view.html')

@app.route('/delete_agent/<agent_id>', methods=['DELETE'])
def remove_agent(agent_id):
    try:
        # Load current tasks
        tasks_data = load_tasks()
        
        # Check if agent exists
        if agent_id not in tasks_data['agents']:
            return jsonify({
                'success': False, 
                'error': f'Agent {agent_id} not found'
            }), 404
        
        # Delete the agent
        deletion_result = delete_agent(agent_id)
        
        if deletion_result:
            # Remove agent from tasks.json
            del tasks_data['agents'][agent_id]
            save_tasks(tasks_data)
            
            return jsonify({
                'success': True,
                'message': f'Agent {agent_id} deleted successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Failed to delete agent {agent_id}'
            }), 500
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    try:
        # Verify database is initialized
        from database import init_db
        init_db()
        
        app.run(debug=True, use_reloader=False)
    except Exception as e:
        print(f"Fatal error during startup: {e}")
        print("Try deleting tasks.db and restarting the application")
