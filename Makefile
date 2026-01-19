.PHONY: help install run test lint format clean docker-build docker-push tf-init tf-apply tf-destroy helm-install helm-uninstall

# Variables
APP_NAME := weather-proxy
AWS_REGION := us-east-1
# These variables should be set or overridden by the user or environment
ECR_REPO_URL ?= $(APP_NAME)
IMAGE_TAG ?= latest

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# --- Development ---

install: ## Install python dependencies
	pip install -e ".[dev,test]"

run: ## Run the application locally
	uvicorn app.main:app --reload

test: ## Run tests
	pytest --cov=app

lint: ## Run linter checks
	ruff check .

format: ## Format code
	ruff format .

clean: ## Clean up cache and temporary files
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	rm -rf __pycache__
	find . -type d -name "__pycache__" -exec rm -rf {} +

# --- Docker ---

docker-build: ## Build docker image
	docker build -t $(APP_NAME) .

docker-login: ## Login to ECR (requires AWS CLI configured)
	aws ecr get-login-password --region $(AWS_REGION) | docker login --username AWS --password-stdin $(shell echo $(ECR_REPO_URL) | cut -d/ -f1)


docker-tag: ## Tag docker image for ECR
	docker tag $(APP_NAME):latest $(ECR_REPO_URL):$(IMAGE_TAG)


docker-push: docker-login docker-tag ## Push docker image to ECR
	docker push $(ECR_REPO_URL):$(IMAGE_TAG)

# --- Terraform ---

tf-init: ## Initialize Terraform
	cd terraform && terraform init


tf-plan: ## Plan Terraform changes
	cd terraform && terraform plan


tf-apply: ## Apply Terraform changes (provisions infrastructure)
	cd terraform && terraform apply


tf-destroy: ## Destroy Terraform infrastructure
	cd terraform && terraform destroy


tf-output: ## Show Terraform outputs
	cd terraform && terraform output

# --- Helm ---

helm-install: ## Install Helm chart
	helms install $(APP_NAME) ./charts/weather-proxy \
		--set image.repository=$(ECR_REPO_URL) \
		--set image.tag=$(IMAGE_TAG)


helm-upgrade: ## Upgrade Helm release
	helm upgrade $(APP_NAME) ./charts/weather-proxy \
		--set image.repository=$(ECR_REPO_URL) \
		--set image.tag=$(IMAGE_TAG)


helm-uninstall: ## Uninstall Helm release
	helm uninstall $(APP_NAME)


k8s-status: ## Check pod and service status
	kubectl get pods
	kubectl get svc $(APP_NAME)

