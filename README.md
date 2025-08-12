# Gmail Attachment Downloader

Automatically download Gmail attachments (PDFs) based on regex filters. Supports multiple accounts and works with both personal Gmail and Google Workspace accounts.

## Features

- **Multi-account support** - Process multiple Gmail/Google Workspace accounts
- **Regex filtering** - Filter emails by From, To, Subject, and Body using regex patterns
- **Wildcard attachment filtering** - Filter attachments by filename patterns
- **Secure credential storage** - OAuth2 tokens are encrypted and stored securely
- **Cross-platform** - Works on Windows, macOS, and Linux
- **Batch processing** - Perfect for scheduled/cron jobs
- **Date range search** - Configurable search period

## Installation

### Quick Install from PyPI

Once published to PyPI, you can install and run easily:

```bash
# Install with uv (recommended)
uvx gmail-attachment-dl  # Run directly without installation

# Or install globally
uv tool install gmail-attachment-dl

# Or install with pip
pip install gmail-attachment-dl
```

### Install from Source

#### Prerequisites

Create and activate a virtual environment:

```bash
python -m venv venv

# On Windows
.\venv\Scripts\Activate.ps1

# On Linux/macOS
source venv/bin/activate
```

### Basic Installation

Install the project in editable mode:

#### For Production Use

```bash
pip install -e "."
```

#### For Development

Install with development tools included:

```bash
pip install -e ".[dev]"
```

### Dependencies

**Core dependencies** (automatically installed):

- `google-auth>=2.0.0` - Google authentication library
- `google-auth-oauthlib>=1.0.0` - OAuth2 flow support
- `google-auth-httplib2>=0.2.0` - HTTP transport for Google APIs
- `google-api-python-client>=2.0.0` - Gmail API client
- `cryptography>=41.0.0` - Token encryption
- `click>=8.0.0` - Command-line interface

**Development dependencies** (installed with `[dev]`):

- `pylint` - Code linting
- `pylint-plugin-utils` - Pylint utilities
- `black` - Code formatting

### Installation Examples

#### Quick Start (Production)

```bash
# Clone and install for production use
git clone <repository-url>
cd gmail-attachment-dl
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows
pip install -e "."
```

#### Developer Setup

```bash
# Clone and setup development environment
git clone <repository-url>
cd gmail-attachment-dl
python -m venv venv
.\venv\Scripts\Activate.ps1  # Windows
pip install -e ".[dev]"

# Run development tools
black src/
ruff check src/
```

## Setup

### 1. Google Cloud Configuration

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Gmail API:
   - Go to "APIs & Services" > "Library"
   - Search for "Gmail API"
   - Click "Enable"
4. Create OAuth2 credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Choose "Desktop app" as application type
   - Download the credentials JSON file
5. Save the file as `client_secret.json` in:
   - Windows: `%APPDATA%\gmail-attachment-dl\credentials\`
   - macOS: `~/Library/Application Support/gmail-attachment-dl/credentials/`
   - Linux: `~/.config/gmail-attachment-dl/credentials/`

### 2. Create Configuration File

Create a `config.json` file (see `config.example.json` for reference):

```json
{
  "default_days": 7,
  "download_base_path": "./downloads",
  "credentials_path": null,
  "accounts": {
    "user@gmail.com": [
      {
        "from": "invoice@.*\\.example\\.com",
        "subject": ["Receipt", "Invoice"],
        "body": "Payment.*confirmed",
        "attachments": ["*.pdf"]
      },
      {
        "from": "billing@.*\\.example\\.com",
        "attachments": ["report_*.pdf", "invoice_*.pdf"]
      }
    ],
    "user@company.com": [
      {
        "from": ["billing@.*", "accounting@.*"],
        "subject": "Statement",
        "attachments": null
      }
    ]
  }
}
```

**Configuration Structure:**

- Each email account has an **array of filter sets**
- Multiple filter sets per account allow different rules
- All conditions within a filter set must match (AND)
- Filter sets are processed independently (OR)

**Path Configuration:**

- `download_base_path`: Base directory for downloads (default: same as config location)
- `credentials_path`: Custom path for credentials storage (default: platform-specific)

### 3. Authenticate Accounts

Authenticate each account (one-time setup):

```bash
gmail-attachment-dl --auth user@gmail.com
gmail-attachment-dl --auth user@company.com
```

This will:

1. Open a browser for OAuth2 authentication
2. Ask you to authorize the application
3. Save encrypted credentials for future use

## Usage

### Command Line Options

```bash
gmail-attachment-dl --help
```

```text
usage: gmail-attachment-dl [-h] [--version] [--config CONFIG] [--days DAYS]
                          [--output OUTPUT] [--auth EMAIL] [--verbose]

Gmail Attachment Downloader

options:
  -h, --help       show this help message and exit
  --version        show program's version number and exit
  --config CONFIG  path to configuration file (default: ./config.json)
  --days DAYS      number of days to search back (default: from config)
  --output OUTPUT  override download directory
  --auth EMAIL     authenticate specific email account
  --verbose, -v    enable verbose output
```

### Command Examples

```bash
# Check version
gmail-attachment-dl --version
```

### Basic Usage

```bash
# Download attachments from last 7 days (default)
gmail-attachment-dl

# Specify number of days
gmail-attachment-dl --days 30

# Use custom config file
gmail-attachment-dl --config /path/to/config.json

# Override output directory (ignores config setting)
gmail-attachment-dl --output /custom/path/downloads

# Verbose output
gmail-attachment-dl -v
```

Downloaded files will be organized by:

- Email account
- Year
- Date and message ID
- Original attachment filename

### Scheduled Execution (Cron)

```bash
# Add to crontab for daily execution at 2 AM
0 2 * * * /usr/local/bin/gmail-attachment-dl --days 1
```

### Using with uv

```bash
# Run directly
uvx gmail-attachment-dl --days 7

# With specific Python version
uv run --python 3.11 gmail-attachment-dl
```

## Configuration

### Filter Options

Each filter set can have the following fields (all optional):

- **from**: Sender email pattern (string or array of strings)
- **to**: Recipient email pattern (string or array of strings)
- **subject**: Subject line pattern (string or array of strings)
- **body**: Email body pattern (string or array of strings)
- **attachments**: Attachment filename patterns (string or array of strings)

**Pattern Types:**

- **Email fields** (from/to/subject/body): Full regex syntax
- **Attachment filenames**: Wildcard patterns (`*.pdf`, `invoice_*.pdf`, etc.)
- `null` or omitted means no filtering on that field

**Matching Logic:**

- Within a filter set: All specified fields must match (AND)
- Multiple patterns in an array: Any pattern can match (OR)
- Multiple filter sets per account: Process each independently

### Examples

```json
{
  "default_days": 30,
  "download_base_path": "~/Documents/receipts",
  "credentials_path": "~/.private/gmail-creds",
  "accounts": {
    "user@gmail.com": [
      {
        "from": ".*@company\\.com",
        "subject": ["Invoice", "Receipt", "Bill"],
        "body": "(Paid|Confirmed|Processed)",
        "attachments": ["*.pdf"]
      },
      {
        "from": "accounting@vendor\\.com",
        "attachments": ["invoice_*.pdf", "receipt_*.pdf"]
      },
      {
        "subject": "Monthly Report",
        "attachments": ["report_202*.pdf"]
      }
    ]
  }
}
```

**Attachment Pattern Examples:**

- `"*.pdf"` - All PDF files
- `"invoice_*.pdf"` - PDFs starting with "invoice_"
- `["*.pdf", "*.xlsx"]` - PDFs and Excel files
- `null` or omitted - All attachments (no filtering)

**Path Options:**

- Relative paths: `"./downloads"` (relative to config file location)
- Absolute paths: `"/home/user/downloads"` or `"C:\\Users\\name\\Downloads"`
- Home directory: `"~/Downloads"` (expanded automatically)
- If omitted, uses platform defaults

## File Storage

Downloaded attachments are organized in a hierarchical structure:

```text
downloads/
├── user@gmail.com/
│   ├── 2025/
│   │   ├── 0108_abc123def456_invoice.pdf
│   │   ├── 0108_abc123def456_receipt.pdf
│   │   ├── 0109_ghi789jkl012_statement.pdf
│   │   └── 0110_mno345pqr678_report.pdf
│   └── 2024/
│       └── 1231_stu901vwx234_document.pdf
└── user@company.com/
    └── 2025/
        └── 0108_yza567bcd890_summary.pdf
```

**File naming:** `MMDD_messageId_originalname.pdf`

- Each email account has its own directory
- Files are organized by year
- Filename prefix includes date (MMDD) and Gmail message ID
- Multiple attachments from the same email share the same prefix
- Duplicate filenames are automatically renamed with `_01`, `_02`, etc.

## Security

- OAuth2 refresh tokens are encrypted using Fernet (symmetric encryption)
- Credentials are stored with restricted file permissions (600 on Unix)
- No passwords are stored - only OAuth2 tokens
- Each account requires individual authorization

## Error Handling

The tool includes comprehensive error handling for common issues:

- **Authentication errors**: Automatic token refresh with fallback to re-authentication
- **Network issues**: Retries with exponential backoff for API calls
- **File system errors**: Proper handling of permission and disk space issues
- **Gmail API limits**: Rate limiting and quota management

## Troubleshooting

### Token Expired

If you see "Token expired" errors:

```bash
gmail-attachment-dl --auth user@gmail.com
```

### Missing Credentials

If credentials are not found, re-authenticate:

```bash
gmail-attachment-dl --auth user@gmail.com
```

### Configuration Issues

If configuration is invalid:

```bash
# Check config file format
gmail-attachment-dl --config /path/to/config.json --verbose
```

### API Limits

Gmail API has generous quotas (1 billion units/day), but be aware of:

- 250 units per message send
- 5 units per message read
- 5 units per attachment download

## Development

### Development Environment Setup

1. **Clone and setup environment:**

```bash
git clone https://github.com/yourusername/gmail-attachment-dl.git
cd gmail-attachment-dl
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\Activate.ps1
# Linux/macOS:
source venv/bin/activate

# Install in development mode
pip install -e ".[dev]"
```

1. **Code formatting and linting:**

```bash
# Format code
black src/

# Run linter
ruff check src/

# Type checking
mypy src/
```

1. **Testing during development:**

```bash
# Run tests
pytest

# Run tests with coverage
pytest --cov=src/

# Test the CLI
gmail-attachment-dl --help

# Test with different options
gmail-attachment-dl --config config.example.json --days 1 --verbose
```
