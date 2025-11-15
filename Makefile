.PHONY: help install test lint format clean run-agent web venv scaffold-agent generate-tests judge server

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

# Create virtual environment
venv:
	@if [ ! -d "$(VENV)" ]; then \
		echo "Creating virtual environment..."; \
		python3 -m venv $(VENV); \
	fi

# Install dependencies
install: venv
	$(PIP) install --upgrade pip
	$(PIP) install google-adk==1.18.0 google-generativeai==0.8.2 python-multipart fastapi uvicorn
	@if [ -f requirements.txt ]; then $(PIP) install -r requirements.txt; fi
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
