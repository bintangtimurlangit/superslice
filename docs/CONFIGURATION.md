# Configuration

All configuration is via environment variables (a `.env` file works too). All
have sensible defaults; the service runs with zero configuration.

| Variable | Default | Description |
| --- | --- | --- |
| `PRUSASLICER_PATH` | `/opt/prusaslicer/usr/bin/prusa-slicer` | Path to the PrusaSlicer binary (set this for local, non-Docker runs). |
| `UPLOAD_DIR` | `/srv/uploads` | Where uploads are written (then deleted per request). |
| `OUTPUT_DIR` | `/srv/output` | Where generated G-code is written (then deleted). |
| `SLICE_TIMEOUT` | `120` | Max slicing time in seconds before a `408`. |
| `MAX_FILE_SIZE` | `104857600` | Max upload size in bytes (100 MB) before a `413`. |
| `CORS_ORIGINS` | `*` | Comma-separated allowed origins. |

### Build volume

| Variable | Default | Description |
| --- | --- | --- |
| `BUILD_VOLUME_X` | `256` | Build plate width (mm). Larger models are flagged, not rejected. |
| `BUILD_VOLUME_Y` | `256` | Build plate depth (mm). |
| `BUILD_VOLUME_Z` | `256` | Max print height (mm). |
| `BED_MARGIN_MM` | `10` | Extra bed margin so an over-sized model still slices instead of erroring. |

Per-request overrides are accepted via the `build_volume_x/y/z` form fields.

### Protection (all opt-in, disabled by default)

| Variable | Default | Description |
| --- | --- | --- |
| `API_KEYS` | _(empty)_ | Comma-separated keys. When set, `/slice` and `/jobs` require a matching `X-API-Key` (or `Authorization: Bearer`) header. Empty = no auth. |
| `RATE_LIMIT_PER_MINUTE` | `0` | Max slice requests per minute per client (by key, else IP). `0` = unlimited. In-process / per replica. |
| `MAX_CONCURRENT_SLICES` | `0` | Max simultaneous slices; extra requests queue. `0` = unlimited. |
| `MIN_FREE_DISK_MB` | `0` | Refuse new slices (`503`) when free disk in the work dir falls below this. `0` = disabled. |

### Slicing history (opt-in)

| Variable | Default | Description |
| --- | --- | --- |
| `HISTORY_ENABLED` | `false` | Persist a record of each slice (parameters + results, never model files) to SQLite, exposed at `/history`. |
| `HISTORY_DB_PATH` | `/srv/data/history.db` | SQLite database location. |

### Async jobs

| Variable | Default | Description |
| --- | --- | --- |
| `JOB_RETENTION` | `100` | Number of finished async jobs kept in the in-memory store. |

Example `.env`:

```bash
SLICE_TIMEOUT=180
MAX_FILE_SIZE=209715200
CORS_ORIGINS=https://example.com,https://app.example.com

# Lock it down for a shared deployment:
API_KEYS=key-for-app-a,key-for-app-b
RATE_LIMIT_PER_MINUTE=30
MAX_CONCURRENT_SLICES=4
HISTORY_ENABLED=true
```

> In Docker the defaults already point at the in-container paths, so you only
> need to set anything here to override behaviour (timeouts, size limits, CORS).
> For local development, set `PRUSASLICER_PATH` and writable `UPLOAD_DIR` /
> `OUTPUT_DIR` — see the [README](../README.md#local-development).
