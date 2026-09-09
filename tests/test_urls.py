import pytest

from youtube_downloader.urls import is_valid_url, normalize_urls


@pytest.mark.parametrize(
    "url",
    [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "http://youtube.com/watch?v=abc",
        "https://youtu.be/dQw4w9WgXcQ",
        "youtube.com/watch?v=abc",
        "https://music.youtube.com/watch?v=abc",
        "https://m.youtube.com/watch?v=abc",
        "https://www.youtube-nocookie.com/embed/abc",
    ],
)
def test_accepts_youtube_urls(url):
    assert is_valid_url(url)


@pytest.mark.parametrize(
    "url",
    [
        "",
        "   ",
        "https://vimeo.com/12345",
        "not a url",
        # The old prefix-anchored regex accepted these look-alike hosts.
        "https://youtube.com.evil.example/watch?v=abc",
        "https://notyoutube.com/watch?v=abc",
    ],
)
def test_rejects_non_youtube_urls(url):
    assert not is_valid_url(url)


def test_music_youtube_was_rejected_by_the_old_pattern():
    # Regression guard: the previous pattern required an optional "www." only.
    assert is_valid_url("https://music.youtube.com/watch?v=abc")


def test_normalize_splits_dedupes_and_preserves_order():
    raw = ["https://youtu.be/a, https://youtu.be/b", " https://youtu.be/a "]
    assert normalize_urls(raw) == ["https://youtu.be/a", "https://youtu.be/b"]


def test_normalize_drops_empty_entries():
    assert normalize_urls(["", "  ", ","]) == []
