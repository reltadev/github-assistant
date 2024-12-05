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
    repo: str
    last_pipeline_run: datetime | None = None
    access_token: str | None = None
    pipeline_status: PipelineStatus | None = None 
    load_issues: bool = Field(default=True)
    load_pull_requests: bool = Field(default=True)
    load_stars: bool = Field(default=True)
    load_commits: bool = Field(default=True)


    def setup_destination_db(self, database_uri):
        """Creates a database in PG with name {repo_owner}_{repo_name}
        """
        url = f"{database_uri}/{self.source_name()}"
        try:
            if not database_exists(url):
                create_database(url)
        except Exception as e:
            print(e)



    def load_data(self, access_token: str):
        """Loads data for the repo from the GitHub API into postgres using DLT helper files"""
        try:
            print(f'Loading github data for {self.owner}/{self.repo}')
            
            data_loaded = []
            DATABASE_URI = os.environ.get('GITHUB_DATABASE_CONNECTION_URI')
            destination_url = f"{DATABASE_URI}/{self.source_name()}"
            
            if self.load_stars:
                load_stargazer_data(self.owner, self.repo, destination_url, access_token=access_token)
                data_loaded.append("stars")
                
            if self.load_issues:
                load_issues_data(self.owner, self.repo, destination_url, access_token=access_token)
                data_loaded.append("issues")
                
            if self.load_pull_requests:
                load_pull_requests_data(self.owner, self.repo, destination_url, access_token=access_token)
                data_loaded.append("pull requests")

            if self.load_commits:
                load_commit_data(self.owner, self.repo, destination_url, access_token=access_token)
                data_loaded.append("commits")

            # Update the instance attributes
            self.last_pipeline_run = datetime.now()
            self.pipeline_status = PipelineStatus.SUCCESS
            
            return {
                "status": "success",
                "message": f"Successfully loaded {', '.join(data_loaded)} data for {self.owner}/{self.repo}",
                "last_refresh": self.last_pipeline_run.isoformat()
            }
        except Exception as e:
            self.last_pipeline_run = datetime.now()
            self.pipeline_status = PipelineStatus.FAILED
            print(e)
            raise ValueError(f"Error loading data: {str(e)}")
        

    def source_name(self) -> str:
        """lowercase and remove special characters"""
        return f"{self.owner.lower()}_{self.repo.lower().replace('-', '')}"
