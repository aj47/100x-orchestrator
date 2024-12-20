import logging
from typing import List, Dict, Any
from datetime import datetime, timedelta
from litellm import completion
from prompts import PROMPT_CRITIQUE

class CritiqueAgent:
    """Evaluate agent performance against defined critique rules using LLM"""
    
    @staticmethod
    def evaluate_agent(agent_data: Dict, critique_rules: str) -> Dict[str, Any]:
        """
        Evaluate agent performance using LLM-based critique
        
        Args:
            agent_data (Dict): Complete agent data dictionary
            critique_rules (str): Multiline string of critique rules
        
        Returns:
            Dict containing critique results
        """
        try:
            # Prepare context for critique
            context = f"""
Agent Details:
- Task: {agent_data.get('task', 'N/A')}
- Progress History: {agent_data.get('progress_history', [])}
- Thought History: {agent_data.get('thought_history', [])}
- Last Action: {agent_data.get('last_action', 'N/A')}
- Aider Output: {agent_data.get('aider_output', 'N/A')}

Critique Rules:
{critique_rules}
"""
            
            # Make LLM call for critique
            response = completion(
                model="anthropic/claude-3-5-sonnet-20240620",
                messages=[
                    {"role": "system", "content": PROMPT_CRITIQUE()},
                    {"role": "user", "content": context}
                ],
                response_format={"type": "json_object"}
            )
            
            # Parse and return critique result
            critique_result = response.choices[0].message.content
            logging.info(f"Critique Result: {critique_result}")
            
            return critique_result
        
        except Exception as e:
            logging.error(f"Error in agent critique: {e}")
            return {
                "approved": False,
                "feedback": f"Critique process failed: {str(e)}",
                "suggestions": []
            }
