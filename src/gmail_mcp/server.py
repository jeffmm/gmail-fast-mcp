"""FastMCP server instance and tool registration."""

from fastmcp import FastMCP

mcp = FastMCP("Gmail")

# Import tool modules to trigger @mcp.tool decorator registration
from gmail_mcp.tools import (  # noqa: E402, F401
    attachment_ops,
    batch_ops,
    email_ops,
    filter_ops,
    label_ops,
    trash_ops,
)
