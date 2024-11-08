# Relta Proof of Concept

## Requirements

- Python 3.9+
- npm or other Node.js package manager
- Git

## Setup

1. Add a remote to the `poc-template` repository and initialize the `relta` submodule

```sh
git remote add template https://github.com/reltadev/poc-template.git && git submodule update --init --recursive
```

2. Create a virtual environment for Relta

```sh
python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
```

3. Setup the `.env` files from `.env.example`

```sh
cp client-poc/.env.example client-poc/.env && cp server-poc/.env.example server-poc/.env
```

4. Set the following environment variables in `server-poc/.env`:
    - `OPENAI_API_KEY`: Your OpenAI API key
    - Optional `GITHUB_TOKEN`: if you want to test the PR flow, a GitHub personal access token with read/write access to the repository.
        - Feedback will still work without this environment variable, but it will not be a PR.

5. Launch Relta

```sh
source .venv/bin/activate && python launch.py
```

## Usage

To run the Relta POC, run
```sh
source .venv/bin/activate && python launch.py
```
Then go to http://localhost:3000/ to access the frontend, and optionally http://localhost:8000/docs to access the backend Swagger docs.

### Caveats

- You must begin the chat by uploading a file and submitting the message just containing the file upload.
- Uploading a new file removes the chat history of the previous chat, despite it being shown on the frontend.
- When restarting the server, the chat history will be empty.

## Updating

We will generally give instructions on how to update Relta or the POC to handle any bugs or new features.
