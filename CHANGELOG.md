# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
