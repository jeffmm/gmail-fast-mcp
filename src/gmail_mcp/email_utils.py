"""RFC 822 message construction using Python stdlib."""

from __future__ import annotations

import base64
import mimetypes
import os
import re
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def validate_email(email: str) -> bool:
    return bool(re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", email))


def create_email_message(
    *,
    to: list[str],
    subject: str,
    body: str,
    html_body: str | None = None,
    mime_type: str = "text/plain",
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
    in_reply_to: str | None = None,
    attachments: list[str] | None = None,
) -> str:
    """Build an RFC 822 message and return its base64url-encoded form.

    Handles three content modes (text/plain, text/html, multipart/alternative)
    and optional file attachments.  Returns a string ready for the Gmail API
    ``raw`` field.
    """
    for addr in to:
        if not validate_email(addr):
            raise ValueError(f"Invalid recipient email address: {addr}")

    # Decide effective MIME type
    if html_body and mime_type != "text/plain":
        mime_type = "multipart/alternative"

    # Build the content part
    if mime_type == "multipart/alternative":
        content = MIMEMultipart("alternative")
        content.attach(MIMEText(body, "plain", "utf-8"))
        content.attach(MIMEText(html_body or body, "html", "utf-8"))
    elif mime_type == "text/html":
        content = MIMEText(html_body or body, "html", "utf-8")
    else:
        content = MIMEText(body, "plain", "utf-8")

    # Wrap in multipart/mixed if there are attachments
    if attachments:
        msg = MIMEMultipart("mixed")
        msg.attach(content)
        for filepath in attachments:
            if not os.path.isfile(filepath):
                raise FileNotFoundError(f"Attachment file not found: {filepath}")
            ctype, _ = mimetypes.guess_type(filepath)
            if ctype is None:
                ctype = "application/octet-stream"
            maintype, subtype = ctype.split("/", 1)
            with open(filepath, "rb") as f:
                part = MIMEBase(maintype, subtype)
                part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                "attachment",
                filename=os.path.basename(filepath),
            )
            msg.attach(part)
    else:
        msg = content

    # Set headers
    msg["From"] = "me"
    msg["To"] = ", ".join(to)
    if cc:
        msg["Cc"] = ", ".join(cc)
    if bcc:
        msg["Bcc"] = ", ".join(bcc)
    msg["Subject"] = subject
    if in_reply_to:
        msg["In-Reply-To"] = in_reply_to
        msg["References"] = in_reply_to

    raw = msg.as_bytes()
    return base64.urlsafe_b64encode(raw).decode("ascii")
