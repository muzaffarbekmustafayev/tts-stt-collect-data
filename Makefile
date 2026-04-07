.PHONY: help install dev run test clean docker-build docker-up docker-down logs

help:
	@echo "Available commands:"
	@echo "  make install       - Install dependencies"
	@echo "  make dev          - Run in development mode"
	@echo "  make run          - Run in production mode"
	@echo "  make test         - Run tests"
	@echo "  make clean        - Clean cache and temp files"
	@echo "  make docker-build - Build Docker image"
	@echo "  make docker-up    - Start Docker containers"
	@echo "  make docker-down  - Stop Docker containers"
	@echo "  make logs         - Show Docker logs"

install:
	pip install -r requirements.txt

dev:
	uvicorn main:app --reload --host 0.0.0.0 --port 8000

run:
	python main.py

test:
	pytest -v

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

logs:
	docker-compose logs -f api

format:
	black app/ bot/
	isort app/ bot/

lint:
	flake8 app/ bot/
	mypy app/ bot/
