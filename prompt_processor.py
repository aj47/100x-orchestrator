import json
import logging

class PromptProcessor:
    def process_response(self, response):
        try:
            data = json.loads(response)
            # Add your prompt processing logic here
            return data.get('action')
        except json.JSONDecodeError:
            logging.error(f"Invalid JSON response: {response}")
            return None

