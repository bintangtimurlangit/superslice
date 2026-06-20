# API Reference

Base URL defaults to `http://localhost:8000`. Interactive docs are served at
`/docs` (Swagger UI) and `/redoc`.

## `GET /`

Health/info endpoint.

```json
{ "service": "SuperSlice API", "status": "running", "version": "1.1.0" }
```

## `GET /filament-types`

Returns the built-in filament densities used to compute weight.

```json
{
  "filament_types": {
    "PLA": 1.24, "PETG": 1.27, "ABS": 1.04,
    "TPU": 1.21, "NYLON": 1.14, "ASA": 1.07
  }
}
```

## `POST /slice`

Slice a model and return print statistics. Body is `multipart/form-data`.

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
  -F "layer_height=0.2" \
  -F "infill_density=20" \
  -F "wall_count=3" \
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

For materials not listed (or a known different density), pass `filament_density`:

```bash
curl -X POST http://localhost:8000/slice \
  -F "file=@model.stl" -F "layer_height=0.2" \
  -F "infill_density=20" -F "wall_count=3" \
  -F "filament_density=1.30"
```

To change the built-in table, edit `FILAMENT_DENSITIES` in `app/config.py`.

## Errors

Standard HTTP status codes; the body is `{ "detail": "<message>" }`.

| Code | Meaning |
| --- | --- |
| `200` | Success |
| `400` | Invalid parameters, unsupported file format, or empty upload |
| `408` | Slicing timeout (model too complex / `SLICE_TIMEOUT` exceeded) |
| `413` | Upload exceeds `MAX_FILE_SIZE` |
| `500` | Internal error (includes the slicer's stderr on slicing failure) |

See [ACCURACY.md](ACCURACY.md) for how realistic the numbers are and how to
improve them.
