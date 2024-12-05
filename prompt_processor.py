import json
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class AgentResponse:
    """Store individual agent responses"""
    progress: str
    thought: str
    action: str
    future: str
    timestamp: datetime = field(default_factory=datetime.now)

class PromptProcessor:
    """Process JSON responses from the prompt and manage agent state"""
    
    def __init__(self):
        self.agent_states: Dict[str, Dict] = {}
        self.response_history: Dict[str, List[AgentResponse]] = {}
        
    def process_response(self, agent_id: str, response: str) -> Optional[str]:
        """Process a JSON response and return the action to execute"""
        try:
            # Parse JSON response
            data = json.loads(response)
            
            # Validate required fields
            required_fields = ['progress', 'thought', 'action', 'future']
            if not all(field in data for field in required_fields):
                logging.error(f"Missing required fields in response: {response}")
                return None
            
            # Create and store response object
            agent_response = AgentResponse(
                progress=data['progress'],
                thought=data['thought'],
                action=data['action'],
                future=data['future']
            )
            
            # Initialize history list if needed
            if agent_id not in self.response_history:
                self.response_history[agent_id] = []
            
            # Add to history (limit to last 100 responses)
            self.response_history[agent_id].append(agent_response)
            if len(self.response_history[agent_id]) > 100:
                self.response_history[agent_id].pop(0)
            
            # Update current state
            self.agent_states[agent_id] = {
                'progress': agent_response.progress,
                'thought': agent_response.thought,
                'future': agent_response.future,
                'last_action': agent_response.action
            }
            
            # Process action
            action = agent_response.action.strip()
            if action.startswith('/instruct '):
                # Return just the instruction without the command
                return action[10:].strip()
            elif action in ['/ls', '/git', '/add', '/finish']:
                # Return the full command for other actions
                return action
            else:
                logging.error(f"Invalid action in response: {action}")
                return None
                
        except json.JSONDecodeError:
            logging.error(f"Invalid JSON response: {response}")
            return None
        except Exception as e:
            logging.error(f"Error processing response: {e}")
            return None
            
    def get_agent_state(self, agent_id: str) -> Dict:
        """Get the current state for an agent"""
        return self.agent_states.get(agent_id, {
            'progress': 'Not started',
            'thought': 'Initializing...',
            'future': 'Waiting to begin',
            'last_action': None
        })
        
    def get_response_history(self, agent_id: str) -> List[AgentResponse]:
        """Get the response history for an agent"""
        return self.response_history.get(agent_id, [])
