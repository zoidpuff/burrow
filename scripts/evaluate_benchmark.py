#!/usr/bin/env python
"""Score predictions on a test benchmark (plain evaluator; the research project ran the same code
through a gated runner that also recorded git state and model checksums in a ledger).

  # per-structure prediction files (<structure_id>.csv, as written by scripts/predict_benchmarks.py)
  python scripts/evaluate_benchmark.py ligysis --pred-dir outputs/preds/ligysis/burrow_all_default_s0/preds

  # the consolidated predictions shipped in predictions/ (re-scores the published numbers)
  python scripts/evaluate_benchmark.py ligysis --pred-file predictions/ligysis.csv.gz

Benchmarks: ligysis ligysis_ni coach420_mlig holo4k_mlig cryptobench pocketwatch af_set af_set_allsites
dimer dimer_chains. Ground truth is read from $BURROW_DATA (scripts/data/README.md). Output:
<out>/summary.csv (30 % sequence-cluster bootstrap CIs), summary_uniprot.csv, per-site/per-pocket tables.
Headline metrics (docs/EVALUATION.md): LIGYSIS-style top-N+2 success at DCC <= 12 A (closest-pocket
rule), DCA4 variant, pooled Precision1K; P2Rank-style DCA4 top-n for COACH420/HOLO4K.
"""
from __future__ import annotations

import argparse
import gzip
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pocketdetect.benchmarks import REGISTRY, run_benchmark  # noqa: E402
from pocketdetect.seeds import BOOTSTRAP_SEED  # noqa: E402

HEADER = "rank,score,center_x,center_y,center_z,residues"


def explode(pred_file: Path, out: Path) -> int:
    """predictions/<bench>.csv.gz (structure_id,rank,...) -> <out>/<structure_id>.csv."""
    import csv
    rows: dict[str, list[str]] = {}
    opener = gzip.open if pred_file.suffix == ".gz" else open
    with opener(pred_file, "rt", newline="") as fh:
        for r in csv.DictReader(fh):
            rows.setdefault(r["structure_id"], []).append(
                ",".join([r["rank"], r["score"], r["center_x"], r["center_y"], r["center_z"], r["residues"]]))
    for sid, lines in rows.items():
        (out / f"{sid}.csv").write_text("\n".join([HEADER] + lines) + "\n")
    return len(rows)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("benchmark", choices=sorted(REGISTRY))
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--pred-dir", type=Path)
    g.add_argument("--pred-file", type=Path, help="consolidated CSV(.gz) with a structure_id column")
    ap.add_argument("--out", type=Path, default=None, help="default: outputs/eval/<benchmark>")
    ap.add_argument("--n-boot", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=BOOTSTRAP_SEED)
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--gt", type=Path, default=None, help="override the ground-truth path")
    a = ap.parse_args(argv)
    out = a.out or ROOT / "outputs" / "eval" / a.benchmark
    with tempfile.TemporaryDirectory() as td:
        pred_dir = a.pred_dir
        if a.pred_file is not None:
            pred_dir = Path(td)
            print(f"[eval] {explode(a.pred_file, pred_dir)} structures from {a.pred_file}")
        head = run_benchmark(a.benchmark, pred_dir, out, n_boot=a.n_boot, seed=a.seed, jobs=a.jobs, gt_path=a.gt)
    for k, v in head.items():
        print(f"{k}\t{v}")
    print(f"[eval] tables -> {out}")


if __name__ == "__main__":
    main()
