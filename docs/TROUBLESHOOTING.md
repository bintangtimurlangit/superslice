# Troubleshooting

## Build

**`sha256sum: WARNING: ... computed checksum did NOT match`**
The pinned PrusaSlicer AppImage failed verification — usually a corrupted or
partial download, or the URL/SHA in the Dockerfile drifted. Re-run the build; if
it persists, confirm the `PRUSASLICER_URL` and `PRUSASLICER_SHA256` build args
match a real release asset.

**`--appimage-extract` does nothing / empty `squashfs-root`**
The AppImage must be executable. The Dockerfile `chmod +x` handles this; if you
extract manually, do the same. Extraction does **not** need FUSE.

## Runtime

**`error while loading shared libraries: libwebkit2gtk-4.1.so.0`**
(or `libGL.so.1`, `libgtk-3.so.0`). A required runtime library is missing. The
final image installs `libgl1 libgtk-3-0 libgomp1 libwebkit2gtk-4.1-0`; if you
changed the base image, reinstall these.

**`/slice` returns 500 `Slicing failed: ...`**
PrusaSlicer rejected the model or parameters. Common causes: a non-manifold
mesh, or an empty/garbage STL. The `stderr` from PrusaSlicer is included in the
response detail.

**`/slice` returns 408**
Slicing exceeded `SLICE_TIMEOUT` (default 120s). Raise it for large/complex
models: `-e SLICE_TIMEOUT=300`.

**`/slice` returns 413 / 400 "Uploaded file is empty"**
The upload exceeded `MAX_FILE_SIZE` (413) or had zero bytes (400). Adjust
`MAX_FILE_SIZE` if you need larger models.

**Estimates look wrong / unrealistic**
Expected with default settings — see [ACCURACY.md](ACCURACY.md). Load a real
printer profile for meaningful numbers.

## Health & monitoring

The container ships a healthcheck that hits `/`. Inspect it with:

```bash
docker inspect --format '{{json .State.Health}}' <container> | python -m json.tool
docker logs <container>
```

## Local development

**`FileNotFoundError: /app/uploads`** when running outside Docker.
`config.py` defaults the work directories to container paths. Set
`UPLOAD_DIR`/`OUTPUT_DIR` to writable local paths (the directories are created
automatically).

**Tests fail to import `app`**
Run `pytest` from the repository root; `pytest.ini` puts the repo root on the
path so the `app` package resolves.
