# Secure Secrets Management with Google Secret Manager

## Why Google Secret Manager?

**Much more secure than GitHub Secrets** because:

✅ **Secrets never leave Google Cloud** - No exposure through GitHub
✅ **Fine-grained access control** - IAM-based permissions
✅ **Automatic audit logging** - Track who accessed secrets
✅ **Secret rotation** - Update secrets without redeploying
✅ **Encryption at rest & in transit** - Google-managed encryption
✅ **No hardcoded secrets in CI/CD** - GitHub only needs deployment permission

## Setup (One-Time)

### Step 1: Sync Secrets to Google Secret Manager

```bash
make sync-secrets
```

This command will:
1. Enable Secret Manager API
2. Read secrets from your `.env` file
3. Create secrets for GEMINI_API_KEY and PINECONE_API_KEY in Google Secret Manager
4. Grant Cloud Run access to the secrets
5. Prompt you to confirm before uploading each secret value

### Step 2: Verify Secrets

```bash
make verify-secrets
```

This will check:
- Secret Manager API is enabled
- Required secrets exist (GEMINI_API_KEY, PINECONE_API_KEY)
- Secrets have values (versions)
- Cloud Run service account has access to secrets

You can also view secrets manually:

```bash
# List all secrets
gcloud secrets list --project=gen-lang-client-0751221742

# View secret metadata (not the actual value!)
gcloud secrets describe GEMINI_API_KEY --project=gen-lang-client-0751221742
```

View in Console:
https://console.cloud.google.com/security/secret-manager?project=gen-lang-client-0751221742

### Step 3: That's It!

Your deployment pipeline will automatically use these secrets. No GitHub Secrets needed for API keys!

## How It Works

### Local Development

Use `.env` file (never commit this):
```bash
GEMINI_API_KEY=your-key-here
PINECONE_API_KEY=your-key-here
```

### Cloud Run (Production)

Secrets are automatically injected as environment variables:
```yaml
# In deployment
--set-secrets GEMINI_API_KEY=GEMINI_API_KEY:latest
```

Cloud Run fetches the secret from Secret Manager at runtime.

### GitHub Actions

Only needs ONE secret:
- `GCP_SA_KEY` - Service account for deployment

API keys are never stored in GitHub!

## Managing Secrets

### Update a Secret

```bash
# Update GEMINI_API_KEY
echo -n "new-api-key-value" | gcloud secrets versions add GEMINI_API_KEY \
  --data-file=- \
  --project=gen-lang-client-0751221742

# Cloud Run will use the new value on next deployment
```

### Add a New Secret

```bash
# Create secret
gcloud secrets create NEW_SECRET_NAME \
  --replication-policy="automatic" \
  --project=gen-lang-client-0751221742

# Add value
echo -n "secret-value" | gcloud secrets versions add NEW_SECRET_NAME \
  --data-file=- \
  --project=gen-lang-client-0751221742

# Grant Cloud Run access
SERVICE_ACCOUNT=$(gcloud run services describe creo \
  --region=us-central1 \
  --project=gen-lang-client-0751221742 \
  --format='value(spec.template.spec.serviceAccountName)')

gcloud secrets add-iam-policy-binding NEW_SECRET_NAME \
  --member="serviceAccount:$SERVICE_ACCOUNT" \
  --role="roles/secretmanager.secretAccessor" \
  --project=gen-lang-client-0751221742

# Update deployment to use it
gcloud run services update creo \
  --update-secrets=NEW_SECRET_NAME=NEW_SECRET_NAME:latest \
  --region=us-central1 \
  --project=gen-lang-client-0751221742
```

### Delete a Secret

```bash
gcloud secrets delete SECRET_NAME --project=gen-lang-client-0751221742
```

### View Secret Value (Requires Permission)

```bash
# View latest version
gcloud secrets versions access latest \
  --secret=GEMINI_API_KEY \
  --project=gen-lang-client-0751221742
```

## Access Control

### Who Can Access Secrets?

1. **Cloud Run Service** - Granted automatically by setup script
2. **You (Owner)** - Full access
3. **Other developers** - Must be explicitly granted

### Grant Access to Another Developer

```bash
# Allow someone to read a secret
gcloud secrets add-iam-policy-binding GEMINI_API_KEY \
  --member="user:developer@example.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project=gen-lang-client-0751221742
```

### Revoke Access

```bash
gcloud secrets remove-iam-policy-binding GEMINI_API_KEY \
  --member="user:developer@example.com" \
  --role="roles/secretmanager.secretAccessor" \
  --project=gen-lang-client-0751221742
```

## Audit Logging

View who accessed secrets:

```bash
# View audit logs
gcloud logging read "protoPayload.serviceName=secretmanager.googleapis.com" \
  --project=gen-lang-client-0751221742 \
  --limit=50
```

Or in Console:
https://console.cloud.google.com/logs/query?project=gen-lang-client-0751221742

## Cost

**FREE tier:**
- First 6 secret versions: FREE
- 10,000 access operations/month: FREE

**After free tier:**
- $0.06 per secret version per month
- $0.03 per 10,000 access operations

For this project: **Stays FREE** (only 2 secrets, low access volume)

## Best Practices

### ✅ DO:
- Store all sensitive credentials in Secret Manager
- Rotate secrets regularly
- Use latest version (`:latest`) for production
- Enable audit logging
- Grant minimal permissions

### ❌ DON'T:
- Commit secrets to Git
- Store secrets in GitHub Secrets (for API keys)
- Share secrets via Slack/Email
- Use hardcoded secrets in code
- Give everyone access to all secrets

## Troubleshooting

### Quick Check

```bash
# Run verification to diagnose issues
make verify-secrets
```

### Error: Permission denied accessing secret

```bash
# Check who has access
gcloud secrets get-iam-policy GEMINI_API_KEY \
  --project=gen-lang-client-0751221742

# Grant access to Cloud Run service account
make sync-secrets
```

### Error: Secret not found

```bash
# List all secrets
gcloud secrets list --project=gen-lang-client-0751221742

# Re-run setup to create missing secrets
make sync-secrets
```

### Cloud Run not picking up new secret value

```bash
# Force new deployment
gcloud run services update creo \
  --region=us-central1 \
  --project=gen-lang-client-0751221742
```

## Comparison: GitHub Secrets vs Secret Manager

| Feature | GitHub Secrets | Google Secret Manager |
|---------|---------------|----------------------|
| **Security** | ⚠️ Exposed to GitHub | ✅ Stays in Google Cloud |
| **Access Control** | ❌ All repo collaborators | ✅ Fine-grained IAM |
| **Audit Logging** | ❌ Limited | ✅ Full audit trail |
| **Rotation** | ❌ Manual, requires re-deployment | ✅ Automatic, no re-deploy |
| **Encryption** | ✅ Yes | ✅ Yes (Google-managed) |
| **Cost** | ✅ Free | ✅ Free (for small usage) |
| **Best For** | Deployment credentials | API keys, passwords, tokens |

## Migration from GitHub Secrets

If you already have secrets in GitHub:

1. **Sync secrets to Secret Manager:**
   ```bash
   make sync-secrets
   ```

2. **Verify setup:**
   ```bash
   make verify-secrets
   ```

3. **Remove API keys from GitHub Secrets:**
   - Keep `GCP_SA_KEY` (still needed for deployment)
   - Remove `GEMINI_API_KEY` and `PINECONE_API_KEY`

4. **Deploy:**
   ```bash
   git tag v1.0.1
   git push origin v1.0.1
   ```

That's it! Much more secure now.

## Quick Reference

```bash
# Setup (one-time)
make sync-secrets

# Verify secrets are configured
make verify-secrets

# List secrets
gcloud secrets list

# Update a secret
echo -n "new-value" | gcloud secrets versions add SECRET_NAME --data-file=-

# View who has access
gcloud secrets get-iam-policy SECRET_NAME

# Deploy with secrets
gcloud run deploy creo \
  --set-secrets GEMINI_API_KEY=GEMINI_API_KEY:latest,PINECONE_API_KEY=PINECONE_API_KEY:latest
```

---

**Pro Tip:** Never commit API keys to Git. Use Secret Manager for production and `.env` (gitignored) for local development.
