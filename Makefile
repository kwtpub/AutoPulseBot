.PHONY: help install test lint format clean docker-build docker-run docker-stop

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install dependencies
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

install-dev: ## Install development dependencies
	pip install -r requirements-dev.txt

install-hooks: ## Install pre-commit hooks
	pre-commit install

test: ## Run tests
	pytest tests/ -v --cov=app --cov-report=html --cov-report=term-missing

test-fast: ## Run tests without coverage
	pytest tests/ -v

lint: ## Run linting
	flake8 app/ main.py
	black --check app/ main.py
	isort --check-only app/ main.py

format: ## Format code
	black app/ main.py
	isort app/ main.py

pre-commit: ## Run pre-commit hooks
	pre-commit run --all-files

security: ## Run security checks
	safety check
	bandit -r app/

clean: ## Clean up generated files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf downloads/*
	rm -rf temp/*
	rm -rf logs/*

docker-build: ## Build Docker image
	docker build -t telegram-auto-post-bot .

docker-run: ## Run with Docker Compose
	docker-compose up -d

docker-stop: ## Stop Docker Compose
	docker-compose down

docker-logs: ## Show Docker logs
	docker-compose logs -f telegram-bot

docker-shell: ## Open shell in running container
	docker-compose exec telegram-bot bash

run: ## Run the bot locally
	python main.py

run-dev: ## Run with development settings
	PYTHONPATH=. python main.py

setup: install install-hooks format ## Setup development environment
	@echo "Development environment setup complete!"

ci: lint test security ## Run CI checks locally
	@echo "All CI checks passed!" 