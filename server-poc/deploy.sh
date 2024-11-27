#!/bin/bash

# Build and push Docker image
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
docker build -t github-assistant .
docker tag github-assistant:latest 011528285911.dkr.ecr.us-east-1.amazonaws.com/github-assistant:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/github-assistant:latest

