"""
Email matching logic with regex support
"""

import re
import fnmatch
from typing import Dict, Any


class EmailMatcher:
    """Matches emails based on regex patterns"""

    def __init__(self, filters: Dict[str, Any]):
        """Initialize matcher with filter configuration"""
        self.filters = filters
        self._compile_patterns()

    def _compile_patterns(self):
        """Pre-compile regex patterns for efficiency"""
        self.patterns = {}

        for field in ["from", "to", "subject", "body"]:
            if field in self.filters and self.filters[field] is not None:
                value = self.filters[field]

                if isinstance(value, str):
                    # Single pattern
                    self.patterns[field] = [re.compile(value, re.IGNORECASE)]

                elif isinstance(value, list):
                    # Multiple patterns (OR condition)
                    self.patterns[field] = [re.compile(pattern, re.IGNORECASE) for pattern in value]
                else:
                    # Skip invalid types
                    continue

        # Handle attachment patterns (wildcards, not regex)
        self.attachment_patterns = []
        if "attachments" in self.filters:
            attachments = self.filters.get("attachments")
            if attachments is not None:
                if isinstance(attachments, str):
                    self.attachment_patterns = [attachments]
                elif isinstance(attachments, list):
                    self.attachment_patterns = attachments

    def match(self, email_data: Dict[str, str]) -> bool:
        """
        Check if email matches all filter criteria

        Args:
            email_data: Dictionary with 'from', 'to', 'subject', 'body' fields

        Returns:
            True if email matches all specified filters (AND condition)
        """

        # If no patterns defined, match everything
        if not self.patterns:
            return True

        # Check each field (AND condition between fields)
        for field, patterns in self.patterns.items():
            field_value = email_data.get(field, "")

            # Ensure field_value is string
            if field_value is None:
                field_value = ""

            # Check if any pattern matches (OR condition within field)
            matched = False
            for pattern in patterns:
                if pattern.search(field_value):
                    matched = True
                    break

            # If no pattern matched for this field, email doesn't match
            if not matched:
                return False

        # All fields matched
        return True

    def match_attachment(self, filename: str) -> bool:
        """
        Check if attachment filename matches the filter patterns

        Args:
            filename: Name of the attachment file

        Returns:
            True if filename matches any pattern or no patterns specified
        """

        # If no attachment patterns specified, match all files
        if not self.attachment_patterns:
            return True

        # Check if filename matches any wildcard pattern
        for pattern in self.attachment_patterns:
            if fnmatch.fnmatch(filename.lower(), pattern.lower()):
                return True

        return False

    def get_gmail_query(self) -> str:
        """
        Generate Gmail search query for initial filtering
        This helps reduce the number of emails to process

        Returns:
            Gmail query string (partial match, not regex)
        """

        query_parts = []

        # Add from filter (Gmail doesn't support regex, so extract keywords)
        if "from" in self.filters and self.filters["from"]:
            from_filter = self.filters["from"]

            if isinstance(from_filter, str):
                # Extract domain or email parts
                domain_match = re.search(r"@([a-zA-Z0-9.-]+)", from_filter)
                if domain_match:
                    query_parts.append(f"from:{domain_match.group(1)}")

            elif isinstance(from_filter, list):
                # Use first valid domain
                for pattern in from_filter:
                    domain_match = re.search(r"@([a-zA-Z0-9.-]+)", pattern)
                    if domain_match:
                        query_parts.append(f"from:{domain_match.group(1)}")
                        break

        # Add subject keywords (extract non-regex parts)
        if "subject" in self.filters and self.filters["subject"]:
            subject_filter = self.filters["subject"]

            if isinstance(subject_filter, str):
                # Extract alphanumeric words
                words = re.findall(r"\b[a-zA-Z0-9]+\b", subject_filter)
                if words:
                    query_parts.append(f"subject:{words[0]}")

            elif isinstance(subject_filter, list):
                # Use first valid word
                for pattern in subject_filter:
                    words = re.findall(r"\b[a-zA-Z0-9]+\b", pattern)
                    if words:
                        query_parts.append(f"subject:{words[0]}")
                        break

        # Always filter for emails with attachments
        query_parts.append("has:attachment")

        return " ".join(query_parts) if query_parts else "has:attachment"

    def describe(self) -> str:
        """Get human-readable description of filters"""

        descriptions = []

        for field in ["from", "to", "subject", "body"]:
            if field in self.filters and self.filters[field] is not None:
                value = self.filters[field]

                if isinstance(value, str):
                    descriptions.append(f"{field}: /{value}/")

                elif isinstance(value, list):
                    patterns = " OR ".join(f"/{p}/" for p in value)
                    descriptions.append(f"{field}: ({patterns})")

        if self.attachment_patterns:
            if len(self.attachment_patterns) == 1:
                descriptions.append(f"attachments: {self.attachment_patterns[0]}")
            else:
                patterns = " OR ".join(self.attachment_patterns)
                descriptions.append(f"attachments: ({patterns})")

        return " AND ".join(descriptions) if descriptions else "No filters"
