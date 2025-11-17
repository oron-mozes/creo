# GitHub Actions Workflows

This directory contains CI/CD workflows for the Creo platform.

## Workflows

### 1. `agent-evaluation.yml`
**Purpose**: Automatically evaluates all agents using the judge system on every push/PR to main.

**Required Secrets**:
- `GEMINI_API_KEY` - Google Gemini API key for AI evaluation
- `PINECONE_API_KEY` - Pinecone API key (optional, may not be needed for evaluation)

**Setup**:
1. Go to repository Settings → Secrets and variables → Actions
2. Add `GEMINI_API_KEY` with your Gemini API key
3. Get your API key from: https://makersuite.google.com/app/apikey

**What it does**:
- Evaluates each agent (onboarding, frontdesk, creator_finder, campaign_brief, outreach_message, campaign_builder, orchestrator)
- Generates confidence scores (0.0-1.0) for each agent
- Posts results as PR comments with emoji indicators:
  - ✅ Score ≥ 0.8 (Good)
  - ⚠️ Score 0.6-0.8 (Needs Improvement)
  - ❌ Score < 0.6 (Failing)
- Uploads detailed evaluation reports as artifacts

**Manual trigger**: Can be triggered manually via GitHub Actions tab

### 2. `contract-tests.yml`
**Purpose**: Verifies API contracts haven't broken on every push/PR.

**Required Secrets**: None (uses test keys)

**What it does**:
- Runs Socket.IO API contract tests
- Ensures server/client communication remains stable
- Comments on PRs if contracts are broken

### 3. `deploy.yml`
**Purpose**: Deploys to Cloud Run when a git tag is pushed.

**Required Secrets**:
- `GCP_SA_KEY` - Google Cloud service account key
- Other deployment secrets (see OPERATIONS.md)

**What it does**:
- Runs tests and evaluation
- Builds Docker image
- Deploys to Google Cloud Run
- Creates GitHub release

## Troubleshooting

### "GEMINI_API_KEY environment variable not set"

**Solution**: Add the secret to your repository:
1. Go to `https://github.com/<owner>/<repo>/settings/secrets/actions`
2. Click "New repository secret"
3. Name: `GEMINI_API_KEY`
4. Value: Your Gemini API key from https://makersuite.google.com/app/apikey
5. Click "Add secret"

### "ModuleNotFoundError: No module named 'google'"

**Solution**: Already fixed in Makefile. If you see this, ensure you're on the latest main branch.

### Agent evaluation timing out

**Cause**: Rate limiting (10 requests/minute for Gemini API)

**Solution**: The judge system includes automatic rate limiting. Long test suites may take time.

## Local Development

To run evaluations locally:

```bash
# Set API key
export GEMINI_API_KEY=your-api-key

# Evaluate specific agent
make judge AGENT=onboarding_agent

# Evaluate all agents
for agent in onboarding_agent frontdesk_agent creator_finder_agent campaign_brief_agent outreach_message_agent campaign_builder_agent orchestrator_agent; do
  make judge AGENT=$agent
done
```

## Rate Limits

- **Gemini API**: 10 requests/minute (free tier)
- The judge system automatically rate-limits to ~9 req/min
- Evaluation of one agent with 5-10 test cases takes ~5-10 minutes

## Artifacts

Evaluation artifacts are uploaded and available for 90 days:
- `evaluation-reports` - Contains `report.json` for each agent
- Text output logs for each agent evaluation
