import builtins

import pytest

from youtube_downloader import cli
from youtube_downloader.result import DownloadResult

URL = "https://youtu.be/dQw4w9WgXcQ"


@pytest.fixture(autouse=True)
def _no_color(monkeypatch):
    monkeypatch.setattr(cli.Tcolors, "clear", "")
    yield


def answers(monkeypatch, *responses):
    queued = list(responses)
    monkeypatch.setattr(builtins, "input", lambda *_: queued.pop(0))


def test_prompt_yes_no_honours_an_explicit_no(monkeypatch):
    answers(monkeypatch, "n")
    # The old logic ORed the answer with the default and always returned True.
    assert cli.prompt_yes_no("Include subtitles?", True) is False


def test_prompt_yes_no_accepts_a_blank_default(monkeypatch):
    answers(monkeypatch, "")
    assert cli.prompt_yes_no("Include subtitles?", True) is True


def test_prompt_yes_no_reprompts_on_junk(monkeypatch):
    answers(monkeypatch, "maybe", "yes")
    assert cli.prompt_yes_no("Include subtitles?", False) is True


def test_prompt_choice_reprompts_until_valid(monkeypatch):
    answers(monkeypatch, "4k", "720p")
    assert cli.prompt_choice("Quality", ("best", "720p"), "best") == "720p"


def test_report_returns_zero_when_everything_succeeded(capsys):
    assert cli.report([DownloadResult.success(URL)]) == cli.EXIT_SUCCESS
    assert "1 succeeded" in capsys.readouterr().out


def test_report_returns_nonzero_on_failure(capsys):
    results = [DownloadResult.success(URL), DownloadResult.failure(URL, "boom")]
    assert cli.report(results) == cli.EXIT_DOWNLOAD_ERROR
    assert "boom" in capsys.readouterr().out


def test_invalid_url_exits_with_a_usage_code(capsys):
    assert cli.main(["https://vimeo.com/1", "-o", "."]) == cli.EXIT_USAGE_ERROR
    assert "vimeo" in capsys.readouterr().err


def test_missing_directory_exits_with_a_usage_code(tmp_path, capsys):
    assert cli.main([URL, "-o", str(tmp_path / "nope")]) == cli.EXIT_USAGE_ERROR
    assert "Not a directory" in capsys.readouterr().err


def test_bad_quality_is_rejected_by_argparse(capsys):
    with pytest.raises(SystemExit):
        cli.main([URL, "-q", "ultra"])


def test_keyboard_interrupt_exits_cleanly(monkeypatch, capsys):
    def boom(*_args, **_kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr(cli, "interactive", boom)
    # The old handler looped forever clearing the console instead of exiting.
    assert cli.main([]) == cli.EXIT_INTERRUPTED


def test_arguments_become_download_options(monkeypatch, tmp_path):
    captured = {}

    class FakeDownloader:
        def __init__(self, options, **_kwargs):
            captured["options"] = options

        def download(self, urls, destination):
            captured["urls"] = urls
            captured["destination"] = destination
            return [DownloadResult.success(urls[0])]

    monkeypatch.setattr(cli, "Downloader", FakeDownloader)
    code = cli.main(
        [URL, "-o", str(tmp_path), "-q", "1080p", "--no-subtitles", "--audio-only", "-a", "mp3"]
    )
    assert code == cli.EXIT_SUCCESS
    options = captured["options"]
    assert options.video_quality == "1080p"
    assert options.audio_format == "mp3"
    assert options.audio_only is True
    assert options.subtitles is False
    assert captured["urls"] == [URL]
