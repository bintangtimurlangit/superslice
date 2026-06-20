# Roadmap

SuperSlice is a developer-facing API. Its single job is to **reproduce the print
time and filament numbers a normal slicer would output**, returned as JSON, so
that other people's 3D-printing apps don't have to slice manually. It does not
price prints, manage orders, or own a UI — consumers build that on top.

This roadmap collects planned and proposed improvements. Nothing here is
committed to a date; it's a menu to pull from. Ordered roughly by value.

## Shipped in v1.2.0

- ✅ Opt-in **API-key auth**, **rate limiting**, and a **concurrency cap**.
- ✅ **Startup file sweep** + **disk-space guard**.
- ✅ Opt-in **slicing history** (SQLite) with `/history` endpoints.
- ✅ **Structured error envelope** (`error.code`), **OpenAPI examples**,
  `/healthz` and `/version`, and an **async job mode** (`POST /jobs` + polling).

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

## 4. Remaining hardening (builds on v1.2.0)

Auth, rate limiting, the concurrency cap, and the disk guard shipped in v1.2.0.
Still open:

- **Global (cross-replica) rate limiting** — the current limiter is in-process;
  a shared backend (e.g. Redis) would enforce limits across replicas.
- **Configurable temp location** and an optional **result retention window**
  (re-fetch a recent result instead of re-slicing).
- **History storage backends** beyond SQLite, and a retention/pruning policy.

## 5. Smaller polish

- Auto-orient / auto-arrange a model before slicing (optional).
- Durable async jobs (survive a restart) — currently in-memory only.
- Per-endpoint OpenAPI request examples beyond the response examples added.

## Out of scope (by design)

- Pricing, checkout, order management — consumers own this.
- A front-end / model viewer.
- Storing customer model files beyond the lifetime of a request.
