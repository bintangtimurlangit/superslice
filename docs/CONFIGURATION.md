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

Example `.env`:

```bash
SLICE_TIMEOUT=180
MAX_FILE_SIZE=209715200
CORS_ORIGINS=https://example.com,https://app.example.com
```

> In Docker the defaults already point at the in-container paths, so you only
> need to set anything here to override behaviour (timeouts, size limits, CORS).
> For local development, set `PRUSASLICER_PATH` and writable `UPLOAD_DIR` /
> `OUTPUT_DIR` — see the [README](../README.md#local-development).
