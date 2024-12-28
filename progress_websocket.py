from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
import logging
from orchestrator import cloneRepository

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!' # Replace with a strong secret key
socketio = SocketIO(app, cors_allowed_origins="*") # Allow all origins for development.  Restrict in production.

@socketio.on('clone_repo')
def handle_clone_repo(data):
    repo_url = data.get('repo_url')
    if not repo_url:
        emit('clone_progress', {'status': 'error', 'message': 'No repository URL provided'})
        return

    def send_progress(message):
        emit('clone_progress', message)

    try:
        for progress_update in cloneRepository(repo_url, progress_callback=send_progress):
            pass  # Progress updates are handled by the generator and send_progress
        emit('clone_progress', {'status': 'success', 'message': 'Repository cloned successfully'})
    except Exception as e:
        emit('clone_progress', {'status': 'error', 'message': f'Error cloning repository: {str(e)}'})

if __name__ == '__main__':
    socketio.run(app, debug=True)
