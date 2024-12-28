import logging
import sqlite3
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.serving import WSGIRequestHandler
from flask_socketio import SocketIO, emit

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
    aider_sessions,
    cloneRepository
)
import os
import threading
import json
from pathlib import Path
import datetime

app = Flask(__name__)
socketio = SocketIO(app) # Initialize SocketIO

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

# ... (rest of the app.py code remains the same)

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    emit('message', {'data': 'Connected'})

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    socketio.run(app, debug=True)
