#!/bin/bash
# Setup GitHub Secret for GCP Service Account
# This creates a service account key and guides you to add it to GitHub Secrets

set -e

PROJECT_ID="gen-lang-client-0751221742"
SERVICE_ACCOUNT_NAME="github-actions-deployer"
SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
KEY_FILE="gcp-sa-key.json"

echo "=========================================="
echo "Setting up GitHub Actions Service Account"
echo "=========================================="
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found. Install from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

echo "1. Creating service account..."
if gcloud iam service-accounts describe $SERVICE_ACCOUNT_EMAIL --project=$PROJECT_ID &>/dev/null; then
    echo "   ✓ Service account already exists"
else
    gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME \
        --display-name="GitHub Actions Deployer" \
        --project=$PROJECT_ID
    echo "   ✓ Service account created"
fi
echo ""

echo "2. Granting necessary roles..."
ROLES=(
    "roles/run.admin"
    "roles/storage.admin"
    "roles/iam.serviceAccountUser"
    "roles/artifactregistry.admin"
    "roles/cloudbuild.builds.editor"
    "roles/serviceusage.serviceUsageConsumer"
)

for ROLE in "${ROLES[@]}"; do
    echo "   Granting $ROLE..."
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" \
        --role="$ROLE" \
        --quiet
done
echo "   ✓ All roles granted"
echo ""

echo "3. Creating service account key..."
if [ -f "$KEY_FILE" ]; then
    echo "   ⚠ Key file already exists. Removing old key..."
    rm "$KEY_FILE"
fi

gcloud iam service-accounts keys create $KEY_FILE \
    --iam-account=$SERVICE_ACCOUNT_EMAIL \
    --project=$PROJECT_ID

echo "   ✓ Key created: $KEY_FILE"
echo ""

echo "=========================================="
echo "✓ Service Account Setup Complete!"
echo "=========================================="
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. Copy the service account key:"
echo "   cat $KEY_FILE | pbcopy"
echo "   (The key has been copied to your clipboard)"
echo ""
echo "2. Add it to GitHub Secrets:"
echo "   • Go to: https://github.com/oron-mozes/creo/settings/secrets/actions"
echo "   • Click 'New repository secret'"
echo "   • Name: GCP_SA_KEY"
echo "   • Value: Paste the key from clipboard"
echo "   • Click 'Add secret'"
echo ""
echo "3. Delete the key file (for security):"
echo "   rm $KEY_FILE"
echo ""
echo "4. Re-run the failed workflow:"
echo "   • Go to: https://github.com/oron-mozes/creo/actions"
echo "   • Click on the failed workflow"
echo "   • Click 'Re-run failed jobs'"
echo ""

# Copy to clipboard if pbcopy is available
if command -v pbcopy &> /dev/null; then
    cat $KEY_FILE | pbcopy
    echo "✓ Key copied to clipboard!"
    echo ""
fi

echo "⚠️  IMPORTANT: Delete $KEY_FILE after adding to GitHub!"
echo "   This file contains sensitive credentials."
echo ""
