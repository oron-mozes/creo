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
- `make server` - Start FastAPI server with Socket.IO on http://localhost:8000
- `make test` - Run tests (if available)
- `make lint` - Run linter
- `make format` - Format code
- `make clean` - Clean cache files and virtual environment
- `make dev-reset` - Reset all development data (sessions, business cards, messages) for testing as a fresh user
- `make help` - Show all available commands

## Testing

### Contract Tests

Before making changes to the API, ensure you understand the contract:

```bash
# Run contract tests to verify API stability
make test

# Run only contract tests
pytest tests/test_socketio_contract.py -v
```

**Important**: Contract tests ensure the Socket.IO and HTTP API contracts remain stable. Breaking these tests means you're introducing a **breaking change** that will affect client applications.

See [`docs/API_CONTRACT.md`](API_CONTRACT.md) for the full API contract documentation.

### Testing Your Agent

1. After creating your agent, run `make web`
2. The agent should appear in the ADK web interface
3. Test it with various inputs to ensure it works as expected
4. Check that examples match the expected behavior

### Testing as a Fresh User

When developing features like onboarding or session management, you may need to test as a completely fresh user. Use the `dev-reset` command:

```bash
make dev-reset
```

This will:
1. Clear all in-memory sessions and runners
2. Clear all in-memory messages
3. Clear all in-memory business cards
4. Prompt you to clear browser localStorage

**Note:** This only affects local development with in-memory storage. If you're connected to Firestore, that data is NOT affected.

**To complete the reset:**
1. Open browser DevTools (F12)
2. Go to Application/Storage → Local Storage
3. Clear `creo_user_id` or clear all localStorage
4. Refresh the page

You can now test the full onboarding flow and other first-time user experiences!

## Code Style

- Follow PEP 8 Python style guidelines
- Use type hints where appropriate
- Keep functions focused and single-purpose
- Add docstrings to functions and classes

## Deployment

### Running the API Server Locally

```bash
# Start the FastAPI server
make server

# Or manually:
source venv/bin/activate
uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

Visit:
- API: http://localhost:8000
- Interactive Docs: http://localhost:8000/docs

### Deployment Options

We support multiple deployment platforms:

#### Option 1: Google Cloud Run (Recommended for Competition)

**Free Tier:** 2 million requests/month

**Requirements:**
- Google Cloud account
- Billing enabled (won't be charged within free tier)
- gcloud CLI installed

**Setup:**

1. Install gcloud CLI:
   ```bash
   # macOS
   brew install google-cloud-sdk
   ```

2. Login and configure:
   ```bash
   # Login with your personal Google account
   gcloud auth login

   # List projects
   gcloud projects list

   # Set active project
   gcloud config set project YOUR_PROJECT_ID
   ```

3. Enable billing at: https://console.cloud.google.com/billing

4. Enable required APIs:
   ```bash
   gcloud services enable run.googleapis.com \
     cloudbuild.googleapis.com \
     artifactregistry.googleapis.com
   ```

5. Deploy:
   ```bash
   gcloud run deploy creo \
     --source . \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars GOOGLE_API_KEY=your-gemini-key,PINECONE_API_KEY=your-pinecone-key
   ```

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed instructions.

#### Option 2: Railway (No Credit Card)

**Free Tier:** $5 credit/month

1. Sign up at https://railway.app
2. New Project → Deploy from GitHub
3. Select repository and add `GOOGLE_API_KEY` env var
4. Deploy automatically!

#### Option 3: Render (Completely Free)

**Free Tier:** Unlimited (with cold starts)

1. Sign up at https://render.com
2. New → Web Service
3. Connect GitHub and configure Docker environment
4. Add `GOOGLE_API_KEY` env var
5. Deploy!

### Environment Variables for Deployment

Required:
- `GOOGLE_API_KEY` - Your Google Gemini API key (get from https://aistudio.google.com/app/apikey)
- `PINECONE_API_KEY` - Your Pinecone API key (get from https://app.pinecone.io/)

Optional:
- `GCP_PROJECT_ID` - Google Cloud project ID (auto-detected if not set)
- `PORT` - Server port (Cloud Run sets this automatically)

## Automated Deployment (CI/CD)

The project uses GitHub Actions for continuous deployment. When you create a git tag, it automatically:

1. ✅ Runs tests and linting
2. ✅ Evaluates all agents
3. ✅ Deploys to Google Cloud Run
4. ✅ Creates a GitHub Release

### Creating a Release

```bash
# Make sure all changes are committed
git add .
git commit -m "Your changes"
git push origin main

# Create and push a version tag (triggers deployment)
git tag v1.0.0
git push origin v1.0.0
```

The workflow will automatically deploy to Cloud Run and create a release with the deployment URL.

See [RELEASE.md](RELEASE.md) for detailed release process documentation.

## Questions?

If you have questions or need help, please open an issue or reach out to the maintainers.

Thank you for contributing! 🎉

