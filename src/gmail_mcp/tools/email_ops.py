"""Email operations: send, draft, read, search, modify."""

from __future__ import annotations

import base64
import math
from typing import Annotated

from gmail_mcp.server import mcp
from gmail_mcp.gmail_service import get_gmail_service
from gmail_mcp.email_utils import create_email_message


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_email_content(part: dict) -> tuple[str, str]:
    """Recursively extract (text, html) content from a MIME part tree."""
    text = ""
    html = ""

    body = part.get("body", {})
    data = body.get("data")
    if data:
        decoded = base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
        mime = part.get("mimeType", "")
        if mime == "text/plain":
            text = decoded
        elif mime == "text/html":
            html = decoded

    for sub in part.get("parts", []):
        t, h = _extract_email_content(sub)
        if t:
            text += t
        if h:
            html += h

    return text, html


def _collect_attachments(part: dict) -> list[dict]:
    """Walk the MIME tree and return attachment metadata dicts."""
    attachments: list[dict] = []
    body = part.get("body", {})
    if body.get("attachmentId"):
        attachments.append({
            "id": body["attachmentId"],
            "filename": part.get("filename") or f"attachment-{body['attachmentId']}",
            "mimeType": part.get("mimeType", "application/octet-stream"),
            "size": body.get("size", 0),
        })
    for sub in part.get("parts", []):
        attachments.extend(_collect_attachments(sub))
    return attachments


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@mcp.tool()
def send_email(
    to: Annotated[list[str], "List of recipient email addresses"],
    subject: Annotated[str, "Email subject"],
    body: Annotated[str, "Email body content (plain text, or fallback when htmlBody not provided)"],
    html_body: Annotated[str | None, "HTML version of the email body"] = None,
    mime_type: Annotated[str | None, "Content type: text/plain, text/html, or multipart/alternative"] = "text/plain",
    cc: Annotated[list[str] | None, "List of CC recipients"] = None,
    bcc: Annotated[list[str] | None, "List of BCC recipients"] = None,
    thread_id: Annotated[str | None, "Thread ID to reply to"] = None,
    in_reply_to: Annotated[str | None, "Message ID being replied to"] = None,
    attachments: Annotated[list[str] | None, "List of file paths to attach"] = None,
) -> str:
    """Send a new email."""
    gmail = get_gmail_service()
    raw = create_email_message(
        to=to,
        subject=subject,
        body=body,
        html_body=html_body,
        mime_type=mime_type or "text/plain",
        cc=cc,
        bcc=bcc,
        in_reply_to=in_reply_to,
        attachments=attachments,
    )
    body_payload: dict = {"raw": raw}
    if thread_id:
        body_payload["threadId"] = thread_id

    result = gmail.users().messages().send(userId="me", body=body_payload).execute()
    return f"Email sent successfully with ID: {result['id']}"


@mcp.tool()
def draft_email(
    to: Annotated[list[str], "List of recipient email addresses"],
    subject: Annotated[str, "Email subject"],
    body: Annotated[str, "Email body content (plain text, or fallback when htmlBody not provided)"],
    html_body: Annotated[str | None, "HTML version of the email body"] = None,
    mime_type: Annotated[str | None, "Content type: text/plain, text/html, or multipart/alternative"] = "text/plain",
    cc: Annotated[list[str] | None, "List of CC recipients"] = None,
    bcc: Annotated[list[str] | None, "List of BCC recipients"] = None,
    thread_id: Annotated[str | None, "Thread ID to reply to"] = None,
    in_reply_to: Annotated[str | None, "Message ID being replied to"] = None,
    attachments: Annotated[list[str] | None, "List of file paths to attach"] = None,
) -> str:
    """Create an email draft."""
    gmail = get_gmail_service()
    raw = create_email_message(
        to=to,
        subject=subject,
        body=body,
        html_body=html_body,
        mime_type=mime_type or "text/plain",
        cc=cc,
        bcc=bcc,
        in_reply_to=in_reply_to,
        attachments=attachments,
    )
    message: dict = {"raw": raw}
    if thread_id:
        message["threadId"] = thread_id

    result = (
        gmail.users()
        .drafts()
        .create(userId="me", body={"message": message})
        .execute()
    )
    return f"Email draft created successfully with ID: {result['id']}"


@mcp.tool()
def read_email(
    message_id: Annotated[str, "ID of the email message to retrieve"],
) -> str:
    """Retrieve the content of a specific email."""
    gmail = get_gmail_service()
    msg = (
        gmail.users()
        .messages()
        .get(userId="me", id=message_id, format="full")
        .execute()
    )

    headers = msg.get("payload", {}).get("headers", [])

    def _header(name: str) -> str:
        for h in headers:
            if h.get("name", "").lower() == name.lower():
                return h.get("value", "")
        return ""

    subject = _header("subject")
    from_ = _header("from")
    to = _header("to")
    date = _header("date")
    thread_id = msg.get("threadId", "")

    text, html = _extract_email_content(msg.get("payload", {}))
    content = text or html or ""
    note = (
        "[Note: This email is HTML-formatted. Plain text version not available.]\n\n"
        if not text and html
        else ""
    )

    attachments = _collect_attachments(msg.get("payload", {}))
    att_info = ""
    if attachments:
        att_lines = [
            f"- {a['filename']} ({a['mimeType']}, {math.ceil(a['size'] / 1024)} KB, ID: {a['id']})"
            for a in attachments
        ]
        att_info = f"\n\nAttachments ({len(attachments)}):\n" + "\n".join(att_lines)

    return (
        f"Thread ID: {thread_id}\n"
        f"Subject: {subject}\n"
        f"From: {from_}\n"
        f"To: {to}\n"
        f"Date: {date}\n\n"
        f"{note}{content}{att_info}"
    )


@mcp.tool()
def search_emails(
    query: Annotated[str, "Gmail search query (e.g., 'from:example@gmail.com')"],
    max_results: Annotated[int | None, "Maximum number of results to return"] = 10,
) -> str:
    """Search for emails using Gmail search syntax."""
    gmail = get_gmail_service()
    resp = (
        gmail.users()
        .messages()
        .list(userId="me", q=query, maxResults=max_results or 10)
        .execute()
    )

    messages = resp.get("messages", [])
    if not messages:
        return "No messages found."

    results: list[str] = []
    for m in messages:
        detail = (
            gmail.users()
            .messages()
            .get(
                userId="me",
                id=m["id"],
                format="metadata",
                metadataHeaders=["Subject", "From", "Date"],
            )
            .execute()
        )
        hdrs = detail.get("payload", {}).get("headers", [])

        def _h(name: str) -> str:
            for h in hdrs:
                if h.get("name") == name:
                    return h.get("value", "")
            return ""

        results.append(
            f"ID: {m['id']}\nSubject: {_h('Subject')}\nFrom: {_h('From')}\nDate: {_h('Date')}\n"
        )

    return "\n".join(results)


@mcp.tool()
def modify_email(
    message_id: Annotated[str, "ID of the email message to modify"],
    label_ids: Annotated[list[str] | None, "List of label IDs to apply"] = None,
    add_label_ids: Annotated[list[str] | None, "List of label IDs to add"] = None,
    remove_label_ids: Annotated[list[str] | None, "List of label IDs to remove"] = None,
) -> str:
    """Modify email labels (move to different folders)."""
    gmail = get_gmail_service()
    body: dict = {}
    if label_ids:
        body["addLabelIds"] = label_ids
    if add_label_ids:
        body["addLabelIds"] = add_label_ids
    if remove_label_ids:
        body["removeLabelIds"] = remove_label_ids

    gmail.users().messages().modify(userId="me", id=message_id, body=body).execute()
    return f"Email {message_id} labels updated successfully"
