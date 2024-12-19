import logging
from litellm_client import LiteLLMClient
import json
from typing import Tuple, List, Dict, Optional

class CritiqueHandler:
    """
    Handles validation of agent work against acceptance criteria.
    
    The CritiqueHandler is responsible for ensuring that all code changes meet
    predefined acceptance criteria before being submitted for review. It uses
    LLM-powered analysis to validate both the code changes and the development
    process documented in session logs.
    
    Features:
    - Automated validation against multiple criteria
    - Detailed feedback on unmet requirements
    - Integration with PR workflow
    - Historical validation tracking
    
    Example acceptance criteria format:
    ```json
    {
        "code_quality": [
            "Follows PEP 8 style guidelines",
            "Includes proper type hints",
            "Has comprehensive docstrings"
        ],
        "testing": [
            "Includes unit tests for new functionality",
            "Maintains existing test coverage",
            "Tests edge cases appropriately"
        ],
        "architecture": [
            "Follows existing project patterns",
            "Maintains separation of concerns",
            "Uses appropriate design patterns"
        ]
    }
    ```
    """
    
    def __init__(self):
        """Initialize the CritiqueHandler with LLM client."""
        self.client = LiteLLMClient()
        
    def validate_submission(self, session_logs: str, code_diff: str, acceptance_criteria: str) -> Tuple[bool, str]:
        """
        Validate if the agent's work meets acceptance criteria.
        
        This method performs a comprehensive analysis of the changes and development
        process to ensure all acceptance criteria are met. It uses LLM to understand
        and validate complex requirements.
        
        Args:
            session_logs: Complete logs from the agent session showing the development process
            code_diff: Git diff showing actual code changes
            acceptance_criteria: User-defined acceptance criteria in structured format
            
        Returns:
            tuple[bool, str]: A tuple containing:
                - bool: Whether all criteria are met
                - str: Detailed feedback explaining the validation results
                
        Example:
            ```python
            handler = CritiqueHandler()
            criteria = {
                "code_quality": ["Follow PEP 8", "Include type hints"],
                "testing": ["Add unit tests", "Maintain coverage"]
            }
            meets_criteria, feedback = handler.validate_submission(
                session_logs="Agent development logs...",
                code_diff="Git diff of changes...",
                acceptance_criteria=json.dumps(criteria)
            )
            ```
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
- "suggestions": specific recommendations for addressing any issues
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
                feedback = self._format_feedback(result)
                return (
                    result.get("meets_criteria", False),
                    feedback
                )
            except json.JSONDecodeError:
                logging.error(f"Invalid JSON response from critique: {response}")
                return False, "Error processing critique response"
                
        except Exception as e:
            logging.error(f"Error in critique validation: {e}")
            return False, f"Error during validation: {str(e)}"
            
    def _format_feedback(self, result: Dict) -> str:
        """
        Format the validation results into a clear, structured feedback message.
        
        Args:
            result: Dictionary containing validation results
            
        Returns:
            str: Formatted feedback message
        """
        feedback_parts = []
        
        # Add main feedback
        feedback_parts.append(result.get("feedback", "No feedback provided"))
        
        # Add unmet criteria
        unmet = result.get("unmet_criteria", [])
        if unmet:
            feedback_parts.append("\nUnmet Criteria:")
            for criterion in unmet:
                feedback_parts.append(f"- {criterion}")
                
        # Add suggestions
        suggestions = result.get("suggestions", [])
        if suggestions:
            feedback_parts.append("\nSuggestions for Improvement:")
            for suggestion in suggestions:
                feedback_parts.append(f"- {suggestion}")
                
        return "\n".join(feedback_parts)
