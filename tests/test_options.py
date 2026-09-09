import os

import pytest

from youtube_downloader.options import (
    AUDIO_FORMATS,
    QUALITY_CHOICES,
    THUMBNAIL_SUBDIR,
    DownloadOptions,
    build_format_selector,
    build_ydl_opts,
    resolve_archive_path,
)


def test_best_quality_selector():
    assert build_format_selector("best") == "bestvideo*+bestaudio/best"


def test_height_limited_selector_uses_a_real_filter():
    selector = build_format_selector("720p")
    assert "height<=720" in selector
    # The old selector interpolated the label directly, producing "/720p".
    assert "720p" not in selector


def test_audio_only_selector_ignores_video_quality():
    assert build_format_selector("1080p", audio_only=True) == "bestaudio/best"


@pytest.mark.parametrize("quality", [q for q in QUALITY_CHOICES if q != "best"])
def test_every_advertised_quality_builds(quality):
    assert f"height<={quality.rstrip('p')}" in build_format_selector(quality)


def test_unknown_quality_is_rejected():
    with pytest.raises(ValueError):
        build_format_selector("ultra")


def test_unknown_audio_format_is_rejected():
    with pytest.raises(ValueError):
        DownloadOptions(audio_format="ogg-vorbis-42")


@pytest.mark.parametrize("audio_format", AUDIO_FORMATS)
def test_every_advertised_audio_format_is_accepted(audio_format):
    assert DownloadOptions(audio_format=audio_format).audio_format == audio_format


def test_subtitles_can_actually_be_disabled(tmp_path):
    # The old prompt logic could never produce False.
    opts = build_ydl_opts(str(tmp_path), DownloadOptions(subtitles=False))
    assert opts["writesubtitles"] is False
    assert opts["subtitleslangs"] == []
    assert all(pp["key"] != "FFmpegEmbedSubtitle" for pp in opts["postprocessors"])


def test_subtitles_enabled_adds_the_embed_postprocessor(tmp_path):
    opts = build_ydl_opts(str(tmp_path), DownloadOptions(subtitles=True))
    assert opts["writesubtitles"] is True
    assert opts["subtitleslangs"] == ["en"]
    assert any(pp["key"] == "FFmpegEmbedSubtitle" for pp in opts["postprocessors"])


def test_thumbnails_are_written_into_their_own_directory(tmp_path):
    opts = build_ydl_opts(str(tmp_path), DownloadOptions())
    assert opts["paths"]["home"] == os.path.normpath(str(tmp_path))
    assert opts["paths"]["thumbnail"] == THUMBNAIL_SUBDIR
    # `paths` is ignored when outtmpl is absolute, so it must stay relative.
    assert not os.path.isabs(opts["outtmpl"]["default"])


def test_uses_the_real_logger_option(tmp_path):
    sentinel = object()
    opts = build_ydl_opts(str(tmp_path), DownloadOptions(), logger=sentinel)
    # "error_logger" is not a yt-dlp option and was silently ignored.
    assert opts["logger"] is sentinel
    assert "error_logger" not in opts


def test_errors_are_not_ignored(tmp_path):
    assert build_ydl_opts(str(tmp_path), DownloadOptions())["ignoreerrors"] is False


def test_no_download_archive_unless_requested(tmp_path):
    assert "download_archive" not in build_ydl_opts(str(tmp_path), DownloadOptions())


def test_relative_archive_resolves_against_the_destination(tmp_path):
    resolved = resolve_archive_path("seen.txt", str(tmp_path))
    assert resolved == os.path.normpath(os.path.join(str(tmp_path), "seen.txt"))


def test_absolute_archive_is_left_alone(tmp_path):
    absolute = str(tmp_path / "elsewhere.txt")
    assert resolve_archive_path(absolute, "/somewhere") == os.path.normpath(absolute)


def test_archive_reaches_ydl_opts(tmp_path):
    opts = build_ydl_opts(str(tmp_path), DownloadOptions(archive="seen.txt"))
    assert opts["download_archive"].startswith(os.path.normpath(str(tmp_path)))


def test_audio_only_extracts_audio_and_skips_subtitles(tmp_path):
    options = DownloadOptions(audio_only=True, audio_format="mp3", subtitles=True)
    opts = build_ydl_opts(str(tmp_path), options)
    keys = [pp["key"] for pp in opts["postprocessors"]]
    assert "FFmpegExtractAudio" in keys
    assert "FFmpegEmbedSubtitle" not in keys
    assert opts["writesubtitles"] is False
    assert opts["final_ext"] == "mp3"


def test_audio_only_best_does_not_transcode(tmp_path):
    opts = build_ydl_opts(str(tmp_path), DownloadOptions(audio_only=True, audio_format="best"))
    assert all(pp["key"] != "FFmpegExtractAudio" for pp in opts["postprocessors"])


def test_thumbnail_embedding_skipped_for_unsupported_container(tmp_path):
    options = DownloadOptions(audio_only=True, audio_format="wav")
    opts = build_ydl_opts(str(tmp_path), options)
    assert all(pp["key"] != "EmbedThumbnail" for pp in opts["postprocessors"])


def test_thumbnails_can_be_turned_off(tmp_path):
    opts = build_ydl_opts(str(tmp_path), DownloadOptions(thumbnails=False))
    assert opts["writethumbnail"] is False
    assert all(pp["key"] != "EmbedThumbnail" for pp in opts["postprocessors"])
