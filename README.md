# 100x-orchestrator

[Previous content remains the same until the Features section]

## Features

- **Advanced Multi-Session Management**: Create and manage multiple AI coding sessions with granular control
- **Real-Time Output Tracking**: Monitor session and Aider instance progress
- **Git Integration**: Automatic repository cloning and branch management
- **Workspace Isolation**: Strict isolation for each session and its Aider instance
- **Web Interface**: Comprehensive dashboard for system monitoring
- **Intelligent Session Management**: Robust handling of session lifecycles and Aider interactions
- **Automated Code Review**: Built-in critique system for validating changes against acceptance criteria

## Acceptance Criteria System

The 100x-orchestrator includes a sophisticated acceptance criteria validation system that ensures all code changes meet predefined quality standards and requirements.

### How It Works

1. **Definition**: Acceptance criteria are defined when creating tasks:
```json
{
    "tasks": [
        {
            "title": "Task Name",
            "description": "Task details",
            "acceptance_criteria": [
                "Must maintain existing test coverage",
                "Should follow PEP 8 style guidelines",
                "Must include appropriate error handling"
            ]
        }
    ]
}
```

2. **Validation Process**:
   - The CritiqueHandler automatically validates all code changes
   - Analyzes both the code diff and session logs
   - Provides detailed feedback on criteria compliance
   - Prevents completion until all criteria are met

3. **Feedback Loop**:
   - Real-time feedback to agents
   - Specific guidance on unmet criteria
   - Automatic PR creation only after validation

### Example Criteria

```json
{
    "acceptance_criteria": [
        "Code must be properly documented with docstrings",
        "All new functions must include type hints",
        "Unit tests must be included for new functionality",
        "Code must pass all existing tests",
        "Changes must not introduce new dependencies",
        "Variable names must be descriptive and follow conventions"
    ]
}
```

[Rest of the README remains the same]
