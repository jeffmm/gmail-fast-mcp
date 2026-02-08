"""OAuth2 browser-based authentication flow."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

from .gmail_service import CONFIG_DIR, CREDENTIALS_PATH, OAUTH_PATH, SCOPES


def authenticate(redirect_uri: str | None = None) -> None:
    """Run the OAuth2 flow, saving tokens to CREDENTIALS_PATH."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    # Copy local OAuth keys to config dir if present
    local_oauth = Path.cwd() / "gcp-oauth.keys.json"
    if local_oauth.exists():
        shutil.copy2(local_oauth, OAUTH_PATH)
        print("OAuth keys found in current directory, copied to global config.")

    if not OAUTH_PATH.exists():
        print(
            f"Error: OAuth keys file not found. "
            f"Place gcp-oauth.keys.json in the current directory or {CONFIG_DIR}",
            file=sys.stderr,
        )
        sys.exit(1)

    flow = InstalledAppFlow.from_client_secrets_file(str(OAUTH_PATH), SCOPES)

    if redirect_uri:
        flow.redirect_uri = redirect_uri
        # For custom redirect URIs, use run_console or manual flow
        creds = flow.run_local_server(
            port=3000,
            open_browser=True,
        )
    else:
        creds = flow.run_local_server(
            port=3000,
            open_browser=True,
        )

    CREDENTIALS_PATH.write_text(creds.to_json())
    print("Authentication completed successfully.")
