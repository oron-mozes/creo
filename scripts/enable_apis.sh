#!/bin/bash
# Enable all required Google Cloud APIs for the project

set -e

PROJECT_ID="gen-lang-client-0751221742"

echo "=========================================="
echo "Enabling Google Cloud APIs"
echo "=========================================="
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found. Install from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# List of required APIs
APIS=(
    "run.googleapis.com"                    # Cloud Run
    "cloudbuild.googleapis.com"             # Cloud Build (for container builds)
    "artifactregistry.googleapis.com"       # Artifact Registry (for container images)
    "secretmanager.googleapis.com"          # Secret Manager
    "firestore.googleapis.com"              # Firestore
    "iam.googleapis.com"                    # IAM
    "cloudresourcemanager.googleapis.com"   # Resource Manager
)

echo "Project: $PROJECT_ID"
echo ""

for API in "${APIS[@]}"; do
    echo "Enabling $API..."
    if gcloud services list --enabled --project=$PROJECT_ID | grep -q "$API"; then
        echo "  ✓ Already enabled"
    else
        gcloud services enable "$API" --project=$PROJECT_ID
        echo "  ✓ Enabled"
    fi
done

echo ""
echo "=========================================="
echo "✓ All APIs Enabled!"
echo "=========================================="
echo ""
echo "Enabled APIs:"
for API in "${APIS[@]}"; do
    echo "  ✓ $API"
done
echo ""
echo "Next steps:"
echo "  1. Re-run the GitHub Actions workflow"
echo "  2. Or deploy manually: git tag v1.0.1 && git push origin v1.0.1"
echo ""
