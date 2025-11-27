<p align="center">
  <img src="static/creo-logo-BesatB3H.png" alt="Creo Logo" width="200">
</p>

# Creo Agent API

AI-powered influencer marketing automation platform with intelligent agents for campaign building, creator discovery, and outreach.

## Quick Start

```bash
# Install dependencies
make install

# Start the server
make server
```

Visit http://localhost:8000 to see the API running.

## Features

### AI Agents (7 Total)
- 🎯 **Orchestrator Agent** - Routes requests and manages workflow transitions
- 👋 **Onboarding Agent** - Collects business information with Google search enrichment
- 💬 **Frontdesk Agent** - Transforms technical responses into friendly user messages
- 📋 **Campaign Brief Agent** - Creates detailed campaign requirements
- 🔍 **Creator Finder Agent** - Discovers influencers using semantic search
- ✉️ **Outreach Message Agent** - Generates personalized outreach messages
- 🚀 **Campaign Builder Agent** - Builds comprehensive marketing campaigns
- 💡 **Suggestions Agent** - Provides personalized campaign recommendations

### Platform Capabilities
- 🔐 **Authentication** - Google OAuth 2.0 + anonymous users with JWT tokens
- 💾 **Dual Database** - Firestore (NoSQL) + Pinecone (vector search)
- 🔄 **Real-time Communication** - Socket.IO for live chat
- 🧠 **Shared Session Context** - Per-session/user context injected into every agent/tool
- 📂 **Creator Persistence** - Creator search results saved per session and exposed via `/api/creators` and the React `/creators?session_id=...` page
- 📊 **Agent Evaluation** - Hybrid testing with LLM judge (Gemini 2.0)
- 🔒 **Secure Secrets** - Google Secret Manager integration
- 🚀 **CI/CD Pipeline** - Automated testing and deployment to Cloud Run
- 🧪 **Contract Testing** - API stability validation

## Documentation

📚 **[View All Documentation](docs/)**

### Core Documentation
- **[API Documentation](docs/API.md)** - HTTP and Socket.IO API specifications
- **[Architecture](docs/ARCHITECTURE.md)** - Multi-agent system design and workflow stages
- **[Authentication](docs/AUTHENTICATION.md)** - Google OAuth and JWT implementation
- **[Context Sharing](docs/CONTEXT_SHARING.md)** - Session memory and state management

### Operations & DevOps
- **[Deployment Guide](docs/DEPLOYMENT.md)** - Google Cloud Run deployment
- **[Database Setup](docs/DATABASE.md)** - Firestore and Pinecone configuration
- **[Secrets Management](docs/SECRETS.md)** - Google Secret Manager setup
- **[Operations Guide](docs/OPERATIONS.md)** - Production operations and troubleshooting

### Development & Testing
- **[Contributing Guide](docs/CONTRIBUTING.md)** - Setup and development workflow
- **[Agent Evaluation Guide](docs/AGENT_EVALUATION_GUIDE.md)** - Testing and evaluation
- **[Agent Evaluation CI](docs/AGENT_EVALUATION_CI.md)** - CI/CD evaluation pipeline

## Architecture

### System Overview

```mermaid
flowchart TB
    User([User])

    subgraph Client[Client Layer]
        WebUI[React Web UI chat & creators via Socket.IO and OAuth]
    end

    subgraph Server[FastAPI Server]
        API[HTTP/Socket.IO API]
        Auth[Authentication (Google OAuth + JWT) + Auth-Gate Tool]
        Session[Session Manager]
        Ctx[Shared Session Context]
    end

    subgraph Orchestration[Agent Orchestration]
        Orchestrator[Orchestrator Agent Workflow Router]
        Frontdesk[Frontdesk Agent Response Formatter]
    end

    subgraph Specialist[Specialist Agents]
        Onboarding[Onboarding Agent]
        Brief[Campaign Brief Agent]
        Creator[Creator Finder Agent]
        Outreach[Outreach Agent]
        Campaign[Campaign Builder Agent]
        Suggestions[Suggestions Agent]
    end

    subgraph Data[Data Layer]
        Firestore[(Firestore Sessions/Messages/Creators In-memory fallback in dev)]
        Pinecone[(Pinecone Vectors)]
    end

    subgraph External[External AI and APIs]
        Gemini[Google Gemini 2.0 LLM + Embeddings]
        Search[Google Search API]
        YouTube[YouTube Data API v3 Creator search]
    end

    subgraph Infrastructure[Google Cloud]
        CloudRun[Cloud Run Serverless Hosting]
        SecretMgr[Secret Manager env injection at deploy]
    end

    User -->|Browser| WebUI
    WebUI <-->|Real-time| API
    WebUI -->|View creators| API
    API --> Auth
    API --> Session
    API --> Ctx
    Session --> Orchestrator
    Ctx --> Orchestrator

    Orchestrator -->|Routes| Onboarding
    Orchestrator -->|Routes| Brief
    Orchestrator -->|Routes| Creator
    Orchestrator -->|Routes| Outreach
    Orchestrator -->|Routes| Campaign
    Orchestrator -->|Routes| Suggestions

    Onboarding --> Frontdesk
    Brief --> Frontdesk
    Creator --> Frontdesk
    Outreach --> Frontdesk
    Campaign --> Frontdesk
    Suggestions --> Frontdesk

    Frontdesk -->|Response| Session

    Onboarding --> Gemini
    Onboarding --> Search
    Brief --> Gemini
    Outreach --> Gemini
    Campaign --> Gemini
    Suggestions --> Gemini
    Creator --> YouTube

    Session --> Firestore
    API --> Firestore
    Creator --> Firestore
    Creator --> Pinecone
    Auth -->|require_auth_for_outreach_tool| Creator

    SecretMgr -.->|Env vars| CloudRun
    CloudRun -.->|Hosts| API
```

### Workflow Stages

The platform guides users through structured workflow stages:

1. **ONBOARDING** → Collect business information
2. **CAMPAIGN_BRIEF** → Define campaign requirements
3. **CREATOR_FINDER** → Discover matching influencers
4. **OUTREACH_MESSAGE** → Generate personalized outreach
5. **CAMPAIGN_BUILDER** → Build comprehensive campaign strategy

Each stage is enforced by the Orchestrator to ensure proper progression.

## Tech Stack

### Backend
- **Framework**: FastAPI + Socket.IO (real-time WebSockets)
- **AI Platform**: Google ADK (Agent Development Kit)
- **LLM**: Google Gemini 2.0 Flash
- **Embeddings**: text-embedding-004
- **Runtime**: Python 3.11 + Uvicorn (ASGI)

### Data & Storage
- **NoSQL Database**: Google Cloud Firestore
  - Collections: conversations, sessions, campaigns, analytics
- **Vector Database**: Pinecone
  - Semantic search for creator discovery
  - 768-dimension embeddings

### Authentication & Security
- **OAuth Provider**: Google OAuth 2.0
- **Token Management**: JWT (HS256)
- **Secrets**: Google Secret Manager
- **Anonymous Support**: Yes (for testing)
- **Auth Gates**: Outreach requires authentication; login prompts can be triggered by the outreach agent tool (`require_auth_for_outreach`) and are enforced server-side.

### Infrastructure & DevOps
- **Hosting**: Google Cloud Run (serverless)
- **CI/CD**: GitHub Actions
  - Automated testing on PR/push
  - Agent evaluation with LLM judge
  - Contract testing for API stability
  - Auto-deployment on version tags
- **Containerization**: Docker

### Frontend
- **UI**: React + Tailwind (served from `frontend` build)
- **Real-time**: Socket.IO client
- **Authentication**: OAuth flow with auth-gate
- **Creator Review**: `/creators?session_id=...` shows saved creator matches per session

## Development

### Common Commands

```bash
# Install dependencies
make install

# Start development server
make server

# Run individual agent in web UI
make web AGENT=orchestrator-agent

# Run tests
make test

# Lint and format code
make lint
make format

# Verify environment setup
make verify-env
```

### Test Notes
- To run unit tests without autoloading agent modules, set `CREO_SKIP_AGENT_AUTOLOAD=1` (see `tests/`).
- Creator search requires a valid YouTube API key without IP restrictions; otherwise the creator finder will surface an API error and no creators will be persisted.

### Agent Development

```bash
# Create new agent scaffold
python scripts/scaffold_agent.py <agent-name>

# Generate tests for agent (hybrid: golden + LLM)
make generate-tests AGENT=orchestrator-agent

# Evaluate agent with LLM judge
make judge AGENT=orchestrator-agent

# Run agent in interactive web interface
make web AGENT=orchestrator-agent
```

### Testing & Quality

```bash
# Run all tests
make test

# Run contract tests (API stability)
pytest tests/test_socketio_contract.py

# Evaluate all agents
make judge AGENT=orchestrator-agent
make judge AGENT=onboarding-agent
# ... etc

# Generate test cases with LLM
make generate-tests-llm AGENT=<agent-name>

# Generate hybrid tests (recommended)
make generate-tests-hybrid AGENT=<agent-name>
```

### Docker & Deployment

```bash
# Build Docker image
make docker-build

# Run in Docker container
make docker-run

# Test Docker build
make docker-test

# Sync secrets to Google Secret Manager
./scripts/setup_secrets.sh

# Verify secrets configuration
./scripts/verify_secrets.sh
```

## Deployment

Deploy with a single command:

```bash
# Tag and push triggers auto-deployment
git tag v1.0.0
git push origin v1.0.0
```

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed instructions.

## License

MIT License - see LICENSE file for details.

## Support

- 📖 [Documentation](docs/)
- 🐛 [Report Issues](https://github.com/oron-mozes/creo/issues)
- 💬 [Discussions](https://github.com/oron-mozes/creo/discussions)
