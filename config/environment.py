"""Environment configuration for Creo application."""
import os
from pathlib import Path


def setup_env() -> None:
    """Setup environment variables for the application.

    Priority:
    1. GOOGLE_API_KEY from runtime env (Cloud Run)
    2. GOOGLE_API_KEY from runtime env (fallback)
    3. .env file (local development only)
    """
    # If GOOGLE_API_KEY already set (e.g., from Cloud Run Secret Manager), use it
    if "GOOGLE_API_KEY" in os.environ:
        return

    # Try GOOGLE_API_KEY as fallback
    if "GOOGLE_API_KEY" in os.environ:
        os.environ["GOOGLE_API_KEY"] = os.environ["GOOGLE_API_KEY"]
        return

    # For local development only: load from .env
    project_root = Path(__file__).resolve().parent.parent
    env_path = project_root / ".env"

    if env_path.exists():
        with open(env_path, "r") as env_file:
            for line in env_file:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()

                # Set GOOGLE_API_KEY as GOOGLE_API_KEY
                if key == "GOOGLE_API_KEY" and "GOOGLE_API_KEY" not in os.environ:
                    os.environ["GOOGLE_API_KEY"] = value

                os.environ.setdefault(key, value)


def verify_required_env_vars() -> None:
    """Verify that all required environment variables are set.

    Raises:
        EnvironmentError: If any required variables are missing
    """
    required_vars = ["GOOGLE_API_KEY", "PINECONE_API_KEY"]
    missing_vars = [var for var in required_vars if not os.environ.get(var)]

    if missing_vars:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing_vars)}\n"
            f"For Cloud Run: Ensure secrets are configured in Secret Manager\n"
            f"For local dev: Add to .env file"
        )
