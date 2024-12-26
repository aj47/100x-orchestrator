import json
import os
from typing import Dict, Any
from jsonschema import validate, ValidationError
import typer

app = typer.Typer()

CONFIG_FILE = "config.json"
SCHEMA_FILE = "config_schema.json"

def load_config(file_path: str) -> Dict[str, Any]:
    """Loads the configuration from a JSON file."""
    if not os.path.exists(file_path):
        return {}  # Return empty dict if file doesn't exist
    with open(file_path, "r") as f:
        return json.load(f)

def save_config(config: Dict[str, Any], file_path: str) -> None:
    """Saves the configuration to a JSON file."""
    with open(file_path, "w") as f:
        json.dump(config, f, indent=4)

def load_schema(file_path: str) -> Dict[str, Any]:
    """Loads the JSON schema from a file."""
    with open(file_path, "r") as f:
        return json.load(f)

def validate_config(config: Dict[str, Any], schema: Dict[str, Any]) -> None:
    """Validates the configuration against the schema."""
    try:
        validate(instance=config, schema=schema)
    except ValidationError as e:
        raise ValueError(f"Configuration validation failed: {e}")


@app.command()
def configure(
    model: str = typer.Option("gpt-3.5-turbo", help="The LLM model to use."),
    temperature: float = typer.Option(0.7, help="The temperature for the LLM."),
    system_prompt: str = typer.Option("You are a helpful assistant.", help="The system prompt for the LLM."),
):
    """Configures the agent settings."""
    config = load_config(CONFIG_FILE)
    schema = load_schema(SCHEMA_FILE)

    config["model"] = model
    config["temperature"] = temperature
    config["system_prompt"] = system_prompt

    try:
        validate_config(config, schema)
        save_config(config, CONFIG_FILE)
        typer.echo("Configuration saved successfully!")
    except ValueError as e:
        typer.echo(f"Error: {e}")
    except Exception as e:
        typer.echo(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    app()
