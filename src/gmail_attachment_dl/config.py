"""
Configuration manager for Gmail Attachment Downloader
"""

import os
import json
import platform
from pathlib import Path
from typing import Dict, Any


class ConfigManager:
    """Manages application configuration and paths"""

    def __init__(self, config_path: Path):
        """Initialize configuration manager"""
        self.config_path = config_path
        self.config_data = {}
        self._load_config()
        self._init_directories()

    def _load_config(self):
        """Load configuration from file"""
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    self.config_data = json.load(f)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in configuration file: {e}") from e
            except Exception as e:
                raise ValueError(f"Failed to load configuration file: {e}") from e

    def _normalize_path(self, path_str: str) -> Path:
        """Normalize a path string to absolute path with user expansion"""
        path = Path(path_str).expanduser()  # ~を展開
        if not path.is_absolute():
            path = path.absolute()  # 相対パスを絶対パスに変換
        return path

    def _init_directories(self):
        """Initialize application directories based on platform and config"""

        # Check for custom app directory path in config
        custom_app_dir = self.config_data.get("app_dir")

        if custom_app_dir:
            # Use custom app directory from config with normalization
            self.app_dir = self._normalize_path(custom_app_dir)
        else:
            # Use default platform-specific paths
            system = platform.system()

            if system == "Windows":
                # Windows: Use %APPDATA%
                base_dir = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
                self.app_dir = base_dir / "gmail-attachment-dl"

            else:
                # Linux and other Unix-like systems
                self.app_dir = Path(Path.home() / ".gmail-attachment-dl")

        # Create app directory
        self.app_dir.mkdir(parents=True, exist_ok=True)

        # Set credentials directory path
        credentials_path = self.config_data.get("credentials_path")
        if credentials_path:
            # Use normalized path for credentials directory
            self.credentials_dir = self._normalize_path(credentials_path)
        else:
            # Default to app_dir/credentials
            self.credentials_dir = self.app_dir / "credentials"

        # Create credentials directory
        self.credentials_dir.mkdir(parents=True, exist_ok=True)

        # Set restrictive permissions on Unix-like systems
        if os.name != "nt":
            os.chmod(self.credentials_dir, 0o700)

        # Set download base path
        download_path = self.config_data.get("download_base_path")
        if download_path:
            # Use normalized path for download base path
            self.download_base_path = self._normalize_path(download_path)
        else:
            # Default to app_dir/downloads
            self.download_base_path = self.app_dir / "downloads"

        # Create download directory
        self.download_base_path.mkdir(parents=True, exist_ok=True)

    def get_app_dir(self) -> Path:
        """Get the application directory path"""
        return self.app_dir

    def get_credentials_dir(self) -> Path:
        """Get the credentials directory path"""
        return self.credentials_dir

    def get_download_base_path(self) -> Path:
        """Get the download base path"""
        return self.download_base_path

    def get_default_days(self) -> int:
        """Get the default number of days to search"""
        return self.config_data.get("default_days", 7)

    def get_accounts(self) -> Dict[str, Any]:
        """Get account configurations"""
        return self.config_data.get("accounts", {})
