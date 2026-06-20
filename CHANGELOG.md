# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- **Self-owned Docker image.** Replaced the third-party
  `mikeah/prusaslicer-novnc` base image with a multi-stage build that downloads,
  checksum-verifies, and extracts the official PrusaSlicer 2.8.1 AppImage. No
  external base image dependency, no bundled GUI/noVNC stack.
- Container now runs as an unprivileged `app` user instead of root.
- `docker-compose.yml`: dropped the obsolete `version` key and added a
  healthcheck.

### Added

- `pytest` unit + API test suite under `tests/` and `requirements-dev.txt`.
- In-depth documentation under `docs/` (architecture, slicer rationale,
  accuracy, troubleshooting) plus a project `ROADMAP.md`.
- Third-party attribution for the bundled AGPL-3.0 PrusaSlicer in the README
  License section (with a pointer to corresponding source).
- `.dockerignore` to keep build context lean.
- Continuous-integration test workflow; release process documented in
  `RELEASING.md`.

### Fixed

- Enforce `MAX_FILE_SIZE` and reject empty uploads (previously the limit was
  defined but never applied).
- Empty/oversized uploads now return the correct `4xx` status instead of `500`.
- `_parse_time_string` no longer crashes when a time unit is absent and now
  understands days.
- Run the blocking PrusaSlicer subprocess in a worker thread so it no longer
  stalls the event loop.
- Reconciled the parameter bounds in `models.py` with the validation in
  `main.py`.
- `config.py` creates its work directories with `parents=True`.

## [1.0.0] - 2026-02-08

### Added

- Initial production release
- RESTful API for 3D model slicing with PrusaSlicer
- Support for STL and 3MF file formats
- Configurable slicing parameters (layer height, infill density, wall count)
- Predefined filament types with accurate density calculations (PLA, PETG, ABS, TPU, NYLON, ASA)
- Custom filament density override support
- Docker-based deployment
- Docker Compose configuration with volumes and restart policy
- Health check endpoint
- Environment variable configuration support
- Comprehensive API documentation (Swagger UI and ReDoc)
- GitHub Actions workflow for automated Docker image building
- GitHub Container Registry (GHCR) integration
- MIT License

### Project Structure

- Modular codebase with separated concerns (config, models, slicer logic)
- Production-ready error handling
- Automatic file cleanup after processing
- CORS middleware support

[1.0.0]: https://github.com/bintangtimurlangit/superslice/releases/tag/v1.0.0
