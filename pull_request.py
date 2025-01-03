import json
import os
import subprocess
from typing import Optional, Dict, List
from github import Github
import logging
from github_token import GitHubTokenManager
from litellm_client import LiteLLMClient
from prompts import PROMPT_PR

class PullRequestManager:
    """Manages GitHub pull request operations"""
    
    def __init__(self):
        self.token_manager = GitHubTokenManager()
        self.litellm_client = LiteLLMClient()

    def generate_pr_info(self, agent_id: str, history: str) -> Optional[Dict]:
        """Generate PR information using LLM"""
        try:
            pr_info = self.litellm_client.chat_completion(
                system_message=PROMPT_PR(),
                user_message=f"Agent history:\n{history}",
                model_type="agent",
                agent_id=agent_id
            )
            return json.loads(pr_info)
        except Exception as e:
            logging.error(f"Error generating PR info: {e}")
            return None

    def create_pull_request(self, agent_id: str, branch_name: str, pr_info: Dict) -> Optional[Dict]:
        """Create a pull request for the agent's changes."""
        try:
            token = self.token_manager.get_token()
            if not token:
                return None

            from orchestrator import load_tasks
            tasks_data = load_tasks()
            repo_url = tasks_data.get('repository_url', '')
            if not repo_url:
                logging.error("No repository URL found")
                return None

            agent_data = tasks_data['agents'].get(agent_id)
            if not agent_data:
                logging.error(f"No agent data found for {agent_id}")
                return None

            repo_path = agent_data.get('repo_path')
            if not repo_path:
                logging.error("No repo path found for agent")
                return None

            g = Github(token)
            repo_parts = repo_url.rstrip('/').split('/')
            repo_name = '/'.join(repo_parts[-2:]).replace('.git', '')
            current_dir = os.getcwd()
            
            try:
                # Check if PR already exists
                repo = g.get_repo(repo_name)
                existing_prs = repo.get_pulls(state='open', head=f"{repo_parts[-2]}:{branch_name}")
                if existing_prs.totalCount > 0:
                    logging.info(f"PR already exists: {existing_prs[0].html_url}")
                    return existing_prs[0]
                    
                # Prepare and push changes
                os.chdir(repo_path)
                subprocess.run(["git", "config", "user.name", "GitHub Actions"], check=True)
                subprocess.run(["git", "config", "user.email", "actions@github.com"], check=True)
                subprocess.run(["git", "add", "."], check=True)
                subprocess.run(["git", "commit", "-m", f"Changes by Agent {agent_id}"], check=False)
                remote_url = f"https://x-access-token:{token}@github.com/{repo_name}.git"
                subprocess.run(["git", "remote", "set-url", "origin", remote_url], check=True)
                subprocess.run(["git", "push", "-u", "origin", branch_name], check=True)
            finally:
                os.chdir(current_dir)
                
            # Create PR
            pr = repo.create_pull(
                title=pr_info.get('title', f'Changes by Agent {agent_id}'),
                body=pr_info.get('description', 'Automated changes'),
                head=branch_name,
                base='main'
            )
            
            # Add labels if specified
            if pr_info.get('labels'):
                try:
                    pr.add_to_labels(*pr_info['labels'])
                except Exception as e:
                    logging.warning(f"Could not add labels: {e}")
                    
            # Add reviewers if specified and they are collaborators
            if pr_info.get('reviewers'):
                try:
                    collaborators = {collab.login.lower() for collab in repo.get_collaborators()}
                    valid_reviewers = [r for r in pr_info['reviewers'] if r.lower() in collaborators]
                    if valid_reviewers:
                        pr.create_review_request(reviewers=valid_reviewers)
                except Exception as e:
                    logging.warning(f"Could not add reviewers: {e}")
                    
            return pr
            
        except Exception as e:
            logging.error(f"Error creating pull request: {e}")
            return None
