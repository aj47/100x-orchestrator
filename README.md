# 100x-orchestrator

A web-based orchestration system for managing AI coding agents with advanced multi-layered architecture.

## Architecture Overview

The 100x-orchestrator system consists of three key components:

1. **Orchestrator**: 
   - The central control unit managing the entire system
   - Coordinates agent creation, task allocation, and monitoring
   - Handles resource management and inter-agent communication

2. **Aider Sessions**: 
   - Individual task-specific sessions responsible for executing coding tasks
   - Each session has its own workspace and dedicated configuration
   - Manages the lifecycle of its associated Aider instance

3. **Aider Instances**: 
   - Actual AI coding assistants that perform specific coding operations
   - Dedicated to each Aider Session
   - Interact directly with the repository and execute coding tasks

## Project Structure

```
100x-orchestrator/
├── app.py                  # Web interface
├── orchestrator/           # Core orchestration logic
│   ├── __init__.py
│   ├── orchestrator.py     # Main orchestration logic
│   ├── aider_session.py    # Aider session management
│   ├── prompt_processor.py # Response processing
│   └── critique_handler.py # Code review validation
├── requirements.txt        # Project dependencies
├── tasks/                  # Task configuration
├── templates/             # Web interface templates
└── workspaces/           # Session workspaces
```

## Features

- **Advanced Multi-Session Management**: Create and manage multiple AI coding sessions with granular control
- **Real-Time Output Tracking**: Monitor session and Aider instance progress
- **Git Integration**: Automatic repository cloning and branch management
- **Workspace Isolation**: Strict isolation for each session and its Aider instance
- **Web Interface**: Comprehensive dashboard for system monitoring
- **Intelligent Session Management**: Robust handling of session lifecycles and Aider interactions

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
    "repository_url": "",
    "config": {
        "aider_session": {}
    }
}
```

## Usage

1. Start the web server:
```bash
python app.py
```

2. Access the web interface at `http://localhost:5000`

3. Create new sessions:
   - Enter a Git repository URL
   - Define your tasks
   - Choose number of sessions per task
   - Click "Create Session"

4. Monitor progress:
   - View real-time session outputs
   - Check session status
   - Manage session lifecycle

## Technical Stack

- Python 3.8+
- Flask
- Aider
- Git
- LiteLLM
- Threading

## Python Coding Standards

1. Conciseness
   - Write clear, concise code that is easy to understand
   - Avoid unnecessary comments - let code be self-documenting
   - Keep functions small and focused
   - Remove redundant code

2. Imports & Structure
   - Group: stdlib > third-party > local
   - Use absolute imports
   - One import per line

3. Naming & Style
   - snake_case for functions/variables
   - PascalCase for classes
   - UPPERCASE for constants
   - Max line length: 100

4. Safety & Error Handling
   - Use subprocess.check_call() over run()
   - Catch specific exceptions
   - Use type hints
   - Always handle errors gracefully

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

[MIT License](LICENSE)
