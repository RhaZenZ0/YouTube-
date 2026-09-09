"""Makes the repository root importable so `pytest` finds `youtube_downloader`.

Without a conftest.py at the root, pytest's default import mode only adds the
`tests/` directory to sys.path and the package import fails.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
