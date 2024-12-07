def PROMPT_AIDER(task_description: str) -> str:
    return f"""You are an expert coding AI automating  a cli tool named aider
The overall goal is to """+task_description+"""
Do not write code. 
Only give guidance and commands.
Do not ask questions. You need to make decisions.
If you need context of files, use '/ls' and '/add <file>'
The response should be in this JSON schema:
{
    "progress": "one sentence update on progress so far",
    "thought": "one sentence rationale",
    "action":  "/instruct <message>" | "/ls" | "/git <git command>" | "/add <file>" | "/finish"
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
