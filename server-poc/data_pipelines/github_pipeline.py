import dlt
import os



from .github import github_reactions, github_stargazers, github_commits




def load_issues_data(owner: str, repo: str, destination: str, access_token: str | None = None) -> None:
    """Loads all issues and their reactions for the specified repo"""
    pipeline = dlt.pipeline(
        "github_issues",
        destination=dlt.destinations.postgres(destination),
        dataset_name="issues"
    )

    # Initialize the data source with the specified parameters
    data = github_reactions(
        owner=owner,
        name=repo,
        access_token=access_token,
        items_per_page=100
    ).with_resources('issues')
    
    # Run the pipeline and print the outcome
    load_info = pipeline.run(data, table_name="issues")
    print(f"Loaded issues:{load_info}", load_info)

def load_pull_requests_data(owner: str, repo: str, destination: str, access_token: str | None = None) -> None:
    """Loads all pull requests and their reactions for the specified repo"""
    print(destination)
    pipeline = dlt.pipeline(
        "github_prs",
        destination=dlt.destinations.postgres(destination),
        dataset_name="pull_requests"
    )

    # Initialize the data source with the specified parameters
    data = github_reactions(
        owner=owner,
        name=repo,
        access_token=access_token,
        items_per_page=100
    ).with_resources('pull_requests')
    
    # Run the pipeline and print the outcome
    load_info = pipeline.run(data, table_name="pull_requests")
    print(f"Loaded pull requests:{load_info}")

def load_stargazer_data(owner:str, repo:str, destination: str, access_token:str | None = None) -> None:
    """Loads all stargazers for dlthub dlt repo"""
    pipeline = dlt.pipeline(
        "github_stargazers",
        destination=dlt.destinations.postgres(destination),
        dataset_name="stargazers"
    )
    data = github_stargazers(owner, repo, access_token= access_token)
    print(pipeline.run(data))

def load_commit_data(owner: str, repo: str, destination: str, access_token: str | None = None) -> None:
    """Loads all commits for the specified repo"""
    pipeline = dlt.pipeline(
        "github_commits",
        destination=dlt.destinations.postgres(destination),
        dataset_name="commits"
    )

    # Initialize the data source with the specified parameters
    data = github_commits(
        owner=owner,
        name=repo,
        access_token=access_token,
        items_per_page=100
    )
    
    # Run the pipeline and print the outcome
    load_info = pipeline.run(data)
    print(f"Loaded commits: {load_info}")



