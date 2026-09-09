#!/usr/bin/env python3
"""Backwards-compatible entry point for the graphical front end."""

import sys

try:
    from youtube_downloader.gui import main
except ImportError as exc:  # pragma: no cover - depends on the system Python
    if "tkinter" not in str(exc):
        raise
    sys.exit(
        "Tkinter is not available in this Python installation.\n"
        "Install it (Debian/Ubuntu: sudo apt install python3-tk) or use the\n"
        "console front end instead: python YouMain.py --help"
    )

if __name__ == "__main__":
    sys.exit(main())
