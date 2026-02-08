"""Label operations: list, create, update, delete, get_or_create."""

from __future__ import annotations

from typing import Annotated

from gmail_fast_mcp.gmail_service import get_gmail_service
from gmail_fast_mcp.server import mcp


@mcp.tool()
def list_email_labels() -> str:
    """Retrieve all available Gmail labels."""
    gmail = get_gmail_service()
    resp = gmail.users().labels().list(userId="me").execute()
    labels = resp.get("labels", [])

    system = [l for l in labels if l.get("type") == "system"]
    user = [l for l in labels if l.get("type") == "user"]

    parts = [
        f"Found {len(labels)} labels ({len(system)} system, {len(user)} user):\n",
        "System Labels:",
    ]
    for l in system:
        parts.append(f"ID: {l['id']}\nName: {l['name']}\n")
    parts.append("\nUser Labels:")
    for l in user:
        parts.append(f"ID: {l['id']}\nName: {l['name']}\n")

    return "\n".join(parts)


@mcp.tool()
def create_label(
    name: Annotated[str, "Name for the new label"],
    message_list_visibility: Annotated[str | None, "show or hide"] = None,
    label_list_visibility: Annotated[
        str | None, "labelShow, labelShowIfUnread, or labelHide"
    ] = None,
) -> str:
    """Create a new Gmail label."""
    gmail = get_gmail_service()
    body = {
        "name": name,
        "messageListVisibility": message_list_visibility or "show",
        "labelListVisibility": label_list_visibility or "labelShow",
    }
    try:
        result = gmail.users().labels().create(userId="me", body=body).execute()
    except Exception as e:
        if "already exists" in str(e):
            raise ValueError(
                f'Label "{name}" already exists. Use a different name.'
            ) from e
        raise

    return (
        f"Label created successfully:\n"
        f"ID: {result['id']}\n"
        f"Name: {result['name']}\n"
        f"Type: {result.get('type', 'user')}"
    )


@mcp.tool()
def update_label(
    id: Annotated[str, "ID of the label to update"],
    name: Annotated[str | None, "New name for the label"] = None,
    message_list_visibility: Annotated[str | None, "show or hide"] = None,
    label_list_visibility: Annotated[
        str | None, "labelShow, labelShowIfUnread, or labelHide"
    ] = None,
) -> str:
    """Update an existing Gmail label."""
    gmail = get_gmail_service()

    # Verify label exists
    gmail.users().labels().get(userId="me", id=id).execute()

    updates: dict = {}
    if name:
        updates["name"] = name
    if message_list_visibility:
        updates["messageListVisibility"] = message_list_visibility
    if label_list_visibility:
        updates["labelListVisibility"] = label_list_visibility

    result = gmail.users().labels().update(userId="me", id=id, body=updates).execute()
    return (
        f"Label updated successfully:\n"
        f"ID: {result['id']}\n"
        f"Name: {result['name']}\n"
        f"Type: {result.get('type', 'user')}"
    )


@mcp.tool()
def delete_label(
    id: Annotated[str, "ID of the label to delete"],
) -> str:
    """Delete a Gmail label."""
    gmail = get_gmail_service()

    label = gmail.users().labels().get(userId="me", id=id).execute()
    if label.get("type") == "system":
        raise ValueError(f'Cannot delete system label with ID "{id}".')

    gmail.users().labels().delete(userId="me", id=id).execute()
    return f'Label "{label["name"]}" deleted successfully.'


@mcp.tool()
def get_or_create_label(
    name: Annotated[str, "Name of the label to get or create"],
    message_list_visibility: Annotated[str | None, "show or hide"] = None,
    label_list_visibility: Annotated[
        str | None, "labelShow, labelShowIfUnread, or labelHide"
    ] = None,
) -> str:
    """Get an existing label by name or create it if it doesn't exist."""
    gmail = get_gmail_service()

    # Search for existing label (case-insensitive)
    resp = gmail.users().labels().list(userId="me").execute()
    for label in resp.get("labels", []):
        if label.get("name", "").lower() == name.lower():
            return (
                f"Successfully found existing label:\n"
                f"ID: {label['id']}\n"
                f"Name: {label['name']}\n"
                f"Type: {label.get('type', 'user')}"
            )

    # Create new label
    body = {
        "name": name,
        "messageListVisibility": message_list_visibility or "show",
        "labelListVisibility": label_list_visibility or "labelShow",
    }
    result = gmail.users().labels().create(userId="me", body=body).execute()
    return (
        f"Successfully created new label:\n"
        f"ID: {result['id']}\n"
        f"Name: {result['name']}\n"
        f"Type: {result.get('type', 'user')}"
    )
