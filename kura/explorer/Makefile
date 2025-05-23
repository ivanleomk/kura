.PHONY: help build up down logs shell clean dev prod

# Default checkpoint directory
CHECKPOINT_DIR ?= ./checkpoints

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

build: ## Build all Docker images
	docker-compose build

up: ## Start all services
	KURA_CHECKPOINT_DIR=$(CHECKPOINT_DIR) docker-compose up

up-d: ## Start all services in detached mode
	KURA_CHECKPOINT_DIR=$(CHECKPOINT_DIR) docker-compose up -d

down: ## Stop all services
	docker-compose down

logs: ## View logs from all services
	docker-compose logs -f

logs-backend: ## View backend logs
	docker-compose logs -f backend

logs-frontend: ## View frontend logs
	docker-compose logs -f frontend

shell-backend: ## Open shell in backend container
	docker-compose exec backend /bin/bash

clean: ## Remove all containers and images
	docker-compose down -v --rmi all

dev-backend: ## Run backend in development mode (local)
	cd backend && uvicorn main:app --reload --port 8001

dev-frontend: ## Run frontend in development mode (local)
	cd frontend && npm run dev

dev: ## Run both backend and frontend locally
	./start.sh

prod: ## Run in production mode with nginx proxy
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml --profile with-proxy up

test-api: ## Test API endpoints
	curl http://localhost:8001/api/health
	@echo "\n"
	curl http://localhost:8001/api/stats

env: ## Create .env file from example
	cp -n .env.example .env || true
	@echo "Created .env file. Please edit it to set your checkpoint directory."