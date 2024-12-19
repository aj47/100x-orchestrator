from flask import Flask, render_template, request, jsonify, send_from_directory
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


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/tasks/tasks.json')
def serve_tasks_json():
    """Serve the tasks.json file, creating it if it doesn't exist"""
    tasks_file = Path('tasks/tasks.json')
    
    # Ensure tasks directory exists
    tasks_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Create file with default content if it doesn't exist
    if not tasks_file.exists():
        default_data = {
            "tasks": [],
            "agents": {},
            "repository_url": "",
            "config": {
                "agent_session": {}
            }
        }
        with tasks_file.open('w') as f:
            json.dump(default_data, f, indent=4)
    
    return send_from_directory('tasks', 'tasks.json')

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
        github_token = data.get('github_token')

        if not github_token:
            return jsonify({'error': 'GitHub token is required'}), 400

        # Save token to .env file
        env_path = Path.home() / '.env'
        with open(env_path, 'a') as f:
            f.write(f"\nGITHUB_TOKEN={github_token}\n")
        
        if not repo_url or not tasks:
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
                task_text = f"{task_description['title']}\n\nDetails:\n{task_description['description']}"
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
    app.run(debug=True)
