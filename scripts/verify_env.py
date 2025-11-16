#!/usr/bin/env python3
"""
Verify environment variables are properly configured for deployment.

This script checks:
1. Local .env file has all required variables
2. Cloud Run service has all required environment variables
3. GitHub Secrets are configured for CI/CD
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set

# Required environment variables for the application
REQUIRED_ENV_VARS = {
    "GEMINI_API_KEY": "Google Gemini API key for AI functionality",
    "PINECONE_API_KEY": "Pinecone API key for vector database",
}

# Optional environment variables
OPTIONAL_ENV_VARS = {
    "GCP_PROJECT_ID": "Google Cloud project ID (auto-detected if not set)",
    "PORT": "Server port (Cloud Run sets automatically)",
    "FIRESTORE_EMULATOR_HOST": "Firestore emulator host for local testing",
}

# GitHub Secrets required for CI/CD
REQUIRED_GITHUB_SECRETS = {
    "GCP_SA_KEY": "Google Cloud service account key for deployment",
    "GEMINI_API_KEY": "Google Gemini API key",
    "PINECONE_API_KEY": "Pinecone API key",
}

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Colors:
    """Terminal colors."""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(text: str) -> None:
    """Print a colored header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}\n")


def print_success(text: str) -> None:
    """Print success message."""
    print(f"{Colors.GREEN}✓{Colors.END} {text}")


def print_warning(text: str) -> None:
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠{Colors.END} {text}")


def print_error(text: str) -> None:
    """Print error message."""
    print(f"{Colors.RED}✗{Colors.END} {text}")


def load_env_file() -> Dict[str, str]:
    """Load variables from .env file."""
    env_file = PROJECT_ROOT / ".env"
    env_vars = {}

    if not env_file.exists():
        return env_vars

    with open(env_file, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, value = line.split("=", 1)
                env_vars[key.strip()] = value.strip()

    return env_vars


def check_local_env() -> tuple[bool, Set[str]]:
    """Check local .env file configuration."""
    print_header("Checking Local .env File")

    env_file = PROJECT_ROOT / ".env"

    if not env_file.exists():
        print_error(f".env file not found at {env_file}")
        print(f"  Create one by copying .env.example:")
        print(f"  {Colors.BOLD}cp .env.example .env{Colors.END}")
        return False, set()

    print_success(f".env file found at {env_file}")

    env_vars = load_env_file()
    missing_vars = set()
    all_ok = True

    # Check required variables
    for var, description in REQUIRED_ENV_VARS.items():
        if var in env_vars and env_vars[var]:
            print_success(f"{var} is set")
        else:
            print_error(f"{var} is missing or empty")
            print(f"  {description}")
            missing_vars.add(var)
            all_ok = False

    # Check optional variables
    print(f"\n{Colors.BOLD}Optional variables:{Colors.END}")
    for var, description in OPTIONAL_ENV_VARS.items():
        if var in env_vars and env_vars[var]:
            print_success(f"{var} is set")
        else:
            print_warning(f"{var} is not set (optional)")
            print(f"  {description}")

    return all_ok, missing_vars


def check_cloud_run_env(service_name: str = "creo", region: str = "us-central1") -> bool:
    """Check Cloud Run service environment variables."""
    print_header("Checking Cloud Run Environment Variables")

    try:
        # Check if gcloud is installed
        subprocess.run(["gcloud", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_warning("gcloud CLI not found. Skipping Cloud Run check.")
        print("  Install: https://cloud.google.com/sdk/docs/install")
        return True  # Not a failure, just can't check

    try:
        # Get Cloud Run service details
        result = subprocess.run(
            [
                "gcloud", "run", "services", "describe", service_name,
                "--region", region,
                "--format", "value(spec.template.spec.containers[0].env)"
            ],
            capture_output=True,
            text=True,
            check=True
        )

        env_output = result.stdout.strip()

        if not env_output or env_output == "None":
            print_error(f"No environment variables set on Cloud Run service '{service_name}'")
            print(f"\n  Set them with:")
            print(f"  {Colors.BOLD}gcloud run services update {service_name} \\")
            print(f"    --region {region} \\")
            print(f"    --set-env-vars GEMINI_API_KEY=xxx,PINECONE_API_KEY=xxx{Colors.END}")
            return False

        # Parse environment variables
        cloud_vars = {}
        for line in env_output.split(";"):
            if "=" in line:
                key = line.split("=")[0].strip()
                cloud_vars[key] = True

        # Check required variables
        all_ok = True
        for var in REQUIRED_ENV_VARS:
            if var in cloud_vars:
                print_success(f"{var} is set on Cloud Run")
            else:
                print_error(f"{var} is NOT set on Cloud Run")
                all_ok = False

        return all_ok

    except subprocess.CalledProcessError:
        print_warning(f"Cloud Run service '{service_name}' not found or not accessible")
        print(f"  This is OK if you haven't deployed yet")
        return True  # Not a failure if service doesn't exist yet


def check_github_secrets(repo: str = "oron-mozes/creo") -> bool:
    """Check if GitHub Secrets are configured."""
    print_header("Checking GitHub Secrets")

    try:
        # Check if gh CLI is installed
        subprocess.run(["gh", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_warning("GitHub CLI not found. Skipping GitHub Secrets check.")
        print("  Install: https://cli.github.com/")
        print("  Or manually check: https://github.com/oron-mozes/creo/settings/secrets/actions")
        return True  # Not a failure, just can't check

    try:
        # List secrets
        result = subprocess.run(
            ["gh", "secret", "list", "--repo", repo],
            capture_output=True,
            text=True,
            check=True
        )

        secret_names = set()
        for line in result.stdout.strip().split("\n"):
            if line:
                # Format: NAME    Updated TIMESTAMP
                parts = line.split()
                if parts:
                    secret_names.add(parts[0])

        # Check required secrets
        all_ok = True
        for secret, description in REQUIRED_GITHUB_SECRETS.items():
            if secret in secret_names:
                print_success(f"{secret} is configured")
            else:
                print_error(f"{secret} is NOT configured")
                print(f"  {description}")
                print(f"  Add at: https://github.com/{repo}/settings/secrets/actions")
                all_ok = False

        return all_ok

    except subprocess.CalledProcessError as e:
        print_warning("Could not check GitHub Secrets (authentication required)")
        print(f"  Run: gh auth login")
        print(f"  Or manually check: https://github.com/{repo}/settings/secrets/actions")
        return True  # Not a failure, just can't check


def main() -> int:
    """Main function."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}Environment Configuration Verification{Colors.END}")
    print(f"{Colors.BOLD}Project: Creo Agent API{Colors.END}\n")

    all_checks_passed = True

    # Check local .env
    local_ok, missing_vars = check_local_env()
    if not local_ok:
        all_checks_passed = False

    # Check Cloud Run
    cloudrun_ok = check_cloud_run_env()
    if not cloudrun_ok:
        all_checks_passed = False

    # Check GitHub Secrets
    github_ok = check_github_secrets()
    if not github_ok:
        all_checks_passed = False

    # Summary
    print_header("Summary")

    if all_checks_passed:
        print_success("All environment variables are properly configured! 🎉")
        print("\nYou're ready to:")
        print("  • Run locally: make server")
        print("  • Deploy: git tag v1.0.0 && git push origin v1.0.0")
        return 0
    else:
        print_error("Some environment variables need attention")

        if missing_vars:
            print(f"\n{Colors.BOLD}Missing variables in .env:{Colors.END}")
            for var in missing_vars:
                print(f"  • {var}")
                print(f"    {REQUIRED_ENV_VARS[var]}")

        print(f"\n{Colors.BOLD}Next steps:{Colors.END}")
        print("  1. Add missing variables to .env file")
        print("  2. Set Cloud Run environment variables (if deploying)")
        print("  3. Configure GitHub Secrets (for CI/CD)")
        print(f"\n  See docs/DATABASE.md and docs/DEPLOYMENT.md for details")

        return 1


if __name__ == "__main__":
    sys.exit(main())
