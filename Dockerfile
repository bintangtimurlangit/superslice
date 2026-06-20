# syntax=docker/dockerfile:1
#
# SuperSlice — self-owned image. No third-party base; we fetch and extract the
# official PrusaSlicer AppImage ourselves and run it headless via the CLI.
#
# Why PrusaSlicer 2.8.1: it is the last PrusaSlicer release distributed as a
# Linux AppImage (2.9+ is Flatpak-only), and it runs cleanly headless with no
# display/GPU — verified by slicing in this exact toolchain.

# ---------------------------------------------------------------------------
# Stage 1: download + verify + extract the pinned PrusaSlicer AppImage
# ---------------------------------------------------------------------------
FROM debian:trixie-slim AS slicer

ARG PRUSASLICER_VERSION=2.8.1
ARG PRUSASLICER_URL="https://github.com/prusa3d/PrusaSlicer/releases/download/version_2.8.1/PrusaSlicer-2.8.1%2Blinux-x64-newer-distros-GTK3-202409181416.AppImage"
ARG PRUSASLICER_SHA256="565f2f4bd4dbb05904a459d54db1916b6932124709c1d17b5aacfe9f5f2f1b03"

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
RUN curl -fsSL -o prusa.AppImage "${PRUSASLICER_URL}" \
    && echo "${PRUSASLICER_SHA256}  prusa.AppImage" | sha256sum -c - \
    && chmod +x prusa.AppImage \
    && ./prusa.AppImage --appimage-extract \
    && rm prusa.AppImage

# ---------------------------------------------------------------------------
# Stage 2: runtime
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS runtime

# Runtime shared libraries PrusaSlicer's CLI links against (no GPU/display needed).
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libgl1 \
        libgtk-3-0 \
        libgomp1 \
        libwebkit2gtk-4.1-0 \
    && rm -rf /var/lib/apt/lists/*

# Bring in the extracted slicer tree from the builder stage.
COPY --from=slicer /build/squashfs-root /opt/prusaslicer
ENV PRUSASLICER_PATH=/opt/prusaslicer/usr/bin/prusa-slicer

WORKDIR /srv
ENV PYTHONPATH=/srv \
    PYTHONUNBUFFERED=1 \
    UPLOAD_DIR=/srv/uploads \
    OUTPUT_DIR=/srv/output

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app /srv/app

# Run as an unprivileged user; give it ownership of the work directories.
RUN useradd --create-home --uid 10001 app \
    && mkdir -p /srv/uploads /srv/output \
    && chown -R app:app /srv
USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/')" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
