import pytest
from prompts import PROMPT_AIDER, PROMPT_PR

def test_prompt_aider():
    """Test the PROMPT_AIDER function."""
    task_description = "Write a Python function to calculate factorial."
    prompt = PROMPT_AIDER(task_description)
    assert "You are an expert coding AI automating  a cli tool named aider" in prompt
    assert task_description in prompt
    assert "Do not write code" in prompt
    assert "JSON schema" in prompt

def test_prompt_pr():
    """Test the PROMPT_PR function."""
    prompt = PROMPT_PR()
    assert "Generate a pull request description" in prompt
    assert "JSON schema" in prompt

