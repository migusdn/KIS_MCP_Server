"""Backward-compatible entrypoint for the KIS MCP server.

The primary implementation lives in :mod:`server`; this module remains
for clients that still invoke `main.py`.
"""

from server import *  # noqa: F401,F403

if __name__ == "__main__":
    from server import main

    main()
