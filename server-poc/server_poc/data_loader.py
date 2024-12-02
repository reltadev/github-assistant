from data_pipelines.github_pipeline import (
    load_issues_data,
    load_pull_requests_data,
    load_stargazer_data,
    load_commit_data
)
from pydantic import BaseModel

class GithubRepoInfo(BaseModel):
    owner: str
    repo: str
    access_token: str | None = None
    load_issues: bool = True
    load_pull_requests: bool = True
    load_stars: bool = True
    load_commits: bool = True

def load_data(repo_info: GithubRepoInfo):
    try:
        print(f'Loading github data for {repo_info.owner}/{repo_info.repo}')
        
        data_loaded = []
        
        if repo_info.load_stars:
            load_stargazer_data(repo_info.owner, repo_info.repo, access_token=repo_info.access_token)
            data_loaded.append("stars")
            
        if repo_info.load_issues:
            load_issues_data(repo_info.owner, repo_info.repo, access_token=repo_info.access_token)
            data_loaded.append("issues")
            
        if repo_info.load_pull_requests:
            load_pull_requests_data(repo_info.owner, repo_info.repo, access_token=repo_info.access_token)
            data_loaded.append("pull requests")

        if repo_info.load_commits:
            load_commit_data(repo_info.owner, repo_info.repo, access_token=repo_info.access_token)
            data_loaded.append("pull requests")
        
        return {
            "status": "success",
            "message": f"Successfully loaded {', '.join(data_loaded)} data for {repo_info.owner}/{repo_info.repo}"
        }
    except Exception as e:
        print(e)
        raise ValueError(f"Error loading data: {str(e)}")
