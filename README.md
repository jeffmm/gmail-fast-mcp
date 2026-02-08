# gmail-fast-mcp

Gmail MCP server built with [FastMCP](https://github.com/jlowin/fastmcp). Provides 19 tools for email operations, label management, filter management, and attachment handling via the Gmail API.

## Setup

### 1. Google OAuth Credentials

Place your Google Cloud OAuth client credentials at `~/.gmail-mcp/gcp-oauth.keys.json` (or in the project directory — they'll be copied automatically).

### 2. Authenticate

```bash
uv run python -m gmail_fast_mcp auth
```

This opens a browser for the OAuth flow and saves tokens to `~/.gmail-mcp/credentials.json`.

For cloud environments with a custom callback URL:

```bash
uv run python -m gmail_fast_mcp auth https://your-domain.com/oauth2callback
```

### 3. Run the Server

```bash
uv run python -m gmail_fast_mcp
```

### MCP Client Configuration

```json
{
  "mcpServers": {
    "gmail": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/gmail-fast-mcp", "python", "-m", "gmail_fast_mcp"]
    }
  }
}
```

## Tools

| Tool | Description |
|------|-------------|
| `send_email` | Send an email (text/html/multipart, attachments, threading) |
| `draft_email` | Create an email draft |
| `read_email` | Retrieve email content and attachment metadata |
| `search_emails` | Search using Gmail query syntax |
| `modify_email` | Add/remove labels on a message |
| `trash_email` | Move a message to trash |
| `batch_modify_emails` | Modify labels on multiple messages |
| `batch_trash_emails` | Trash multiple messages |
| `list_email_labels` | List all Gmail labels |
| `create_label` | Create a new label |
| `update_label` | Update label name/visibility |
| `delete_label` | Delete a user label |
| `get_or_create_label` | Find existing label or create it |
| `create_filter` | Create a filter with custom criteria/actions |
| `list_filters` | List all filters |
| `get_filter` | Get filter details |
| `delete_filter` | Delete a filter |
| `create_filter_from_template` | Create a filter from a preset template |
| `download_attachment` | Download an attachment to disk |

## Gmail API Scopes

- `gmail.modify` — Read, send, modify emails and labels
- `gmail.settings.basic` — Manage filters and settings
