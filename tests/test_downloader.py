import os

import pytest
import yt_dlp

from youtube_downloader.downloader import (
    Downloader,
    ensure_destination,
    summarize,
    validate_urls,
    yt_dlp_version,
)
from youtube_downloader.options import THUMBNAIL_SUBDIR, DownloadOptions
from youtube_downloader.result import DownloadResult

URL = "https://youtu.be/dQw4w9WgXcQ"
OTHER = "https://youtu.be/oHg5SJYRHA0"


class FakeYDL:
    """Stands in for yt_dlp.YoutubeDL so no network access is needed."""

    def __init__(self, opts, retcode=0, raises=None):
        self.opts = opts
        self.retcode = retcode
        self.raises = raises
        self.downloaded = []
        self.closed = False

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        self.closed = True
        return False

    def download(self, urls):
        if self.raises is not None:
            raise self.raises
        self.downloaded.extend(urls)
        return self.retcode


def factory(retcode=0, raises=None, sink=None):
    def make(opts):
        instance = FakeYDL(opts, retcode=retcode, raises=raises)
        if sink is not None:
            sink.append(instance)
        return instance

    return make


def test_reports_the_imported_library_version():
    assert yt_dlp_version() == yt_dlp.version.__version__


def test_ensure_destination_creates_the_thumbnails_folder(tmp_path):
    resolved = ensure_destination(str(tmp_path))
    assert os.path.isdir(os.path.join(resolved, THUMBNAIL_SUBDIR))


def test_ensure_destination_rejects_a_missing_directory(tmp_path):
    with pytest.raises(NotADirectoryError):
        ensure_destination(str(tmp_path / "nope"))


def test_ensure_destination_rejects_an_empty_path():
    with pytest.raises(NotADirectoryError):
        ensure_destination("")


def test_validate_urls_rejects_an_empty_batch():
    with pytest.raises(ValueError):
        validate_urls([])


def test_validate_urls_names_the_bad_entry():
    with pytest.raises(ValueError, match="vimeo"):
        validate_urls([URL, "https://vimeo.com/1"])


def test_successful_download_reports_success(tmp_path):
    sink = []
    downloader = Downloader(DownloadOptions(), ydl_factory=factory(sink=sink))
    results = downloader.download([URL], str(tmp_path))
    assert results == [DownloadResult.success(URL)]
    assert sink[0].downloaded == [URL]
    assert sink[0].closed


def test_download_error_is_reported_not_swallowed(tmp_path):
    error = yt_dlp.utils.DownloadError("video unavailable")
    downloader = Downloader(DownloadOptions(), ydl_factory=factory(raises=error))
    (result,) = downloader.download([URL], str(tmp_path))
    assert not result.ok
    assert "video unavailable" in result.error


def test_nonzero_retcode_is_a_failure(tmp_path):
    downloader = Downloader(DownloadOptions(), ydl_factory=factory(retcode=1))
    (result,) = downloader.download([URL], str(tmp_path))
    assert not result.ok
    assert "code 1" in result.error


def test_os_error_is_reported(tmp_path):
    downloader = Downloader(
        DownloadOptions(), ydl_factory=factory(raises=PermissionError("read-only"))
    )
    (result,) = downloader.download([URL], str(tmp_path))
    assert not result.ok
    assert "read-only" in result.error


def test_each_url_gets_its_own_result(tmp_path):
    downloader = Downloader(DownloadOptions(), ydl_factory=factory())
    results = downloader.download([f"{URL}, {OTHER}"], str(tmp_path))
    assert [r.url for r in results] == [URL, OTHER]
    assert all(r.ok for r in results)


def test_progress_hooks_are_passed_through(tmp_path):
    sink = []
    hook = lambda status: None  # noqa: E731
    downloader = Downloader(DownloadOptions(), progress_hooks=[hook], ydl_factory=factory(sink=sink))
    downloader.download([URL], str(tmp_path))
    assert sink[0].opts["progress_hooks"] == [hook]


def test_summarize_counts_failures():
    results = [DownloadResult.success(URL), DownloadResult.failure(OTHER, "boom")]
    assert summarize(results) == "1 succeeded, 1 failed"


def test_summarize_omits_failures_when_there_are_none():
    assert summarize([DownloadResult.success(URL)]) == "1 succeeded"
