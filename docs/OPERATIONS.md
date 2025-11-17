# Operations Guide

> **Deployment, database setup, secrets management, and release process**

This document covers everything you need to deploy and operate the Creo platform in production.

## Table of Contents

1. [Database Setup](#database-setup)
2. [Secrets Management](#secrets-management)
3. [Deployment](#deployment)
4. [Release Process](#release-process)

---

## Database Setup

Creo uses two databases:
1. **Firestore** - NoSQL document database for structured data
2. **Pinecone** - Vector database for semantic search

### Firestore Setup

#### What It Stores
- Conversations (chat messages)
- Sessions (user session data)
- Campaigns (marketing campaigns)
- Analytics (usage events)

#### Free Tier
- ✅ 1GB storage FREE
- ✅ 50,000 reads/day FREE
- ✅ 20,000 writes/day FREE

#### Quick Setup

```bash
# Enable Firestore API
gcloud services enable firestore.googleapis.com

# Create database (Native mode)
gcloud firestore databases create \
  --location=nam5 \
  --project=YOUR_PROJECT_ID
```

Or via [Console](https://console.cloud.google.com/firestore) → Create Database → Native mode

#### Local Testing

```bash
# Using Docker
docker-compose up firestore

# Set environment variable
export FIRESTORE_EMULATOR_HOST=localhost:8080
export GCP_PROJECT_ID=demo-creo
```

### Pinecone Setup

#### What It Stores
- Semantic search embeddings
- RAG (Retrieval Augmented Generation) context
- Conversation memory

#### Free Tier
- ✅ 100,000 vectors FREE forever
- ✅ 1 index
- ✅ 2GB storage

#### Quick Setup

1. **Create account**: https://www.pinecone.io/ (no credit card)
2. **Get API key**: https://app.pinecone.io/ → API Keys
3. **Add to environment**:
   ```bash
   # .env file
   PINECONE_API_KEY=your-pinecone-api-key
   ```

Index is created automatically on first use.

### Environment Variables

```bash
# .env file
GOOGLE_API_KEY=your-gemini-api-key
PINECONE_API_KEY=your-pinecone-api-key
GCP_PROJECT_ID=your-project-id

# For local Firestore emulator (optional)
FIRESTORE_EMULATOR_HOST=localhost:8080
```

---

## Secrets Management

Use Google Secret Manager instead of GitHub Secrets for better security.

### Why Secret Manager?

✅ **Secrets never leave Google Cloud** - No exposure through GitHub
✅ **Fine-grained access control** - IAM-based permissions
✅ **Automatic audit logging** - Track who accessed secrets
✅ **Secret rotation** - Update without redeploying
✅ **Encryption at rest & in transit** - Google-managed

### One-Time Setup

#### Step 1: Sync Secrets

```bash
make sync-secrets
```

This will:
1. Enable Secret Manager API
2. Read secrets from `.env` file
3. Create secrets in Google Secret Manager
4. Grant Cloud Run access to secrets

#### Step 2: Verify

```bash
make verify-secrets
```

Checks:
- Secret Manager API enabled
- Required secrets exist
- Secrets have values
- Cloud Run has access

#### Step 3: Done!

Deployment pipeline automatically uses these secrets. No GitHub Secrets needed for API keys!

### Managing Secrets

#### Update a Secret

```bash
echo -n "new-api-key-value" | gcloud secrets versions add GOOGLE_API_KEY \
  --data-file=- \
  --project=YOUR_PROJECT_ID
```

#### Add New Secret

```bash
# Create
gcloud secrets create NEW_SECRET \
  --replication-policy="automatic" \
  --project=YOUR_PROJECT_ID

# Add value
echo -n "secret-value" | gcloud secrets versions add NEW_SECRET \
  --data-file=- \
  --project=YOUR_PROJECT_ID

# Grant access to Cloud Run
gcloud secrets add-iam-policy-binding NEW_SECRET \
  --member="serviceAccount:CLOUD_RUN_SA" \
  --role="roles/secretmanager.secretAccessor" \
  --project=YOUR_PROJECT_ID
```

#### View Secrets

```bash
# List all secrets
gcloud secrets list --project=YOUR_PROJECT_ID

# View secret metadata
gcloud secrets describe GOOGLE_API_KEY --project=YOUR_PROJECT_ID
```

Console: https://console.cloud.google.com/security/secret-manager

### Cost

**FREE tier:**
- First 6 secret versions: FREE
- 10,000 access operations/month: FREE

For this project: **Stays FREE** (only 2 secrets, low access volume)

---

## Deployment

### Prerequisites

1. **Google Cloud Account** - https://cloud.google.com
2. **gcloud CLI** - https://cloud.google.com/sdk/docs/install
3. **Docker** (optional for local testing)

### Initial Setup

```bash
# Login to Google Cloud
gcloud auth login

# Set your project
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable artifactregistry.googleapis.com
```

### Deploy to Cloud Run

#### Option A: Direct Deploy (Easiest)

```bash
gcloud run deploy creo \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-secrets=GOOGLE_API_KEY=GOOGLE_API_KEY:latest,PINECONE_API_KEY=PINECONE_API_KEY:latest
```

#### Option B: Build and Deploy Separately

```bash
# 1. Build container
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/creo

# 2. Deploy
gcloud run deploy creo \
  --image gcr.io/YOUR_PROJECT_ID/creo \
  --region us-central1 \
  --allow-unauthenticated \
  --set-secrets=GOOGLE_API_KEY=GOOGLE_API_KEY:latest
```

#### Option C: Makefile (Coming Soon)

```bash
make deploy
```

### Configuration

#### Set Memory and CPU

```bash
gcloud run deploy creo \
  --memory 2Gi \
  --cpu 2 \
  --max-instances 10
```

#### Set Custom Domain

```bash
gcloud run services update creo \
  --region us-central1 \
  --add-custom-domain your-domain.com
```

### Testing Deployment

After deployment, you'll get a URL like: `https://creo-xxxxxxxxxx-uc.a.run.app`

```bash
# Health check
curl https://YOUR-CLOUD-RUN-URL/health

# Test chat endpoint
curl -X POST https://YOUR-CLOUD-RUN-URL/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "I need to find fashion influencers", "user_id": "test"}'
```

### Viewing Logs

```bash
# Stream logs in real-time
gcloud run logs tail creo --region us-central1

# View logs in console
gcloud run services describe creo --region us-central1
```

### Updating the Service

After code changes:

```bash
# Just deploy again - updates existing service
gcloud run deploy creo --source . --region us-central1
```

### Cost Optimization

Cloud Run pricing:
- **Free tier**: 2 million requests/month
- **Pay per use**: Only charged when handling requests
- **Scales to zero**: No cost when not in use

Tips:
- Set `--min-instances 0` to scale to zero (default)
- Set `--max-instances` to control costs
- Use `--memory 512Mi` for lower costs if sufficient

---

## Release Process

### Overview

The project uses GitHub Actions for CI/CD. Creating a git tag automatically:

1. ✅ Runs linter
2. ✅ Runs tests
3. ✅ Evaluates agents with judge system
4. ✅ Deploys to Google Cloud Run
5. ✅ Tests the deployment
6. ✅ Creates a GitHub Release

### Prerequisites

#### 1. Create Service Account

```bash
PROJECT_ID="YOUR_PROJECT_ID"

# Create service account
gcloud iam service-accounts create github-actions \
  --display-name="GitHub Actions Deployment" \
  --project=$PROJECT_ID

# Grant permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

# Create key
gcloud iam service-accounts keys create github-actions-key.json \
  --iam-account=github-actions@${PROJECT_ID}.iam.gserviceaccount.com
```

#### 2. Add GitHub Secrets

Go to: https://github.com/YOUR_USERNAME/creo/settings/secrets/actions

Add:
1. **GCP_SA_KEY** - Contents of `github-actions-key.json`
2. **GOOGLE_API_KEY** - Your Gemini API key
3. **PINECONE_API_KEY** - Your Pinecone API key

Then delete local key file:
```bash
rm github-actions-key.json
```

### Creating a Release

#### Step 1: Prepare Changes

```bash
git add .
git commit -m "Your changes"
git push origin main
```

#### Step 2: Create Version Tag

Use semantic versioning (MAJOR.MINOR.PATCH):

```bash
# Create and push tag
git tag v1.0.0
git push origin v1.0.0
```

Or with annotation:

```bash
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

#### Step 3: Watch Deployment

1. Go to: https://github.com/YOUR_USERNAME/creo/actions
2. Watch "Deploy to Cloud Run" workflow
3. Jobs: Test → Judge Agents → Deploy

#### Step 4: Verify

Once complete:

1. **Check GitHub Release**: https://github.com/YOUR_USERNAME/creo/releases
2. **Test the API**:
   ```bash
   SERVICE_URL="https://creo-xxxxx-uc.a.run.app"

   curl $SERVICE_URL/health

   curl -X POST $SERVICE_URL/api/chat \
     -H "Content-Type: application/json" \
     -d '{"message": "test", "user_id": "test"}'
   ```

### Rollback a Release

#### Option 1: Redeploy Previous Tag

```bash
# Find previous tags
git tag -l

# Push previous tag again
git push origin v1.0.0 --force
```

#### Option 2: Cloud Console

1. Go to: https://console.cloud.google.com/run/detail/us-central1/creo/revisions
2. Find previous working revision
3. Click "Manage Traffic"
4. Route 100% traffic to working revision

#### Option 3: CLI

```bash
# List revisions
gcloud run revisions list --service=creo --region=us-central1

# Route traffic
gcloud run services update-traffic creo \
  --region=us-central1 \
  --to-revisions=creo-00001-abc=100
```

### Version Strategy

- **v0.x.x**: Pre-release, development
- **v1.0.0**: First production release
- **v1.x.x**: Minor updates, new features
- **v2.0.0**: Major changes, breaking changes

### Quick Reference

```bash
# Create release
git tag v1.0.0
git push origin v1.0.0

# Delete tag (if mistake)
git tag -d v1.0.0
git push origin :refs/tags/v1.0.0

# List tags
git tag -l

# View logs
gcloud run logs tail creo --region=us-central1

# Get service URL
gcloud run services describe creo \
  --region=us-central1 \
  --format="value(status.url)"
```

---

## Troubleshooting

### Database Issues

**Firestore Permission denied**
```bash
# Re-authenticate
gcloud auth application-default login
```

**Pinecone API key invalid**
- Check key at https://app.pinecone.io/
- Verify environment variable is set

### Deployment Issues

**Build fails**
```bash
gcloud builds log --region us-central1
```

**Service won't start**
```bash
gcloud run logs read creo --region us-central1 --limit 50
```

**Permission denied**
```bash
gcloud run services add-iam-policy-binding creo \
  --region us-central1 \
  --member="allUsers" \
  --role="roles/run.invoker"
```

### Secrets Issues

**Quick check**
```bash
make verify-secrets
```

**Permission denied accessing secret**
```bash
# Check access
gcloud secrets get-iam-policy GOOGLE_API_KEY --project=YOUR_PROJECT_ID

# Grant access
make sync-secrets
```

---

## Security Best Practices

### ✅ DO:
- Store all sensitive credentials in Secret Manager
- Rotate secrets regularly
- Use latest version (`:latest`) for production
- Enable audit logging
- Grant minimal permissions
- Set up Cloud Armor for DDoS protection

### ❌ DON'T:
- Commit secrets to Git
- Store API keys in GitHub Secrets
- Share secrets via Slack/Email
- Use hardcoded secrets in code
- Give everyone access to all secrets

---

## Next Steps

After first deployment:

- [ ] Set up custom domain
- [ ] Configure monitoring and alerts
- [ ] Set up Cloud Armor for DDoS protection
- [ ] Add rate limiting
- [ ] Set up Cloud CDN (optional)
- [ ] Implement Firestore security rules
- [ ] Create Firestore indexes
- [ ] Set up backup strategy

---

## Summary

The Creo operations setup provides:

✅ **Firestore** - Free NoSQL database for structured data
✅ **Pinecone** - Free vector database for semantic search
✅ **Secret Manager** - Secure secrets management
✅ **Cloud Run** - Serverless deployment with auto-scaling
✅ **CI/CD** - Automated deployment via GitHub Actions
✅ **Cost optimization** - Free tiers and pay-per-use pricing

For questions or issues, check the Cloud Run docs or open an issue on GitHub.
