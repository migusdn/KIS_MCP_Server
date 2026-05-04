"""Backward-compatible entrypoint for the KIS MCP server.

The primary implementation now lives in :mod:`server`, matching the MCP
server.py convention used by Korea Investment's official MCP examples.
"""

from server import *  # noqa: F401,F403

if __name__ == "__main__":
    from server import main

    main()
