"""Pre-built filter templates for common Gmail filter patterns."""

from __future__ import annotations


def from_sender(
    sender_email: str,
    label_ids: list[str] | None = None,
    archive: bool = False,
) -> dict:
    return {
        "criteria": {"from": sender_email},
        "action": {
            "addLabelIds": label_ids or [],
            "removeLabelIds": ["INBOX"] if archive else [],
        },
    }


def with_subject(
    subject_text: str,
    label_ids: list[str] | None = None,
    mark_as_read: bool = False,
) -> dict:
    return {
        "criteria": {"subject": subject_text},
        "action": {
            "addLabelIds": label_ids or [],
            "removeLabelIds": ["UNREAD"] if mark_as_read else [],
        },
    }


def with_attachments(label_ids: list[str] | None = None) -> dict:
    return {
        "criteria": {"hasAttachment": True},
        "action": {"addLabelIds": label_ids or []},
    }


def large_emails(
    size_in_bytes: int,
    label_ids: list[str] | None = None,
) -> dict:
    return {
        "criteria": {"size": size_in_bytes, "sizeComparison": "larger"},
        "action": {"addLabelIds": label_ids or []},
    }


def containing_text(
    search_text: str,
    label_ids: list[str] | None = None,
    mark_important: bool = False,
) -> dict:
    ids = list(label_ids or [])
    if mark_important:
        ids.append("IMPORTANT")
    return {
        "criteria": {"query": f'"{search_text}"'},
        "action": {"addLabelIds": ids},
    }


def mailing_list(
    list_identifier: str,
    label_ids: list[str] | None = None,
    archive: bool = True,
) -> dict:
    return {
        "criteria": {
            "query": f"list:{list_identifier} OR subject:[{list_identifier}]",
        },
        "action": {
            "addLabelIds": label_ids or [],
            "removeLabelIds": ["INBOX"] if archive else [],
        },
    }


TEMPLATES = {
    "fromSender": from_sender,
    "withSubject": with_subject,
    "withAttachments": with_attachments,
    "largeEmails": large_emails,
    "containingText": containing_text,
    "mailingList": mailing_list,
}
