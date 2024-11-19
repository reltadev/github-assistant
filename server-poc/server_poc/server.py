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



SOURCE_NAME = "issues"
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
        self.source: Optional[DataSource] = None
        self.chat = None
        self.repo: Optional[GithubRepoInfo] = None

server_state = ServerState()

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

    owner=os.environ.get('GITHUB_USER')
    repo=os.environ.get('GITHUB_REPO')
    access_token=os.environ.get('GITHUB_TOKEN')
    
    # Check if data exists
    data_exists = os.path.exists(f'data/{repo}_github_data.duckdb')
    
    if data_exists and not force_refresh:
        print("Found existing GitHub data. Loading from existing database...")
        server_state.source = server_state.client.get_or_create_datasource(
            connection_uri=f'data/{repo}_github_data.duckdb', 
            name='github_data'
        )
    else:
        print("Loading fresh GitHub data...")
        server_state.repo = GithubRepoInfo(
            owner=owner,
            repo=repo,
            access_token=access_token
        )
        load_data(server_state.repo)
        server_state.source = server_state.client.get_or_create_datasource(
            connection_uri=f'data/{repo}_github_data.duckdb',
            name='github_data'
        )

    server_state.source.deploy()
    server_state.chat = server_state.client.create_chat(server_state.source)

# Update the route handlers to use server_state
@app.post("/chat")
def create_chat():
    server_state.chat = server_state.client.create_chat(server_state.source)
    print("new chat created")
    return server_state.chat

@app.post("/prompt")
def add_prompt_to_chat(prompt: Prompt):
    try:
        server_state.source = server_state.client.get_datasource(SOURCE_NAME)
        server_state.chat = server_state.client.create_chat(server_state.source)
        response = server_state.chat.prompt(prompt.prompt, debug=True)
        print(response)
    except Exception as e:
        print(e)
        response = {"message": {"content": "No Datasource connected to Relta"}}
    return response

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


"""@app.post("/uploadfile/")
async def create_upload_file(
    file: Annotated[UploadFile, File(description="The CSV file that will be queried")],
):
    global chat
    global source
    client.delete_datasource(name=SOURCE_NAME)
    if file.content_type != "text/csv":
        raise HTTPException(400, detail="Invalid document type")
    async with aiofiles.open(f"data/data.csv", "wb+") as out_file:
        content = await file.read()  # async read
        await out_file.write(content)

    source = client.get_or_create_datasource(
        connection_uri=f"data/data.csv", name=SOURCE_NAME
    )
    source.deploy()
    chat = client.create_chat(source)
    return {
        "message": {
            "content": f"The file {file.filename} was succesfully uploaded to server-poc/data/data.csv"
        }
    }"""


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


    


