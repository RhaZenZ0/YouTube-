"""GUI tests.

Importing the module only needs tkinter to be installed; it does not need a
display. Anything that constructs a Tk root is skipped without one.
"""

import importlib
import importlib.util
import py_compile

import pytest

HAS_TKINTER = importlib.util.find_spec("tkinter") is not None


def test_gui_module_compiles():
    py_compile.compile("youtube_downloader/gui.py", doraise=True)


@pytest.mark.skipif(not HAS_TKINTER, reason="tkinter is not installed")
def test_gui_module_imports():
    gui = importlib.import_module("youtube_downloader.gui")
    assert hasattr(gui, "YouTubeDownloaderGUI")


@pytest.mark.skipif(not HAS_TKINTER, reason="tkinter is not installed")
def test_download_button_is_held_as_an_attribute():
    # The old code looked the button up as ".!button", which was Browse.
    gui = importlib.import_module("youtube_downloader.gui")
    source = importlib.import_module("inspect").getsource(gui)
    assert "self.download_button" in source
    assert "nametowidget" not in source
