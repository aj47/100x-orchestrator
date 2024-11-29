# 100x-orchestrator

A web-based orchestration system for managing AI coding agents. The system uses Aider (an AI coding assistant) to handle coding tasks and provides real-time monitoring of agent outputs through a user-friendly interface.

## Features

- **Multi-Agent Management**: Create and manage multiple AI coding agents
- **Real-Time Output Tracking**: Monitor agent progress and outputs in real-time
- **Git Integration**: Automatic repository cloning and branch management
- **Workspace Isolation**: Each agent works in an isolated environment
- **Web Interface**: User-friendly dashboard for agent management
- **Session Management**: Robust handling of agent sessions and outputs

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/100x-orchestrator.git
cd 100x-orchestrator
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
.venv\Scripts\activate  # On Windows
source .venv/bin/activate  # On Unix/MacOS
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

1. Set up your environment variables:
```bash
set LITELLM_MODEL=anthropic/claude-3-5-sonnet-20240620  # On Windows
# export LITELLM_MODEL=anthropic/claude-3-5-sonnet-20240620  # On Unix/MacOS
```

2. The system uses tasks.json for configuration:
```json
{
    "tasks": [],
    "agents": {},
    "repository_url": ""
}
```

## Usage

1. Start the web server:
```bash
python app.py
```

2. Access the web interface at `http://localhost:5000`

3. Create new agents:
   - Enter a Git repository URL
   - Define your tasks
   - Choose number of agents per task
   - Click "Create Agent"

4. Monitor progress:
   - View real-time agent outputs
   - Check agent status
   - Manage agent lifecycle

## Project Structure

```
100x-orchestrator/
├── app.py              # Web interface
├── orchestrator.py     # Core orchestration logic
├── requirements.txt    # Project dependencies
├── tasks/             # Task configuration
├── templates/         # Web interface templates
└── workspaces/        # Agent workspaces
```

## Technical Stack

- Python 3.8+
- Flask
- Aider
- Git
- LiteLLM
- Threading

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[MIT License](LICENSE)
