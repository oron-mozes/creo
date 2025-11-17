# Agent Evaluation CI/CD

This document explains the automated agent evaluation pipeline that runs on every pull request and push to main.

## Overview

The GitHub Actions workflow `.github/workflows/agent-evaluation.yml` automatically evaluates all agents using their test files and presents scores per agent.

## How It Works

### 1. Trigger Events
The workflow runs on:
- **Pull Requests** to `main` branch
- **Pushes** to `main` branch
- **Manual trigger** via GitHub Actions UI (workflow_dispatch)

### 2. Evaluation Process

For each agent, the workflow:
1. Runs `make judge AGENT=<agent_name>`
2. Extracts the average confidence score from the generated `report.json`
3. Saves the score for later reporting
4. Continues even if an agent evaluation fails (`continue-on-error: true`)

### 3. Agents Evaluated

The following agents are evaluated:
- `onboarding_agent`
- `frontdesk_agent`
- `creator_finder_agent`
- `campaign_brief_agent`
- `outreach_message_agent`
- `campaign_builder_agent`
- `orchestrator_agent`

### 4. Score Interpretation

The workflow uses the following thresholds:
- ✅ **Good** (Score ≥ 0.8) - Agent performs well
- ⚠️ **Needs Improvement** (Score 0.6-0.8) - Agent needs attention
- ❌ **Failing** (Score < 0.6) - Agent has significant issues

### 5. Reporting

The workflow provides scores in three ways:

#### A. PR Comments (Pull Requests Only)
Automatically posts a comment on the PR with a score table:

```markdown
## 🤖 Agent Evaluation Results

| Agent | Score |
|-------|-------|
| onboarding agent | ✅ 0.85 |
| frontdesk agent | ✅ 0.92 |
| creator finder agent | ⚠️ 0.75 |
| campaign brief agent | ✅ 0.88 |
| outreach message agent | ✅ 0.81 |
| campaign builder agent | ⚠️ 0.68 |
| orchestrator agent | ✅ 0.90 |

**Legend:**
- ✅ Score ≥ 0.8 (Good)
- ⚠️ Score 0.6-0.8 (Needs Improvement)
- ❌ Score < 0.6 (Failing)
```

#### B. GitHub Actions Summary
Creates a summary visible in the GitHub Actions UI with all scores.

#### C. Downloadable Artifacts
Uploads all evaluation reports and output logs as artifacts:
- `agents/*/evaluation/report.json` - Detailed JSON reports per agent
- `*_output.txt` - Full console output from each evaluation

## Required Secrets

The workflow requires the following GitHub secrets to be configured:
- `GOOGLE_API_KEY` - API key for Gemini LLM (used by judge)
- `PINECONE_API_KEY` - API key for Pinecone (if agents use it)

To add these secrets:
1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**
3. Add each secret with its value

## Local Testing

To run evaluations locally (same as CI):

```bash
# Evaluate a single agent
make judge AGENT=onboarding_agent

# Evaluate all agents (manual loop)
for agent in onboarding_agent frontdesk_agent creator_finder_agent \
             campaign_brief_agent outreach_message_agent \
             campaign_builder_agent orchestrator_agent; do
  echo "Evaluating $agent..."
  make judge AGENT=$agent
done
```

## Report Format

Each agent's `evaluation/report.json` contains:

```json
{
  "average_confidence_score": 0.85,
  "total_cases": 10,
  "test_results": [
    {
      "description": "Test case name",
      "score": 0.9,
      "rationale": "Brief explanation of score"
    }
  ]
}
```

## Troubleshooting

### Workflow fails with "No evaluation scores"
- Check that `agents/<agent>/evaluation/test.json` exists
- Verify test file format is correct
- Check workflow logs for agent-specific errors

### Scores are all N/A
- Verify API keys are configured correctly in GitHub secrets
- Check if `make judge` command works locally
- Review individual agent output logs in artifacts

### Agent evaluation times out
- Default timeout is based on test file size
- For large test files, consider splitting into smaller batches
- Check if LLM API is responding slowly

## Best Practices

1. **Add tests before code** - Write evaluation tests when creating new agent features
2. **Monitor score trends** - Track score changes across PRs to catch regressions
3. **Set quality gates** - Consider blocking PRs that drop scores significantly
4. **Review failing tests** - Download artifacts and check rationales for low scores
5. **Keep tests up-to-date** - Update test.json when agent behavior changes intentionally

## Future Enhancements

Potential improvements:
- [ ] Add score trend visualization across commits
- [ ] Set minimum score thresholds that block PRs
- [ ] Compare scores between PR and main branch
- [ ] Generate diff reports showing which tests improved/regressed
- [ ] Add cost tracking for LLM usage in evaluations
- [ ] Cache evaluation results to speed up re-runs
