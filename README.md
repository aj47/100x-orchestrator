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

### Environment Variables

You need to set up environment variables to configure API keys and model choices.

1. Create a `.env` file in your home directory:

    ```bash
    touch ~/.env
    ```

2. Add your API keys and model preferences to the `.env` file using LiteLLM notation. You can specify any model and its associated API key. For example:

    ```
    OPENROUTER_API_KEY=your_openrouter_api_key
    ANY_OTHER_API_KEY=your_other_api_key
    ```

    You can set the default models for Orchestrator, Aider, and Agent components in the web interface under the "Configuration" section. Use LiteLLM model strings to specify your preferred models. For example:

    ```
    MY_MODEL=provider/model_name
    ```
    -   **Note**: LiteLLM model strings can be found [here](https://docs.litellm.ai/docs/providers).
3. Add your `GITHUB_TOKEN` to the `.env` file:

    ```
    GITHUB_TOKEN=your_github_token
    ```

    -   **Note**: The GitHub token requires `repo` scope to enable all necessary repository operations. You can create a token at [GitHub Settings - Personal access tokens](https://github.com/settings/tokens). The exact usage of this token may require code inspection to confirm.

### Database

The system uses an SQLite database (`tasks.db`) to store:

-   Agent configurations
-   Task details
-   Model configurations
-   General configurations

The database is automatically initialized when you first run the application.

### Model Configuration

You can configure the default models for the Orchestrator, Aider, and Agent components. By default, all use `openrouter/google/gemini-flash-1.5`.

To change the defaults:

1. Go to the "Configuration" section in the web interface.
2. Enter the desired LiteLLM model strings.
3. Click "Update Configuration".

### Usage

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

