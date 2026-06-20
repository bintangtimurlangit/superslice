# SuperSlice

[![Docker Build](https://github.com/bintangtimurlangit/superslice/actions/workflows/docker-build.yml/badge.svg)](https://github.com/bintangtimurlangit/superslice/actions/workflows/docker-build.yml)
[![Tests](https://github.com/bintangtimurlangit/superslice/actions/workflows/tests.yml/badge.svg)](https://github.com/bintangtimurlangit/superslice/actions/workflows/tests.yml)
[![GitHub release](https://img.shields.io/github/v/release/bintangtimurlangit/superslice)](https://github.com/bintangtimurlangit/superslice/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A small REST API for **3D print estimation**. POST an STL or 3MF file and get
back the print time and filament usage a slicer would report — as JSON — so your
own app doesn't have to run a slicer. It does one thing: estimate. Pricing,
orders, and UI are left to whoever consumes it.

It works by invoking **PrusaSlicer** headlessly and parsing the result.

## Quick start

Run the published image:

```bash
docker run -d --name superslice -p 8000:8000 \
  ghcr.io/bintangtimurlangit/superslice:latest
```

Or build from source: `docker compose up --build`. Either way the API is at
`http://localhost:8000` (interactive docs at `/docs`).

Slice a model:

```bash
curl -X POST http://localhost:8000/slice \
  -F "file=@model.stl" \
  -F "layer_height=0.2" -F "infill_density=20" -F "wall_count=3" \
  -F "filament_type=PLA"
```

```json
{
  "success": true,
  "print_time_formatted": "45m 30s",
  "print_time_minutes": 45.5,
  "filament_length_mm": 1234.56,
  "filament_volume_cm3": 2.98,
  "filament_weight_g": 3.69,
  "filament_type": "PLA"
}
```

→ Full endpoints, parameters, and error codes: **[docs/API.md](docs/API.md)**.

## Documentation

| Doc | What's in it |
| --- | --- |
| [API.md](docs/API.md) | Endpoints, parameters, responses, filament types, errors |
| [CONFIGURATION.md](docs/CONFIGURATION.md) | Environment variables |
| [DEPLOYMENT.md](docs/DEPLOYMENT.md) | Docker, Compose, cloud, reverse proxy |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | How it's built and how an estimate is produced |
| [SLICER.md](docs/SLICER.md) | Why PrusaSlicer 2.8.1 is pinned |
| [ACCURACY.md](docs/ACCURACY.md) | How realistic the numbers are, and how to improve them |
| [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | Common issues |
| [ROADMAP.md](docs/ROADMAP.md) | What's planned next |

## Local development

The app is a small FastAPI package; it needs a PrusaSlicer binary on the host.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
export PRUSASLICER_PATH=/path/to/prusa-slicer
export UPLOAD_DIR=./uploads OUTPUT_DIR=./output
uvicorn app.main:app --reload   # run from the repo root
pytest                          # run the tests (slicer is mocked)
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for conventions and
[RELEASING.md](RELEASING.md) for the release process.

## License & attribution

SuperSlice's own code is [MIT](LICENSE) — use it freely, including commercially.

It bundles an **official, unmodified** build of **PrusaSlicer 2.8.1**
([AGPL-3.0](https://www.gnu.org/licenses/agpl-3.0.txt)), which it invokes as a
separate program;
[corresponding source](https://github.com/prusa3d/PrusaSlicer/releases/tag/version_2.8.1).
The distributed image as a whole therefore contains AGPL-3.0 software — keep
this attribution if you redistribute it. "PrusaSlicer" and "Prusa" are
trademarks of Prusa Research a.s.; SuperSlice is not affiliated with them.
