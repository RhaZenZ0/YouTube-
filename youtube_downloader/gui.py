"""Tkinter front end."""

from __future__ import annotations

import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from youtube_downloader.downloader import Downloader, summarize
from youtube_downloader.options import (
    AUDIO_FORMATS,
    DEFAULT_AUDIO_FORMAT,
    DEFAULT_VIDEO_QUALITY,
    QUALITY_CHOICES,
    DownloadOptions,
)
from youtube_downloader.result import DownloadResult
from youtube_downloader.urls import normalize_urls

_POLL_MS = 100


class YouTubeDownloaderGUI:
    """A small Tk front end around :class:`Downloader`."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("YouTube Downloader")
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.video_url_var = tk.StringVar()
        self.file_location_var = tk.StringVar()
        self.quality_var = tk.StringVar(value=DEFAULT_VIDEO_QUALITY)
        self.audio_format_var = tk.StringVar(value=DEFAULT_AUDIO_FORMAT)
        self.audio_only_var = tk.BooleanVar(value=False)
        self.subtitles_var = tk.BooleanVar(value=True)
        self.status_var = tk.StringVar(value="Ready")
        self.progress_var = tk.DoubleVar(value=0.0)

        # Worker threads must not touch Tk; they post messages here instead.
        self._events: queue.Queue[tuple] = queue.Queue()
        self._worker: threading.Thread | None = None

        self._create_widgets()
        self.root.after(_POLL_MS, self._drain_events)

    # ------------------------------------------------------------------ UI --
    def _create_widgets(self) -> None:
        frame = ttk.Frame(self.root, padding=10)
        frame.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)

        ttk.Label(frame, text="YouTube URL(s):").grid(row=0, column=0, sticky="w", pady=4)
        ttk.Entry(frame, textvariable=self.video_url_var, width=48).grid(
            row=0, column=1, columnspan=2, sticky="ew", pady=4
        )

        ttk.Label(frame, text="Save files to:").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Entry(frame, textvariable=self.file_location_var, width=38).grid(
            row=1, column=1, sticky="ew", pady=4
        )
        ttk.Button(frame, text="Browse", command=self.browse_file_location).grid(
            row=1, column=2, sticky="ew", padx=(6, 0), pady=4
        )

        options = ttk.LabelFrame(frame, text="Download options", padding=8)
        options.grid(row=2, column=0, columnspan=3, sticky="ew", pady=8)
        options.columnconfigure(1, weight=1)

        ttk.Label(options, text="Video quality:").grid(row=0, column=0, sticky="w", pady=3)
        self.quality_menu = ttk.Combobox(
            options, textvariable=self.quality_var, values=list(QUALITY_CHOICES), state="readonly"
        )
        self.quality_menu.grid(row=0, column=1, sticky="ew", pady=3)

        ttk.Label(options, text="Audio format:").grid(row=1, column=0, sticky="w", pady=3)
        ttk.Combobox(
            options, textvariable=self.audio_format_var, values=list(AUDIO_FORMATS), state="readonly"
        ).grid(row=1, column=1, sticky="ew", pady=3)

        ttk.Checkbutton(
            options, text="Audio only", variable=self.audio_only_var, command=self._sync_audio_only
        ).grid(row=2, column=0, sticky="w", pady=3)
        self.subtitles_check = ttk.Checkbutton(
            options, text="Include subtitles", variable=self.subtitles_var
        )
        self.subtitles_check.grid(row=2, column=1, sticky="w", pady=3)

        # Held as an attribute: the old code looked the widget up by the Tk path
        # ".!button", which resolved to the Browse button instead.
        self.download_button = ttk.Button(frame, text="Download", command=self.download)
        self.download_button.grid(row=3, column=0, columnspan=3, pady=6)

        self.progress_bar = ttk.Progressbar(
            frame, variable=self.progress_var, maximum=100.0, mode="determinate"
        )
        self.progress_bar.grid(row=4, column=0, columnspan=3, sticky="ew", pady=4)

        ttk.Label(frame, textvariable=self.status_var, anchor="w").grid(
            row=5, column=0, columnspan=3, sticky="ew"
        )

    def _sync_audio_only(self) -> None:
        audio_only = self.audio_only_var.get()
        state = "disabled" if audio_only else "readonly"
        self.quality_menu.configure(state=state)
        self.subtitles_check.configure(state="disabled" if audio_only else "normal")

    def browse_file_location(self) -> None:
        location = filedialog.askdirectory()
        if location:
            self.file_location_var.set(location)

    # ------------------------------------------------------------- actions --
    def _collect_options(self) -> DownloadOptions:
        return DownloadOptions(
            video_quality=self.quality_var.get(),
            audio_format=self.audio_format_var.get(),
            audio_only=self.audio_only_var.get(),
            subtitles=self.subtitles_var.get() and not self.audio_only_var.get(),
            quiet=True,
        )

    def download(self) -> None:
        if self._worker is not None and self._worker.is_alive():
            return
        urls = normalize_urls([self.video_url_var.get()])
        destination = self.file_location_var.get()
        try:
            options = self._collect_options()
        except ValueError as exc:
            messagebox.showerror("Error", str(exc))
            return

        self.download_button.configure(state="disabled")
        self.progress_var.set(0.0)
        self.status_var.set("Starting...")

        self._worker = threading.Thread(
            target=self._run_download, args=(urls, destination, options), daemon=True
        )
        self._worker.start()

    def _run_download(self, urls: list[str], destination: str, options: DownloadOptions) -> None:
        """Runs off the Tk thread; results are delivered through the queue."""
        try:
            downloader = Downloader(options, progress_hooks=[self._progress_hook])
            results = downloader.download(urls, destination)
            self._events.put(("done", results))
        except (ValueError, NotADirectoryError, OSError) as exc:
            self._events.put(("error", str(exc)))
        except Exception as exc:  # noqa: BLE001 - last resort, reported to the user
            self._events.put(("error", f"Unexpected error: {exc}"))

    def _progress_hook(self, status: dict) -> None:
        if status.get("status") == "downloading":
            total = status.get("total_bytes") or status.get("total_bytes_estimate")
            done = status.get("downloaded_bytes") or 0
            percent = (done / total * 100.0) if total else None
            self._events.put(("progress", percent, status.get("_speed_str") or ""))
        elif status.get("status") == "finished":
            self._events.put(("progress", 100.0, "post-processing"))

    # -------------------------------------------------------- Tk main loop --
    def _drain_events(self) -> None:
        """Applies worker updates on the Tk thread. Tk is not thread-safe."""
        try:
            while True:
                event = self._events.get_nowait()
                self._handle_event(event)
        except queue.Empty:
            pass
        finally:
            self.root.after(_POLL_MS, self._drain_events)

    def _handle_event(self, event: tuple) -> None:
        kind = event[0]
        if kind == "progress":
            _, percent, note = event
            if percent is None:
                self.progress_bar.configure(mode="indeterminate")
            else:
                self.progress_bar.configure(mode="determinate")
                self.progress_var.set(percent)
            self.status_var.set(f"Downloading... {note}".strip())
        elif kind == "done":
            results: list[DownloadResult] = event[1]
            self._finish()
            self.status_var.set(summarize(results))
            failures = [result for result in results if not result.ok]
            if failures:
                detail = "\n".join(f"{r.url}: {r.error}" for r in failures)
                messagebox.showerror("Download failed", detail)
            else:
                messagebox.showinfo("Success", "Download completed successfully.")
        elif kind == "error":
            self._finish()
            self.status_var.set("Failed")
            messagebox.showerror("Error", event[1])

    def _finish(self) -> None:
        self.download_button.configure(state="normal")
        self.progress_bar.configure(mode="determinate")
        self.progress_var.set(0.0)

    def on_close(self) -> None:
        if self._worker is not None and self._worker.is_alive():
            if not messagebox.askokcancel("Exit", "A download is running. Quit anyway?"):
                return
        elif not messagebox.askokcancel("Exit", "Are you sure you want to exit?"):
            return
        self.root.destroy()


def main() -> int:
    root = tk.Tk()
    YouTubeDownloaderGUI(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
