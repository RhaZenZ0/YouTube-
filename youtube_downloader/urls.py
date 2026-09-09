"""URL validation helpers."""

from __future__ import annotations

import re
from collections.abc import Iterable

#: Hosts that yt-dlp resolves as YouTube.
_YOUTUBE_HOST = re.compile(
    r"^(?:(?:www|m|music)\.)?(?:youtube\.com|youtube-nocookie\.com|youtu\.be)$",
    re.IGNORECASE,
)

_URL = re.compile(r"^(?P<scheme>https?://)?(?P<host>[^/?#]+)(?P<rest>[/?#].*)?$")


def is_valid_url(url: str) -> bool:
    """Return True for URLs that point at a YouTube host.

    The check is deliberately host-based: the old prefix match accepted
    ``youtube.com.example.com`` and rejected ``music.youtube.com``.
    """
    if not isinstance(url, str):
        return False
    match = _URL.match(url.strip())
    if match is None:
        return False
    host = match.group("host").split("@")[-1].split(":")[0]
    return bool(_YOUTUBE_HOST.match(host))


def normalize_urls(urls: Iterable[str]) -> list[str]:
    """Split, strip and de-duplicate a batch of URLs, preserving order."""
    seen = set()
    result = []
    for raw in urls:
        for candidate in str(raw).replace(",", " ").split():
            candidate = candidate.strip()
            if candidate and candidate not in seen:
                seen.add(candidate)
                result.append(candidate)
    return result
