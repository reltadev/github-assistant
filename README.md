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

## Deployment to AWS

### Prerequisites

- AWS CLI configured with appropriate credentials
- Terraform installed
- Docker installed

### Deployment Steps

1. Create a `terraform.tfvars` file in the `terraform` directory with your variables:

```hcl
aws_region = "us-west-2"
openai_api_key = "your-openai-api-key"
github_token = "your-github-token"
github_user = "your-github-username"
github_repo = "your-github-repo"
```

2. Run the deployment script:

```sh
chmod +x deploy.sh
./deploy.sh
```

3. After deployment, the application will be available at the ALB DNS name output by Terraform.

### Cleanup

To destroy the AWS resources:

```sh
cd terraform
terraform destroy -auto-approve
```
