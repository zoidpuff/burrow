"""`burrow predict --output-rule region` (optional, non-default; results/dev/biolip/V3b_CYCLE.md).

* the region output keeps the default (v2) list as its prefix and only adds pockets;
* reference implementation and fast backend give identical files;
* `--output-rule region` cannot be combined with `--min-score`.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from pocketdetect.burrow.cli import _stem, main

ROOT = Path(__file__).resolve().parents[1]
FILES = sorted((ROOT / "examples").glob("*.pdb"))

pytestmark = pytest.mark.skipif(not FILES, reason="example structures not available")


def _run(tmp_path, name, *extra):
    out = tmp_path / name
    assert main(["predict", *map(str, FILES), "--out", str(out), "--ranker", "small", "--workers", "1", "--no-points",
                 *extra]) == 0
    return out


@pytest.mark.parametrize("backend", ["reference", "fast"])
def test_region_extends_v2(tmp_path, backend):
    v2 = _run(tmp_path, f"v2_{backend}", "--backend", backend)
    reg = _run(tmp_path, f"region_{backend}", "--backend", backend, "--output-rule", "region")
    for f in FILES:
        a = pd.read_csv(v2 / f"{_stem(str(f))}.csv", keep_default_na=False)
        b = pd.read_csv(reg / f"{_stem(str(f))}.csv", keep_default_na=False)
        assert len(b) >= len(a)
        pd.testing.assert_frame_equal(a, b.iloc[: len(a)].reset_index(drop=True))
        assert (b.score.iloc[len(a):] >= 0.005).all()


def test_region_reference_equals_fast(tmp_path):
    r = _run(tmp_path, "r", "--backend", "reference", "--output-rule", "region")
    f = _run(tmp_path, "f", "--backend", "fast", "--output-rule", "region")
    for x in FILES:
        s = _stem(str(x))
        assert (r / f"{s}.csv").read_text() == (f / f"{s}.csv").read_text(), s


def test_region_rule_rejects_min_score(tmp_path):
    with pytest.raises(SystemExit):
        main(["predict", str(FILES[0]), "--out", str(tmp_path / "x"), "--output-rule", "region", "--min-score", "0.1"])
