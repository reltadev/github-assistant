from data_pipelines.github_pipeline import (
    load_issues_data,
    load_pull_requests_data,
    load_stargazer_data,
    load_commit_data
)
from datetime import datetime
from enum import Enum
from sqlmodel import Field, SQLModel
from sqlalchemy_utils import create_database, database_exists
from sqlalchemy import MetaData
import os

class PipelineStatus(Enum):
    RUNNING = 1
    FAILED = 2
    SUCCESS = 3


class GithubRepoInfo(SQLModel, table=True):
    metadata = MetaData()
    id: int | None = Field(default=None, primary_key=True)
    owner: str
    repo_name: str
    last_pipeline_run: datetime | None = None
    pipeline_status: PipelineStatus | None = None 
    loaded_issues: bool = Field(default=True)
    loaded_pull_requests: bool = Field(default=True)
    loaded_stars: bool = Field(default=True)
    loaded_commits: bool = Field(default=True)


    def setup_destination_db(self, database_uri):
        """Creates a database in PG with name {repo_owner}_{repo_name}
        """
        url = f"{database_uri}/{self.source_name()}"
        try:
            if not database_exists(url):
                create_database(url)
        except Exception as e:
            print(e)



    def load_data(self, access_token: str, load_issues=True, load_pull_requests=True, 
                 load_stars=True, load_commits=True):
        """Loads data for the repo from the GitHub API into postgres using DLT helper files"""
        print(f'Loading github data for {self.owner}/{self.repo_name}')
        
        DATABASE_URI = os.environ.get('GITHUB_DATABASE_CONNECTION_URI')
        destination_url = f"{DATABASE_URI}/{self.source_name()}"
        
        # Reset loaded flags
        self.loaded_stars = False
        self.loaded_issues = False
        self.loaded_pull_requests = False
        self.loaded_commits = False
        
        if load_stars:
            try:
                load_stargazer_data(self.owner, self.repo_name, destination_url, access_token=access_token)
                self.loaded_stars = True
            except Exception as e:
                print(f"Failed to load star data: {e}")
                
                
        if load_issues:
            try:
                load_issues_data(self.owner, self.repo_name, destination_url, access_token=access_token)
                self.loaded_issues = True
            except Exception as e:
                print(f"Failed to load issues data: {e}")
                
                
        if load_pull_requests:
            try:
                load_pull_requests_data(self.owner, self.repo_name, destination_url, access_token=access_token)
                self.loaded_pull_requests = True
            except Exception as e:
                print(f"Failed to load pull requests data: {e}")
                

        if load_commits:
            try:
                load_commit_data(self.owner, self.repo_name, destination_url, access_token=access_token)
                self.loaded_commits = True
            except Exception as e:
                print(f"Failed to load commit data: {e}")
                

        # If nothing was loaded successfully, raise an exception
        if not any([self.loaded_stars, self.loaded_issues, 
                    self.loaded_pull_requests, self.loaded_commits]):
            raise Exception("Failed to load any data")
        
       


    def source_name(self) -> str:
        """lowercase and remove special characters"""
        return f"{self.owner.lower()}_{self.repo_name.lower().replace('-', '')}"
