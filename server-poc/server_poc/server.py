from fastapi import FastAPI, File, UploadFile, HTTPException
from relta import Client
from relta.datasource import DataSource
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Annotated
import aiofiles


SOURCE_NAME = "data"


class Prompt(BaseModel):
    # chat_id: str
    prompt: str


class Feedback(BaseModel):
    type: str
    message: dict


load_dotenv()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

client = Client()
source = client.get_or_create_datasource(
    connection_uri="data/data.csv", name=SOURCE_NAME
)
source.deploy()
chat = client.create_chat(source)


# @app.get("/datasource/{name}")
# async def get_datasource(name) -> DataSource:
#     return client.get_datasource(name)


@app.post("/chat")
def create_chat():
    global chat
    # source = client.get_datasource(source_name)
    print("new chat created")
    chat = client.create_chat(source)
    return chat


@app.post("/prompt")
def add_prompt_to_chat(prompt: Prompt):
    global chat
    try:
        # source = client.get_datasource(SOURCE_NAME)
        # chat = client.create_chat(source)
        response = chat.prompt(prompt.prompt, debug=True)
        print(response)
    except Exception as e:
        print(e)
        response = {"message": {"content": "No Datasource connected to Relta"}}
    return response


@app.post("/feedback")
def record_feedback(feedback: Feedback):
    global chat
    if feedback.type == "positive":
        # ignore positive feedback
        print("ignoring positive feedback")
        return {"status": "success"}

    # source = client.get_datasource(SOURCE_NAME)
    # chat = client.create_chat(source)
    # response = chat.prompt("what is the longest route flown?")
    print(feedback.message)
    match_resp = None
    for resp in chat.responses:
        if resp.text == feedback.message["content"][0]["text"]:
            match_resp = resp
            break
    if match_resp:
        match_resp.feedback(feedback.type)
    else:
        print("Couldn't find matching Response for feedback")
    # response.feedback(
    #     "negative",
    #     "add in a way to track length of routes",
    # )
    layer = source.semantic_layer
    layer.refine(pr=True)

    # if (feedback.type) == "negative":
    #     print(feedback.message)
    return {"status": "success"}


@app.get("/")
async def root():
    return {"message": "hello"}


@app.post("/uploadfile/")
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
    }
