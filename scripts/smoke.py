#!/usr/bin/env python
"""1-minute end-to-end check of an installation: model checksums, reference == fast backend on the
shipped examples, and agreement with examples/expected/ (CPU).

  python scripts/smoke.py
"""
from __future__ import annotations

import hashlib
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
try:  # use the installed package if there is one, else the sources
    import pocketdetect  # noqa: F401
except ImportError:
    sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))


def main():
    t0 = time.time()
    from pocketdetect.burrow.cli import main as cli
    from test_examples import CASES, compare

    # 1. model integrity
    md = ROOT / "models"
    want = [l.split() for l in (md / "SHA256SUMS").read_text().splitlines() if l.strip()]
    bad = [n for h, n in want if hashlib.sha256((md / n).read_bytes()).hexdigest() != h]
    assert want and not bad, f"model sha256 mismatch: {bad}"
    print(f"[smoke] {len(want)} model files verified")

    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        # 2. reference vs fast backend
        ex = str(ROOT / "examples/1a28_A.pdb")
        for b in ("reference", "fast"):
            assert cli(["predict", ex, "--out", str(tmp / b), "--backend", b, "--no-points"]) == 0, b
        from pocketdetect.burrow.fast import guard
        st = guard._status()
        assert st and all(st.values()), f"fast backend disabled for stages {[k for k, v in st.items() if not v]} " \
            "(burrow/fast/validated.json missing or reference code changed): outputs fall back to the reference"
        rows = [l.split(",") for l in (tmp / "fast/timing.csv").read_text().splitlines()[1:]]
        assert rows and all(r[1] == "ok" and "reference" not in r for r in rows), \
            f"--backend fast fell back to the reference implementation: {rows}"
        assert (tmp / "reference/1a28_A.csv").read_text() == (tmp / "fast/1a28_A.csv").read_text()
        print(f"[smoke] fast backend active ({', '.join(st)}) and identical to the reference implementation")
        # 3. expected outputs
        for inp, expected, extra in CASES:
            out = tmp / expected.split("/")[0]
            assert cli(["predict", str(ROOT / "examples" / inp), "--out", str(out), "--no-points", *extra]) == 0
            compare(out / Path(expected).name, ROOT / "examples/expected" / expected)
            print(f"[smoke] {inp} {' '.join(extra) or '(default)'}: matches examples/expected/{expected}")
    print(f"[smoke] PASSED in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
