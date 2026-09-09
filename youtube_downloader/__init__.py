"""A small, tested wrapper around yt-dlp for downloading YouTube videos.

The heavy lifting is done by yt-dlp (https://github.com/yt-dlp/yt-dlp); this
package only builds sensible options, organises the output files and provides
a console and a Tkinter front end.
"""

from youtube_downloader.options import (
    AUDIO_FORMATS,
    QUALITY_CHOICES,
    DownloadOptions,
    build_format_selector,
    build_ydl_opts,
)
from youtube_downloader.result import DownloadResult
from youtube_downloader.urls import is_valid_url, normalize_urls

__all__ = [
    "AUDIO_FORMATS",
    "QUALITY_CHOICES",
    "DownloadOptions",
    "DownloadResult",
    "build_format_selector",
    "build_ydl_opts",
    "is_valid_url",
    "normalize_urls",
]

__version__ = "2.0.0"
