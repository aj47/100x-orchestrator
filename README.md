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

- **GitHub Integration**: 
  - Simple authentication using Personal Access Token
  - Repository selection from user's repositories
  - Automatic issue import as tasks
  - External repository support
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

1. Set up your environment variables in `~/.env`:
```bash
# Required for LiteLLM
LITELLM_MODEL=anthropic/claude-3-5-sonnet-20240620

# Required for Flask
FLASK_SECRET_KEY=your_secret_key
```

2. The system uses tasks.json for configuration:
```json
{
    "tasks": [],
    "agents": {},
    "repository_url": ""
}
```

## GitHub Setup

1. Create a Personal Access Token (PAT):
   - Go to GitHub Settings > Developer settings > Personal access tokens
   - Click "Generate new token (classic)"
   - Give it a name (e.g., "100x-orchestrator")
   - Select the `repo` scope
   - Click "Generate token" and copy it
   - You'll enter this token when you first launch the application

Note: Your Personal Access Token is stored securely in your browser's local storage and is only used to communicate directly with GitHub's API.

## Usage

1. Start the web server:
```bash
python app.py
```

2. Access the web interface at `http://localhost:5000`

3. First Time Setup:
   - Enter your GitHub Personal Access Token
   - Click "Connect with GitHub"

4. Create new agents:
   - Select a repository from your GitHub account or enter an external repository URL
   - Click "Load Issues as Tasks" to import repository issues
   - Choose number of agents per task
   - Click "Create Agent"

5. Monitor progress:
   - View real-time agent outputs
   - Check agent status
   - Manage agent lifecycle

## Project Structure

```
100x-orchestrator/
|-- app.py              # Web interface and GitHub integration
|-- github_client.py    # GitHub API integration
|-- orchestrator.py     # Core orchestration logic
|-- requirements.txt    # Project dependencies
|-- static/            # Static assets
|   |-- css/          # CSS stylesheets
|   |   `-- styles.css
|   `-- js/           # JavaScript modules
|       |-- index.js      # Homepage functionality
|       `-- agent_view.js # Agent monitoring dashboard
|-- tasks/             # Task configuration
|-- templates/         # Web interface templates
|   |-- index.html    # Homepage template
|   `-- agent_view.html # Agent monitoring template
`-- workspaces/        # Agent workspaces
```

## Technical Stack

- Backend:
  - Python 3.8+
  - Flask
  - PyGithub
  - OAuth2
  - Aider
  - Git
  - LiteLLM
  - Threading

- Frontend:
  - HTML5
  - CSS3
  - JavaScript (ES6+)
  - Bootstrap 5
  - Font Awesome

## JavaScript Architecture

The frontend JavaScript is organized into two main modules:

1. **index.js**:
   - GitHub token management
   - Repository selection and management
   - Task creation and management
   - Agent creation form handling
   - Real-time repository data fetching

2. **agent_view.js**:
   - Real-time agent monitoring
   - Output tracking and display
   - Agent state management
   - Agent deletion handling
   - Keyboard shortcuts
   - Auto-refresh functionality

Best Practices:
- Modular code organization
- Event delegation for dynamic elements
- Async/await for API calls
- Error handling and user feedback
- Clean separation of concerns
- Performance optimization with debouncing
- Memory leak prevention
- Consistent error handling
- Real-time updates with proper cleanup

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
