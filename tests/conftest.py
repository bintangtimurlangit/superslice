"""Shared test fixtures and environment setup.

The app's ``config`` module creates its upload/output directories at import
time, defaulting to ``/app/...`` (the container paths). Point them at a
temporary location *before* anything imports ``config`` so the suite runs
anywhere.
"""
import os
import tempfile
from pathlib import Path

_tmp = Path(tempfile.mkdtemp(prefix="superslice-tests-"))
os.environ.setdefault("UPLOAD_DIR", str(_tmp / "uploads"))
os.environ.setdefault("OUTPUT_DIR", str(_tmp / "output"))
