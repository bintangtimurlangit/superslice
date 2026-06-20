# Roadmap

SuperSlice is a developer-facing API. Its single job is to **reproduce the print
time and filament numbers a normal slicer would output**, returned as JSON, so
that other people's 3D-printing apps don't have to slice manually. It does not
price prints, manage orders, or own a UI — consumers build that on top.

This roadmap collects planned and proposed improvements. Nothing here is
committed to a date; it's a menu to pull from. Ordered roughly by value.

## 1. Printer & filament presets  *(next up)*

Today the API exposes only layer height, walls, and infill; everything else uses
PrusaSlicer defaults (see [ACCURACY.md](ACCURACY.md)). The biggest accuracy win
is letting callers pick a **bundled preset**:

- Ship a library of PrusaSlicer printer + filament + process profiles.
- New request fields, e.g. `printer` and `filament` (names from the library),
  resolved to a `--load <profile.ini>` for the slice.
- Expose the catalogue via a `GET /presets` endpoint so consumers can discover
  valid values.
- Keep raw overrides (layer height, etc.) layered on top of the preset.

## 2. Richer slice output (build-plate & support flags)

Consumers asked for more than time + grams. PrusaSlicer already knows these;
surface them as extra JSON fields rather than new endpoints:

- `fits_build_volume` / `exceeds_build_volume` (needs a printer preset's bed
  size — depends on item 1) with the model's bounding box.
- `requires_supports` (overhang detection / support material generated).
- Object count, bounding box dimensions, estimated layers.
- Per-extruder / per-filament breakdown for multi-material.

## 3. Power / energy estimation

A future printer preset could include wattage so the API can return estimated
energy use. Keep cost out of the core (no pricing), but allow an optional input:

- Printer preset carries average draw (W) or an energy model.
- Optional request field like `energy_cost_per_kwh` → returns
  `estimated_energy_kwh` and, only if a cost is supplied, a derived cost.

## 4. Hardening for public/shared deployments

- **Authentication:** optional API-key middleware (header-based), toggled by an
  env var so it stays zero-config for local use.
- **Rate limiting:** per-key / per-IP limits to protect the slicer from abuse
  (slicing is CPU-heavy).
- **Concurrency cap:** bound simultaneous slices so the host isn't overwhelmed
  (a semaphore around `run_in_threadpool`).

## 5. Temp-file & disk hygiene

Files are already deleted per request in a `finally` block. Make this robust:

- Startup sweep of any orphaned files from crashed requests.
- Disk-usage guard / configurable temp location.
- Optional retention window if a result needs to be re-fetched.

## 6. Slicing history (optional, opt-in)

Persist a record of past slices (parameters + results, not the model files) for
consumers who want it:

- Pluggable storage (start with SQLite), disabled by default.
- `GET /history` / `GET /history/{id}` endpoints.
- Clear data-retention + privacy story, since models belong to the caller.

## 7. Smaller polish

- Structured error responses (consistent JSON error schema).
- OpenAPI examples on every endpoint for easier integration.
- A `/healthz` (liveness) vs `/` split, and a `/version` endpoint.
- Async job mode (`202 Accepted` + poll) for very large models that exceed a
  request timeout.
- Auto-orient / auto-arrange before slicing (optional).

## Out of scope (by design)

- Pricing, checkout, order management — consumers own this.
- A front-end / model viewer.
- Storing customer model files beyond the lifetime of a request.
