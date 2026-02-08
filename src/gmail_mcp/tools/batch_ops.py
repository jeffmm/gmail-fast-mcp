"""Batch operations: batch_modify_emails + process_batches helper."""

from __future__ import annotations

from typing import Annotated, Callable, TypeVar

from gmail_mcp.server import mcp
from gmail_mcp.gmail_service import get_gmail_service

T = TypeVar("T")
U = TypeVar("U")


def process_batches(
    items: list[T],
    batch_size: int,
    process_fn: Callable[[list[T]], list[U]],
) -> tuple[list[U], list[tuple[T, str]]]:
    """Process items in chunks with per-item retry on batch failure.

    Returns (successes, failures) where failures is a list of (item, error_message).
    """
    successes: list[U] = []
    failures: list[tuple[T, str]] = []

    for i in range(0, len(items), batch_size):
        batch = items[i : i + batch_size]
        try:
            results = process_fn(batch)
            successes.extend(results)
        except Exception:
            # Retry individually
            for item in batch:
                try:
                    result = process_fn([item])
                    successes.extend(result)
                except Exception as item_err:
                    failures.append((item, str(item_err)))

    return successes, failures


@mcp.tool()
def batch_modify_emails(
    message_ids: Annotated[list[str], "List of message IDs to modify"],
    add_label_ids: Annotated[list[str] | None, "Label IDs to add to all messages"] = None,
    remove_label_ids: Annotated[list[str] | None, "Label IDs to remove from all messages"] = None,
    batch_size: Annotated[int | None, "Number of messages per batch (default: 50)"] = 50,
) -> str:
    """Modify labels for multiple emails in batches."""
    gmail = get_gmail_service()

    body: dict = {}
    if add_label_ids:
        body["addLabelIds"] = add_label_ids
    if remove_label_ids:
        body["removeLabelIds"] = remove_label_ids

    def _modify_batch(batch: list[str]) -> list[dict]:
        results = []
        for mid in batch:
            gmail.users().messages().modify(
                userId="me", id=mid, body=body
            ).execute()
            results.append({"messageId": mid, "success": True})
        return results

    successes, failures = process_batches(
        message_ids, batch_size or 50, _modify_batch
    )

    lines = [
        "Batch label modification complete.",
        f"Successfully processed: {len(successes)} messages",
    ]
    if failures:
        lines.append(f"Failed to process: {len(failures)} messages\n")
        lines.append("Failed message IDs:")
        for item, error in failures:
            lines.append(f"- {item[:16]}... ({error})")
    return "\n".join(lines)
