.PHONY: setup test lint format docker-up docker-down clean help

help:
	@echo "DCIS Development Commands"
	@echo "========================="
	@echo "make setup       - Initialize development environment"
	@echo "make test        - Run all tests with coverage"
	@echo "make lint        - Run linting (Ruff + mypy)"
	@echo "make format      - Format code (Ruff + Prettier)"
	@echo "make docker-up   - Start Docker services"
	@echo "make docker-down - Stop Docker services"
	@echo "make clean       - Clean build artifacts"

setup:
	@echo "Setting up Python environment..."
	cd backend && poetry install
	@echo "Setting up Node.js environment..."
	cd frontend && pnpm install
	@echo "Installing pre-commit hooks..."
	pre-commit install
	@echo "Setup complete!"

test:
	@echo "Running backend tests..."
	cd backend && poetry run pytest --cov=src --cov-report=html --cov-report=term
	@echo "Running frontend tests..."
	cd frontend && pnpm test

lint:
	@echo "Linting backend..."
	cd backend && poetry run ruff check src/
	cd backend && poetry run mypy src/
	@echo "Linting frontend..."
	cd frontend && pnpm lint

format:
	@echo "Formatting backend..."
	cd backend && poetry run ruff format src/
	@echo "Formatting frontend..."
	cd frontend && pnpm format

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type d -name .ruff_cache -exec rm -rf {} +
	find . -type d -name .mypy_cache -exec rm -rf {} +
	rm -rf backend/htmlcov/
	rm -rf frontend/.next/
	rm -rf frontend/out/
