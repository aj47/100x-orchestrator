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
        """
        Filter log records to suppress messages for '/tasks/tasks.json' requests.
        
        This method checks if the log record's message contains '/tasks/tasks.json' and returns
        False to suppress logging for these specific requests; otherwise, it returns True.
        """
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
    level=logging.WARNING,
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
    """
    Render the main index page.
    
    This view function renders and returns the 'index.html' template as the landing page.
    """
    return render_template('index.html')

@app.route('/tasks/tasks.json')
def serve_tasks_json():
    """Serve tasks data in JSON format from database."""
    tasks_data = load_tasks()
    return jsonify(tasks_data)

@app.route('/agents')
def agent_view():
    """
    Render the agent view HTML with updated agent details.
    
    Loads tasks data, ensures each agent contains default fields for output and progress
    tracking (such as 'aider_output', 'last_updated', 'progress', 'thought', 'future',
    and 'last_action'), saves any modifications, and returns the rendered HTML template.
    """
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
    """
    Creates coding agents based on repository and task information provided in a JSON request.
    
    Extracts the repository URL, tasks, number of agents, and aider commands from the JSON payload, and requires a 
    GitHub token supplied in the "X-GitHub-Token" header. For each task, initializes an agent using the repository and 
    task details, updates the tasks store, and ensures that the main orchestrator loop is running in a separate thread.
    Returns a JSON response with a success flag and agent identifiers if agents are created successfully; otherwise, 
    an error message with an appropriate HTTP status code.
    """
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
    """
    Update and persist model configuration settings.
    
    This endpoint processes a JSON payload containing updated model settings for the orchestrator,
    aider, and agent. The payload must include the following keys:
      - orchestrator_model
      - aider_model
      - agent_model
      - orchestrator_api_key
      - aider_api_key
      - agent_api_key
      - provider
    
    Optionally, an 'aider_prompt_suffix' can be provided; if omitted, the existing value is retained.
    Upon successful validation, any previous configuration is cleared and the new settings are saved
    to the database. A JSON response is returned indicating success or describing any error encountered.
    """
    try:
        data = request.get_json()
        required_fields = ['orchestrator_model', 'aider_model', 'agent_model', 'orchestrator_api_key', 'aider_api_key', 'agent_api_key', 'provider']
        
        if not all(field in data for field in required_fields):
            return jsonify({
                'success': False,
                'error': 'Missing required fields. Need orchestrator_model, aider_model, agent_model, orchestrator_api_key, aider_api_key, agent_api_key and provider'
            }), 400
        
        # Get existing config to preserve aider_prompt_suffix if not provided
        existing_config = get_model_config()
        aider_prompt_suffix = data.get('aider_prompt_suffix', (existing_config or {}).get('aider_prompt_suffix', ''))
        
        # Save to database
        with sqlite3.connect(DATABASE_PATH) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            cursor = conn.cursor()
            # Delete any existing config
            cursor.execute("DELETE FROM model_config")
            # Insert new config
            cursor.execute("""
                INSERT INTO model_config (
                    orchestrator_model, aider_model, agent_model, 
                    aider_prompt_suffix, created_at, updated_at,
                    orchestrator_api_key, aider_api_key, agent_api_key, provider
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['orchestrator_model'],
                data['aider_model'],
                data['agent_model'],
                aider_prompt_suffix,
                datetime.datetime.now().isoformat(),
                datetime.datetime.now().isoformat(),
                data['orchestrator_api_key'],
                data['aider_api_key'],
                data['agent_api_key'],
                data['provider']
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
    """
    Retrieve the latest model configuration from the database.
    
    This function queries the "model_config" table for the most recent record. If a configuration
    is found, it verifies that all required fields—namely, orchestrator_model, aider_model, agent_model,
    aider_prompt_suffix, orchestrator_api_key, aider_api_key, agent_api_key, and provider—are present,
    assigning default values for any missing fields. If no record is found, a default configuration is returned.
    In case of a database error, the function returns an error dictionary paired with an HTTP 500 status code.
    
    Returns:
        dict: On success, a dictionary with "success" set to True and a "config" key containing the model
              configuration. On error, a tuple where the first element is a dictionary with "success" set to
              False and an "error" message, and the second element is the HTTP status code 500.
    """
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM model_config ORDER BY id DESC LIMIT 1")
            config = cursor.fetchone()
            
            if config:
                config_dict = dict(config)
                # Ensure all required fields are present
                required_fields = ['orchestrator_model', 'aider_model', 'agent_model', 'aider_prompt_suffix', 'orchestrator_api_key', 'aider_api_key', 'agent_api_key', 'provider']
                for field in required_fields:
                    if field not in config_dict:
                        config_dict[field] = {
                            'orchestrator_model': 'openrouter/google/gemini-flash-1.5',
                            'aider_model': 'openrouter/google/gemini-flash-1.5',
                            'agent_model': 'openrouter/google/gemini-flash-1.5',
                            'aider_prompt_suffix': '',
                            'orchestrator_api_key': '',
                            'aider_api_key': '',
                            'agent_api_key': '',
                            'provider': ''
                        }[field]
                return {
                    'success': True,
                    'config': config_dict
                }
            else:
                # Return default values if no config exists
                return {
                    'success': True,
                    'config': {
                        'orchestrator_model': 'openrouter/google/gemini-flash-1.5',
                        'aider_model': 'openrouter/google/gemini-flash-1.5',
                        'agent_model': 'openrouter/google/gemini-flash-1.5',
                        'aider_prompt_suffix': '',
                        'orchestrator_api_key': '',
                        'aider_api_key': '',
                        'agent_api_key': '',
                        'provider': ''
                    }
                }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }, 500

@app.route('/config')
def config_view():
    """Render the configuration view."""
    return render_template('config_view.html')

@app.route('/delete_agent/<agent_id>', methods=['DELETE'])
def remove_agent(agent_id):
    """
    Remove an agent identified by agent_id from the tasks data and database.
    
    This function loads the current tasks data and checks for the existence of the specified agent.
    If the agent is found, it attempts to delete the agent from the database and, upon success,
    removes the agent from the tasks data and updates the JSON file. It returns a JSON response
    with a success message if the deletion is successful, or an error message with an appropriate
    HTTP status code if the agent is not found or if the deletion fails.
      
    Args:
        agent_id: The identifier of the agent to remove.
      
    Returns:
        A JSON response object containing a 'success' flag and either a success message or an error message.
    """
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
        
        app.run(debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true', use_reloader=False)
    except Exception as e:
        print(f"Fatal error during startup: {e}")
        print("Try deleting tasks.db and restarting the application")
