"""
Configuration manager for Gmail Attachment Downloader
"""

import os
import platform
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigManager:
    """Manages application configuration and paths"""

    def __init__(self, config_path: Path, config_data: Optional[Dict[str, Any]] = None):
        """Initialize configuration manager"""
        self.config_path = config_path
        self.config_data = config_data or {}
        self._init_directories()

    def _init_directories(self):
        """Initialize application directories based on platform and config"""

        # Check for custom credentials path in config
        custom_creds_path = self.config_data.get("credentials_path")

        if custom_creds_path:
            # Use custom path from config
            custom_creds_path = Path(custom_creds_path).expanduser()
            # If relative path, make it relative to config file location
            if not custom_creds_path.is_absolute():
                custom_creds_path = (self.config_path.parent / custom_creds_path).resolve()
            self.credentials_dir = custom_creds_path
            self.app_dir = self.credentials_dir.parent
        else:
            # Use default platform-specific paths
            system = platform.system()

            if system == "Windows":
                # Windows: Use %APPDATA%
                base_dir = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
                self.app_dir = base_dir / "gmail-attachment-dl"

            elif system == "Darwin":  # macOS
                # macOS: Use ~/Library/Application Support
                self.app_dir = Path.home() / "Library" / "Application Support" / "gmail-attachment-dl"

            else:  # Linux and other Unix-like systems
                # Linux: Use XDG config directory
                xdg_config = os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")
                self.app_dir = Path(xdg_config) / "gmail-attachment-dl"

            # Set up subdirectories
            self.credentials_dir = self.app_dir / "credentials"

        # Create directories if they don't exist
        self.app_dir.mkdir(parents=True, exist_ok=True)
        self.credentials_dir.mkdir(parents=True, exist_ok=True)

        # Set restrictive permissions on Unix-like systems
        if os.name != "nt":
            os.chmod(self.app_dir, 0o700)
            os.chmod(self.credentials_dir, 0o700)

        # Set download base path
        download_path = self.config_data.get("download_base_path")
        if download_path:
            download_path = Path(download_path).expanduser()
            # If relative path, make it relative to config file location
            if not download_path.is_absolute():
                download_path = (self.config_path.parent / download_path).resolve()
            self.download_base_path = download_path
        else:
            # Default to config directory
            self.download_base_path = self.config_path.parent / "downloads"

        # Create download directory
        self.download_base_path.mkdir(parents=True, exist_ok=True)

    def get_credentials_dir(self) -> Path:
        """Get the credentials directory path"""
        return self.credentials_dir

    def get_app_dir(self) -> Path:
        """Get the application directory path"""
        return self.app_dir

    def get_download_base_path(self) -> Path:
        """Get the download base path"""
        return self.download_base_path

    @staticmethod
    def get_default_config() -> Dict[str, Any]:
        """Get default configuration template"""
        return {
            "default_days": 7,
            "download_base_path": "./downloads",
            "credentials_path": None,
            "accounts": {
                "example@gmail.com": [
                    {"from": "invoice@.*\\.example\\.com", "subject": ["Receipt", "Invoice"], "body": "Payment.*confirmed", "attachments": ["*.pdf"]}
                ],
                "user@domain.com": [{"from": ["billing@service1\\.com", "noreply@service2\\.com"], "subject": "Monthly Statement", "attachments": null}],
            },
        }

    @staticmethod
    def validate_config(config: Dict[str, Any]) -> bool:
        """Validate configuration structure"""

        if not isinstance(config, dict):
            return False

        # Check optional path fields
        if "download_base_path" in config:
            if not isinstance(config["download_base_path"], (str, type(None))):
                return False

        if "credentials_path" in config:
            if not isinstance(config["credentials_path"], (str, type(None))):
                return False

        # Check for required fields
        if "accounts" not in config:
            return False

        accounts = config.get("accounts", {})
        if not isinstance(accounts, dict):
            return False

        # Validate each account configuration
        for email, filter_list in accounts.items():
            # Must be a list of filter dictionaries
            if not isinstance(filter_list, list):
                return False

            for filters in filter_list:
                if not isinstance(filters, dict):
                    return False

                # Check filter fields (all optional but must be correct type)
                for field in ["from", "to", "subject", "body"]:
                    if field in filters:
                        value = filters[field]
                        # Must be string, list of strings, or None
                        if value is not None:
                            if isinstance(value, str):
                                continue
                            elif isinstance(value, list):
                                if not all(isinstance(v, str) for v in value):
                                    return False
                            else:
                                return False

                # Check attachments field
                if "attachments" in filters:
                    attachments = filters["attachments"]
                    if attachments is not None:
                        if isinstance(attachments, str):
                            continue
                        elif isinstance(attachments, list):
                            if not all(isinstance(v, str) for v in attachments):
                                return False
                        else:
                            return False

        return True
