"""Per-URL outcome of a download."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DownloadResult:
    """The outcome of downloading a single URL."""

    url: str
    ok: bool
    error: str | None = None

    @classmethod
    def success(cls, url: str) -> DownloadResult:
        return cls(url=url, ok=True)

    @classmethod
    def failure(cls, url: str, error: str) -> DownloadResult:
        return cls(url=url, ok=False, error=error)
