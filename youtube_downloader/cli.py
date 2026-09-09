"""Console front end.

Runs non-interactively when URLs are passed as arguments, and falls back to the
original interactive prompt loop otherwise.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from collections.abc import Sequence

from youtube_downloader import __version__
from youtube_downloader.colors import Tcolors, autoconfigure
from youtube_downloader.downloader import (
    Downloader,
    ensure_destination,
    summarize,
    validate_urls,
    yt_dlp_version,
)
from youtube_downloader.options import (
    AUDIO_FORMATS,
    DEFAULT_AUDIO_FORMAT,
    DEFAULT_SUBTITLE_LANGS,
    DEFAULT_SUBTITLES,
    DEFAULT_VIDEO_QUALITY,
    QUALITY_CHOICES,
    DownloadOptions,
)
from youtube_downloader.result import DownloadResult

EXIT_SUCCESS = 0
EXIT_DOWNLOAD_ERROR = 1
EXIT_USAGE_ERROR = 2
EXIT_INTERRUPTED = 130

_AFFIRMATIVE = {"y", "yes"}
_NEGATIVE = {"n", "no"}


def banner() -> None:
    print(f"{Tcolors.bold}YouTube Downloader{Tcolors.clear}")
    print(f"{Tcolors.gray}yt-dlp {yt_dlp_version()} on Python {sys.version.split()[0]}{Tcolors.clear}")
    print("-----------")


def error(message: str) -> None:
    print(f"{Tcolors.red}Error: {message}{Tcolors.clear}", file=sys.stderr)


def prompt_yes_no(question: str, default: bool) -> bool:
    """Ask a yes/no question.

    The old implementation was ``input(...) == 'y' or DEFAULT_SUBTITLES``, so
    with a default of True the answer was always True and subtitles could never
    be turned off.
    """
    suffix = "Y/n" if default else "y/N"
    while True:
        answer = input(f"{question} ({suffix}): ").strip().lower()
        if not answer:
            return default
        if answer in _AFFIRMATIVE:
            return True
        if answer in _NEGATIVE:
            return False
        print(f"{Tcolors.red}Please answer 'y' or 'n'.{Tcolors.clear}")


def prompt_choice(question: str, choices: Sequence[str], default: str) -> str:
    options = "/".join(choices)
    while True:
        answer = input(f"{question} [{options}] (default: {default}): ").strip().lower()
        if not answer:
            return default
        if answer in choices:
            return answer
        print(f"{Tcolors.red}Please choose one of: {options}{Tcolors.clear}")


def prompt_options() -> DownloadOptions:
    audio_only = prompt_yes_no("Audio only?", False)
    quality = DEFAULT_VIDEO_QUALITY
    subtitles = False
    if not audio_only:
        quality = prompt_choice("Video quality", QUALITY_CHOICES, DEFAULT_VIDEO_QUALITY)
        subtitles = prompt_yes_no("Include subtitles?", DEFAULT_SUBTITLES)
    audio_format = prompt_choice("Audio format", AUDIO_FORMATS, DEFAULT_AUDIO_FORMAT)
    return DownloadOptions(
        video_quality=quality,
        audio_format=audio_format,
        audio_only=audio_only,
        subtitles=subtitles,
    )


def prompt_destination(previous: str | None) -> str:
    while True:
        suffix = f" (default: {previous})" if previous else ""
        raw = input(f"{Tcolors.cyan}Enter file location to save files{suffix}: {Tcolors.clear}").strip()
        candidate = raw or previous or ""
        # Quoted paths from a file manager drag-and-drop are common.
        candidate = candidate.strip("'\"")
        try:
            return ensure_destination(candidate)
        except (NotADirectoryError, OSError) as exc:
            error(str(exc))


def prompt_urls() -> list[str]:
    while True:
        raw = input(f"{Tcolors.cyan}Enter one or more YouTube URLs: {Tcolors.clear}")
        try:
            return validate_urls([raw])
        except ValueError as exc:
            error(str(exc))


def report(results: Sequence[DownloadResult]) -> int:
    for result in results:
        if result.ok:
            print(f"{Tcolors.green}OK{Tcolors.clear}  {result.url}")
        else:
            print(f"{Tcolors.red}FAIL{Tcolors.clear} {result.url}: {result.error}")
    print(summarize(results))
    return EXIT_SUCCESS if all(result.ok for result in results) else EXIT_DOWNLOAD_ERROR


def interactive(args: argparse.Namespace) -> int:
    """Prompt loop.

    Implemented as a loop rather than the old mutual recursion between
    ``run()`` and ``start_again()``, which grew the stack on every download.
    """
    banner()
    destination = args.output
    exit_code = EXIT_SUCCESS
    while True:
        urls = prompt_urls()
        destination = prompt_destination(destination)
        options = prompt_options()
        options.archive = args.archive
        options.overwrites = args.overwrite
        downloader = Downloader(options)
        exit_code = report(downloader.download(urls, destination))
        if not prompt_yes_no(f"{Tcolors.cyan}Download something else?{Tcolors.clear}", False):
            print("\nBye")
            return exit_code


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="youtube-downloader",
        description="Download YouTube videos with yt-dlp and keep thumbnails tidy.",
    )
    parser.add_argument("urls", nargs="*", help="YouTube URLs. Omit to run interactively.")
    parser.add_argument(
        "-o", "--output", default=None, help="Destination directory (default: current directory)."
    )
    parser.add_argument(
        "-q", "--quality", default=DEFAULT_VIDEO_QUALITY, choices=list(QUALITY_CHOICES),
        help="Maximum video height.",
    )
    parser.add_argument(
        "-a", "--audio-format", default=DEFAULT_AUDIO_FORMAT, choices=list(AUDIO_FORMATS),
        help="Audio codec to convert to when using --audio-only.",
    )
    parser.add_argument("--audio-only", action="store_true", help="Download audio only.")
    subs = parser.add_mutually_exclusive_group()
    subs.add_argument(
        "--subtitles", dest="subtitles", action="store_true", default=DEFAULT_SUBTITLES,
        help="Download and embed subtitles (default).",
    )
    subs.add_argument(
        "--no-subtitles", dest="subtitles", action="store_false", help="Skip subtitles."
    )
    parser.add_argument(
        "--sub-langs", default=",".join(DEFAULT_SUBTITLE_LANGS),
        help="Comma-separated subtitle languages.",
    )
    parser.add_argument("--no-thumbnails", dest="thumbnails", action="store_false", default=True,
                        help="Do not download or embed thumbnails.")
    parser.add_argument("--archive", default=None,
                        help="Record downloads in this file and skip anything already listed.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing files.")
    parser.add_argument("--quiet", action="store_true", help="Suppress yt-dlp progress output.")
    parser.add_argument("--no-color", action="store_true", help="Disable coloured output.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.no_color:
        Tcolors.disable()
    else:
        autoconfigure()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(levelname)s %(name)s: %(message)s",
    )

    try:
        if not args.urls:
            return interactive(args)

        options = DownloadOptions(
            video_quality=args.quality,
            audio_format=args.audio_format,
            audio_only=args.audio_only,
            subtitles=args.subtitles,
            subtitle_langs=[lang.strip() for lang in args.sub_langs.split(",")],
            thumbnails=args.thumbnails,
            archive=args.archive,
            overwrites=args.overwrite,
            quiet=args.quiet,
        )
        destination = args.output or os.getcwd()
        return report(Downloader(options).download(args.urls, destination))
    except KeyboardInterrupt:
        # The old handler spun forever in `while True: clear_console()`.
        print("\nInterrupted", file=sys.stderr)
        return EXIT_INTERRUPTED
    except EOFError:
        print("\nInterrupted", file=sys.stderr)
        return EXIT_INTERRUPTED
    except (ValueError, NotADirectoryError) as exc:
        error(str(exc))
        return EXIT_USAGE_ERROR


if __name__ == "__main__":
    sys.exit(main())
