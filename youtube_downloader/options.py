"""Download options and translation into yt-dlp parameters.

Everything in this module is pure: it turns user choices into a plain
dictionary of yt-dlp options. That keeps the interesting logic testable
without touching the network.
"""

from __future__ import annotations

import os
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

#: Video quality choices offered by both front ends.
QUALITY_CHOICES: Sequence[str] = ("best", "2160p", "1440p", "1080p", "720p", "480p", "360p")

#: Audio codecs FFmpegExtractAudio understands, plus "best" for "leave as-is".
AUDIO_FORMATS: Sequence[str] = ("best", "mp3", "m4a", "opus", "flac", "wav", "vorbis", "aac")

#: Container used when yt-dlp has to merge separate video and audio streams.
MERGE_OUTPUT_FORMAT = "mp4/mkv"

#: Sub-directory (relative to the destination) that thumbnails are written to.
THUMBNAIL_SUBDIR = "thumbnails"

DEFAULT_VIDEO_QUALITY = "best"
DEFAULT_AUDIO_FORMAT = "best"
DEFAULT_SUBTITLES = True
DEFAULT_SUBTITLE_LANGS = ("en",)

#: Containers whose thumbnails ffmpeg can embed. Anything else and we skip the
#: EmbedThumbnail post-processor rather than letting it raise.
_THUMBNAIL_EMBEDDABLE = frozenset({"mp3", "mkv", "mka", "ogg", "opus", "flac", "m4a", "mp4", "m4v", "mov"})


def _height_from_quality(quality: str) -> int | None:
    """Return the pixel height encoded in a quality label, or None for "best"."""
    quality = (quality or "").strip().lower()
    if quality in ("", "best"):
        return None
    digits = quality.rstrip("p")
    if digits.isdigit():
        return int(digits)
    raise ValueError(
        f"Unsupported video quality {quality!r}; expected 'best' or one of "
        + ", ".join(q for q in QUALITY_CHOICES if q != "best")
    )


def build_format_selector(
    quality: str = DEFAULT_VIDEO_QUALITY,
    *,
    audio_only: bool = False,
) -> str:
    """Build a yt-dlp format selector.

    The previous selector was ``bestvideo[ext=mp4]+bestaudio[ext=best]/...``,
    which could never match: ``best`` is not a file extension, and a label like
    ``720p`` is not a format id. Heights are now expressed as a real filter.
    """
    if audio_only:
        return "bestaudio/best"
    height = _height_from_quality(quality)
    if height is None:
        return "bestvideo*+bestaudio/best"
    return f"bestvideo[height<={height}]+bestaudio/best[height<={height}]/best"


@dataclass
class DownloadOptions:
    """User-facing download settings."""

    video_quality: str = DEFAULT_VIDEO_QUALITY
    audio_format: str = DEFAULT_AUDIO_FORMAT
    audio_only: bool = False
    subtitles: bool = DEFAULT_SUBTITLES
    subtitle_langs: list[str] = field(default_factory=lambda: list(DEFAULT_SUBTITLE_LANGS))
    thumbnails: bool = True
    archive: str | None = None
    overwrites: bool = False
    quiet: bool = False

    def __post_init__(self) -> None:
        self.video_quality = (self.video_quality or DEFAULT_VIDEO_QUALITY).strip().lower()
        self.audio_format = (self.audio_format or DEFAULT_AUDIO_FORMAT).strip().lower()
        if self.audio_format not in AUDIO_FORMATS:
            raise ValueError(
                f"Unsupported audio format {self.audio_format!r}; expected one of "
                + ", ".join(AUDIO_FORMATS)
            )
        # Raises early on a bad quality label instead of silently downloading
        # something the user did not ask for.
        _height_from_quality(self.video_quality)
        self.subtitle_langs = [lang for lang in (self.subtitle_langs or []) if lang]
        if self.subtitles and not self.subtitle_langs:
            self.subtitle_langs = list(DEFAULT_SUBTITLE_LANGS)

    @property
    def format_selector(self) -> str:
        return build_format_selector(self.video_quality, audio_only=self.audio_only)

    @property
    def final_ext(self) -> str:
        """Best guess at the container the finished file will use."""
        if self.audio_only:
            return "m4a" if self.audio_format == "best" else self.audio_format
        return "mp4"


def _postprocessors(options: DownloadOptions) -> list[dict[str, Any]]:
    processors: list[dict[str, Any]] = []
    if options.audio_only and options.audio_format != "best":
        processors.append(
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": options.audio_format,
                "preferredquality": "0",
            }
        )
    if options.subtitles and not options.audio_only:
        processors.append({"key": "FFmpegEmbedSubtitle"})
    processors.append({"key": "FFmpegMetadata", "add_metadata": True})
    if options.thumbnails and options.final_ext in _THUMBNAIL_EMBEDDABLE:
        # already_have_thumbnail keeps the image file on disk so it stays in
        # the thumbnails/ directory after being embedded.
        processors.append({"key": "EmbedThumbnail", "already_have_thumbnail": True})
    return processors


def resolve_archive_path(archive: str | None, destination: str) -> str | None:
    """Resolve a download-archive path relative to the destination directory.

    The old code passed a bare ``downloaded_songs.txt``, so the archive was
    written to the current working directory and a download started from a
    different directory silently ignored it.
    """
    if not archive:
        return None
    expanded = os.path.expanduser(archive)
    if os.path.isabs(expanded):
        return os.path.normpath(expanded)
    return os.path.normpath(os.path.join(destination, expanded))


def build_ydl_opts(
    destination: str,
    options: DownloadOptions | None = None,
    *,
    logger: Any = None,
    progress_hooks: Sequence[Any] | None = None,
) -> dict[str, Any]:
    """Translate :class:`DownloadOptions` into yt-dlp parameters."""
    options = options or DownloadOptions()
    destination = os.path.normpath(os.path.expanduser(destination))
    want_subtitles = options.subtitles and not options.audio_only

    ydl_opts: dict[str, Any] = {
        "format": options.format_selector,
        "merge_output_format": MERGE_OUTPUT_FORMAT,
        # A relative outtmpl is required for `paths` to apply; an absolute one
        # makes yt-dlp ignore `paths` entirely.
        "outtmpl": {"default": "%(title)s [%(id)s].%(ext)s"},
        "paths": {"home": destination, "thumbnail": THUMBNAIL_SUBDIR},
        "windowsfilenames": os.name == "nt",
        "overwrites": options.overwrites,
        "quiet": options.quiet,
        "no_warnings": False,
        "noprogress": options.quiet,
        # Surface failures instead of swallowing them: the caller reports them.
        "ignoreerrors": False,
        "writesubtitles": want_subtitles,
        "writeautomaticsub": False,
        "subtitleslangs": list(options.subtitle_langs) if want_subtitles else [],
        "writethumbnail": options.thumbnails,
        "postprocessors": _postprocessors(options),
    }

    if options.audio_only:
        # Lets yt-dlp notice an already-converted file instead of re-fetching it.
        ydl_opts["final_ext"] = options.final_ext

    archive_path = resolve_archive_path(options.archive, destination)
    if archive_path:
        ydl_opts["download_archive"] = archive_path
    if logger is not None:
        # `logger` is the real yt-dlp option; the old `error_logger` key was
        # silently ignored, so nothing was ever logged.
        ydl_opts["logger"] = logger
    if progress_hooks:
        ydl_opts["progress_hooks"] = list(progress_hooks)
    return ydl_opts
