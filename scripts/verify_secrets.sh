#!/bin/bash
# Verify secrets are properly configured in Google Secret Manager
# and accessible by Cloud Run

set -e

PROJECT_ID="gen-lang-client-0751221742"
REGION="us-central1"
SERVICE_NAME="creo"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

echo -e "${BOLD}${BLUE}==========================================${NC}"
echo -e "${BOLD}${BLUE}Verifying Google Secret Manager Setup${NC}"
echo -e "${BOLD}${BLUE}==========================================${NC}"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI not found. Install from: https://cloud.google.com/sdk/docs/install${NC}"
    exit 1
fi

# Required secrets
REQUIRED_SECRETS=("GOOGLE_API_KEY" "PINECONE_API_KEY")

echo -e "${BOLD}Checking Secret Manager API...${NC}"
if gcloud services list --enabled --project=$PROJECT_ID | grep -q secretmanager.googleapis.com; then
    echo -e "${GREEN}✓ Secret Manager API is enabled${NC}"
else
    echo -e "${RED}✗ Secret Manager API is not enabled${NC}"
    echo "  Run: make sync-secrets"
    exit 1
fi
echo ""

echo -e "${BOLD}Checking Secrets...${NC}"
ALL_SECRETS_OK=true
for SECRET in "${REQUIRED_SECRETS[@]}"; do
    if gcloud secrets describe $SECRET --project=$PROJECT_ID &>/dev/null; then
        echo -e "${GREEN}✓ $SECRET exists${NC}"

        # Check if secret has a value
        VERSIONS=$(gcloud secrets versions list $SECRET --project=$PROJECT_ID --format="value(name)" | wc -l)
        if [ "$VERSIONS" -gt 0 ]; then
            echo -e "  ${BLUE}ℹ${NC} Versions: $VERSIONS"
        else
            echo -e "  ${YELLOW}⚠${NC} No versions found (secret is empty)"
            ALL_SECRETS_OK=false
        fi
    else
        echo -e "${RED}✗ $SECRET does not exist${NC}"
        ALL_SECRETS_OK=false
    fi
done
echo ""

echo -e "${BOLD}Checking Cloud Run Service Account Access...${NC}"

# Try to get the Cloud Run service account
SERVICE_ACCOUNT=$(gcloud run services describe $SERVICE_NAME \
    --region=$REGION \
    --project=$PROJECT_ID \
    --format='value(spec.template.spec.serviceAccountName)' 2>/dev/null || echo "")

if [ -z "$SERVICE_ACCOUNT" ]; then
    echo -e "${YELLOW}⚠ Cloud Run service '$SERVICE_NAME' not found or not deployed yet${NC}"
    echo "  This is OK if you haven't deployed yet"
    echo "  Service account access will be granted on first deployment"
else
    echo -e "${GREEN}✓ Cloud Run service found${NC}"
    echo -e "  Service account: ${BLUE}$SERVICE_ACCOUNT${NC}"
    echo ""

    # Check if service account has access to each secret
    for SECRET in "${REQUIRED_SECRETS[@]}"; do
        if gcloud secrets get-iam-policy $SECRET --project=$PROJECT_ID 2>/dev/null | grep -q "$SERVICE_ACCOUNT"; then
            echo -e "${GREEN}✓ $SERVICE_ACCOUNT has access to $SECRET${NC}"
        else
            echo -e "${RED}✗ $SERVICE_ACCOUNT does NOT have access to $SECRET${NC}"
            echo "  Run: make sync-secrets"
            ALL_SECRETS_OK=false
        fi
    done
fi
echo ""

echo -e "${BOLD}${BLUE}==========================================${NC}"
if [ "$ALL_SECRETS_OK" = true ]; then
    echo -e "${GREEN}✓ All secrets are properly configured!${NC}"
    echo ""
    echo "View in Console:"
    echo "https://console.cloud.google.com/security/secret-manager?project=$PROJECT_ID"
    echo ""
    echo "Next steps:"
    echo "  • Deploy: git tag v1.0.0 && git push origin v1.0.0"
    echo "  • Or run locally: make server"
    exit 0
else
    echo -e "${RED}✗ Some secrets need attention${NC}"
    echo ""
    echo "To fix:"
    echo "  1. Run: make sync-secrets"
    echo "  2. Ensure you have values in your .env file"
    echo "  3. Run: make verify-secrets (to verify again)"
    exit 1
fi
