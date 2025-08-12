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

        # Process all fields that support Gmail search
        for field_name in ["from", "to", "subject", "body"]:
            query_part = self._generate_field_query(field_name)
            if query_part:
                query_parts.append(query_part)

        # Always filter for emails with attachments
        query_parts.append("has:attachment")

        return " ".join(query_parts)

    def _generate_field_query(self, field_name: str) -> str:
        """Generate Gmail query part for a specific field"""
        if field_name not in self.filters or not self.filters[field_name]:
            return ""

        field_filter = self.filters[field_name]

        # Normalize to list to eliminate type branching
        if isinstance(field_filter, str):
            patterns = [field_filter]
        elif isinstance(field_filter, list):
            patterns = field_filter
        else:
            return ""

        # Extract keywords from all patterns
        keywords = []
        for pattern in patterns:
            if field_name in ["from", "to"]:
                # Extract domain first, then fallback to keywords
                domain_match = re.search(r"@([a-zA-Z0-9.-]+)", pattern)
                if domain_match:
                    domain = domain_match.group(1)
                    if domain not in keywords:
                        keywords.append(domain)
                else:
                    # Fallback to extract keywords
                    words = re.findall(r"\b[a-zA-Z0-9]+\b", pattern)
                    if words and words[0] not in keywords:
                        keywords.append(words[0])

            elif field_name in ["subject", "body"]:
                # Extract alphanumeric words
                words = re.findall(r"\b[a-zA-Z0-9]+\b", pattern)
                if words:
                    keyword = words[0]  # Use first valid word from each pattern
                    if keyword not in keywords:
                        keywords.append(keyword)

        if not keywords:
            return ""

        # Generate query part
        if len(keywords) == 1:
            # Single keyword
            if field_name == "body":
                return f"{keywords[0]}"  # Body searches without field prefix
            else:
                return f"{field_name}:{keywords[0]}"
        else:
            # Multiple keywords (OR condition)
            if field_name == "body":
                keyword_query = " OR ".join(f"{keyword}" for keyword in keywords)
            else:
                keyword_query = " OR ".join(f"{field_name}:{keyword}" for keyword in keywords)
            return f"({keyword_query})"

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
