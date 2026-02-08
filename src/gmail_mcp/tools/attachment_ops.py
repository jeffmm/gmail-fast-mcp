"""Attachment operations: download_attachment."""

from __future__ import annotations

import base64
import os
from typing import Annotated

from gmail_mcp.gmail_service import get_gmail_service
from gmail_mcp.server import mcp


def _find_attachment_filename(part: dict, attachment_id: str) -> str | None:
    """Walk the MIME tree to find the original filename for an attachment."""
    body = part.get("body", {})
    if body.get("attachmentId") == attachment_id:
        return part.get("filename") or f"attachment-{attachment_id}"
    for sub in part.get("parts", []):
        found = _find_attachment_filename(sub, attachment_id)
        if found:
            return found
    return None


@mcp.tool()
def download_attachment(
    message_id: Annotated[str, "ID of the email message containing the attachment"],
    attachment_id: Annotated[str, "ID of the attachment to download"],
    filename: Annotated[
        str | None, "Filename to save as (uses original if not provided)"
    ] = None,
    save_path: Annotated[
        str | None, "Directory to save the attachment (defaults to current directory)"
    ] = None,
) -> str:
    """Download an email attachment to a specified location."""
    gmail = get_gmail_service()

    att_resp = (
        gmail.users()
        .messages()
        .attachments()
        .get(userId="me", messageId=message_id, id=attachment_id)
        .execute()
    )

    data = att_resp.get("data")
    if not data:
        return "Failed to download attachment: no attachment data received"

    file_bytes = base64.urlsafe_b64decode(data)

    dest_dir = save_path or os.getcwd()
    if not filename:
        msg = (
            gmail.users()
            .messages()
            .get(userId="me", id=message_id, format="full")
            .execute()
        )
        filename = (
            _find_attachment_filename(msg.get("payload", {}), attachment_id)
            or f"attachment-{attachment_id}"
        )

    os.makedirs(dest_dir, exist_ok=True)
    full_path = os.path.join(dest_dir, filename)

    with open(full_path, "wb") as f:
        f.write(file_bytes)

    return (
        f"Attachment downloaded successfully:\n"
        f"File: {filename}\n"
        f"Size: {len(file_bytes)} bytes\n"
        f"Saved to: {full_path}"
    )
