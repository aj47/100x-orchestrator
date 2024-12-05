from github import Github
from typing import List, Dict, Optional
import os
from pathlib import Path
from dotenv import load_dotenv
import logging

class GitHubClient:
    """Client for interacting with GitHub API"""
    
    def __init__(self):
        # Load environment variables from ~/.env
        env_path = Path.home() / '.env'
        if not load_dotenv(env_path):
            logging.warning(f"Could not load {env_path}")
            
        self.token = os.getenv('GITHUB_TOKEN')
        if not self.token:
            raise ValueError(f"GITHUB_TOKEN not found in {env_path}")
            
        self.client = Github(self.token)
        
    def get_repositories(self) -> List[Dict]:
        """Get list of repositories the user has access to"""
        try:
            repos = []
            for repo in self.client.get_user().get_repos():
                repos.append({
                    'id': repo.id,
                    'name': repo.name,
                    'full_name': repo.full_name,
                    'description': repo.description,
                    'url': repo.html_url,
                    'private': repo.private
                })
            return repos
        except Exception as e:
            logging.error(f"Error getting repositories: {e}")
            return []
            
    def create_pull_request(self, repo_name: str, title: str, 
                          head: str, base: str = "main",
                          body: Optional[str] = None) -> Dict:
        """Create a pull request"""
        try:
            repo = self.client.get_repo(repo_name)
            pr = repo.create_pull(
                title=title,
                body=body,
                head=head,
                base=base
            )
            return {
                'id': pr.id,
                'number': pr.number,
                'title': pr.title,
                'url': pr.html_url,
                'state': pr.state
            }
        except Exception as e:
            logging.error(f"Error creating pull request: {e}")
            return {}
            
    def get_recent_commits(self, repo_name: str, branch: str = "main",
                          limit: int = 10) -> List[Dict]:
        """Get recent commits for a repository"""
        try:
            repo = self.client.get_repo(repo_name)
            commits = []
            for commit in repo.get_commits(sha=branch)[:limit]:
                commits.append({
                    'sha': commit.sha,
                    'message': commit.commit.message,
                    'author': commit.commit.author.name,
                    'date': commit.commit.author.date.isoformat(),
                    'url': commit.html_url
                })
            return commits
        except Exception as e:
            logging.error(f"Error getting commits: {e}")
            return []
