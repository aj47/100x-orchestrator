import json
import logging
from typing import Dict, Optional

class PromptProcessor:
    """Process JSON responses from the prompt and manage agent state"""
    
    def __init__(self):
        self.agent_states: Dict[str, Dict] = {}
        
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
                
            # Store agent state
            self.agent_states[agent_id] = {
                'progress': data['progress'],
                'thought': data['thought'],
                'future': data['future'],
                'last_action': data['action']
            }
            
            # Process action
            action = data['action'].strip()
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
