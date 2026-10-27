"""CLI output score floor (FREEZE v2, decision D13): `--min-score` behaviour."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from pocketdetect.burrow.cli import DEFAULT_MODELS, main
from pocketdetect.paths import models_dir

ROOT = Path(__file__).resolve().parents[1]
REAL = ROOT / "examples/1a28_A.pdb"
_MD = models_dir(required=False)
V2 = (_MD / DEFAULT_MODELS[("small", "default")]) if _MD else Path("/nonexistent")

pytestmark = pytest.mark.skipif(not (REAL.exists() and V2.exists()), reason="example structure or models not available")


def _run(tmp_path, name, *extra):
    out = tmp_path / name
    assert main(["predict", str(REAL), "--out", str(out), "--ranker", "small", "--no-points", *extra]) == 0
    return out / f"{REAL.stem}.csv"


def test_default_is_v2_with_floor():
    m = json.loads(V2.read_text())
    assert m["formation"]["min_score"] == 0.03 and m["formation"]["min_keep"] == 3


def test_v2_default_respects_floor(tmp_path):
    df = pd.read_csv(_run(tmp_path, "v2"))
    assert len(df) >= 1
    assert (df.score.iloc[3:] >= 0.03).all()  # beyond min_keep = 3, only pockets above the floor


def test_floor_output_is_prefix_of_full_list(tmp_path):
    full = pd.read_csv(_run(tmp_path, "full", "--min-score", "none"), keep_default_na=False)
    v2 = pd.read_csv(_run(tmp_path, "v2b"), keep_default_na=False)
    strict = pd.read_csv(_run(tmp_path, "strict", "--min-score", "0.5"), keep_default_na=False)
    assert len(strict) <= len(v2) <= len(full)
    for part in (v2, strict):
        pd.testing.assert_frame_equal(part, full.iloc[: len(part)].reset_index(drop=True))
    assert len(strict) >= min(3, len(full))  # min_keep still applies
