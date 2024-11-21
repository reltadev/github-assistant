import dlt
from .github import github_reactions, github_repo_events, github_stargazers


def load_repo_reactions_issues_only(owner: str, repo: str, access_token: str | None = None) -> None:
    """Loads issues, their comments and reactions for a given repository
    
    Args:
        owner: The owner/organization of the repository
        repo: The name of the repository
        access_token: Optional GitHub access token
    """
    pipeline = dlt.pipeline(
        "github_issues",
        destination=dlt.destinations.duckdb(f"data/{repo}_github_data.duckdb"),
        dataset_name="issues"
    )
    data = github_reactions(
        owner, repo, items_per_page=100, max_items=100, access_token=access_token
    ).with_resources("issues")
    print(pipeline.run(data, refresh="drop_sources"))


def load_repo_events(owner: str, repo: str, access_token: str | None = None) -> None:
    """Loads repository events. Shows incremental loading.
    
    Args:
        owner: The owner/organization of the repository
        repo: The name of the repository
        access_token: Optional GitHub access token
    """
    pipeline = dlt.pipeline(
        "github_events", destination=dlt.destinations.duckdb(f"data/{repo}_github_data.duckdb"), dataset_name="events"
    )
    data = github_repo_events(owner, repo, access_token=access_token)
    print(pipeline.run(data, refresh="drop_sources"))


def load_repo_all_data(owner: str, repo: str, access_token: str | None = None) -> None:
    """Loads all issues, pull requests and comments for a given repository
    
    Args:
        owner: The owner/organization of the repository
        repo: The name of the repository
        access_token: Optional GitHub access token
    """
    pipeline = dlt.pipeline(
        "github_reactions",
        destination=dlt.destinations.duckdb(f"data/{repo}_github_data.duckdb"),
        dataset_name="reactions"
    )
    data = github_reactions(owner, repo, access_token=access_token)
    print(pipeline.run(data, refresh="drop_sources"))


def load_repo_stargazers(owner: str, repo: str, access_token: str | None = None) -> None:
    """Loads all stargazers for a given repository
    
    Args:
        owner: The owner/organization of the repository
        repo: The name of the repository
        access_token: Optional GitHub access token
    """
    pipeline = dlt.pipeline(
        "github_stargazers",
        destination=dlt.destinations.duckdb(f"data/{repo}_github_data.duckdb"),
        dataset_name="stargazers"
    )
    data = github_stargazers(owner, repo, access_token=access_token)
    print(pipeline.run(data, refresh="drop_sources"))


if __name__ == "__main__":
    # Example usage with the original repositories
    load_repo_reactions_issues_only("duckdb", "duckdb")
    load_repo_events("apache", "airflow")
    load_repo_all_data("dlt-hub", "dlt")
    load_repo_stargazers("dlt-hub", "dlt")
