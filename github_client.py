from github import Github
from typing import List, Dict, Optional
import os
from pathlib import Path
import logging

class GitHubClient:
    """Client for interacting with GitHub API"""
    
    def __init__(self, token: str):
        """Initialize with GitHub Personal Access Token"""
        self.token = token
        self.client = Github(token)
    
    def verify_token(self) -> bool:
        """Verify if the token is valid by making a test API call"""
        try:
            # Try to get the authenticated user's username
            self.client.get_user().login
            return True
        except Exception as e:
            logging.error(f"Token verification failed: {e}")
            return False
        
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

    def get_repository_issues(self, repo_name: str) -> List[Dict]:
        """Get open issues from a repository"""
        try:
            repo = self.client.get_repo(repo_name)
            issues = []
            for issue in repo.get_issues(state='open'):
                # Skip pull requests (they are also considered issues in GitHub's API)
                if issue.pull_request:
                    continue
                    
                issues.append({
                    'number': issue.number,
                    'title': issue.title,
                    'body': issue.body,
                    'url': issue.html_url,
                    'state': issue.state,
                    'labels': [label.name for label in issue.labels],
                    'created_at': issue.created_at.isoformat(),
                    'updated_at': issue.updated_at.isoformat(),
                    'assignees': [assignee.login for assignee in issue.assignees]
                })
            return issues
        except Exception as e:
            logging.error(f"Error getting repository issues: {e}")
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
