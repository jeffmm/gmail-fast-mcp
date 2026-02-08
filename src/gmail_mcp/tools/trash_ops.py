"""Trash operations: trash_email, batch_trash_emails."""

from __future__ import annotations

from typing import Annotated

from gmail_mcp.server import mcp
from gmail_mcp.gmail_service import get_gmail_service
from gmail_mcp.tools.batch_ops import process_batches


@mcp.tool()
def trash_email(
    message_id: Annotated[str, "ID of the email message to trash"],
) -> str:
    """Move an email to the trash."""
    gmail = get_gmail_service()
    gmail.users().messages().trash(userId="me", id=message_id).execute()
    return f"Email {message_id} moved to trash successfully"


@mcp.tool()
def batch_trash_emails(
    message_ids: Annotated[list[str], "List of message IDs to trash"],
    batch_size: Annotated[int | None, "Number of messages per batch (default: 50)"] = 50,
) -> str:
    """Move multiple emails to trash in batches."""
    gmail = get_gmail_service()

    def _trash_batch(batch: list[str]) -> list[dict]:
        results = []
        for mid in batch:
            gmail.users().messages().trash(userId="me", id=mid).execute()
            results.append({"messageId": mid, "success": True})
        return results

    successes, failures = process_batches(message_ids, batch_size or 50, _trash_batch)

    lines = [
        "Batch trash operation complete.",
        f"Successfully trashed: {len(successes)} messages",
    ]
    if failures:
        lines.append(f"Failed to trash: {len(failures)} messages\n")
        lines.append("Failed message IDs:")
        for item, error in failures:
            lines.append(f"- {item[:16]}... ({error})")
    return "\n".join(lines)
