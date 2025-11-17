#!/usr/bin/env python3
"""Interactive CLI script to set up Google OAuth authentication for Creo.

This script will:
1. Guide you through creating Google OAuth credentials
2. Help you configure your .env file
3. Test the authentication setup
"""

import os
import sys
import secrets
import webbrowser
from pathlib import Path

# ANSI color codes for pretty output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")

def print_success(text):
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.OKBLUE}ℹ {text}{Colors.ENDC}")

def print_warning(text):
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")

def print_step(step_num, text):
    print(f"\n{Colors.OKCYAN}{Colors.BOLD}Step {step_num}: {text}{Colors.ENDC}")

def get_input(prompt, default=None):
    if default:
        user_input = input(f"{prompt} [{default}]: ").strip()
        return user_input if user_input else default
    return input(f"{prompt}: ").strip()

def yes_no(prompt, default=True):
    default_str = "Y/n" if default else "y/N"
    response = input(f"{prompt} [{default_str}]: ").strip().lower()
    if not response:
        return default
    return response in ['y', 'yes']

def check_env_file():
    """Check if .env file exists and backup if needed."""
    env_path = Path('.env')
    env_example_path = Path('.env.example')

    if env_path.exists():
        print_info(".env file found")
        if yes_no("Do you want to backup your current .env file?", default=True):
            backup_path = Path('.env.backup')
            with open(env_path, 'r') as f:
                content = f.read()
            with open(backup_path, 'w') as f:
                f.write(content)
            print_success(f"Backed up to {backup_path}")
        return True
    else:
        print_warning(".env file not found")
        if env_example_path.exists():
            print_info("Found .env.example, will use it as template")
            return False
        else:
            print_error(".env.example not found!")
            return False

def open_google_console():
    """Open Google Cloud Console in browser."""
    print_step(1, "Open Google Cloud Console")
    print("\nWe'll now open Google Cloud Console in your browser.")
    print("If you don't have a Google Cloud project yet, you'll need to create one.")

    if yes_no("\nReady to open Google Cloud Console?", default=True):
        webbrowser.open('https://console.cloud.google.com/apis/credentials')
        print_success("Opened Google Cloud Console")
        return True
    return False

def guide_oauth_creation():
    """Guide user through OAuth credential creation."""
    print_step(2, "Create OAuth 2.0 Credentials")

    print(f"""
{Colors.BOLD}Follow these steps in the Google Cloud Console:{Colors.ENDC}

1. Select your project (or create a new one)
2. Click "Create Credentials" → "OAuth 2.0 Client ID"
3. If prompted, configure the OAuth consent screen:
   - User Type: External (for testing)
   - App name: Creo
   - User support email: Your email
   - Developer contact: Your email
   - Save and continue through the remaining steps

4. Back on the Credentials page:
   - Application type: Web application
   - Name: Creo Web Client

5. Add Authorized redirect URIs:
   - For local development: http://localhost:8000/api/auth/google/callback
   - Click "Add URI" if you need multiple environments

6. Click "Create"
7. Copy the Client ID and Client Secret
""")

    input(f"\n{Colors.BOLD}Press Enter when you've created the credentials...{Colors.ENDC}")

def collect_credentials():
    """Collect OAuth credentials from user."""
    print_step(3, "Enter Your Credentials")

    print("\nPaste your credentials from Google Cloud Console:")

    client_id = get_input("\nGoogle Client ID")
    while not client_id or not client_id.endswith('.apps.googleusercontent.com'):
        print_warning("Client ID should end with .apps.googleusercontent.com")
        client_id = get_input("Google Client ID")

    client_secret = get_input("Google Client Secret")
    while not client_secret:
        print_warning("Client Secret cannot be empty")
        client_secret = get_input("Google Client Secret")

    return client_id, client_secret

def get_redirect_uri():
    """Get redirect URI configuration."""
    print_step(4, "Configure Redirect URI")

    print("\nWhat's your environment?")
    print("1. Local development (localhost:8000)")
    print("2. Cloud Run / Production")
    print("3. Custom URL")

    choice = get_input("\nSelect option [1-3]", default="1")

    if choice == "1":
        return "http://localhost:8000/api/auth/google/callback"
    elif choice == "2":
        app_name = get_input("Enter your Cloud Run service name")
        return f"https://{app_name}.run.app/api/auth/google/callback"
    else:
        return get_input("Enter your custom redirect URI")

def generate_secret_key():
    """Generate a secure secret key for JWT."""
    print_step(5, "Generate Session Secret Key")

    secret_key = secrets.token_urlsafe(32)
    print_success(f"Generated secure secret key: {secret_key[:20]}...")

    return secret_key

def update_env_file(client_id, client_secret, redirect_uri, secret_key):
    """Update or create .env file with OAuth credentials."""
    print_step(6, "Update .env File")

    env_path = Path('.env')
    env_example_path = Path('.env.example')

    # Read existing .env or .env.example
    if env_path.exists():
        with open(env_path, 'r') as f:
            lines = f.readlines()
    elif env_example_path.exists():
        with open(env_example_path, 'r') as f:
            lines = f.readlines()
    else:
        lines = []

    # Update or add OAuth variables
    oauth_vars = {
        'GOOGLE_CLIENT_ID': client_id,
        'GOOGLE_CLIENT_SECRET': client_secret,
        'GOOGLE_REDIRECT_URI': redirect_uri,
        'SESSION_SECRET_KEY': secret_key,
    }

    updated_lines = []
    updated_vars = set()

    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith('#'):
            key = stripped.split('=')[0].strip()
            if key in oauth_vars:
                updated_lines.append(f"{key}={oauth_vars[key]}\n")
                updated_vars.add(key)
            else:
                updated_lines.append(line)
        else:
            updated_lines.append(line)

    # Add any missing variables
    for key, value in oauth_vars.items():
        if key not in updated_vars:
            updated_lines.append(f"{key}={value}\n")

    # Write to .env
    with open(env_path, 'w') as f:
        f.writelines(updated_lines)

    print_success(f"Updated {env_path}")

    # Show what was configured
    print("\n" + Colors.BOLD + "Configuration:" + Colors.ENDC)
    print(f"  GOOGLE_CLIENT_ID={client_id[:30]}...")
    print(f"  GOOGLE_CLIENT_SECRET={client_secret[:20]}...")
    print(f"  GOOGLE_REDIRECT_URI={redirect_uri}")
    print(f"  SESSION_SECRET_KEY={secret_key[:20]}...")

def verify_setup():
    """Verify the setup by checking environment variables."""
    print_step(7, "Verify Setup")

    # Try to load .env
    env_path = Path('.env')
    if not env_path.exists():
        print_error(".env file not found!")
        return False

    # Check if all required variables are set
    required_vars = [
        'GOOGLE_CLIENT_ID',
        'GOOGLE_CLIENT_SECRET',
        'GOOGLE_REDIRECT_URI',
        'SESSION_SECRET_KEY',
    ]

    env_vars = {}
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key.strip()] = value.strip()

    missing_vars = [var for var in required_vars if var not in env_vars or not env_vars[var]]

    if missing_vars:
        print_error(f"Missing required variables: {', '.join(missing_vars)}")
        return False

    print_success("All required variables are set!")
    return True

def test_server():
    """Guide user to test the server."""
    print_step(8, "Test Your Setup")

    print(f"""
{Colors.BOLD}To test your authentication setup:{Colors.ENDC}

1. Install dependencies (if not already done):
   {Colors.OKCYAN}pip install -r requirements.txt{Colors.ENDC}

2. Start the server:
   {Colors.OKCYAN}python server.py{Colors.ENDC}

3. Open your browser:
   {Colors.OKCYAN}http://localhost:8000{Colors.ENDC}

4. You should be redirected to the login page
5. Click "Continue with Google"
6. Complete the OAuth flow
7. You should be redirected back, authenticated!

{Colors.BOLD}Troubleshooting:{Colors.ENDC}
- If you get a redirect URI mismatch error:
  → Check that the redirect URI in Google Cloud Console matches exactly
  → Make sure there are no trailing slashes

- If the login doesn't work:
  → Check server logs for errors
  → Verify all environment variables are set correctly
  → Try clearing browser cookies and localStorage
""")

    if yes_no("\nWould you like to start the server now?", default=False):
        print_info("Starting server...")
        os.system("python server.py")

def main():
    """Main setup flow."""
    print_header("Creo Google OAuth Setup")

    print(f"""
{Colors.BOLD}Welcome to the Creo Google OAuth setup wizard!{Colors.ENDC}

This interactive script will help you:
✓ Create Google OAuth 2.0 credentials
✓ Configure your .env file
✓ Test your authentication setup

{Colors.WARNING}Prerequisites:{Colors.ENDC}
- A Google Cloud account (free tier is fine)
- Access to Google Cloud Console
- About 5-10 minutes

Let's get started!
""")

    if not yes_no("Ready to begin?", default=True):
        print_info("Setup cancelled")
        return

    # Check and backup .env
    check_env_file()

    # Open Google Cloud Console
    if open_google_console():
        # Guide through OAuth creation
        guide_oauth_creation()

        # Collect credentials
        client_id, client_secret = collect_credentials()

        # Get redirect URI
        redirect_uri = get_redirect_uri()

        # Generate secret key
        secret_key = generate_secret_key()

        # Update .env file
        update_env_file(client_id, client_secret, redirect_uri, secret_key)

        # Verify setup
        if verify_setup():
            print_success("\n🎉 Setup complete!")

            # Test server
            test_server()
        else:
            print_error("\n⚠️  Setup verification failed. Please check your .env file.")
    else:
        print_info("\nSetup cancelled. You can run this script again anytime.")
        print_info("Run: python scripts/setup_google_auth.py")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_info("\n\nSetup cancelled by user")
        sys.exit(0)
    except Exception as e:
        print_error(f"\n\nAn error occurred: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
