#!/usr/bin/env python3
"""Backwards-compatible entry point.

The implementation now lives in the ``youtube_downloader`` package; this file
keeps ``python YouMain.py`` working as documented in the README.
"""

import sys

from youtube_downloader.cli import main

if __name__ == "__main__":
    sys.exit(main())
