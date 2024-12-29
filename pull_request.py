from typing import Optional, Dict, List
from github import Github
import logging
from github_token import GitHubTokenManager
from litellm_client import LiteLLMClient
from prompts import PROMPT_PR, PROMPT_REVIEW

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
                model_type="agent"
            )
            return json.loads(pr_info)
        except Exception as e:
            logging.error(f"Error generating PR info: {e}")
            return None

    def review_changes(self, history: str) -> Optional[Dict]:
        """Review changes using LLM"""
        try:
            review_response = self.litellm_client.chat_completion(
                system_message=PROMPT_REVIEW(),
                user_message=f"Agent history:\n{history}",
                model_type="review"
            )
            return json.loads(review_response)
        except Exception as e:
            logging.error(f"Error reviewing changes: {e}")
            return None
    
    def create_pull_request(self, repo_url: str, branch_name: str, pr_info: Dict) -> Optional[Dict]:
        """Create a pull request with the given information"""
        try:
            token = self.token_manager.get_token()
            if not token:
                logging.error("No GitHub token available")
                return None
                
            g = Github(token)
            repo_parts = repo_url.rstrip('/').split('/')
            repo_name = '/'.join(repo_parts[-2:]).replace('.git', '')
            
            # Get repository
            repo = g.get_repo(repo_name)
            
            # Check for existing PR
            existing_prs = repo.get_pulls(state='open', head=f"{repo_parts[-2]}:{branch_name}")
            if existing_prs.totalCount > 0:
                pr = existing_prs[0]
                return {
                    'url': pr.html_url,
                    'number': pr.number,
                    'state': pr.state
                }
            
            # Create new PR
            pr = repo.create_pull(
                title=pr_info.get('title', 'Automated PR'),
                body=pr_info.get('description', 'Automated changes'),
                head=branch_name,
                base='main'
            )
            
            # Add labels if specified
            if pr_info.get('labels'):
                pr.add_to_labels(*pr_info['labels'])
            
            # Add reviewers if specified
            if pr_info.get('reviewers'):
                collaborators = {collab.login.lower() for collab in repo.get_collaborators()}
                valid_reviewers = [r for r in pr_info['reviewers'] if r.lower() in collaborators]
                if valid_reviewers:
                    pr.create_review_request(reviewers=valid_reviewers)
            
            return {
                'url': pr.html_url,
                'number': pr.number,
                'state': pr.state
            }
            
        except Exception as e:
            logging.error(f"Error creating pull request: {e}")
            return None
