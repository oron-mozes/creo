# Deployment Guide - Google Cloud Run

This guide will help you deploy the Creo Agent API to Google Cloud Run.

## Prerequisites

1. **Google Cloud Account** - Sign up at https://cloud.google.com
2. **gcloud CLI** - Install from https://cloud.google.com/sdk/docs/install
3. **Docker** (optional for local testing)

## Setup

### 1. Install Google Cloud CLI

```bash
# Install gcloud CLI (if not already installed)
# macOS
brew install google-cloud-sdk

# Or download from: https://cloud.google.com/sdk/docs/install
```

### 2. Initialize and Authenticate

```bash
# Login to Google Cloud
gcloud auth login

# Set your project (or create a new one)
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable artifactregistry.googleapis.com
```

### 3. Set Environment Variables

Your app needs these environment variables:
- `GEMINI_API_KEY` - For AI agent functionality
- `PINECONE_API_KEY` - For vector database (semantic search)
- `GCP_PROJECT_ID` - Your Google Cloud project ID (optional, auto-detected)

Get your API keys:
- Gemini: https://aistudio.google.com/app/apikey
- Pinecone: https://app.pinecone.io/ → API Keys (free tier available)

## Deployment Options

### Option A: Deploy Directly (Recommended - Easiest)

```bash
# Deploy to Cloud Run (builds and deploys in one command)
gcloud run deploy creo \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GEMINI_API_KEY=your-gemini-api-key,PINECONE_API_KEY=your-pinecone-api-key,GCP_PROJECT_ID=gen-lang-client-0751221742
```

### Option B: Build and Deploy Separately

```bash
# 1. Build the container image
gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/creo

# 2. Deploy to Cloud Run
gcloud run deploy creo \
  --image gcr.io/YOUR_PROJECT_ID/creo \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars GEMINI_API_KEY=your-gemini-api-key,PINECONE_API_KEY=your-pinecone-api-key,GCP_PROJECT_ID=gen-lang-client-0751221742
```

### Option C: Deploy with Makefile (Coming Soon)

```bash
make deploy
```

## Configuration Options

### Set Environment Variables

```bash
gcloud run services update creo \
  --update-env-vars GEMINI_API_KEY=your-api-key
```

### Set Memory and CPU

```bash
gcloud run deploy creo \
  --memory 2Gi \
  --cpu 2 \
  --max-instances 10
```

### Set Custom Domain

```bash
gcloud run services update creo \
  --region us-central1 \
  --add-custom-domain your-domain.com
```

## Testing Deployment

After deployment, you'll get a URL like: `https://creo-xxxxxxxxxx-uc.a.run.app`

Test the deployment:

```bash
# Health check
curl https://YOUR-CLOUD-RUN-URL/health

# Test chat endpoint
curl -X POST https://YOUR-CLOUD-RUN-URL/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "I need to find fashion influencers", "user_id": "test_user"}'
```

## Viewing Logs

```bash
# Stream logs in real-time
gcloud run logs tail creo --region us-central1

# View logs in Cloud Console
gcloud run services describe creo --region us-central1
```

## Updating the Service

After making code changes:

```bash
# Just run deploy again - it will update the existing service
gcloud run deploy creo --source . --region us-central1
```

## Cost Optimization

Cloud Run pricing:
- **Free tier**: 2 million requests/month
- **Pay per use**: Only charged when handling requests
- **Scales to zero**: No cost when not in use

Tips:
- Set `--min-instances 0` to scale to zero (default)
- Set `--max-instances` to control costs
- Use `--memory 512Mi` for lower costs if sufficient

## Adding a Custom UI

You can add a frontend in several ways:

### 1. Serve Static Files from FastAPI

Create a `static/` directory and mount it in `server.py`:

```python
from fastapi.staticfiles import StaticFiles
app.mount("/static", StaticFiles(directory="static"), name="static")
```

### 2. Add HTML Templates

Use Jinja2 templates for server-side rendering:

```bash
pip install jinja2
```

### 3. Separate Frontend (React/Vue)

Build your frontend and serve the `dist/` folder as static files.

## Troubleshooting

### Build Fails

```bash
# Check build logs
gcloud builds log --region us-central1
```

### Service Won't Start

```bash
# Check service logs
gcloud run logs read creo --region us-central1 --limit 50
```

### Permission Denied

```bash
# Make service publicly accessible
gcloud run services add-iam-policy-binding creo \
  --region us-central1 \
  --member="allUsers" \
  --role="roles/run.invoker"
```

## Security Best Practices

1. **Don't commit .env files** - Already in .gitignore
2. **Use Secret Manager** for sensitive data:
   ```bash
   echo -n "your-api-key" | gcloud secrets create gemini-api-key --data-file=-
   ```
3. **Enable authentication** if you don't want public access
4. **Set up Cloud Armor** for DDoS protection

## Next Steps

- [ ] Set up CI/CD with GitHub Actions
- [ ] Add monitoring and alerts
- [ ] Configure custom domain
- [ ] Add rate limiting
- [ ] Implement caching
- [ ] Add authentication

## Support

For issues:
- Cloud Run docs: https://cloud.google.com/run/docs
- Project issues: https://github.com/oron-mozes/creo/issues
