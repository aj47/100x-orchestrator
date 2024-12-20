# Critique Agent Implementation Plan

## Overview
Add a critique agent that monitors agent progress against user-defined rules to provide feedback and quality control.

## Implementation Steps

1. Add Rules UI to Index Page
- Add rules section to index.html form
- Allow users to add/remove rules
- Store rules in tasks.json

2. Create Critique Agent Class
- Create critique_agent.py
- Implement rule parsing and validation
- Add methods to evaluate progress against rules
- Store critique history

3. Integrate with Orchestrator
- Add critique agent initialization to orchestrator.py
- Hook into agent progress updates
- Store critique results in agent state

4. Update Agent View UI
- Add critiques section to agent cards
- Show rule compliance status
- Display critique history

5. Add Critique API Endpoints
- Add endpoints to fetch critique status
- Allow updating/managing rules
- Enable manual critique triggers

## Technical Details

### Rule Format
```json
{
  "rules": [
    {
      "name": "Progress Rate",
      "condition": "progress_updates > 1 per 5min",
      "severity": "warning"
    }
  ]
}
```

### Critique Result Format
```json
{
  "timestamp": "2024-03-21T10:00:00Z",
  "rule_results": [
    {
      "rule": "Progress Rate",
      "status": "failed",
      "message": "No progress updates in last 10 minutes"
    }
  ]
}
```
