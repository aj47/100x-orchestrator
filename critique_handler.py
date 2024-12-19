import logging
from litellm_client import LiteLLMClient
import json

class CritiqueHandler:
    """Handles validation of agent work against acceptance criteria"""
    
    def __init__(self):
        self.client = LiteLLMClient()
        
    def validate_submission(self, session_logs: str, code_diff: str, acceptance_criteria: str) -> tuple[bool, str]:
        """
        Validate if the agent's work meets acceptance criteria
        
        Args:
            session_logs: Complete logs from the agent session
            code_diff: Git diff of changes
            acceptance_criteria: User-defined acceptance criteria
            
        Returns:
            tuple[bool, str]: (meets_criteria, feedback)
        """
        try:
            system_prompt = f"""You are a code reviewer validating changes against acceptance criteria.
            
Acceptance Criteria:
{acceptance_criteria}

Your task is to:
1. Review the code changes and session logs
2. Determine if ALL acceptance criteria are met
3. Provide specific feedback on what criteria are/aren't met

Return a JSON response with:
- "meets_criteria": boolean
- "feedback": detailed explanation
- "unmet_criteria": list of unmet criteria (empty if all met)
"""
            
            user_message = f"""Code Changes:
{code_diff}

Session Logs:
{session_logs}
"""
            
            response = self.client.chat_completion(
                system_message=system_prompt,
                user_message=user_message
            )
            
            try:
                result = json.loads(response)
                return (
                    result.get("meets_criteria", False),
                    result.get("feedback", "No feedback provided")
                )
            except json.JSONDecodeError:
                logging.error(f"Invalid JSON response from critique: {response}")
                return False, "Error processing critique response"
                
        except Exception as e:
            logging.error(f"Error in critique validation: {e}")
            return False, f"Error during validation: {str(e)}"
