include .env 

.EXPORT_ALL_VARIABLES:
APP_NAME=github-assistant

TAG=latest
TF_VAR_app_name=${APP_NAME}
REGISTRY_NAME=${APP_NAME}
TF_VAR_image=${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${REGISTRY_NAME}:${TAG}
TF_VAR_region=${AWS_REGION}


setup-ecr: 
	cd server-poc/infra/setup && terraform init && terraform apply 

deploy-container:
	cd server-poc && sh deploy.sh

deploy-service:
	cd server-poc/infra/app && terraform init && terraform apply -auto-approve

destroy-service:
	cd server-poc/infra/app && terraform init && terraform destroy -auto-approve