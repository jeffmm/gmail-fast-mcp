"""Filter operations: create, list, get, delete, create_from_template."""

from __future__ import annotations

from typing import Annotated

from gmail_mcp.server import mcp
from gmail_mcp.gmail_service import get_gmail_service
from gmail_mcp.filter_templates import TEMPLATES


def _format_dict(d: dict | None) -> str:
    if not d:
        return ""
    return ", ".join(
        f"{k}: {', '.join(v) if isinstance(v, list) else v}"
        for k, v in d.items()
        if v is not None and (not isinstance(v, list) or v)
    )


@mcp.tool()
def create_filter(
    criteria: Annotated[dict, "Criteria for matching emails (from, to, subject, query, negatedQuery, hasAttachment, excludeChats, size, sizeComparison)"],
    action: Annotated[dict, "Actions to perform (addLabelIds, removeLabelIds, forward)"],
) -> str:
    """Create a new Gmail filter with custom criteria and actions."""
    gmail = get_gmail_service()
    result = (
        gmail.users()
        .settings()
        .filters()
        .create(userId="me", body={"criteria": criteria, "action": action})
        .execute()
    )
    return (
        f"Filter created successfully:\n"
        f"ID: {result['id']}\n"
        f"Criteria: {_format_dict(criteria)}\n"
        f"Actions: {_format_dict(action)}"
    )


@mcp.tool()
def list_filters() -> str:
    """Retrieve all Gmail filters."""
    gmail = get_gmail_service()
    resp = (
        gmail.users().settings().filters().list(userId="me").execute()
    )
    filters = resp.get("filter", [])
    if not filters:
        return "No filters found."

    parts: list[str] = [f"Found {len(filters)} filters:\n"]
    for f in filters:
        parts.append(
            f"ID: {f.get('id')}\n"
            f"Criteria: {_format_dict(f.get('criteria'))}\n"
            f"Actions: {_format_dict(f.get('action'))}\n"
        )
    return "\n".join(parts)


@mcp.tool()
def get_filter(
    filter_id: Annotated[str, "ID of the filter to retrieve"],
) -> str:
    """Get details of a specific Gmail filter."""
    gmail = get_gmail_service()
    result = (
        gmail.users()
        .settings()
        .filters()
        .get(userId="me", id=filter_id)
        .execute()
    )
    return (
        f"Filter details:\n"
        f"ID: {result.get('id')}\n"
        f"Criteria: {_format_dict(result.get('criteria'))}\n"
        f"Actions: {_format_dict(result.get('action'))}"
    )


@mcp.tool()
def delete_filter(
    filter_id: Annotated[str, "ID of the filter to delete"],
) -> str:
    """Delete a Gmail filter."""
    gmail = get_gmail_service()
    gmail.users().settings().filters().delete(userId="me", id=filter_id).execute()
    return f'Filter "{filter_id}" deleted successfully.'


@mcp.tool()
def create_filter_from_template(
    template: Annotated[str, "Template name: fromSender, withSubject, withAttachments, largeEmails, containingText, or mailingList"],
    sender_email: Annotated[str | None, "Sender email (for fromSender)"] = None,
    subject_text: Annotated[str | None, "Subject text (for withSubject)"] = None,
    search_text: Annotated[str | None, "Text to search for (for containingText)"] = None,
    list_identifier: Annotated[str | None, "Mailing list identifier (for mailingList)"] = None,
    size_in_bytes: Annotated[int | None, "Size threshold in bytes (for largeEmails)"] = None,
    label_ids: Annotated[list[str] | None, "Label IDs to apply"] = None,
    archive: Annotated[bool | None, "Whether to archive (skip inbox)"] = None,
    mark_as_read: Annotated[bool | None, "Whether to mark as read"] = None,
    mark_important: Annotated[bool | None, "Whether to mark as important"] = None,
) -> str:
    """Create a filter using a pre-defined template for common scenarios."""
    template_fn = TEMPLATES.get(template)
    if template_fn is None:
        raise ValueError(f"Unknown template: {template}. Valid: {', '.join(TEMPLATES)}")

    # Build kwargs based on template
    if template == "fromSender":
        if not sender_email:
            raise ValueError("sender_email is required for fromSender template")
        config = template_fn(sender_email, label_ids, archive or False)
    elif template == "withSubject":
        if not subject_text:
            raise ValueError("subject_text is required for withSubject template")
        config = template_fn(subject_text, label_ids, mark_as_read or False)
    elif template == "withAttachments":
        config = template_fn(label_ids)
    elif template == "largeEmails":
        if not size_in_bytes:
            raise ValueError("size_in_bytes is required for largeEmails template")
        config = template_fn(size_in_bytes, label_ids)
    elif template == "containingText":
        if not search_text:
            raise ValueError("search_text is required for containingText template")
        config = template_fn(search_text, label_ids, mark_important or False)
    elif template == "mailingList":
        if not list_identifier:
            raise ValueError("list_identifier is required for mailingList template")
        config = template_fn(list_identifier, label_ids, archive if archive is not None else True)
    else:
        raise ValueError(f"Unknown template: {template}")

    gmail = get_gmail_service()
    result = (
        gmail.users()
        .settings()
        .filters()
        .create(userId="me", body=config)
        .execute()
    )
    return (
        f"Filter created from template '{template}':\n"
        f"ID: {result['id']}\n"
        f"Template used: {template}"
    )
