# Architecture

SuperSlice is a small, single-purpose HTTP service: it accepts a 3D model and
returns print-time and filament estimates. This document explains how the pieces
fit together and why.

## High-level flow

```
        ┌──────────┐   multipart    ┌─────────────────────────────┐
client ─┤ POST     ├───────────────▶│ FastAPI (app.routes)        │
        │ /slice   │                │  1. validate file + params  │
        └──────────┘                │  2. stream upload to disk   │
                                    │  3. run PrusaSlicer (CLI)   │
                                    │  4. parse G-code comments   │
                                    │  5. compute weight          │
                                    │  6. delete temp files       │
                                    └──────────────┬──────────────┘
                                                   │ JSON
                                                   ▼
                                          SliceResponse
```

The actual geometry work is done by **PrusaSlicer**, invoked as a separate
command-line process. SuperSlice never links PrusaSlicer's code; it shells out,
reads the G-code it produces, and throws the G-code away.

## Layout

The package is grouped by responsibility:

```
app/
├── main.py              # application factory + lifespan
├── config.py            # environment-driven settings & constants
├── models.py            # Pydantic schemas (responses, jobs, history, errors)
├── api/
│   └── routes.py        # all HTTP endpoints
├── core/
│   ├── errors.py        # APIError + structured error handlers
│   └── security.py      # opt-in auth, rate limiting, concurrency cap
└── services/
    ├── slicer.py        # PrusaSlicer CLI + G-code parsing
    ├── slicing.py       # orchestration: validate, save, slice, sweep
    ├── jobs.py          # in-memory async job manager
    └── history.py       # opt-in SQLite history
```

Dependency direction: `api → services → core → config`. The `core` and
`services` layers never import from `api`.

## How an estimate is produced

1. **Slicing.** `run_slicer` calls PrusaSlicer with the three parameters the API
   exposes:

   ```
   prusa-slicer --export-gcode \
     --layer-height <h> --perimeters <n> --fill-density <d>% \
     --output <out.gcode> <input.stl>
   ```

2. **Parsing.** PrusaSlicer writes summary comments at the end of the G-code.
   `parse_gcode_statistics` extracts them with regexes:

   ```
   ; filament used [mm] = 1506.53
   ; filament used [cm3] = 3.62
   ; estimated printing time (normal mode) = 19m 22s
   ```

3. **Weight.** Volume (cm³) × filament density (g/cm³) → grams. Densities live in
   `FILAMENT_DENSITIES`; callers can override with an explicit `filament_density`.

## Concurrency

PrusaSlicer is a blocking subprocess. The endpoint runs it via
`run_in_threadpool` so a slice does not stall FastAPI's event loop. Each request
uses a unique job id for its temp files, and those files are always removed in a
`finally` block.

## Why this shape

- **Stateless.** Nothing persists between requests; temp files are deleted
  immediately. This makes the service trivial to scale horizontally and safe to
  run on ephemeral infrastructure (Cloud Run, Fargate, etc.).
- **Slicer as a subprocess** keeps SuperSlice's own code under a permissive
  license while using an AGPL slicer — see the License section of the
  [main README](../README.md#license--attribution).

For the rationale behind the specific slicer and version, see
[SLICER.md](SLICER.md). For estimate accuracy, see [ACCURACY.md](ACCURACY.md).
