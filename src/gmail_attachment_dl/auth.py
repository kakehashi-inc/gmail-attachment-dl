"""
OAuth2 authentication manager for Gmail API
"""

import os
import json
import base64
from pathlib import Path
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2


class AuthManager:
    """Manages OAuth2 authentication and credential storage"""
    
    # OAuth2 scopes required for Gmail API
    SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
    
    # Client configuration for OAuth2
    CLIENT_CONFIG = {
        "installed": {
            "client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com",
            "client_secret": "YOUR_CLIENT_SECRET",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "redirect_uris": ["http://localhost"]
        }
    }
    
    def __init__(self, credentials_dir: Path):
        """Initialize auth manager with credentials directory"""
        self.credentials_dir = credentials_dir
        self.credentials_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize encryption key
        self._init_encryption_key()
    
    def _init_encryption_key(self):
        """Initialize or load encryption key for credential storage"""
        key_file = self.credentials_dir / ".key"
        
        if key_file.exists():
            with open(key_file, "rb") as f:
                self.cipher = Fernet(f.read())
        else:
            # Generate new key
            # In production, use a more secure key derivation
            salt = os.urandom(16)
            kdf = PBKDF2(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(b"gmail-attachment-dl"))
            self.cipher = Fernet(key)
            
            # Save key
            with open(key_file, "wb") as f:
                f.write(key)
            
            # Set restrictive permissions
            if os.name != "nt":  # Unix-like systems
                os.chmod(key_file, 0o600)
    
    def authenticate(self, email: str) -> Credentials:
        """Perform OAuth2 authentication flow"""
        
        # Check if we need to load client config from file
        client_config_file = self.credentials_dir / "client_secret.json"
        
        if client_config_file.exists():
            # Use custom client configuration
            flow = Flow.from_client_secrets_file(
                str(client_config_file),
                scopes=self.SCOPES,
                redirect_uri="http://localhost:8080"
            )
        else:
            # Use default configuration
            print("Warning: Using default client configuration.")
            print(f"For production use, place your client_secret.json in: {self.credentials_dir}")
            flow = Flow.from_client_config(
                self.CLIENT_CONFIG,
                scopes=self.SCOPES,
                redirect_uri="http://localhost:8080"
            )
        
        # Get authorization URL
        auth_url, _ = flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
            login_hint=email
        )
        
        print("\nPlease visit this URL to authorize the application:")
        print(auth_url)
        
        # Get authorization code from user
        auth_code = input("\nEnter the authorization code: ").strip()
        
        # Exchange authorization code for tokens
        flow.fetch_token(code=auth_code)
        
        return flow.credentials
    
    def save_credentials(self, email: str, credentials: Credentials):
        """Save encrypted credentials to file"""
        
        # Prepare credential data
        cred_data = {
            "token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_uri": credentials.token_uri,
            "client_id": credentials.client_id,
            "client_secret": credentials.client_secret,
            "scopes": credentials.scopes
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
            raise ValueError(f"Failed to decrypt credentials: {e}")
        
        # Create Credentials object
        credentials = Credentials(
            token=cred_data.get("token"),
            refresh_token=cred_data.get("refresh_token"),
            token_uri=cred_data.get("token_uri"),
            client_id=cred_data.get("client_id"),
            client_secret=cred_data.get("client_secret"),
            scopes=cred_data.get("scopes")
        )
        
        # Refresh if expired
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
            # Save updated credentials
            self.save_credentials(email, credentials)
        
        return credentials
    
    def verify_credentials(self, credentials: Credentials) -> bool:
        """Verify that credentials are valid"""
        try:
            service = build("gmail", "v1", credentials=credentials)
            service.users().getProfile(userId="me").execute()
            return True
        except Exception:
            return False