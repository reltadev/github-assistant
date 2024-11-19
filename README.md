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
    - `GITHUB_TOKEN`, `GITHUB_USER`, `GITHUB_REPO`: This will be used to copy data from the github repo which questions will be answered from. The GITHUB_USER is the org that owns the repo. 

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

- The first time when data gets loaded can take a few minutes. On subsequent restarts if a local copy of the GitHub data is found then the user is prompted on whether they want to refresh.
- Currently only GitHub issues data is connected, even though we are copying all the data in the initial data pipeline run.

## Updating

We will generally give instructions on how to update Relta or the POC to handle any bugs or new features.
