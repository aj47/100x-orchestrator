# 100x-orchestrator

A web-based orchestration system for managing AI coding agents with advanced multi-layered architecture.

## Architecture Overview

The 100x-orchestrator system consists of three key components:

1. **Orchestrator**: 
   - The central control unit managing the entire system
   - Coordinates agent creation, task allocation, and monitoring
   - Handles resource management and inter-agent communication

2. **Aider Agents**: 
   - Individual task-specific agents responsible for executing coding tasks
   - Each agent has its own workspace and dedicated configuration
   - Manages the lifecycle of its associated Aider instance

3. **Aider Instances**: 
   - Actual AI coding assistants that perform specific coding operations
   - Dedicated to each Aider Agent
   - Interact directly with the repository and execute coding tasks

## Features

- **Advanced Multi-Agent Management**: Create and manage multiple AI coding agents with granular control
- **Real-Time Output Tracking**: Monitor agent and Aider instance progress
- **Git Integration**: Automatic repository cloning and branch management
- **Workspace Isolation**: Strict isolation for each agent and its Aider instance
- **Web Interface**: Comprehensive dashboard for system monitoring
- **Intelligent Session Management**: Robust handling of agent lifecycles and Aider interactions

## Architecture Diagram

```
+-------------------+
|   Orchestrator    |
|  (Central Control)|
+--------+----------+
         |
         | Manages
         v
+--------+----------+
|   Aider Agents    |
| (Task Executors)  |
+--------+----------+
         |
         | Instantiates
         v
+--------+----------+
| Aider Instances   |
| (AI Coding Tools) |
+-------------------+
```

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

1. Set up your environment variables:  (e.g., `LITELLM_MODEL`, `GITHUB_TOKEN`)
   - You'll need to set environment variables like `LITELLM_MODEL` (specifying your LLM) and `GITHUB_TOKEN` (for GitHub interaction).  The `.env` file is a convenient way to manage these.
```bash
set LITELLM_MODEL=anthropic/claude-3-5-sonnet-20240620  # On Windows
# export LITELLM_MODEL=anthropic/claude-3-5-sonnet-20240620  # On Unix/MacOS
```

2. The system uses `tasks.json` for configuration:
```json
{
    "tasks": [],
    "agents": {},
    "repository_url": ""
}
```

## Running the Project

1. **Start the web server:** This command runs the Flask application, making the web interface accessible.
```bash
python app.py
```
2. **Access the web interface:** Open your web browser and go to `http://localhost:5000` to interact with the application.

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

Python Coding Standards

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

## License

[MIT License](LICENSE)
