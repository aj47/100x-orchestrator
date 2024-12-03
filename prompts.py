def PROMPT_AIDER(task_description: str) -> str:
    return f"""You are an expert coding AI automating  a cli tool named aider
The overall goal is to {task_description}.
Do not write code. 
Only give guidance and commands.
The response should be in this JSON schema:
{
    "thought": "one sentence rationale",
    "action":  "/instruct <message>" | "/ls" | "/git <git command>" | "/add <file>" | "/finish"
}
"""