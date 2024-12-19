import json
from typing import Dict, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime
from github import Github
from critique_handler import CritiqueHandler
from task_manager import load_tasks

@dataclass
class AgentResponse:
    progress: str
    thought: str
    action: str
    future: str
    timestamp: datetime = field(default_factory=datetime.now)

class PromptProcessor:
    def __init__(self):
        self.agent_states: Dict[str, Dict] = {}
        self.response_history: Dict[str, List[AgentResponse]] = {}
        self.critique_handler = CritiqueHandler()
        
    def process_response(self, agent_id: str, response: str, acceptance_criteria: str = '') -> Optional[str]:
        """
        Process agent response and validate against structured acceptance criteria.
        
        Args:
            agent_id: Unique identifier for the agent
            response: JSON response from the agent
            acceptance_criteria: JSON string containing structured criteria categories
            
        Returns:
            Optional[str]: Next action for the agent or None
        """
        try:
            data = json.loads(response)
            
            required_fields = ['progress', 'thought', 'action', 'future']
            if not all(field in data for field in required_fields):
                return None
            
            agent_response = AgentResponse(
                progress=data['progress'],
                thought=data['thought'],
                action=data['action'],
                future=data['future']
            )
            
            if agent_id not in self.response_history:
                self.response_history[agent_id] = []
            
            self.response_history[agent_id].append(agent_response)
            if len(self.response_history[agent_id]) > 100:
                self.response_history[agent_id].pop(0)
            
            self.agent_states[agent_id] = {
                'progress': agent_response.progress,
                'thought': agent_response.thought,
                'future': agent_response.future,
                'last_action': agent_response.action
            }
            
            action = agent_response.action.strip()
            if action == '/finish':
                tasks_data = load_tasks()
                if not acceptance_criteria:
                    # Try to get structured criteria from tasks data
                    agent_data = tasks_data.get('agents', {}).get(agent_id, {})
                    acceptance_criteria = agent_data.get('acceptance_criteria', "")

                if not acceptance_criteria:
                    return None

                history = "\n".join([
                    f"Progress: {r.progress}\nThought: {r.thought}\nAction: {r.action}\nFuture: {r.future}\n"
                    for r in self.response_history[agent_id]
                ])

                code_diff = ""  # In future, could get this from git

                meets_criteria, feedback = self.critique_handler.validate_submission(
                    history, code_diff, acceptance_criteria
                )

                if not meets_criteria:
                    self.agent_states[agent_id]['critique_feedback'] = feedback
                    return f"/instruct Please address this feedback before submitting: {feedback}"

                from litellm_client import LiteLLMClient
                from prompts import PROMPT_PR
                    
                client = LiteLLMClient()
                pr_info = client.chat_completion(
                    system_message=PROMPT_PR(),
                    user_message=f"Agent history:\n{history}\n\nAcceptance Criteria:\n{acceptance_criteria}"
                )
                
                try:
                    pr_data = json.loads(pr_info)
                    self.agent_states[agent_id]['pr_info'] = pr_data
                    self.agent_states[agent_id]['status'] = 'creating_pr'
                except json.JSONDecodeError:
                    pass
                
                return action
                
            elif action.startswith('/instruct '):
                return action[10:].strip()
            elif action.startswith(('/ls', '/git', '/add')):
                return action
            else:
                return None
                
        except json.JSONDecodeError:
            return None
        except Exception:
            return None
            
    def get_agent_state(self, agent_id: str) -> Dict:
        """Get current state of an agent including structured criteria status."""
        return self.agent_states.get(agent_id, {
            'progress': 'Not started',
            'thought': 'Initializing...',
            'future': 'Waiting to begin',
            'last_action': None,
            'acceptance_criteria': {
                "code_quality": [],
                "testing": [],
                "architecture": []
            }
        })
        
    def get_response_history(self, agent_id: str) -> List[AgentResponse]:
        """Get complete response history for an agent."""
        return self.response_history.get(agent_id, [])
