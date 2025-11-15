# Contributing to Creo

Thank you for your interest in contributing to Creo! This guide will help you get started with the project.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- `make` command-line tool
- `pip` (Python package installer)

### Installing Prerequisites

#### macOS

1. **Install Homebrew** (if not already installed):
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. **Install Python**:
   ```bash
   brew install python@3.14
   ```
   Or install the latest Python 3:
   ```bash
   brew install python3
   ```

3. **Install make**:
   ```bash
   brew install make
   ```
   Note: On macOS, `make` might already be installed via Xcode Command Line Tools. If not, install Xcode Command Line Tools:
   ```bash
   xcode-select --install
   ```

4. **Verify installations**:
   ```bash
   python3 --version  # Should show Python 3.8 or higher
   pip3 --version     # Should show pip version
   make --version     # Should show make version
   ```

#### Linux (Ubuntu/Debian)

1. **Update package list**:
   ```bash
   sudo apt update
   ```

2. **Install Python and pip**:
   ```bash
   sudo apt install python3 python3-pip python3-venv
   ```

3. **Install make**:
   ```bash
   sudo apt install build-essential
   ```
   This installs `make` along with other essential build tools.

4. **Verify installations**:
   ```bash
   python3 --version  # Should show Python 3.8 or higher
   pip3 --version     # Should show pip version
   make --version     # Should show make version
   ```

#### Linux (Fedora/RHEL/CentOS)

1. **Install Python and pip**:
   ```bash
   sudo dnf install python3 python3-pip
   ```

2. **Install make**:
   ```bash
   sudo dnf install make gcc
   ```

3. **Verify installations**:
   ```bash
   python3 --version
   pip3 --version
   make --version
   ```

#### Windows

1. **Install Python**:
   - Download Python from [python.org](https://www.python.org/downloads/)
   - During installation, check "Add Python to PATH"
   - Verify installation:
     ```cmd
     python --version
     pip --version
     ```

2. **Install make**:
   - Option 1: Install via Chocolatey (recommended):
     ```cmd
     choco install make
     ```
   - Option 2: Install via winget:
     ```cmd
     winget install GnuWin32.Make
     ```
   - Option 3: Use WSL (Windows Subsystem for Linux) and follow Linux instructions
   - Option 4: Use Git Bash which includes make

3. **Alternative for Windows**: Use WSL2 (Windows Subsystem for Linux)
   - Install WSL2: `wsl --install`
   - Follow the Linux (Ubuntu/Debian) instructions above

### Setup Instructions

1. **Clone the repository** (if you haven't already):
   ```bash
   # Using SSH (recommended if you have SSH keys set up)
   git clone git@github.com:oron-mozes/creo.git
   
   # Or using HTTPS
   git clone https://github.com/oron-mozes/creo.git
   
   cd creo
   ```

2. **Install dependencies**:
   ```bash
   make install
   ```
   This will:
   - Create a virtual environment (if it doesn't exist)
   - Install `google-adk` and other dependencies
   - Upgrade pip to the latest version

3. **Set up environment variables**:
   ```bash
   cp .env.example .env
   ```
   Then edit `.env` and add your API keys:
   - For each agent, add the corresponding `AGENT_NAME_GOOGLE_API_KEY` variable
   - Or use a shared `GOOGLE_API_KEY` that will be available to all agents
   - Set `GOOGLE_GENAI_USE_VERTEXAI=0` if using API keys (or `1` for Vertex AI)

4. **Run the agents**:
   ```bash
   make web
   ```
   This will start the ADK web interface where you can interact with all available agents.

## Agent Architecture

Our agents are structured in a consistent, modular way. Here's how they're organized:

### Directory Structure

Each agent follows this structure:

```
agents/
├── agent-name/
│   ├── __init__.py          # Package initialization
│   ├── agent.py             # Agent definition
│   ├── instruction.md       # Agent instructions (required)
│   └── examples.md          # Example inputs/outputs (optional)
├── utils.py                 # Shared utilities
└── __init__.py              # Main package initialization
```

### Creating a New Agent

#### Quick Start (Recommended)

Use the scaffold script to automatically create a new agent with all necessary files:

```bash
make scaffold-agent NAME="Your Agent Name" DESC="Brief description of what the agent does"
```

Or using Python directly:

```bash
python scripts/scaffold_agent.py "Your Agent Name" "Brief description of what the agent does"
```

This will:
- Create the agent directory structure
- Generate all necessary files (`__init__.py`, `agent.py`, `instruction.md`, `examples.md`)
- Update `utils.py` with the new agent enum
- Update `__init__.py` to import the new agent
- Update `.env.example` with environment variable template
- Update orchestrator instructions

After scaffolding, you'll need to:
1. Edit `agents/your-agent-name/instruction.md` with detailed instructions for your agent
2. Edit `agents/your-agent-name/examples.md` with real examples
3. Add your API key to `.env` file: `YOUR_AGENT_NAME_GOOGLE_API_KEY=your-key`
4. Test your agent: `make web`

### Key Design Principles

1. **Separation of Concerns**:
   - Instructions and examples are stored in markdown files, not hardcoded in Python
   - This makes it easy to update agent behavior without touching code

2. **Shared Utilities**:
   - All agents use `load_agent_instruction()` to load their instructions
   - All agents use `load_agent_env()` to load environment variables
   - This ensures consistency and reduces code duplication

3. **Environment Variables**:
   - Each agent can have its own environment variables with the prefix `AGENT_NAME_`
   - Shared variables (without prefix) are available to all agents
   - Variables are loaded from a single `.env` file at the project root

4. **Agent Discovery**:
   - All agents are automatically discovered by ADK through the `agents/__init__.py` file
   - The orchestrator agent (root_agent) helps route users to the right agent

### Available Make Commands

- `make install` - Install dependencies and create virtual environment
- `make web` - Start the ADK web interface
- `make test` - Run tests (if available)
- `make lint` - Run linter
- `make format` - Format code
- `make clean` - Clean cache files and virtual environment
- `make help` - Show all available commands

## Testing Your Agent

1. After creating your agent, run `make web`
2. The agent should appear in the ADK web interface
3. Test it with various inputs to ensure it works as expected
4. Check that examples match the expected behavior

## Code Style

- Follow PEP 8 Python style guidelines
- Use type hints where appropriate
- Keep functions focused and single-purpose
- Add docstrings to functions and classes

## Questions?

If you have questions or need help, please open an issue or reach out to the maintainers.

Thank you for contributing! 🎉

