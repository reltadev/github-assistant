from data_pipelines.github_pipeline import (
    load_repo_reactions_issues_only,
    load_repo_events,
    load_repo_all_data,
    load_repo_stargazers
)
from pydantic import BaseModel

class GithubRepoInfo(BaseModel):
    owner: str
    repo: str
    access_token: str | None = None  # Make token optional with default None

def load_data(repo_info: GithubRepoInfo):
    try:
        print('loading github_data')
        # Pass the access token to all pipeline functions
        load_repo_stargazers(repo_info.owner, repo_info.repo, repo_info.access_token)
        load_repo_reactions_issues_only(repo_info.owner, repo_info.repo, repo_info.access_token)
        load_repo_events(repo_info.owner, repo_info.repo, repo_info.access_token)
        #load_repo_all_data(repo_info.owner, repo_info.repo, repo_info.access_token)
        
        
        return {
            "status": "success",
            "message": f"Successfully loaded data for {repo_info.owner}/{repo_info.repo}"
        }
    except Exception as e:
        print(e)
        raise ValueError("Error ")
