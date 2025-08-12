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

### Using uv (Recommended)

```bash
# Install globally
uv tool install gmail-attachment-dl

# Or run directly without installation
uvx gmail-attachment-dl --help
```

### Using pip

```bash
pip install gmail-attachment-dl
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

```
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

### API Limits

Gmail API has generous quotas (1 billion units/day), but be aware of:
- 250 units per message send
- 5 units per message read
- 5 units per attachment download

## Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/yourusername/gmail-attachment-dl.git
cd gmail-attachment-dl

# Install with uv
uv sync

# Run tests
uv run pytest

# Format code
uv run black src/
uv run ruff check src/
```

### Building for PyPI

```bash
# Build package
uv build

# Upload to PyPI
uv publish
```

## License

MIT License - see LICENSE file for details

## Contributing

Pull requests are welcome! Please ensure:
- Code follows existing style
- Tests pass
- Documentation is updated

## Support

For issues and questions:
- GitHub Issues: [github.com/yourusername/gmail-attachment-dl/issues](https://github.com/yourusername/gmail-attachment-dl/issues)