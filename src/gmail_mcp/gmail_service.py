"""Lazy singleton for the authenticated Gmail API service."""

from __future__ import annotations

import json
import os
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

CONFIG_DIR = Path.home() / ".gmail-mcp"
OAUTH_PATH = Path(os.environ.get("GMAIL_OAUTH_PATH", CONFIG_DIR / "gcp-oauth.keys.json"))
CREDENTIALS_PATH = Path(os.environ.get("GMAIL_CREDENTIALS_PATH", CONFIG_DIR / "credentials.json"))
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
            "Run 'uv run python -m gmail_mcp auth' first."
        )

    creds = Credentials.from_authorized_user_info(
        json.loads(CREDENTIALS_PATH.read_text()), SCOPES
    )

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        CREDENTIALS_PATH.write_text(creds.to_json())

    from googleapiclient.discovery import build

    _service = build("gmail", "v1", credentials=creds)
    return _service
