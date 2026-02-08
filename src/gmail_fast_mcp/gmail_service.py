"""Lazy singleton for the authenticated Gmail API service."""

from __future__ import annotations

import json
import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

CONFIG_DIR = Path.home() / ".gmail-mcp"
OAUTH_PATH = Path(
    os.environ.get("GMAIL_OAUTH_PATH", CONFIG_DIR / "gcp-oauth.keys.json")
)
CREDENTIALS_PATH = Path(
    os.environ.get("GMAIL_CREDENTIALS_PATH", CONFIG_DIR / "credentials.json")
)
SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.settings.basic",
]

_service = None


def get_gmail_service():
    """Return a cached Gmail API service, creating it on first call."""
    global _service
    if _service is not None:
        return _service

    if not CREDENTIALS_PATH.exists():
        raise RuntimeError(
            f"No credentials found at {CREDENTIALS_PATH}. "
            "Run 'uv run python -m gmail_fast_mcp auth' first."
        )

    token_data = json.loads(CREDENTIALS_PATH.read_text())

    # Node.js OAuth libraries save tokens without client_id/client_secret.
    # Merge them from the OAuth keys file if missing.
    if "client_id" not in token_data and OAUTH_PATH.exists():
        oauth_keys = json.loads(OAUTH_PATH.read_text())
        client_info = oauth_keys.get("installed") or oauth_keys.get("web", {})
        token_data["client_id"] = client_info.get("client_id", "")
        token_data["client_secret"] = client_info.get("client_secret", "")

    creds = Credentials.from_authorized_user_info(token_data, SCOPES)

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        CREDENTIALS_PATH.write_text(creds.to_json())

    from googleapiclient.discovery import build

    _service = build("gmail", "v1", credentials=creds)
    return _service
