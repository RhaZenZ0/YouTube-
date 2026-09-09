# YouTube Downloader

A small, tested front end for [yt-dlp](https://github.com/yt-dlp/yt-dlp). It
downloads YouTube videos, embeds metadata, subtitles and thumbnails, and keeps
thumbnail images in their own folder.

## Requirements

- Python 3.10 or later
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) (installed via `requirements.txt`)
- **ffmpeg** — a system binary, not a Python package. It is required for
  merging video and audio, embedding subtitles and thumbnails, and extracting
  audio.

  | Platform | Command |
  | --- | --- |
  | Debian/Ubuntu | `sudo apt install ffmpeg` |
  | macOS | `brew install ffmpeg` |
  | Windows | `winget install Gyan.FFmpeg` |

- For the graphical front end, Tkinter (`sudo apt install python3-tk` on
  Debian/Ubuntu; bundled with the official installers elsewhere).

## Getting started

```bash
git clone https://github.com/RhaZenZ0/YouTube-.git
cd YouTube-
pip install -r requirements.txt
```

## Usage

Pass URLs on the command line:

```bash
python YouMain.py "https://youtu.be/VIDEO_ID" -o ~/Videos
python YouMain.py URL1 URL2 -o ~/Videos --quality 1080p --no-subtitles
python YouMain.py URL --audio-only --audio-format mp3 -o ~/Music
```

Run it without URLs for the interactive prompt:

```bash
python YouMain.py
```

Or start the graphical front end:

```bash
python GUI.py
```

Installing the package also provides `youtube-downloader` and
`youtube-downloader-gui` commands:

```bash
pip install .
youtube-downloader --help
```

### Options

| Flag | Description |
| --- | --- |
| `-o`, `--output` | Destination directory (default: current directory). |
| `-q`, `--quality` | `best`, `2160p`, `1440p`, `1080p`, `720p`, `480p`, `360p`. |
| `--audio-only` | Download audio only. |
| `-a`, `--audio-format` | `best`, `mp3`, `m4a`, `opus`, `flac`, `wav`, `vorbis`, `aac`. |
| `--subtitles` / `--no-subtitles` | Download and embed subtitles (on by default). |
| `--sub-langs` | Comma-separated subtitle languages (default: `en`). |
| `--no-thumbnails` | Skip downloading and embedding thumbnails. |
| `--archive PATH` | Record downloads and skip anything already listed. |
| `--overwrite` | Overwrite existing files. |
| `--quiet`, `-v`, `--no-color` | Output control. |

### Exit codes

| Code | Meaning |
| --- | --- |
| 0 | Every download succeeded. |
| 1 | At least one download failed. |
| 2 | Invalid arguments, URL or destination directory. |
| 130 | Interrupted with Ctrl-C. |

## Output layout

```
<destination>/
├── Video Title [VIDEO_ID].mp4
└── thumbnails/
    └── Video Title [VIDEO_ID].webp
```

Thumbnails are written straight into `thumbnails/` by yt-dlp. Files are named
with the video id so two videos sharing a title do not overwrite each other.

## Project layout

```
youtube_downloader/
├── cli.py          console front end
├── gui.py          Tkinter front end
├── downloader.py   download orchestration
├── options.py      user options -> yt-dlp parameters
├── urls.py         URL validation
├── result.py       per-URL outcome
└── colors.py       terminal colours
tests/              pytest suite
YouMain.py          entry point for the console front end
GUI.py              entry point for the graphical front end
```

## Development

```bash
pip install -r requirements-dev.txt
pytest
ruff check .
```

Tests do not touch the network: the yt-dlp object is injected, so the option
building and error handling are exercised directly.

## Contributing

Contributions are welcome. See the [contribution guidelines](CONTRIBUTING.md).

## License

MIT — see [LICENSE.md](LICENSE.md).

## Acknowledgments

Built on [yt-dlp](https://github.com/yt-dlp/yt-dlp), which does all the real work.
