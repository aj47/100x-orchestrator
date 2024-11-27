### Introduction
The goal is to develop an orchestration system that efficiently manages AI coding agents, integrating robust version control and adhering to Test Driven Development (TDD) principles using FastAPI. This system will handle multiple agents, manage their progress, and ensure that their contributions are effectively merged into the main codebase.

### Concise Requirements

#### Agent Management
- **Start/Stop Agents:** Dynamically control the initialization and termination of AI coding agents.
- **Monitor Agent Progress:** Provide real-time progress tracking and a dashboard for status visualization.
- **Edit Agent Parameters:** Allow modifications to agent configurations during runtime.

#### Progress Evaluation
- **Critique Overall Project Progress:** Aggregate outputs to evaluate against project goals, identifying areas for improvement.
- **Critique Individual Agent Performance:** Assess and provide feedback on each agent's efficiency and code quality.

#### Version Control
- **Manage Git Branches:** Automate branch creation for task isolation and manage merging processes.
- **Merge Agent Contributions:** Automate merging, handle conflicts, and ensure code integrity through continuous testing.

#### Development Process
- **Implement TDD with FastAPI:** Enforce writing tests before code and utilize FastAPI for building and testing APIs.

#### Inputs Handling
- **Source Input:** Accept and validate inputs either as a GitHub URL or a local source folder.
- **Clone Repositories:** Automatically clone repositories for each agent, ensuring isolated environments.
- **Project Goals and Requirements:** Parse and distribute a comprehensive requirements document to guide agent tasks.
- **Configuration Settings:** Customize settings such as the number of agents per task and resource allocation.

This orchestration system aims to streamline the development process by managing multiple AI agents efficiently, ensuring that their contributions align with the overarching project goals, and maintaining high standards of code quality through TDD.
