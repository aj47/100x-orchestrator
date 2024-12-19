from flask import Flask, render_template, request, jsonify, send_from_directory

from orchestrator import (
    initialiseCodingAgent, 
    main_loop, 
    load_tasks, 
    save_tasks, 
    delete_agent,
    aider_sessions
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
    tasks_file = Path('tasks/tasks.json')
    tasks_file.parent.mkdir(parents=True, exist_ok=True)
    
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
    tasks_data = load_tasks()
    agents = tasks_data.get('agents', {})
    
    now = datetime.datetime.now()
    next_check = now + datetime.timedelta(seconds=30)
    
    for agent_id, agent in list(agents.items()):
        agent.setdefault('aider_output', '')
        agent.setdefault('last_updated', None)
        agent.setdefault('progress', '')
        agent.setdefault('thought', '')
        agent.setdefault('future', '')
        agent.setdefault('last_action', '')
    
    save_tasks(tasks_data)
    
    return render_template('agent_view.html', agents=agents)

@app.route('/agents/<agent_id>/history')
def agent_history(agent_id):
    tasks_data = load_tasks()
    agent = tasks_data["agents"].get(agent_id)
    if not agent:
        return jsonify({"error": "Agent not found"}), 404
    progress_history = agent.get("progress_history", [])
    thought_history  = agent.get("thought_history", [])
    feedback_history = agent.get("feedback_history", [])
    return render_template(
        'agent_history.html',
        agent_id=agent_id,
        progress_history=progress_history,
        thought_history=thought_history,
        feedback_history=feedback_history
    )

@app.route('/create_agent', methods=['POST'])
def create_agent():
    try:
        data = request.get_json()
        repo_url = data.get('repo_url')
        tasks = data.get('tasks', [])
        num_agents = data.get('num_agents', 1)
        aider_commands = data.get('aider_commands')
        github_token = data.get('github_token')

        # Add these two lines to read and save acceptance_criteria
        acceptance_criteria = data.get('acceptance_criteria', "")
        tasks_data = load_tasks()
        tasks_data['acceptance_criteria'] = acceptance_criteria
        save_tasks(tasks_data)

        if not github_token:
            return jsonify({'error': 'GitHub token is required'}), 400

        env_path = Path.home() / '.env'
        with open(env_path, 'a') as f:
            f.write(f"\nGITHUB_TOKEN={github_token}\n")
        
        if not repo_url or not tasks:
            return jsonify({'error': 'Repository URL and tasks are required'}), 400
        
        if isinstance(tasks, str):
            tasks = [tasks]
        
        tasks_data = load_tasks()
        created_agents = []
        
        for task_description in tasks:
            os.environ['REPOSITORY_URL'] = repo_url
            
            try:
                task_text = f"{task_description['title']}\n\nDetails:\n{task_description['description']}"
                agent_ids = initialiseCodingAgent(
                    repository_url=repo_url, 
                    task_description=task_text,
                    num_agents=num_agents,
                    aider_commands=aider_commands
                )
                
                if agent_ids:
                    created_agents.extend(agent_ids)
                    if task_description not in tasks_data['tasks']:
                        tasks_data['tasks'].append(task_description)
            except Exception as task_error:
                return jsonify({'error': str(task_error)}), 500
        
        def check_and_start_main_loop():
            for thread in threading.enumerate():
                if thread.name == 'OrchestratorMainLoop':
                    return
            
            thread = threading.Thread(target=main_loop, name='OrchestratorMainLoop')
            thread.daemon = True
            thread.start()
        
        check_and_start_main_loop()
        
        if created_agents:
            return jsonify({
                'success': True,
                'agent_ids': created_agents,
                'message': f'Agents {", ".join(created_agents)} created successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to create any agents'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/delete_agent/<agent_id>', methods=['DELETE'])
def remove_agent(agent_id):
    try:
        tasks_data = load_tasks()
        
        if agent_id not in tasks_data['agents']:
            return jsonify({
                'success': False, 
                'error': f'Agent {agent_id} not found'
            }), 404
        
        deletion_result = delete_agent(agent_id)
        
        if deletion_result:
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
