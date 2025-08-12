"""
OAuth2 authentication manager for Gmail API
"""

import os
import json
import base64
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.auth.credentials import Credentials as BaseCredentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class AuthManager:
    """Manages OAuth2 authentication and credential storage"""

    # OAuth2 scopes required for Gmail API
    SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

    def __init__(self, credentials_dir: Path, encryption_salt: str):
        """Initialize auth manager with credentials directory and encryption salt"""
        self.credentials_dir = credentials_dir
        self.encryption_salt = encryption_salt
        self.credentials_dir.mkdir(parents=True, exist_ok=True)

        # Initialize encryption key
        self._init_encryption_key()

    def _init_encryption_key(self):
        """Initialize encryption key for credential storage"""
        # Convert salt string to bytes
        salt = self.encryption_salt.encode("utf-8")

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )

        # Derive key from application-specific string
        key = base64.urlsafe_b64encode(kdf.derive(b"gmail-attachment-dl-encryption-key-v1"))
        self.cipher = Fernet(key)

    def authenticate(self, email: str) -> BaseCredentials:
        """Perform OAuth2 authentication flow"""

        # Check if we need to load client config from file
        client_config_file = self.credentials_dir / "client_secret.json"

        if client_config_file.exists():
            # Use custom client configuration
            flow = InstalledAppFlow.from_client_secrets_file(str(client_config_file), scopes=self.SCOPES)
        else:
            # Error: client_secret.json is required
            print("Error: client_secret.json file is required for authentication.")
            print(f"Please place your client_secret.json in: {self.credentials_dir}")
            print("\nTo obtain client_secret.json:")
            print("1. Go to Google Cloud Console (https://console.cloud.google.com/)")
            print("2. Create or select a project")
            print("3. Enable Gmail API")
            print("4. Create OAuth 2.0 Client ID (Application type: Desktop application)")
            print("5. Download the JSON file as client_secret.json")
            raise FileNotFoundError("client_secret.json not found")

        # Use local server to automatically handle OAuth callback
        print(f"\nStarting authentication for: {email}")
        print("A browser window will open for authentication...")
        print("After completing authentication, the browser can be closed.")

        try:
            # Run local server to receive OAuth callback
            credentials = flow.run_local_server(host="localhost", port=8580, open_browser=True)
            return credentials
        except Exception as e:
            print(f"\nAutomatic authentication failed: {e}")
            print("Falling back to manual authentication...")

            # Fallback to manual method
            auth_url, _ = flow.authorization_url(prompt="consent", login_hint=email)
            print("\nPlease visit this URL to authorize the application:")
            print(auth_url)
            print("\nAfter authorization, you will be redirected to localhost.")
            print("Copy the 'code' parameter from the URL and paste it below.")

            # Get authorization code from user
            auth_code = input("\nEnter the authorization code: ").strip()

            # Exchange authorization code for tokens
            flow.fetch_token(code=auth_code)

        return flow.credentials

    def save_credentials(self, email: str, credentials: BaseCredentials):
        """Save encrypted credentials to file"""

        # Prepare credential data
        cred_data = {
            "token": getattr(credentials, "token", None),
            "refresh_token": getattr(credentials, "refresh_token", None),
            "token_uri": getattr(credentials, "token_uri", None),
            "client_id": getattr(credentials, "client_id", None),
            "client_secret": getattr(credentials, "client_secret", None),
            "scopes": getattr(credentials, "scopes", None),
        }

        # Convert to JSON and encrypt
        json_data = json.dumps(cred_data)
        encrypted_data = self.cipher.encrypt(json_data.encode())

        # Save to file with email as filename
        cred_file = self.credentials_dir / f"{email}.json"
        with open(cred_file, "wb") as f:
            f.write(encrypted_data)

        # Set restrictive permissions
        if os.name != "nt":  # Unix-like systems
            os.chmod(cred_file, 0o600)

        print(f"Credentials saved: {cred_file}")

    def load_credentials(self, email: str) -> Credentials:
        """Load and decrypt credentials from file"""

        cred_file = self.credentials_dir / f"{email}.json"

        if not cred_file.exists():
            raise FileNotFoundError(f"Credentials not found for: {email}")

        # Read and decrypt
        with open(cred_file, "rb") as f:
            encrypted_data = f.read()

        try:
            json_data = self.cipher.decrypt(encrypted_data).decode()
            cred_data = json.loads(json_data)
        except Exception as e:
            raise ValueError(f"Failed to decrypt credentials: {e}") from e

        # Create Credentials object
        credentials = Credentials(
            token=cred_data.get("token"),
            refresh_token=cred_data.get("refresh_token"),
            token_uri=cred_data.get("token_uri"),
            client_id=cred_data.get("client_id"),
            client_secret=cred_data.get("client_secret"),
            scopes=cred_data.get("scopes"),
        )

        # Refresh if expired
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
            # Save updated credentials
            self.save_credentials(email, credentials)

        return credentials

    def verify_credentials(self, credentials: BaseCredentials) -> bool:
        """Verify that credentials are valid"""
        try:
            service = build("gmail", "v1", credentials=credentials)
            service.users().getProfile(userId="me").execute()  # type: ignore # pylint: disable=no-member
            return True
        except Exception:
            return False
