#!/usr/bin/env python3
"""
Gmail Attachment Downloader
Main entry point for the application
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

from .auth import AuthManager
from .config import ConfigManager
from .downloader import EmailDownloader
from .matcher import EmailMatcher


def parse_args() -> argparse.Namespace:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Download Gmail attachments based on regex filters")

    # Authentication mode
    parser.add_argument("--auth", metavar="EMAIL", help="Authenticate the specified email account")

    # Days override
    parser.add_argument("--days", type=int, metavar="N", help="Override the number of days to search back")

    # Config file path
    parser.add_argument("--config", type=Path, default=Path("config.json"), help="Path to configuration file (default: config.json)")

    # Verbose output
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")

    return parser.parse_args()


def run_auth_mode(email: str, config_manager: Optional[ConfigManager]) -> int:
    """Run authentication mode for specified email"""
    print(f"Starting authentication for: {email}")

    # Determine credentials directory based on config manager availability
    if config_manager is not None:
        credentials_dir = config_manager.get_credentials_dir()
    else:
        credentials_dir = Path.cwd()

    auth_manager = AuthManager(credentials_dir)

    try:
        # Perform OAuth2 flow
        credentials = auth_manager.authenticate(email)

        # Save encrypted credentials
        auth_manager.save_credentials(email, credentials)

        print(f"Successfully authenticated: {email}")
        print(f"Credentials saved to: {credentials_dir}")
        return 0

    except Exception as e:
        print(f"Authentication failed: {e}", file=sys.stderr)
        return 1


def run_download_mode(args: argparse.Namespace, config_manager: ConfigManager) -> int:
    """Run download mode for all configured accounts"""

    # Determine search days
    search_days = args.days if args.days else config_manager.get_default_days()

    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=search_days)

    print(f"Searching emails from {start_date.date()} to {end_date.date()}")

    # Use download base path from config
    download_base = config_manager.get_download_base_path()

    print(f"Download base directory: {download_base}")
    print("-" * 50)

    # Create base output directory
    download_base.mkdir(parents=True, exist_ok=True)

    # Track results
    successful_accounts = []
    failed_accounts = []
    total_downloaded = 0

    auth_manager = AuthManager(config_manager.get_credentials_dir())

    accounts = config_manager.get_accounts()

    for email, filter_list in accounts.items():
        print(f"\nProcessing: {email}")

        # Ensure filter_list is a list
        if not isinstance(filter_list, list):
            print(f"  Error: Invalid configuration format for {email}")
            failed_accounts.append((email, "Invalid configuration"))
            continue

        try:
            # Load credentials
            credentials = auth_manager.load_credentials(email)

            # Create account-specific output directory
            account_output_dir = download_base / email
            account_output_dir.mkdir(parents=True, exist_ok=True)

            # Create downloader
            downloader = EmailDownloader(credentials=credentials, output_dir=account_output_dir, email_address=email, verbose=args.verbose)

            # Process emails with each filter set
            total_count = 0
            for idx, filters in enumerate(filter_list):
                if args.verbose:
                    print(f"  Using filter set {idx + 1}/{len(filter_list)}")

                # Create matcher with filters
                matcher = EmailMatcher(filters)

                # Process emails
                count = downloader.process_emails(start_date=start_date, end_date=end_date, matcher=matcher)

                total_count += count

                if args.verbose:
                    print(f"    Filter set {idx + 1}: {count} attachments")

            successful_accounts.append(email)
            total_downloaded += total_count
            print(f"  Total downloaded: {total_count} attachments")

        except FileNotFoundError:
            failed_accounts.append((email, "Credentials not found"))
            print("  Error: Credentials not found - need authentication")

        except Exception as e:
            error_msg = str(e)
            if "invalid_grant" in error_msg or "Token has been expired" in error_msg:
                failed_accounts.append((email, "Token expired"))
                print("  Error: Token expired - need re-authentication")
            else:
                failed_accounts.append((email, error_msg))
                print(f"  Error: {error_msg}")

    # Print summary
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)

    print(f"Processed: {len(successful_accounts)}/{len(accounts)} accounts")
    print(f"Total attachments downloaded: {total_downloaded}")

    if successful_accounts:
        print(f"\nSuccessful accounts ({len(successful_accounts)}):")
        for email in successful_accounts:
            print(f"  OK: {email}")

    if failed_accounts:
        print(f"\nFailed accounts ({len(failed_accounts)}):")
        for email, error in failed_accounts:
            print(f"  NG: {email} - {error}")

        print("\nTo re-authenticate failed accounts, run:")
        for email, _ in failed_accounts:
            if "Token expired" in _ or "Credentials not found" in _:
                print(f"  gmail-attachment-dl --auth {email}")

    return 0 if not failed_accounts else 1


def main() -> int:
    """Main entry point"""
    args = parse_args()

    # Authentication mode - doesn't require existing config file
    if args.auth:
        if args.config.exists():
            # Config file exists - use configured credentials directory
            try:
                config_manager = ConfigManager(args.config)
                return run_auth_mode(args.auth, config_manager)
            except ValueError as e:
                print(f"Configuration error: {e}", file=sys.stderr)
                return 1
        else:
            # Config file doesn't exist - use current directory for authentication
            print("Configuration file not found. Using current directory for authentication.")
            return run_auth_mode(args.auth, None)

    # Download mode - requires existing config file
    if not args.config.exists():
        print(f"Configuration file not found: {args.config}", file=sys.stderr)
        print("Create a config.json file with account filters.", file=sys.stderr)
        return 1

    try:
        config_manager = ConfigManager(args.config)
        return run_download_mode(args, config_manager)

    except ValueError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        return 1

    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        return 130

    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
