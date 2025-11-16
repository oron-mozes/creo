.PHONY: help install test lint format clean run-agent web venv scaffold-agent generate-tests judge server docker-build docker-run docker-test docker-stop docker-clean verify-env sync-secrets verify-secrets

# Virtual environment path
VENV = venv
PYTHON = $(VENV)/bin/python3
PIP = $(PYTHON) -m pip

# Default target
help:
	@echo "Available commands:"
	@echo "  make install      - Install dependencies (creates venv if needed)"
	@echo "  make test         - Run tests"
	@echo "  make lint         - Run linter"
	@echo "  make format       - Format code"
	@echo "  make clean        - Clean cache files and venv"
	@echo "  make run-agent    - Run the campaign planner agent"
	@echo "  make web          - Start ADK web interface"
	@echo "  make venv         - Create virtual environment"
	@echo "  make scaffold-agent NAME=\"Agent Name\" DESC=\"Description\" - Scaffold a new agent"
	@echo "  make generate-tests - Generate synthetic test data for all agents"
	@echo "  make judge AGENT=\"Agent-folder-name\""
	@echo "  make server       - Start FastAPI server (exposes orchestrator agent)"
	@echo ""
	@echo "Docker commands:"
	@echo "  make docker-build - Build Docker image"
	@echo "  make docker-run   - Run Docker container locally"
	@echo "  make docker-test  - Build and test Docker container"
	@echo "  make docker-stop  - Stop running Docker container"
	@echo "  make docker-clean - Remove Docker images and containers"
	@echo ""
	@echo "Environment:"
	@echo "  make verify-env     - Verify all environment variables are configured"
	@echo "  make sync-secrets   - Sync secrets from .env to Google Secret Manager"
	@echo "  make verify-secrets - Verify secrets in Google Secret Manager"

# Create virtual environment
venv:
	@if [ ! -d "$(VENV)" ]; then \
		echo "Creating virtual environment..."; \
		python3 -m venv $(VENV); \
	fi

# Install dependencies
install: venv
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@echo "Installation complete. Activate venv with: source $(VENV)/bin/activate"

# Run tests
test: venv
	$(PYTHON) -m pytest tests/ -v

# Run linter
lint: venv
	$(VENV)/bin/ruff check agents/
	@echo "Linting complete"

# Format code
format: venv
	$(VENV)/bin/ruff format agents/
	@echo "Formatting complete"

# Clean cache files
clean:
	find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -r {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -r {} + 2>/dev/null || true
	@if [ -d "$(VENV)" ]; then rm -rf $(VENV); echo "Removed virtual environment"; fi
	@echo "Cleaned cache files"

# Run the campaign planner agent
run-agent: venv
	$(PYTHON) -m agents.campaing-planner-agent.agent

# Start ADK web interface
web: venv
	$(VENV)/bin/adk web

# Scaffold a new agent
scaffold-agent: venv
	@if [ -z "$(NAME)" ]; then \
		echo "Error: NAME is required. Usage: make scaffold-agent NAME=\"Agent Name\" DESC=\"Description\""; \
		exit 1; \
	fi
	$(PYTHON) scripts/scaffold_agent.py "$(NAME)" "$(DESC)"

# Generate synthetic test data for all agents
generate-tests: venv
	$(PYTHON) agents/test_utils.py

judge: venv
	@if [ -z "$(AGENT)" ]; then \
		echo "Usage: make judge AGENT=<agent-folder-name>"; \
		exit 1; \
	fi
	$(PYTHON) scripts/judge_agent.py --agent-dir agents/$(AGENT)

# Start FastAPI server
server: venv
	@echo "Starting FastAPI server on http://localhost:8000"
	@echo "API Documentation: http://localhost:8000/docs"
	$(VENV)/bin/uvicorn server:app --reload --host 0.0.0.0 --port 8000

# Docker commands
DOCKER_IMAGE = creo-agent-api
DOCKER_CONTAINER = creo-container
PORT = 8000

# Build Docker image
docker-build:
	@echo "Building Docker image..."
	@if [ ! -f .env ]; then \
		echo "Warning: .env file not found. Make sure to pass GEMINI_API_KEY when running."; \
	fi
	docker build -t $(DOCKER_IMAGE):latest .
	@echo "✓ Docker image built: $(DOCKER_IMAGE):latest"

# Run Docker container locally
docker-run:
	@echo "Starting Docker container on http://localhost:$(PORT)"
	@if [ ! -f .env ]; then \
		echo "Error: .env file not found. Create one with GEMINI_API_KEY=your-key"; \
		exit 1; \
	fi
	docker run -d \
		--name $(DOCKER_CONTAINER) \
		-p $(PORT):8080 \
		--env-file .env \
		$(DOCKER_IMAGE):latest
	@echo "✓ Container started: $(DOCKER_CONTAINER)"
	@echo "  Visit: http://localhost:$(PORT)"
	@echo "  API Docs: http://localhost:$(PORT)/docs"
	@echo "  Logs: docker logs -f $(DOCKER_CONTAINER)"

# Build and test Docker container
docker-test: docker-build
	@echo "Testing Docker container..."
	@echo "Starting container..."
	@if [ ! -f .env ]; then \
		echo "Error: .env file not found. Create one with GEMINI_API_KEY=your-key"; \
		exit 1; \
	fi
	@docker run -d --name $(DOCKER_CONTAINER)-test -p 8001:8080 --env-file .env $(DOCKER_IMAGE):latest
	@echo "Waiting for container to start..."
	@sleep 5
	@echo "Testing health endpoint..."
	@curl -f http://localhost:8001/health || (echo "❌ Health check failed" && docker logs $(DOCKER_CONTAINER)-test && docker stop $(DOCKER_CONTAINER)-test && docker rm $(DOCKER_CONTAINER)-test && exit 1)
	@echo "✓ Health check passed!"
	@echo "Testing API endpoint..."
	@curl -f -X POST http://localhost:8001/api/chat \
		-H "Content-Type: application/json" \
		-d '{"message":"test","user_id":"test"}' > /dev/null || (echo "❌ API test failed" && docker logs $(DOCKER_CONTAINER)-test && docker stop $(DOCKER_CONTAINER)-test && docker rm $(DOCKER_CONTAINER)-test && exit 1)
	@echo "✓ API test passed!"
	@docker stop $(DOCKER_CONTAINER)-test
	@docker rm $(DOCKER_CONTAINER)-test
	@echo "✓ All tests passed! Docker container is ready for deployment."

# Stop running Docker container
docker-stop:
	@echo "Stopping Docker container..."
	@docker stop $(DOCKER_CONTAINER) 2>/dev/null || echo "Container not running"
	@docker rm $(DOCKER_CONTAINER) 2>/dev/null || echo "Container already removed"
	@echo "✓ Container stopped"

# Clean up Docker images and containers
docker-clean: docker-stop
	@echo "Cleaning up Docker resources..."
	@docker rmi $(DOCKER_IMAGE):latest 2>/dev/null || echo "Image already removed"
	@docker system prune -f
	@echo "✓ Docker cleanup complete"

# Verify environment variables
verify-env: venv
	@$(PYTHON) scripts/verify_env.py

# Sync secrets to Google Secret Manager
sync-secrets:
	@echo "Syncing secrets to Google Secret Manager..."
	@bash scripts/setup_secrets.sh

# Verify secrets in Google Secret Manager
verify-secrets:
	@bash scripts/verify_secrets.sh
