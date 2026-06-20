# The slicer: lineage, choice, and version

SuperSlice depends on exactly one external program — a slicer. This document
records which one, why, and the constraints behind the choice.

## Lineage

All the relevant slicers descend from one project:

```
Slic3r (2011)
  └─ PrusaSlicer            fork by Prusa Research (was "Slic3r Prusa Edition")
       ├─ SuperSlicer       fork by supermerill
       └─ Bambu Studio      fork by Bambu Lab
            └─ OrcaSlicer    fork of Bambu Studio
```

PrusaSlicer's binary path historically contained `/slic3r/...` for this reason.

## Why PrusaSlicer 2.8.1 (pinned)

The image bundles **PrusaSlicer 2.8.1**, deliberately pinned. Two facts drive
this:

1. **2.9+ dropped Linux AppImages.** Starting with 2.9, PrusaSlicer is
   distributed for Linux as a Flatpak only, because it now depends on WebKitGTK
   which is hard to bundle portably. **2.8.1 is the last AppImage release**, so
   it is the newest PrusaSlicer that packages cleanly into a minimal,
   self-contained container.
2. **It runs cleanly headless.** `--export-gcode` needs no display or GPU. This
   was verified by slicing a model in the exact build toolchain used here.

### Why not OrcaSlicer (the "latest, maintained" option)

OrcaSlicer was evaluated empirically in a container and rejected for now:

- Its CLI **segfaults during `--slice`** in a headless container — even on its
  own self-contained project files.
- It pulls in WebKitGTK + GTK3 + X11 + Mesa software GL even for CLI use.
- Loading presets via the CLI hits an opaque "process not compatible with
  printer" wall.

OrcaSlicer remains a reasonable *future* target if run under a virtual display
(xvfb) on a heavier host, or once a reliable headless recipe exists. It would
also require adapting the G-code parser, whose comment format differs.

## How the version is pinned

The Dockerfile fetches the AppImage by exact URL and verifies its SHA-256 before
extracting it:

```dockerfile
ARG PRUSASLICER_VERSION=2.8.1
ARG PRUSASLICER_URL="https://github.com/prusa3d/PrusaSlicer/releases/download/version_2.8.1/PrusaSlicer-2.8.1%2Blinux-x64-newer-distros-GTK3-202409181416.AppImage"
ARG PRUSASLICER_SHA256="565f2f4bd4dbb05904a459d54db1916b6932124709c1d17b5aacfe9f5f2f1b03"
```

To move to a different version, update all three `ARG`s. The runtime shared
libraries the binary needs are installed in the final stage:
`libgl1 libgtk-3-0 libgomp1 libwebkit2gtk-4.1-0`.
