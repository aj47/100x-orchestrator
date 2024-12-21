from flask import Flask, request, jsonify
import json
import logging
from pathlib import Path

app = Flask(__name__)
CONFIG_FILE = Path("tasks/tasks.json")

@app.route('/add_task', methods=['POST'])
def add_task():
    try:
        data = request.get_json()
        task = data.get('task')
        if not task:
            return jsonify({'error': 'Task data is missing'}), 400

        tasks_data = load_tasks()
        tasks_data['tasks'].append(task)
        save_tasks(tasks_data)
        return jsonify({'message': 'Task added successfully'}), 201
    except Exception as e:
        logging.exception(f"Error adding task: {e}")
        return jsonify({'error': 'Failed to add task'}), 500

def load_tasks():
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {'tasks': []}
    except json.JSONDecodeError:
        logging.exception("Error decoding tasks.json")
        return {'tasks': []}

def save_tasks(tasks_data):
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(tasks_data, f, indent=4)
    except Exception as e:
        logging.exception(f"Error saving tasks: {e}")

if __name__ == '__main__':
    app.run(debug=True)
