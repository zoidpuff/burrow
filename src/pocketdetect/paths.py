"""Repository-relative default locations, overridable by environment variables.

* ``BURROW_DATA``        data directory (default ``<repo>/data``): raw downloads, processed ground truth, inputs
* ``BURROW_MODELS``      model directory (see :func:`models_dir` for the resolution order)
* ``BURROW_PDB_MIRROR``  local wwPDB mirror root containing ``structures/divided/mmCIF`` (default
                         ``$BURROW_DATA/pdb``; ``POCKETDETECT_PDB_MIRROR`` is accepted as an alias)
* ``BURROW_TOOLS``       external binaries such as ``bin/mmseqs`` (default ``<repo>/tools``; falls back to PATH)
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.environ.get("BURROW_DATA", REPO_ROOT / "data"))
MODEL_GLOB = "burrow_*_s0.json"


def _has_models(d) -> bool:
    return d is not None and Path(d).is_dir() and any(Path(d).glob(MODEL_GLOB))


def models_dir(cli_dir=None, required: bool = True):
    """Directory with the BURROW model JSONs, first match of:
    1. ``cli_dir`` (``burrow predict --model-dir``), 2. ``$BURROW_MODELS``, 3. ``./models`` in the current
    working directory, 4. ``<repo>/models`` next to the package sources (editable install / source tree).
    Raises FileNotFoundError with instructions if none contains models (or returns None if not ``required``)."""
    env = os.environ.get("BURROW_MODELS")
    for d, origin in ((cli_dir, "--model-dir"), (env, "BURROW_MODELS")):
        if d:
            if not _has_models(d):
                raise FileNotFoundError(f"{origin}={d}: no BURROW model files ({MODEL_GLOB}) in this directory")
            return Path(d)
    for d in (Path.cwd() / "models", REPO_ROOT / "models"):
        if _has_models(d):
            return d
    if not required:
        return None
    raise FileNotFoundError(
        "BURROW model files not found. The models are shipped in the models/ directory of the BURROW repository. "
        "Point to it with `burrow predict ... --model-dir /path/to/burrow/models`, or set "
        "BURROW_MODELS=/path/to/burrow/models, or run from the repository root, or install the repository in "
        "editable mode (pip install -e .).")


# backwards-compatible constant (None if no model directory can be found at import time)
MODELS_DIR = models_dir(required=False)
PDB_MIRROR = Path(os.environ.get("BURROW_PDB_MIRROR") or os.environ.get("POCKETDETECT_PDB_MIRROR") or DATA_DIR / "pdb")
TOOLS_DIR = Path(os.environ.get("BURROW_TOOLS", REPO_ROOT / "tools"))


def tool(name: str) -> str:
    """Path of an external binary: ``$BURROW_TOOLS/bin/<name>`` if present, else ``<name>`` on PATH."""
    p = TOOLS_DIR / "bin" / name
    return str(p) if p.exists() else (shutil.which(name) or name)
