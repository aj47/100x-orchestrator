import subprocess
import logging
import json
from typing import Optional, List, Dict
from pathlib import Path

class GitHubClient:
    """Wrapper for GitHub CLI operations"""
    
    def __init__(self):
        self._check_gh_cli()
        self._ensure_auth()
        
    def _check_gh_cli(self):
        """Verify gh CLI is installed"""
        try:
            subprocess.run(['gh', '--version'], 
                         capture_output=True, 
                         check=True)
        except subprocess.CalledProcessError:
            raise RuntimeError("GitHub CLI (gh) not installed. Please install it first.")
        except FileNotFoundError:
            raise RuntimeError("GitHub CLI (gh) not found in PATH. Please install it first.")

    def _ensure_auth(self):
        """Ensure gh CLI is authenticated"""
        try:
            result = subprocess.run(['gh', 'auth', 'status'],
                                  capture_output=True,
                                  text=True)
            if result.returncode != 0:
                logging.error("GitHub CLI not authenticated")
                raise RuntimeError("Please authenticate with 'gh auth login' first")
        except subprocess.CalledProcessError as e:
            logging.error(f"Error checking auth status: {e}")
            raise

    def clone_repository(self, repo_url: str, target_dir: Optional[Path] = None) -> bool:
        """Clone a repository using gh cli"""
        try:
            cmd = ['gh', 'repo', 'clone', repo_url]
            if target_dir:
                cmd.append(str(target_dir))
                
            result = subprocess.run(cmd,
                                  capture_output=True,
                                  text=True)
            
            if result.returncode != 0:
                logging.error(f"Failed to clone repository: {result.stderr}")
                return False
                
            return True
            
        except subprocess.SubprocessError as e:
            logging.error(f"Error cloning repository: {e}")
            return False

    def get_repository_issues(self, repo: str) -> List[Dict]:
        """Get list of open issues for a repository"""
        try:
            result = subprocess.run(
                ['gh', 'issue', 'list', '--repo', repo, '--json', 'number,title,body'],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logging.error(f"Failed to get issues: {result.stderr}")
                return []
                
            return json.loads(result.stdout)
            
        except subprocess.SubprocessError as e:
            logging.error(f"Error getting issues: {e}")
            return []
            
    def create_issue(self, repo: str, title: str, body: str) -> Optional[Dict]:
        """Create a new issue in the repository"""
        try:
            result = subprocess.run(
                ['gh', 'issue', 'create',
                 '--repo', repo,
                 '--title', title,
                 '--body', body,
                 '--json', 'number,title,url'],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                logging.error(f"Failed to create issue: {result.stderr}")
                return None
                
            return json.loads(result.stdout)
            
        except subprocess.SubprocessError as e:
            logging.error(f"Error creating issue: {e}")
            return None
