import subprocess
import logging
import sys
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def execute_git_command(command, working_directory):
    """Executes a Git command and returns the exit code."""
    try:
        # Construct the full command
        full_command = ["git"] + command.split()

        # Execute the command
        logging.info(f"Executing Git command: {' '.join(full_command)} in directory: {working_directory}")
        process = subprocess.Popen(
            full_command,
            cwd=working_directory,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate()

        # Log the output
        if stdout:
            logging.info(f"Git command output:\n{stdout}")
        if stderr:
            logging.error(f"Git command error:\n{stderr}")

        # Return the exit code
        return process.returncode

    except FileNotFoundError:
        logging.error("Git command not found.  Ensure Git is installed and in your PATH.")
        return 1  # Indicate an error

    except subprocess.CalledProcessError as e:
        logging.error(f"Git command failed with error code {e.returncode}: {e}")
        return e.returncode

    except Exception as e:
        logging.exception(f"An unexpected error occurred: {e}")
        return 1  # Indicate an error


if __name__ == "__main__":
    if len(sys.argv) != 2:
        logging.error("Usage: python version_control.py <git_command>")
        sys.exit(1)

    git_command = sys.argv[1]
    working_directory = os.getcwd() # Use current working directory by default

    exit_code = execute_git_command(git_command, working_directory)
    sys.exit(exit_code)

