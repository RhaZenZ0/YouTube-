# Contributing Guidelines

Thank you for considering contributing to this project! Whether you're fixing a bug, improving an existing feature, or adding a new feature, your contribution is welcome.

## Getting Started

1. Fork the repository and clone it locally.
   
   ```bash
   git clone https://github.com/RhaZenZ0/YouTube-.git
   ```
   
2. Create a new branch for your contribution.

   ```bash
   git checkout -b feature/your-feature
   ```

3. Make your changes and test them thoroughly.

4. Commit your changes with a clear and descriptive commit message.

   ```bash
   git commit -m "Add your descriptive commit message here"
   ```
   
5. Push your changes to your fork.

   ```bash
   git push origin feature/your-feature
   ```
   
6. Open a pull request.

## Code Style

The project is linted with [ruff](https://docs.astral.sh/ruff/); its
configuration lives in `pyproject.toml`. Run `ruff check .` before pushing.

## Testing

Install the development dependencies and run the checks before opening a pull
request. CI runs the same two commands on Python 3.9, 3.11 and 3.13.

```bash
pip install -r requirements-dev.txt
pytest
ruff check .
```

Tests must not hit the network. `Downloader` takes a `ydl_factory` argument so
the yt-dlp object can be replaced with a stub; see `tests/test_downloader.py`.

If you're adding a feature, add tests for it. If you're fixing a bug, add a test
that fails without the fix.

## Reporting Issues

If you find any issues or have suggestions for improvement, please open an issue on the Issues page.

## Code of Conduct

Please adhere to the project's Code of Conduct.

## License

By contributing to this project, you agree that your contributions will be licensed under the project's MIT License.

Thank you for your contribution!