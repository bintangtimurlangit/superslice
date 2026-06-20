# Estimate accuracy

SuperSlice's goal is to reproduce the print time and filament numbers a normal
slicer would report, so consumers of the API don't have to slice by hand. Those
numbers are only as good as the slicer settings behind them. This document
explains the current behaviour and how to make estimates track a specific
printer/filament.

## Current behaviour

The `/slice` endpoint passes **only three** settings to PrusaSlicer:

- `--layer-height`
- `--perimeters` (wall count)
- `--fill-density`

**Everything else uses PrusaSlicer's built-in defaults** — nozzle diameter,
filament diameter, print/travel speeds, temperatures, retraction, cooling, and
so on. Those defaults will not match any specific machine, so the reported time
and filament weight are *ballpark*, not production quotes.

## Making estimates match a specific printer

To make the output track a real machine/filament instead of generic defaults,
bundle a PrusaSlicer configuration exported from that machine and load it:

1. In PrusaSlicer (desktop), set up the printer, filament, and print settings
   you actually use.
2. Export the combined config: **File → Export → Export Config** → `profile.ini`.
3. Add the file to the image and load it in `run_slicer` (`app/slicer.py`):

   ```python
   cmd = [
       PRUSASLICER_PATH,
       "--load", "/opt/profiles/profile.ini",   # bundled real profile
       "--layer-height", str(layer_height),
       "--perimeters", str(wall_count),
       "--fill-density", f"{infill_density}%",
       "--export-gcode",
       "--output", str(output_path),
       str(input_path),
   ]
   ```

   Command-line flags override values from `--load`, so the three API parameters
   still take effect on top of the profile.

## Filament weight

Weight is computed as `volume_cm3 × density`, not measured by the slicer.
Densities are defined in `FILAMENT_DENSITIES` (`app/config.py`):

| Type | g/cm³ |
| --- | --- |
| PLA | 1.24 |
| PETG | 1.27 |
| ABS | 1.04 |
| TPU | 1.21 |
| NYLON | 1.14 |
| ASA | 1.07 |

Callers can override with the `filament_density` form field for materials not in
the table or with a known different density. These are nominal values; real
spools vary by a few percent.

## What is *not* modelled

- Multi-material / multi-extruder prints.
- Supports, brims, rafts beyond what the default profile generates.
- Per-machine acceleration/jerk that affects real-world time.
- Spool waste, purge, and failed prints.
