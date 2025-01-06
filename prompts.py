#TODO: do not hardcode powershell, the LLM should be able to determine which Terminal is being used
def PROMPT_AIDER(task_description: str) -> str:
    from database import get_model_config
    config = get_model_config()
    suffix = config.get('aider_prompt_suffix', '') if config else ''
    
    # Ensure suffix has proper formatting
    suffix = suffix.strip() if suffix else ''
    if suffix and not suffix.startswith('\n'):
        suffix = '\n' + suffix
    if suffix and not suffix.endswith('\n'):
        suffix += '\n'
    
    return f"""You are an expert software developer manager.
You are talking to Aider, an AI programming assistant.
Do not write code. 
Only give instructions and commands.
Do not ask aider questions.
You need to make decisions and assumptions yourself.
You can give aider file structure and context using '/ls' and '/add <file>'.
For your own context run /map first to get a sense of the project.
It is recommended to do some analysis with /ls , /map and /run other commands first before starting to instruct code changes.
Commits are done automatically by aider so you DO NOT need to run git commit commands. 
The response should be in this JSON schema:
{{
    "progress": "one sentence update on progress so far",
    "thought": "one sentence rationale",
    "action":  "/instruct <message>" | "/ls" | "/git <git command>" | "/add <file>" | "/finish" | "/run <shell_command>" | "/map",
    "future": "one sentence prediction",
}}
The overall goal is: {task_description}

{suffix}
"""

def PROMPT_PR() -> str:
    return """Generate a pull request description based on the changes made.
The response should be in this JSON schema:
{
    "title": "Brief, descriptive PR title",
    "description": "Detailed description of changes made",
    "labels": ["list", "of", "relevant", "labels"],
    "reviewers": ["list", "of", "suggested", "reviewers"]
}
"""
