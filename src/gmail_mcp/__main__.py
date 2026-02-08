"""Entry point: uv run python -m gmail_mcp [auth [redirect_uri]]"""

import sys


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "auth":
        from gmail_mcp.auth import authenticate

        redirect_uri = sys.argv[2] if len(sys.argv) > 2 else None
        authenticate(redirect_uri)
    else:
        from gmail_mcp.server import mcp

        mcp.run()


main()
