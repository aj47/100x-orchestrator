import os
from pathlib import Path
from typing import Optional

class GitHubTokenManager:
    """Manages GitHub token storage and retrieval"""
    
    def __init__(self):
        self.token: Optional[str] = None
        self._load_token()
    
    def _load_token(self):
        """Load token from environment or .env file"""
        self.token = os.getenv('GITHUB_TOKEN')
        if not self.token:
            try:
                env_path = Path.home() / '.env'
                if env_path.exists():
                    with open(env_path) as f:
                        for line in f:
                            if line.startswith('GITHUB_TOKEN='):
                                self.token = line.split('=', 1)[1].strip()
                                break
            except Exception as e:
                self.token = None
    
    def get_token(self) -> Optional[str]:
        """Get the current GitHub token"""
        return self.token
    
    def set_token(self, token: str) -> bool:
        """Set a new GitHub token"""
        if not token:
            return False
            
        try:
            env_path = Path.home() / '.env'
            lines = []
            token_exists = False
            
            # Read existing file if it exists
            if env_path.exists():
                with open(env_path, 'r') as f:
                    lines = f.readlines()
                
                # Check if token already exists
                for i, line in enumerate(lines):
                    if line.startswith('GITHUB_TOKEN='):
                        # Update existing token line
                        lines[i] = f'GITHUB_TOKEN={token}\n'
                        token_exists = True
                        break
            
            # If token didn't exist, append it
            if not token_exists:
                lines.append(f'GITHUB_TOKEN={token}\n')
            
            # Write all lines back to file
            with open(env_path, 'w') as f:
                f.writelines(lines)
                
            self.token = token
            os.environ['GITHUB_TOKEN'] = token
            return True
        except Exception as e:
            print(f"Error saving token: {e}")
            return False
