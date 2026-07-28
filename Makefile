SHELL := /bin/bash
.DEFAULT_GOAL := help

.PHONY: help bootstrap up up-rag up-frontend down logs ps pull-models lint format typecheck test build build-all compose-config

help:
	@awk 'BEGIN {FS = ":.*##"; printf "Usage: make <target>\n\n"} /^[a-zA-Z_-]+:.*?##/ {printf "  %-18s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

bootstrap: ## Prepare and start the current AgentForge foundation
	./scripts/bootstrap.sh

up: ## Start the AgentForge API foundation and PostgreSQL
	docker compose up --build -d postgres api

up-rag: ## Start the API plus AF-2B Ollama and Chroma infrastructure
	docker compose --profile rag up --build -d

up-frontend: ## Start the foundation plus the AgentForge frontend
	docker compose --profile frontend up --build -d

down: ## Stop the development stack
	docker compose down

logs: ## Follow service logs
	docker compose logs -f

ps: ## Show container status
	docker compose ps

pull-models: ## Start Ollama and pull the configured local models
	docker compose --profile rag up -d ollama
	./scripts/pull_models.sh

lint: ## Run backend and frontend linters
	cd apps/api && uv run --extra dev ruff check .
	npm run lint

format: ## Format backend and frontend files
	cd apps/api && uv run --extra dev ruff format .
	npm run format

typecheck: ## Run Python and TypeScript type checks
	cd apps/api && uv run --extra dev mypy app
	npm run typecheck

test: ## Run backend and frontend unit tests
	cd apps/api && uv run --extra dev pytest
	npm run test

build: ## Build the AgentForge API foundation image
	docker compose build api

build-all: ## Build API and frontend images explicitly
	docker compose build api web

compose-config: ## Validate the Docker Compose files
	docker compose config --quiet
	docker compose -f compose.test.yaml config --quiet
