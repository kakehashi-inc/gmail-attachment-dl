"""
Gmail attachment downloader
"""

import base64
import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .matcher import EmailMatcher


class EmailDownloader:
    """Downloads attachments from Gmail based on filters"""

    def __init__(self, credentials: Credentials, output_dir: Path, verbose: bool = False):
        """
        Initialize downloader with Gmail service

        Args:
            credentials: OAuth2 credentials
            output_dir: Directory to save attachments (account-specific)
            verbose: Enable verbose output
        """
        self.service = build("gmail", "v1", credentials=credentials)
        self.output_dir = output_dir
        self.verbose = verbose

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def process_emails(self, start_date: datetime, end_date: datetime, matcher: EmailMatcher) -> int:
        """
        Process emails within date range using matcher

        Args:
            start_date: Start of date range
            end_date: End of date range
            matcher: EmailMatcher instance with filters

        Returns:
            Number of attachments downloaded
        """

        # Build Gmail query
        date_query = f"after:{start_date.strftime('%Y/%m/%d')} before:{end_date.strftime('%Y/%m/%d')}"
        gmail_query = f"{date_query} {matcher.get_gmail_query()}"

        if self.verbose:
            print(f"  Gmail query: {gmail_query}")
            print(f"  Filters: {matcher.describe()}")

        # Get message list
        messages = self._list_messages(gmail_query)

        if not messages:
            if self.verbose:
                print("  No messages found")
            return 0

        if self.verbose:
            print(f"  Found {len(messages)} messages to check")

        # Process each message
        download_count = 0

        for msg_data in messages:
            msg_id = msg_data["id"]

            try:
                # Get full message
                message = self._get_message(msg_id)

                # Extract email fields
                email_data = self._extract_email_data(message)

                # Check if message matches filters
                if not matcher.match(email_data):
                    if self.verbose:
                        print(f"    Message {msg_id}: No match")
                    continue

                # Download attachments
                count = self._download_attachments(message, matcher)
                download_count += count

                if self.verbose and count > 0:
                    print(f"    Message {msg_id}: Downloaded {count} attachments")

            except Exception as e:
                if self.verbose:
                    print(f"    Message {msg_id}: Error - {e}")
                continue

        return download_count

    def _list_messages(self, query: str) -> List[Dict[str, Any]]:
        """Get list of messages matching query"""

        messages = []
        page_token = None

        try:
            while True:
                results = self.service.users().messages().list(userId="me", q=query, pageToken=page_token, maxResults=100).execute()  # type: ignore # pylint: disable=no-member

                if "messages" in results:
                    messages.extend(results["messages"])

                page_token = results.get("nextPageToken")
                if not page_token:
                    break

        except HttpError as e:
            if self.verbose:
                print(f"  Error listing messages: {e}")

        return messages

    def _get_message(self, msg_id: str) -> Dict[str, Any]:
        """Get full message by ID"""

        return self.service.users().messages().get(userId="me", id=msg_id, format="full").execute()  # type: ignore # pylint: disable=no-member

    def _extract_email_data(self, message: Dict[str, Any]) -> Dict[str, str]:
        """Extract email fields for matching"""

        headers = message["payload"].get("headers", [])

        # Extract header fields
        email_data = {"from": "", "to": "", "subject": "", "body": ""}

        for header in headers:
            name = header["name"].lower()
            if name in email_data:
                email_data[name] = header["value"]

        # Extract body
        body_text = self._extract_body(message["payload"])
        email_data["body"] = body_text

        return email_data

    def _extract_body(self, payload: Dict[str, Any]) -> str:
        """Extract text body from message payload"""

        body_text = ""

        # Check for parts
        if "parts" in payload:
            for part in payload["parts"]:
                if part["mimeType"] == "text/plain":
                    data = part["body"].get("data", "")
                    if data:
                        body_text += base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")

                elif "parts" in part:
                    # Nested parts (e.g., multipart/alternative)
                    body_text += self._extract_body(part)

        elif payload.get("body", {}).get("data"):
            # Direct body data
            data = payload["body"]["data"]
            body_text = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")

        return body_text

    def _download_attachments(self, message: Dict[str, Any], matcher: EmailMatcher) -> int:
        """Download all attachments from message"""

        count = 0
        msg_id = message["id"]

        # Get date for prefix
        internal_date = int(message.get("internalDate", "0"))
        msg_datetime = datetime.fromtimestamp(internal_date / 1000)

        # Create directory structure: year/
        year_dir = self.output_dir / str(msg_datetime.year)
        year_dir.mkdir(parents=True, exist_ok=True)

        # Create filename prefix: MMDD_messageId_
        month_day = msg_datetime.strftime("%m%d")
        file_prefix = f"{month_day}_{msg_id}_"

        # Process parts
        parts = self._get_parts_with_attachments(message["payload"])

        for part in parts:
            filename = part.get("filename", "")

            if not filename:
                continue

            # Check if filename matches attachment patterns
            if not matcher.match_attachment(filename):
                if self.verbose:
                    print(f"      Skipping (no pattern match): {filename}")
                continue

            # Get attachment
            att_id = part["body"]["attachmentId"]

            try:
                attachment = self.service.users().messages().attachments().get(userId="me", messageId=msg_id, id=att_id).execute()  # type: ignore # pylint: disable=no-member

                # Decode attachment data
                file_data = base64.urlsafe_b64decode(attachment["data"])

                # Create safe filename with prefix
                safe_filename = self._create_safe_filename(filename)
                final_filename = f"{file_prefix}{safe_filename}"

                # Save file in year directory
                file_path = year_dir / final_filename

                # Handle duplicates (multiple attachments with same name in same email)
                if file_path.exists():
                    base = file_path.stem
                    ext = file_path.suffix
                    counter = 1

                    while file_path.exists():
                        file_path = year_dir / f"{base}_{counter:02d}{ext}"
                        counter += 1

                with open(file_path, "wb") as f:
                    f.write(file_data)

                if self.verbose:
                    relative_path = file_path.relative_to(self.output_dir.parent)
                    print(f"      Saved: {relative_path}")

                count += 1

            except Exception as e:
                if self.verbose:
                    print(f"      Error downloading {filename}: {e}")
                continue

        return count

    def _get_parts_with_attachments(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Recursively get all parts with attachments"""

        parts = []

        if "parts" in payload:
            for part in payload["parts"]:
                if part.get("filename"):
                    parts.append(part)

                # Check nested parts
                if "parts" in part:
                    parts.extend(self._get_parts_with_attachments(part))

        elif payload.get("filename"):
            parts.append(payload)

        return parts

    def _create_safe_filename(self, original: str) -> str:
        """Create safe filename from original name"""

        # Get name and extension
        name = Path(original).stem
        ext = Path(original).suffix

        # Remove unsafe characters
        safe_name = re.sub(r'[<>:"/\\|?*]', "_", name)

        # Limit length (leave room for counter if needed)
        safe_name = safe_name[:100]

        return f"{safe_name}{ext}"
