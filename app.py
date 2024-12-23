from flask import Flask, render_template, jsonify
from orchestrator import Orchestrator

app = Flask(__name__)
orchestrator = Orchestrator()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/agents')
def agents():
    # Replace this with your actual agent data retrieval logic
    agents = [
        {'id': 'agent1', 'status': 'pending'},
        {'id': 'agent2', 'status': 'completed', 'pr_url': 'https://github.com/example/repo/pull/1'}
    ]
    return jsonify(agents)

if __name__ == '__main__':
    app.run(debug=True)
