# API Reference

Base URL defaults to `http://localhost:8000`. Interactive docs are served at
`/docs` (Swagger UI) and `/redoc`.

## Authentication

Disabled by default. If `API_KEYS` is configured (see
[CONFIGURATION.md](CONFIGURATION.md)), the slicing endpoints (`/slice`, `/jobs`)
require a key via either header:

```
X-API-Key: <key>
Authorization: Bearer <key>
```

Missing/invalid keys return `401` with `error.code = "UNAUTHORIZED"`.

## Health & info

| Endpoint | Purpose |
| --- | --- |
| `GET /` | Service info: `{ "service", "status", "version" }` |
| `GET /healthz` | Liveness probe: `{ "status": "ok" }` |
| `GET /version` | `{ "service", "version", "slicer": "PrusaSlicer 2.8.1" }` |

## `GET /filament-types`

```json
{ "filament_types": { "PLA": 1.24, "PETG": 1.27, "ABS": 1.04, "TPU": 1.21, "NYLON": 1.14, "ASA": 1.07 } }
```

## `POST /slice`

Slice a model and return print statistics synchronously. Body is
`multipart/form-data`.

| Field | Required | Description |
| --- | --- | --- |
| `file` | yes | 3D model file (`.stl` or `.3mf`) |
| `layer_height` | yes | Layer height in mm (0.01 – 1.0) |
| `infill_density` | yes | Infill percentage (0 – 100) |
| `wall_count` | yes | Number of perimeter walls (1 – 20) |
| `filament_type` | no | Filament type (default `PLA`) |
| `filament_density` | no | Custom density in g/cm³ (overrides `filament_type`) |

```bash
curl -X POST http://localhost:8000/slice \
  -F "file=@model.stl" \
  -F "layer_height=0.2" -F "infill_density=20" -F "wall_count=3" \
  -F "filament_type=PLA"
```

```json
{
  "success": true,
  "print_time_minutes": 45.5,
  "print_time_formatted": "45m 30s",
  "filament_length_mm": 1234.56,
  "filament_volume_cm3": 2.98,
  "filament_weight_g": 3.69,
  "filament_type": "PLA",
  "layer_height": 0.2,
  "infill_density": 20,
  "wall_count": 3
}
```

## Async slicing (large models)

For models that may exceed a normal request timeout, submit a job and poll.

### `POST /jobs`

Same form fields as `/slice`. Returns `202 Accepted`:

```json
{ "job_id": "834528f6...", "status": "pending", "status_url": "/jobs/834528f6..." }
```

### `GET /jobs/{job_id}`

```json
{
  "job_id": "834528f6...",
  "status": "succeeded",
  "created_at": 1781990263.42,
  "finished_at": 1781990263.68,
  "result": { "success": true, "print_time_formatted": "19m 22s", "...": "..." },
  "error": null
}
```

`status` is one of `pending`, `running`, `succeeded`, `failed`. Jobs are stored
in memory and do not survive a restart (see `JOB_RETENTION`). Unknown ids return
`404`.

## Slicing history (opt-in)

Enabled with `HISTORY_ENABLED=true`. Stores parameters + results of past slices
(never the model files). When disabled, these return `404 HISTORY_DISABLED`.

| Endpoint | Description |
| --- | --- |
| `GET /history?limit=50&offset=0` | `{ "count", "items": [ ... ] }` |
| `GET /history/{id}` | A single record |

## Filament types & density

Weight is computed as `volume_cm3 × density`. Built-in densities (g/cm³):

| Type | Density | Description |
| --- | --- | --- |
| PLA | 1.24 | Polylactic Acid — most common, biodegradable |
| PETG | 1.27 | Polyethylene Terephthalate Glycol — strong, flexible |
| ABS | 1.04 | Acrylonitrile Butadiene Styrene — durable, heat resistant |
| TPU | 1.21 | Thermoplastic Polyurethane — flexible, rubber-like |
| NYLON | 1.14 | Polyamide — strong, abrasion resistant |
| ASA | 1.07 | Acrylonitrile Styrene Acrylate — UV resistant |

For materials not listed (or a known different density), pass `filament_density`.
To change the built-in table, edit `FILAMENT_DENSITIES` in `app/config.py`.

## Errors

Every error uses a consistent envelope. `detail` is the human-readable message;
`error.code` is the stable identifier to branch on:

```json
{ "detail": "File exceeds maximum size of 104857600 bytes",
  "error": { "code": "FILE_TOO_LARGE", "message": "File exceeds maximum size of 104857600 bytes" } }
```

| Status | `error.code` examples |
| --- | --- |
| `400` | `UNSUPPORTED_FILE`, `EMPTY_FILE`, `INVALID_PARAMETER` |
| `401` | `UNAUTHORIZED` |
| `404` | `JOB_NOT_FOUND`, `RECORD_NOT_FOUND`, `HISTORY_DISABLED` |
| `408` | `SLICE_TIMEOUT` |
| `413` | `FILE_TOO_LARGE` |
| `422` | `VALIDATION_ERROR` (malformed request) |
| `429` | `RATE_LIMITED` (includes `Retry-After` header) |
| `500` | `SLICE_FAILED`, `INTERNAL_ERROR` |
| `503` | `INSUFFICIENT_STORAGE` |

See [ACCURACY.md](ACCURACY.md) for how realistic the numbers are.
