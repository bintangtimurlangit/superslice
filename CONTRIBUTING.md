# Contributing to SuperSlice

Thank you for your interest in contributing to SuperSlice!

## Reporting Issues

If you find a bug or have a feature request, please open an issue on GitHub with:

- Clear description of the problem or feature
- Steps to reproduce (for bugs)
- Expected vs actual behavior
- Your environment (OS, Docker version, etc.)

## Development Setup

1. Fork the repository
2. Clone your fork
3. Create a feature branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Test locally with Docker
6. Commit with clear messages
7. Push to your fork
8. Open a Pull Request

## Commit messages

This project follows
[Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/): start
each commit with a type, e.g. `feat:`, `fix:`, `docs:`, `refactor:`, `chore:`,
`test:`. See [RELEASING.md](RELEASING.md) for how these map to versions.

## Code Style

- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Keep functions focused and modular

## Testing

Run the unit + API test suite (no slicer binary required — PrusaSlicer is
mocked):

```bash
pip install -r requirements-dev.txt
pytest
```

Before submitting a PR:

- `pytest` passes
- The Docker image builds: `docker compose build`
- The API endpoints work (`docker compose up`, then exercise `/slice`)
- Update `CHANGELOG.md` (under `Unreleased`) and docs if behaviour changed

## Pull Request Process

1. Update the README.md if needed
2. Update CHANGELOG.md with your changes
3. Ensure Docker image builds successfully
4. Wait for review and address feedback

## Questions?

Feel free to open an issue for any questions about contributing.
