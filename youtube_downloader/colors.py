"""ANSI colour helpers that degrade gracefully on dumb terminals."""

from __future__ import annotations

import os
import sys


class Tcolors:
    """ANSI escape codes, blanked out when the terminal cannot render them."""

    cyan = "\033[96m"
    green = "\033[92m"
    yellow = "\033[93m"
    red = "\033[91m"
    gray = "\033[90m"
    clear = "\033[0m"
    underline = "\033[4m"
    bold = "\033[1m"

    _NAMES = ("cyan", "green", "yellow", "red", "gray", "clear", "underline", "bold")

    @classmethod
    def disable(cls) -> None:
        for name in cls._NAMES:
            setattr(cls, name, "")


def color_supported(stream=None) -> bool:
    """Return True when it is safe to emit ANSI escapes on ``stream``."""
    stream = stream if stream is not None else sys.stdout
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("TERM") == "dumb":
        return False
    try:
        return bool(stream.isatty())
    except (AttributeError, ValueError):
        return False


def autoconfigure(stream=None) -> bool:
    """Disable colours when unsupported. Returns whether colours stay enabled."""
    if color_supported(stream):
        return True
    Tcolors.disable()
    return False
