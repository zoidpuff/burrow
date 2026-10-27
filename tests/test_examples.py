"""Regression test: `burrow predict` on the shipped examples reproduces examples/expected/ (CPU).

Scores and centres are compared with a small tolerance (floating-point results can differ in the last
digits across CPUs / library builds); residue lists and the number of pockets must match exactly."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from pocketdetect.burrow.cli import main

ROOT = Path(__file__).resolve().parents[1]
EX = ROOT / "examples"
CASES = [  # (input, expected file, extra CLI arguments)
    ("1a28_A.pdb", "default/1a28_A.csv", []),
    ("1a28_A.pdb", "fast/1a28_A.csv", ["--preset", "fast"]),
    ("AF-P00918-F1-model_v6.cif.gz", "af_mode/AF-P00918-F1-model_v6.csv", ["--af-mode"]),
]


def compare(got: Path, want: Path, tol_score=1e-4, tol_xyz=1e-2):
    a = pd.read_csv(got, keep_default_na=False)
    b = pd.read_csv(want, keep_default_na=False)
    assert len(a) == len(b), f"{got.name}: {len(a)} vs {len(b)} pockets"
    assert list(a["residues"]) == list(b["residues"])
    assert np.abs(a.score.to_numpy() - b.score.to_numpy()).max(initial=0) <= tol_score
    xyz = ["center_x", "center_y", "center_z"]
    assert np.abs(a[xyz].to_numpy() - b[xyz].to_numpy()).max(initial=0) <= tol_xyz


@pytest.mark.parametrize("inp,expected,extra", CASES, ids=[c[1].split("/")[0] for c in CASES])
def test_example_matches_expected(tmp_path, inp, expected, extra):
    assert main(["predict", str(EX / inp), "--out", str(tmp_path), "--no-points", "--device", "cpu", *extra]) == 0
    stem = Path(expected).name
    compare(tmp_path / stem, EX / "expected" / expected)
