"""pocketdetect.burrow.export.pocket_representations: pockets identical to the frozen pipeline, consistent
point / descriptor tables, and the same pockets as the shipped expected CLI output."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from pocketdetect.burrow.cli import DEFAULT_MODELS
from pocketdetect.burrow.export import pocket_representations
from pocketdetect.burrow.model import BurrowModel
from pocketdetect.burrow.pipeline import predict_protein
from pocketdetect.burrow.prep import load_protein
from pocketdetect.paths import models_dir

ROOT = Path(__file__).resolve().parents[1]
REAL = ROOT / "examples/1a28_A.pdb"
MD = models_dir(required=False)

pytestmark = pytest.mark.skipif(not (REAL.exists() and MD is not None), reason="example structure or models not available")


@pytest.mark.parametrize("ranker,preset", [("all", "default"), ("small", "default"), ("all", "fast")])
def test_pockets_identical_to_predict_protein(ranker, preset):
    rep = pocket_representations(REAL, ranker=ranker, preset=preset)
    m = BurrowModel.load(MD / DEFAULT_MODELS[(ranker, preset)])
    ref = predict_protein(load_protein(REAL), m)
    pk = rep["pockets"]
    assert len(pk) == len(ref.scores) > 0
    assert np.allclose(pk[["center_x", "center_y", "center_z"]].to_numpy(), ref.centers)
    assert np.allclose(pk.score.to_numpy(), ref.scores)
    assert list(pk.residues) == [" ".join(sorted(r)) for r in ref.residues]
    for r, pts in zip(pk["rank"], ref.points):        # point sets of every pocket
        assert np.allclose(rep["points"].loc[rep["pocket_points"][r], ["x", "y", "z"]].to_numpy(), pts)


def test_tables_are_consistent():
    rep = pocket_representations(REAL, ranker="all", min_score=None)
    pts, pk = rep["points"], rep["pockets"]
    assert len(rep["point_feature_names"]) == 84 and len(rep["descriptor_names"]) == 76
    assert all(n in pts.columns for n in rep["point_feature_names"])
    assert all(n in pk.columns for n in rep["descriptor_names"])
    assert len(pk) >= len(pocket_representations(REAL, ranker="all")["pockets"])   # floor only removes pockets
    for r, n in zip(pk["rank"], pk.n_points):
        assert len(rep["pocket_points"][r]) == n == pk.loc[pk["rank"] == r, "n_pts"].iloc[0]


def test_matches_expected_cli_output():
    """Same pockets as the shipped default CLI output (examples/expected/default)."""
    want = pd.read_csv(ROOT / "examples/expected/default/1a28_A.csv", keep_default_na=False)
    pk = pocket_representations(REAL, ranker="all")["pockets"]
    assert len(pk) == len(want)
    assert np.allclose(pk.score.to_numpy(), want.score.to_numpy(), atol=1e-5)
    assert np.allclose(pk[["center_x", "center_y", "center_z"]].to_numpy(),
                       want[["center_x", "center_y", "center_z"]].to_numpy(), atol=1e-3)
    assert [set(r.split()) for r in pk.residues] == [set(r.split()) for r in want.residues]
