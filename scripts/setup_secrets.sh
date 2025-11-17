#!/bin/bash
# Setup Google Secret Manager for secure credential storage
# This is MUCH more secure than storing keys in GitHub Secrets

set -e

PROJECT_ID="gen-lang-client-0751221742"
REGION="us-central1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_ROOT/.env"

echo "=========================================="
echo "Setting up Google Secret Manager"
echo "=========================================="
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found. Install from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Load environment variables from .env file
load_env_value() {
    local KEY=$1
    local VALUE=""

    if [ -f "$ENV_FILE" ]; then
        # Try exact match first
        VALUE=$(grep "^${KEY}=" "$ENV_FILE" | cut -d '=' -f 2- | head -n 1)

        # If not found, try GOOGLE_API_KEY for GOOGLE_API_KEY
        if [ -z "$VALUE" ] && [ "$KEY" = "GOOGLE_API_KEY" ]; then
            VALUE=$(grep "^GOOGLE_API_KEY=" "$ENV_FILE" | cut -d '=' -f 2- | head -n 1)
        fi
    fi

    echo "$VALUE"
}

echo "📁 Loading values from .env file: $ENV_FILE"
if [ ! -f "$ENV_FILE" ]; then
    echo "⚠️  .env file not found. You'll need to enter values manually."
fi
echo ""

# Enable Secret Manager API
echo "Enabling Secret Manager API..."
gcloud services enable secretmanager.googleapis.com --project=$PROJECT_ID

echo "✓ Secret Manager API enabled"
echo ""

# Function to create or update a secret
create_or_update_secret() {
    local SECRET_NAME=$1
    local SECRET_DESCRIPTION=$2
    local ENV_KEY=$3  # Optional: different env var name to read from

    echo "Setting up secret: $SECRET_NAME"
    echo "Description: $SECRET_DESCRIPTION"

    # Check if secret exists
    if gcloud secrets describe $SECRET_NAME --project=$PROJECT_ID &>/dev/null; then
        echo "  Secret already exists"
    else
        echo "  Creating new secret..."
        gcloud secrets create $SECRET_NAME \
            --replication-policy="automatic" \
            --project=$PROJECT_ID
        echo "  ✓ Secret created"
    fi

    # Try to load value from .env
    SECRET_VALUE=$(load_env_value "${ENV_KEY:-$SECRET_NAME}")

    if [ -n "$SECRET_VALUE" ]; then
        echo "  ✓ Found value in .env file"
        echo -n "  Use this value? [Y/n]: "
        read -r USE_ENV_VALUE
        if [[ ! "$USE_ENV_VALUE" =~ ^[Nn] ]]; then
            # Use value from .env
            echo -n "$SECRET_VALUE" | gcloud secrets versions add $SECRET_NAME \
                --data-file=- \
                --project=$PROJECT_ID
            echo "  ✓ Secret value stored from .env"
            echo ""
            return
        fi
    fi

    # Prompt for secret value
    echo -n "  Enter value for $SECRET_NAME: "
    read -s SECRET_VALUE
    echo ""

    if [ -z "$SECRET_VALUE" ]; then
        echo "  ⚠ Skipped (no value entered)"
    else
        # Add new version
        echo -n "$SECRET_VALUE" | gcloud secrets versions add $SECRET_NAME \
            --data-file=- \
            --project=$PROJECT_ID
        echo "  ✓ Secret value stored"
    fi

    echo ""
}

# Create secrets
# For GOOGLE_API_KEY, we'll check both GOOGLE_API_KEY and GOOGLE_API_KEY in .env
create_or_update_secret "GOOGLE_API_KEY" "Google Gemini API key for AI functionality" "GOOGLE_API_KEY"
create_or_update_secret "PINECONE_API_KEY" "Pinecone API key for vector database" "PINECONE_API_KEY"

echo "=========================================="
echo "Granting Cloud Run access to secrets"
echo "=========================================="
echo ""

# Get the Cloud Run service account
SERVICE_ACCOUNT=$(gcloud run services describe $SERVICE_NAME \
    --region=$REGION \
    --project=$PROJECT_ID \
    --format='value(spec.template.spec.serviceAccountName)' 2>/dev/null || echo "")

if [ -z "$SERVICE_ACCOUNT" ]; then
    echo "⚠ Cloud Run service not found yet"
    echo "Using default Compute Engine service account..."

    # Get project number
    PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')
    SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
fi

echo "Service Account: $SERVICE_ACCOUNT"
echo ""

# Grant access to secrets
for SECRET in "GOOGLE_API_KEY" "PINECONE_API_KEY"; do
    echo "Granting access to $SECRET..."

    # Check if binding already exists
    if gcloud secrets get-iam-policy $SECRET --project=$PROJECT_ID 2>/dev/null | grep -q "$SERVICE_ACCOUNT"; then
        echo "  ✓ Access already granted"
    else
        gcloud secrets add-iam-policy-binding $SECRET \
            --member="serviceAccount:$SERVICE_ACCOUNT" \
            --role="roles/secretmanager.secretAccessor" \
            --project=$PROJECT_ID
        echo "  ✓ Access granted"
    fi
done

echo ""
echo "=========================================="
echo "✓ Setup Complete!"
echo "=========================================="
echo ""
echo "Your secrets are now stored securely in Google Secret Manager."
echo ""
echo "View secrets at:"
echo "https://console.cloud.google.com/security/secret-manager?project=$PROJECT_ID"
echo ""
echo "Next steps:"
echo "  1. Deploy your app: git tag v1.0.0 && git push origin v1.0.0"
echo "  2. Secrets will be automatically loaded from Secret Manager"
echo ""
echo "Benefits:"
echo "  ✓ Secrets never leave Google Cloud"
echo "  ✓ Automatic rotation supported"
echo "  ✓ Audit logging enabled"
echo "  ✓ Fine-grained access control"
echo ""
