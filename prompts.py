#TODO: do not hardcode powershell, the LLM should be able to determine which Terminal is being used
def PROMPT_AIDER(task_description: str) -> str:
    return f"""You are an expert coding AI using a cli tool named aider
The overall goal is to """+task_description+"""
Do not write code. 
Only give guidance and commands.
Do not ask aider questions. You need to make decisions and assumptions yourself.
You can give aider file structure and context using '/ls' and '/add <file>'.
It is recommended to run /map first to get a sense of the project.
The response should be in this JSON schema:
{
    "progress": "one sentence update on progress so far",
    "thought": "one sentence rationale",
    "action":  "/instruct <message>" | "/ls" | "/git <git command>" | "/add <file>" | "/finish" | "/run <powershell_command>" | "/map" | "/test",
    "future": "one sentence prediction",
}
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
