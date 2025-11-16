#!/usr/bin/env python3
"""
Test script to verify secrets are accessible at runtime.

This script checks:
1. Runtime environment variables are set (GEMINI_API_KEY, PINECONE_API_KEY)
2. Secrets can be used to make actual API calls
3. Simulates Cloud Run environment (no .env file loading)

Usage:
  # Test with runtime env vars (simulates Cloud Run)
  GEMINI_API_KEY=xxx PINECONE_API_KEY=yyy python scripts/test_secrets_runtime.py

  # Or export them first
  export GEMINI_API_KEY=xxx
  export PINECONE_API_KEY=yyy
  python scripts/test_secrets_runtime.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Colors for output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text: str) -> None:
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}\n")

def print_success(text: str) -> None:
    print(f"{Colors.GREEN}✓{Colors.END} {text}")

def print_error(text: str) -> None:
    print(f"{Colors.RED}✗{Colors.END} {text}")

def print_warning(text: str) -> None:
    print(f"{Colors.YELLOW}⚠{Colors.END} {text}")

def print_info(text: str) -> None:
    print(f"{Colors.BLUE}ℹ{Colors.END} {text}")

def check_runtime_env() -> None:
    """Check if runtime environment variables are available."""
    print_header("Checking Runtime Environment")

    # Map GOOGLE_API_KEY to GEMINI_API_KEY if needed (for backwards compatibility)
    if "GEMINI_API_KEY" not in os.environ and "GOOGLE_API_KEY" in os.environ:
        os.environ["GEMINI_API_KEY"] = os.environ["GOOGLE_API_KEY"]
        print_info("Mapped GOOGLE_API_KEY → GEMINI_API_KEY")

    # Check if running in Cloud Run
    if "K_SERVICE" in os.environ:
        print_success("Running in Cloud Run environment")
        print_info(f"Service: {os.environ['K_SERVICE']}")
    else:
        print_warning("Not running in Cloud Run (local environment)")

def test_env_vars() -> bool:
    """Test that required environment variables are available."""
    print_header("Testing Environment Variables")

    required_vars = {
        "GEMINI_API_KEY": "Google Gemini API key",
        "PINECONE_API_KEY": "Pinecone API key",
    }

    all_ok = True
    for var, description in required_vars.items():
        value = os.environ.get(var)
        if value:
            # Mask the key for security
            masked = value[:8] + "..." + value[-4:] if len(value) > 12 else "***"
            print_success(f"{var}: {masked}")
        else:
            print_error(f"{var} is not set")
            print(f"  {description}")
            all_ok = False

    return all_ok

def test_gemini_api() -> bool:
    """Test that Gemini API key works."""
    print_header("Testing Gemini API Connection")

    try:
        import google.generativeai as genai

        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            print_error("GEMINI_API_KEY not found")
            return False

        genai.configure(api_key=api_key)

        # Try to list models
        models = list(genai.list_models())
        if models:
            print_success(f"Successfully connected to Gemini API")
            print_info(f"Found {len(models)} available models")
            return True
        else:
            print_error("Connected but no models found")
            return False

    except Exception as e:
        print_error(f"Failed to connect to Gemini API: {e}")
        return False

def test_pinecone_api() -> bool:
    """Test that Pinecone API key works."""
    print_header("Testing Pinecone API Connection")

    try:
        from pinecone import Pinecone

        api_key = os.environ.get("PINECONE_API_KEY")
        if not api_key:
            print_error("PINECONE_API_KEY not found")
            return False

        pc = Pinecone(api_key=api_key)

        # Try to list indexes
        indexes = pc.list_indexes()
        print_success(f"Successfully connected to Pinecone API")
        print_info(f"Found {len(indexes)} indexes")
        return True

    except Exception as e:
        print_error(f"Failed to connect to Pinecone API: {e}")
        return False

def main() -> int:
    """Main test function."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}Secrets Runtime Test{Colors.END}")
    print(f"{Colors.BOLD}Project: Creo Agent API{Colors.END}\n")
    print(f"{Colors.YELLOW}NOTE: This test expects runtime environment variables.{Colors.END}")
    print(f"{Colors.YELLOW}It does NOT load from .env file (simulates Cloud Run).{Colors.END}\n")

    # Check runtime environment
    check_runtime_env()

    # Test environment variables
    env_ok = test_env_vars()
    if not env_ok:
        print_error("\n❌ Environment variables are not properly configured")
        print("\nTo test runtime env vars, run:")
        print(f"  {Colors.BOLD}export GEMINI_API_KEY=your-key{Colors.END}")
        print(f"  {Colors.BOLD}export PINECONE_API_KEY=your-key{Colors.END}")
        print(f"  {Colors.BOLD}python scripts/test_secrets_runtime.py{Colors.END}")
        return 1

    # Test API connections
    gemini_ok = test_gemini_api()
    pinecone_ok = test_pinecone_api()

    # Summary
    print_header("Summary")

    if gemini_ok and pinecone_ok:
        print_success("All secrets are properly configured and accessible! 🎉")
        print("\nRuntime environment variables work correctly.")
        print("This simulates how secrets will work in Cloud Run.")
        print("\nNext steps:")
        print("  • Setup Cloud Run secrets: bash scripts/setup_secrets.sh")
        print("  • Deploy: git tag v1.0.0 && git push origin v1.0.0")
        return 0
    else:
        print_error("Some secrets are not working correctly")
        print("\nNext steps:")
        print("  1. Verify API keys are valid")
        print("  2. Check internet connection")
        print("  3. Verify API key permissions and quotas")
        return 1

if __name__ == "__main__":
    sys.exit(main())
