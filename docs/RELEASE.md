# Release Process

This document describes how to create a new release and deploy to Cloud Run.

## Overview

The project uses GitHub Actions for CI/CD. When you create a git tag, it automatically:

1. ✅ Runs linter
2. ✅ Runs tests (if available)
3. ✅ Evaluates agents with judge system
4. ✅ Deploys to Google Cloud Run
5. ✅ Tests the deployment
6. ✅ Creates a GitHub Release with deployment info

## Prerequisites

Before your first release, you need to set up GitHub Secrets:

### 1. Create a Google Cloud Service Account

```bash
# Set your project ID
PROJECT_ID="gen-lang-client-0751221742"

# Create service account
gcloud iam service-accounts create github-actions \
  --display-name="GitHub Actions Deployment" \
  --project=$PROJECT_ID

# Grant necessary permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/cloudbuild.builds.builder"

# Create and download key
gcloud iam service-accounts keys create github-actions-key.json \
  --iam-account=github-actions@${PROJECT_ID}.iam.gserviceaccount.com

# Display the key (copy this for GitHub Secrets)
cat github-actions-key.json
```

### 2. Add GitHub Secrets

Go to: https://github.com/oron-mozes/creo/settings/secrets/actions

Add these secrets:

1. **GCP_SA_KEY**
   - The entire contents of `github-actions-key.json`
   - This allows GitHub Actions to authenticate with Google Cloud

2. **GEMINI_API_KEY**
   - Your Google Gemini API key
   - Get it from: https://aistudio.google.com/app/apikey

3. **PINECONE_API_KEY**
   - Your Pinecone API key for vector database
   - Get it from: https://app.pinecone.io/ → API Keys

After adding secrets, **delete the local key file**:
```bash
rm github-actions-key.json
```

## Creating a Release

### Step 1: Prepare Your Changes

Make sure all your changes are committed and pushed to the `main` branch:

```bash
git add .
git commit -m "Your changes"
git push origin main
```

### Step 2: Create a Version Tag

Use semantic versioning (MAJOR.MINOR.PATCH):

- **MAJOR**: Breaking changes (v2.0.0)
- **MINOR**: New features (v1.1.0)
- **PATCH**: Bug fixes (v1.0.1)

```bash
# Create and push a tag
git tag v1.0.0
git push origin v1.0.0
```

Or create a tag with annotation:

```bash
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

### Step 3: Watch the Deployment

1. Go to: https://github.com/oron-mozes/creo/actions
2. You'll see the "Deploy to Cloud Run" workflow running
3. The workflow has three jobs:
   - **Test**: Runs linter and tests
   - **Judge Agents**: Evaluates all agents
   - **Deploy**: Deploys to Cloud Run and creates release

### Step 4: Verify Deployment

Once the workflow completes:

1. **Check the GitHub Release**:
   - Go to: https://github.com/oron-mozes/creo/releases
   - The release notes will include the Cloud Run URL

2. **Test the API**:
   ```bash
   # Replace with your actual Cloud Run URL
   SERVICE_URL="https://creo-xxxxx-uc.a.run.app"

   # Health check
   curl $SERVICE_URL/health

   # Test chat endpoint
   curl -X POST $SERVICE_URL/api/chat \
     -H "Content-Type: application/json" \
     -d '{"message": "I need to find fashion influencers", "user_id": "test"}'
   ```

## Rollback a Release

If something goes wrong, you can rollback to a previous version:

### Option 1: Redeploy Previous Tag

```bash
# Find previous tags
git tag -l

# Push the previous tag again (this will trigger redeployment)
git push origin v1.0.0 --force
```

### Option 2: Manual Rollback via Cloud Console

1. Go to: https://console.cloud.google.com/run/detail/us-central1/creo/revisions
2. Find the previous working revision
3. Click "Manage Traffic"
4. Route 100% traffic to the working revision

### Option 3: Manual Rollback via CLI

```bash
# List revisions
gcloud run revisions list --service=creo --region=us-central1

# Route traffic to specific revision
gcloud run services update-traffic creo \
  --region=us-central1 \
  --to-revisions=creo-00001-abc=100
```

## Troubleshooting

### Workflow Fails at Test Step

- Check the workflow logs in GitHub Actions
- Fix the issues locally
- Create a new tag (increment patch version)

### Workflow Fails at Judge Step

- Agent evaluations might be failing
- Check evaluation reports in workflow artifacts
- This won't block deployment (continue-on-error is set)

### Workflow Fails at Deploy Step

**Authentication Error:**
- Verify `GCP_SA_KEY` secret is set correctly
- Check service account has proper permissions

**API Not Enabled:**
```bash
gcloud services enable run.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com
```

**Billing Not Enabled:**
- Go to: https://console.cloud.google.com/billing
- Enable billing for the project

### Deployment Succeeds but Service Returns Errors

1. Check Cloud Run logs:
   ```bash
   gcloud run logs read creo --region=us-central1 --limit=50
   ```

2. Verify environment variables:
   ```bash
   gcloud run services describe creo \
     --region=us-central1 \
     --format="value(spec.template.spec.containers[0].env)"
   ```

## Workflow Configuration

The deployment workflow is defined in `.github/workflows/deploy.yml`:

- **Trigger**: Tags matching `v*` pattern
- **Test Job**: Runs linting and tests
- **Judge Job**: Evaluates agents (up to 3 test cases per agent)
- **Deploy Job**: Deploys to Cloud Run only if previous jobs pass

You can customize:
- Number of test cases: Edit `--max-cases` parameter
- Agents to evaluate: Edit the `matrix.agent` list
- Deployment region: Edit `REGION` environment variable

## Version Strategy

Recommended versioning:

- **v0.x.x**: Pre-release, development versions
- **v1.0.0**: First production release
- **v1.x.x**: Minor updates, new features
- **v2.0.0**: Major changes, breaking API changes

## Quick Reference

```bash
# Create a new release
git tag v1.0.0
git push origin v1.0.0

# Delete a tag (if made a mistake)
git tag -d v1.0.0
git push origin :refs/tags/v1.0.0

# List all tags
git tag -l

# View deployment logs
gcloud run logs tail creo --region=us-central1

# Get service URL
gcloud run services describe creo \
  --region=us-central1 \
  --format="value(status.url)"
```

## Manual Deployment (Without Tags)

If you need to deploy without creating a release:

```bash
gcloud run deploy creo \
  --source . \
  --region us-central1 \
  --project gen-lang-client-0751221742 \
  --allow-unauthenticated \
  --set-env-vars GEMINI_API_KEY=your-key
```

## Next Steps

After your first successful deployment:

- [ ] Set up custom domain (optional)
- [ ] Configure monitoring and alerts
- [ ] Set up Cloud Armor for DDoS protection
- [ ] Add rate limiting
- [ ] Set up Cloud CDN (optional)

---

**Need Help?** Check the GitHub Actions logs or open an issue at https://github.com/oron-mozes/creo/issues
