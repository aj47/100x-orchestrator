import logging
import os
from functools import wraps
from flask import Flask, render_template, request, jsonify, send_from_directory, session, redirect, url_for
from dotenv import load_dotenv
from github_client import GitHubClient
from orchestrator import (
    initialiseCodingAgent, 
    main_loop, 
    load_tasks, 
    save_tasks, 
    delete_agent,
    normalize_path,
    validate_agent_paths,
    aider_sessions  # Add this import
)
import os
import threading
import json
from pathlib import Path
import datetime

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev')



# Initialize GitHub client map to store client instances per token
github_clients = {}

def get_github_client(token):
    """Get or create a GitHub client instance for the given token"""
    if token not in github_clients:
        try:
            github_clients[token] = GitHubClient(token)
        except Exception as e:
            app.logger.error(f"Failed to initialize GitHub client: {e}")
            return None
    return github_clients[token]

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('X-GitHub-Token')
        if not token or not get_github_client(token):
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

# Configure logging to be more verbose
from logging.handlers import RotatingFileHandler

# Create a file handler
file_handler = RotatingFileHandler('flask_debug.log', maxBytes=10000, backupCount=3)
file_handler.setLevel(logging.DEBUG)

# Create a console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Create a formatter and add it to the handlers
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add the handlers to the app's logger
app.logger.addHandler(file_handler)
app.logger.addHandler(console_handler)
# app.logger.setLevel(logging.DEBUG)

@app.route('/')
def index():
    token = request.headers.get('X-GitHub-Token')
    authenticated = bool(token and get_github_client(token))
    return render_template('index.html', authenticated=authenticated)

@app.route('/verify_token', methods=['POST'])
def verify_token():
    """Verify if a GitHub token is valid"""
    data = request.get_json()
    token = data.get('token')
    
    if not token:
        return jsonify({'valid': False}), 400
        
    try:
        client = get_github_client(token)
        if client and client.verify_token():
            return jsonify({'valid': True})
        return jsonify({'valid': False})
    except Exception as e:
        app.logger.error(f"Token verification error: {e}")
        return jsonify({'valid': False})

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
    
    # Add debug URLs to each agent
    for agent_id in agents:
        agents[agent_id]['debug_urls'] = {
            'info': f'/debug/agent/{agent_id}',
            'validate': f'/debug/validate_paths/{agent_id}'
        }
    
    # Calculate time until next check (reduced to 30 seconds for more frequent updates)
    now = datetime.datetime.now()
    next_check = now + datetime.timedelta(seconds=30)
    time_until_next_check = int((next_check - now).total_seconds())
    
    # Ensure basic agent data exists
    for agent_id, agent in list(agents.items()):
        if 'aider_output' not in agent:
            agent['aider_output'] = ''
        if 'last_updated' not in agent:
            agent['last_updated'] = None
    
    # Save updated tasks data
    save_tasks(tasks_data)
    
    return render_template('agent_view.html', 
                           agents=agents, 
                           time_until_next_check=time_until_next_check)

@app.route('/create_agent', methods=['POST'])
def create_agent():
    try:
        data = request.get_json()
        repo_url = data.get('repo_url')
        tasks = data.get('tasks', [])
        num_agents = data.get('num_agents', 1)  # Default to 1 if not specified
        
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
                agent_ids = initialiseCodingAgent(
                    repository_url=repo_url, 
                    task_description=task_description, 
                    num_agents=num_agents
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
        
        # Update tasks.json with repo URL and agents
        tasks_data['repository_url'] = repo_url
        tasks_data['agents'] = tasks_data.get('agents', {})
        for agent_id in created_agents:
            tasks_data['agents'][agent_id] = {
                'task': tasks_data['tasks'][-1],
                'repo_url': repo_url,
                'status': 'pending',
                'created_at': datetime.datetime.now().isoformat(),
                'last_updated': datetime.datetime.now().isoformat(),
                'aider_output': ''
            }
        
        # Save updated tasks
        save_tasks(tasks_data)
        
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

@app.route('/debug/agent/<agent_id>')
def debug_agent(agent_id):
    """Debug endpoint to show agent details and path information."""
    try:
        tasks_data = load_tasks()
        agent_data = tasks_data['agents'].get(agent_id)
        
        if not agent_data:
            return jsonify({
                'error': f'Agent {agent_id} not found'
            }), 404
            
        # Get normalized paths
        workspace_path = normalize_path(agent_data.get('workspace'))
        repo_path = normalize_path(agent_data.get('repo_path'))
        
        # Get aider session info if it exists
        aider_session = aider_sessions.get(agent_id)
        aider_workspace = normalize_path(aider_session.workspace_path) if aider_session else None
        
        debug_info = {
            'agent_id': agent_id,
            'paths': {
                'workspace': {
                    'raw': agent_data.get('workspace'),
                    'normalized': workspace_path,
                    'exists': os.path.exists(workspace_path) if workspace_path else False
                },
                'repo_path': {
                    'raw': agent_data.get('repo_path'),
                    'normalized': repo_path,
                    'exists': os.path.exists(repo_path) if repo_path else False
                },
                'aider_workspace': {
                    'raw': aider_session.workspace_path if aider_session else None,
                    'normalized': aider_workspace,
                    'exists': os.path.exists(aider_workspace) if aider_workspace else False
                }
            },
            'aider_session': {
                'exists': aider_session is not None,
                'output_buffer_length': len(aider_session.get_output()) if aider_session else 0,
                'session_id': aider_session.session_id if aider_session else None
            },
            'agent_data': {
                'status': agent_data.get('status'),
                'created_at': agent_data.get('created_at'),
                'last_updated': agent_data.get('last_updated'),
                'aider_output_length': len(agent_data.get('aider_output', '')),
                'task': agent_data.get('task')
            }
        }
        
        return jsonify(debug_info)
        
    except Exception as e:
        app.logger.error(f"Error in debug endpoint: {str(e)}", exc_info=True)
        return jsonify({
            'error': str(e)
        }), 500

@app.route('/debug/validate_paths/<agent_id>')
def debug_validate_paths(agent_id):
    """Debug endpoint to validate path matching for an agent."""
    try:
        tasks_data = load_tasks()
        agent_data = tasks_data['agents'].get(agent_id)
        
        if not agent_data:
            return jsonify({
                'error': f'Agent {agent_id} not found'
            }), 404
        
        # Get aider session
        aider_session = aider_sessions.get(agent_id)
        
        validation_results = {
            'agent_id': agent_id,
            'paths': {
                'workspace': {
                    'raw': agent_data.get('workspace'),
                    'normalized': normalize_path(agent_data.get('workspace'))
                },
                'repo_path': {
                    'raw': agent_data.get('repo_path'),
                    'normalized': normalize_path(agent_data.get('repo_path'))
                },
                'aider_workspace': {
                    'raw': aider_session.workspace_path if aider_session else None,
                    'normalized': normalize_path(aider_session.workspace_path) if aider_session else None
                }
            },
            'validation': {
                'has_aider_session': aider_session is not None
            }
        }
        
        if aider_session:
            # Validate paths
            validation_results['validation']['path_match'] = validate_agent_paths(
                agent_id, 
                aider_session.workspace_path
            )
            validation_results['validation']['output_length'] = len(aider_session.get_output())
            validation_results['validation']['stored_output_length'] = len(agent_data.get('aider_output', ''))
        
        return jsonify(validation_results)
        
    except Exception as e:
        app.logger.error(f"Error in path validation debug endpoint: {str(e)}", exc_info=True)
        return jsonify({
            'error': str(e)
        }), 500

@app.route('/github/repositories')
@login_required
def list_repositories():
    """Get list of GitHub repositories"""
    token = request.headers.get('X-GitHub-Token')
    client = get_github_client(token)
    
    if not client:
        return jsonify({'error': 'GitHub client not initialized'}), 500
        
    repos = client.get_repositories()
    return jsonify({'repositories': repos})

@app.route('/github/commits/<path:repo_name>')
@login_required
def get_commits(repo_name):
    """Get recent commits for a repository"""
    if not github_client:
        return jsonify({'error': 'GitHub client not initialized'}), 500
        
    branch = request.args.get('branch', 'main')
    limit = int(request.args.get('limit', 10))
    
    commits = github_client.get_recent_commits(repo_name, branch, limit)
    return jsonify({'commits': commits})

@app.route('/github/pull-request', methods=['POST'])
@login_required
def create_pull_request():
    """Create a new pull request"""
    if not github_client:
        return jsonify({'error': 'GitHub client not initialized'}), 500
        
    data = request.get_json()
    required = ['repo_name', 'title', 'head']
    if not all(k in data for k in required):
        return jsonify({'error': 'Missing required fields'}), 400
        
    pr = github_client.create_pull_request(
        repo_name=data['repo_name'],
        title=data['title'],
        head=data['head'],
        base=data.get('base', 'main'),
        body=data.get('body')
    )
    
    if pr:
        return jsonify({'pull_request': pr})
    return jsonify({'error': 'Failed to create pull request'}), 500

@app.route('/github/issues/<path:repo_identifier>')
@login_required
def get_repository_issues(repo_identifier):
    """Get issues from a GitHub repository"""
    if not github_client:
        return jsonify({'error': 'GitHub client not initialized'}), 500
    
    try:
        # Handle both full repository names and URLs
        if '/' not in repo_identifier or repo_identifier.count('/') != 1:
            # Try to extract owner/repo from URL
            from urllib.parse import urlparse
            parsed = urlparse(repo_identifier)
            path_parts = parsed.path.strip('/').split('/')
            if len(path_parts) >= 2:
                repo_identifier = f"{path_parts[-2]}/{path_parts[-1].replace('.git', '')}"
            else:
                return jsonify({'error': 'Invalid repository identifier'}), 400
        
        issues = github_client.get_repository_issues(repo_identifier)
        return jsonify({'issues': issues})
    except Exception as e:
        app.logger.error(f"Error getting repository issues: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
