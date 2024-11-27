from fastapi import FastAPI, File, UploadFile, HTTPException
from relta import Client
from relta.datasource import DataSource
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Annotated
import aiofiles
from .data_loader import GithubRepoInfo, load_data
from dotenv import load_dotenv
import os
import os.path
from typing import Optional



REPO_NAMES = [ "assistant-ui", "crewai","dlt", "langchain", "llama_index"]

app = FastAPI()

class Prompt(BaseModel):
    # chat_id: str
    prompt: str


class Feedback(BaseModel):
    type: str
    message: dict


# Move global variables into a class for better organization
class ServerState:
    def __init__(self):
        self.client: Optional[Client] = None
        self.current_source: Optional[DataSource] = None
        self.chat = None
        self.repo: Optional[GithubRepoInfo] = None

server_state = ServerState()

def _source_name_from_repo_name(repo_name:str) -> str:
    """lowercase and remove special characters"""
    return repo_name.lower().replace('-', '')

def initialize_server(force_refresh: bool = False):
    """Initialize the server with GitHub data source"""
    load_dotenv()
    
    # Setup CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Initialize Relta client
    server_state.client = Client()
    base_url = os.environ.get('DATA_BUCKET_BASE_URL')
    default_data_url = f"{base_url}/{REPO_NAMES[0]}_github_data.duckdb"
    server_state.source = server_state.client.get_or_create_datasource(connection_uri=default_data_url, name=_source_name_from_repo_name(REPO_NAMES[0]))
    server_state.source.deploy()
    server_state.chat = server_state.client.create_chat(server_state.source)


# Update the route handlers to use server_state
@app.post("/chat")
def create_chat():
    server_state.chat = server_state.client.create_chat(server_state.source)
    print("new chat created")
    return server_state.chat

@app.post("/prompt")
def add_prompt_to_chat(prompt: Prompt, repo_name: str = REPO_NAMES[0]):
    # Check repo_name validity before entering try block
    if repo_name not in REPO_NAMES:
        raise HTTPException(
            status_code=404,
            detail=f"Repository '{repo_name}' data is not connected. Available repos: {REPO_NAMES}"
        )
    
    try:
        source_name = _source_name_from_repo_name(repo_name)
        
        # Check if we need to switch to a different source
        if not server_state.source or server_state.source.name != source_name:
            base_url = os.environ.get('DATA_BUCKET_BASE_URL')
            data_url = f"{base_url}/{repo_name}_github_data.duckdb"
            server_state.source = server_state.client.get_or_create_datasource(
                connection_uri=data_url,
                name=source_name
            )
            server_state.source.deploy()
            
        server_state.chat = server_state.client.create_chat(server_state.source)
        response = server_state.chat.prompt(prompt.prompt, debug=True)
        print(response)
        return response
        
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=500,
            detail="No Datasource connected to Relta"
        )

@app.post("/feedback")
def record_feedback(feedback: Feedback):
    if feedback.type == "positive":
        print("ignoring positive feedback")
        return {"status": "success"}

    print(feedback.message)
    match_resp = None
    for resp in server_state.chat.responses:
        if resp.text == feedback.message["content"][0]["text"]:
            match_resp = resp
            break
    if match_resp:
        match_resp.feedback(feedback.type)
    else:
        print("Couldn't find matching Response for feedback")

    layer = server_state.source.semantic_layer
    layer.refine(pr=True)
    return {"status": "success"}

@app.get("/")
async def root():
    return {"message": "hello"}


@app.post("/load-github-data")
async def load_github_data(repo_info: GithubRepoInfo):
    try:
        load_data(repo_info)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load GitHub data: {str(e)}"
        )

# Initialize server when module loads
initialize_server(force_refresh=bool(os.environ.get('FORCE_REFRESH')))


    


