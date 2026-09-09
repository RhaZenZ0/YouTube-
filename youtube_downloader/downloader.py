"""Download orchestration on top of the yt-dlp library.

See https://github.com/yt-dlp/yt-dlp for the library this wraps.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Callable, Iterable, Sequence
from typing import Any

import yt_dlp

from youtube_downloader.options import THUMBNAIL_SUBDIR, DownloadOptions, build_ydl_opts
from youtube_downloader.result import DownloadResult
from youtube_downloader.urls import is_valid_url, normalize_urls

logger = logging.getLogger(__name__)

ProgressHook = Callable[[dict], None]


def yt_dlp_version() -> str:
    """Version of the yt-dlp library that is actually imported."""
    return yt_dlp.version.__version__


def ensure_destination(destination: str, *, create_thumbnail_dir: bool = True) -> str:
    """Validate the destination directory and prepare the thumbnails folder."""
    if not destination or not str(destination).strip():
        # normpath("") is ".", which would silently target the working directory.
        raise NotADirectoryError("No destination directory given")
    resolved = os.path.normpath(os.path.expanduser(str(destination).strip()))
    if not os.path.isdir(resolved):
        raise NotADirectoryError(f"Not a directory: {destination!r}")
    if create_thumbnail_dir:
        os.makedirs(os.path.join(resolved, THUMBNAIL_SUBDIR), exist_ok=True)
    return resolved


def validate_urls(urls: Iterable[str]) -> list[str]:
    """Normalise a batch of URLs, raising on the first invalid entry."""
    candidates = normalize_urls(urls)
    if not candidates:
        raise ValueError("No URLs given")
    invalid = [url for url in candidates if not is_valid_url(url)]
    if invalid:
        raise ValueError("Not a YouTube URL: " + ", ".join(invalid))
    return candidates


class Downloader:
    """Downloads one or more URLs into a destination directory."""

    def __init__(
        self,
        options: DownloadOptions | None = None,
        *,
        progress_hooks: Sequence[ProgressHook] | None = None,
        ydl_factory: Callable[[dict], Any] | None = None,
    ) -> None:
        self.options = options or DownloadOptions()
        self.progress_hooks = list(progress_hooks or [])
        # Injectable so tests can exercise the flow without touching the network.
        self._ydl_factory = ydl_factory or yt_dlp.YoutubeDL

    def build_opts(self, destination: str) -> dict:
        return build_ydl_opts(
            destination,
            self.options,
            logger=logger,
            progress_hooks=self.progress_hooks,
        )

    def download_one(self, url: str, destination: str) -> DownloadResult:
        """Download a single URL, converting failures into a result object."""
        opts = self.build_opts(destination)
        try:
            with self._ydl_factory(opts) as ydl:
                retcode = ydl.download([url])
        except yt_dlp.utils.DownloadError as error:
            logger.error("Download failed for %s: %s", url, error)
            return DownloadResult.failure(url, str(error))
        except OSError as error:
            logger.error("Filesystem error for %s: %s", url, error)
            return DownloadResult.failure(url, str(error))
        if retcode:
            # yt-dlp reports a non-zero code for problems it chose not to raise.
            return DownloadResult.failure(url, f"yt-dlp exited with code {retcode}")
        return DownloadResult.success(url)

    def download(self, urls: Iterable[str], destination: str) -> list[DownloadResult]:
        """Download every URL in order and return one result per URL."""
        candidates = validate_urls(urls)
        resolved = ensure_destination(destination)
        return [self.download_one(url, resolved) for url in candidates]


def summarize(results: Sequence[DownloadResult]) -> str:
    """Human-readable one-line summary of a batch."""
    ok = sum(1 for result in results if result.ok)
    failed = len(results) - ok
    if failed:
        return f"{ok} succeeded, {failed} failed"
    return f"{ok} succeeded"
