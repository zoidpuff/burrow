#!/usr/bin/env python
"""Run BURROW on the test benchmarks with the pre-registered settings and write per-structure
prediction files that `scripts/evaluate_benchmark.py` can score.

  python scripts/predict_benchmarks.py [bench ...] [--preset default] [--seed 0] [--device cpu|cuda:0,1]
                                       [--workers 8] [--out outputs/preds]

Benchmarks (inputs from scripts/data/build_inputs.py, i.e. $BURROW_DATA/inputs/<bench>/):

  bench          ranker  --af-mode  notes
  ligysis        all     no         TRANS-frame chains; predictions are mapped to the wwPDB frame
  ligysis_ni     small   no         same inputs as ligysis
  coach420_mlig  small   no         prediction file names keep the .pdb suffix (<name>.pdb.csv)
  holo4k_mlig    small   no         idem
  cryptobench    small   no         apo structures
  pocketwatch    small   yes        predicted structures
  af_set         all     yes        AFDB v6 models (file stem "-model_v6" is dropped)
  dimer          all     no         biological assembly 1 (full assembly input)
  dimer_chains   all     no         isolated chains of the same assemblies (descriptive)

Output: <out>/<bench>/<variant>/raw/ (CLI output) and <out>/<bench>/<variant>/preds/ (scored files).
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pocketdetect.paths import DATA_DIR, models_dir  # noqa: E402

PLAN = {  # bench -> (input dir name, ranker, af_mode, scored-file suffix)
    "ligysis": ("ligysis", "all", False, ""),
    "ligysis_ni": ("ligysis", "small", False, ""),
    "coach420_mlig": ("coach420_mlig", "small", False, ".pdb"),
    "holo4k_mlig": ("holo4k_mlig", "small", False, ".pdb"),
    "cryptobench": ("cryptobench", "small", False, ""),
    "pocketwatch": ("pocketwatch", "small", True, ""),
    "af_set": ("af_set", "all", True, ""),
    "dimer": ("dimer", "all", False, ""),
    "dimer_chains": ("dimer_chains", "all", False, ""),
}


def finalize(bench: str, raw: Path, pdir: Path, suffix: str) -> None:
    """raw/<stem>.csv -> preds/<structure_id>.csv (+ LIGYSIS TRANS -> wwPDB frame mapping)."""
    if pdir.exists():
        shutil.rmtree(pdir)
    pdir.mkdir(parents=True)
    tmp = pdir.parent / "preds_inputframe"
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir()
    for f in raw.glob("*.csv"):
        if f.name == "timing.csv" or f.name.endswith(".points.csv"):
            continue
        stem = f.stem
        if bench == "af_set" and stem.endswith("-model_v6"):
            stem = stem[: -len("-model_v6")]
        shutil.copy(f, tmp / f"{stem}{suffix}.csv")
    if bench in ("ligysis", "ligysis_ni"):
        from pocketdetect.ligysis import trans_preds_to_original
        trans_preds_to_original(tmp, pdir)
    else:
        shutil.rmtree(pdir)
        tmp.rename(pdir)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("benchmarks", nargs="*", default=list(PLAN), help="default: all")
    ap.add_argument("--preset", choices=["default", "accurate", "fast"], default="default")
    ap.add_argument("--seed", type=int, default=0, choices=[0, 1, 2], help="model seed index (s0/s1/s2)")
    ap.add_argument("--inputs", type=Path, default=DATA_DIR / "inputs", help="default: $BURROW_DATA/inputs")
    ap.add_argument("--out", type=Path, default=ROOT / "outputs" / "preds")
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--extra", nargs=argparse.REMAINDER, default=[], help="extra `burrow predict` arguments")
    a = ap.parse_args(argv)
    for bench in a.benchmarks:
        idir, ranker, af, suffix = PLAN[bench]
        inputs = a.inputs / idir
        if not inputs.exists():
            sys.exit(f"{bench}: input directory {inputs} not found (run scripts/data/build_inputs.py)")
        model = models_dir() / f"burrow_{ranker}_{a.preset}_s{a.seed}.json"
        variant = f"burrow_{ranker}_{a.preset}_s{a.seed}" + ("_af" if af else "")
        vdir = a.out / bench / variant
        cmd = [sys.executable, "-m", "pocketdetect.burrow", "predict", str(inputs), "--out", str(vdir / "raw"),
               "--model", str(model), "--ranker", ranker, "--device", a.device, "--workers", str(a.workers),
               "--no-points"] + (["--af-mode"] if af else []) + a.extra
        print("[predict]", " ".join(cmd[2:]), flush=True)
        rc = subprocess.run(cmd).returncode
        if rc not in (0, 1):
            sys.exit(f"{bench}: burrow exited with {rc}")
        finalize(bench, vdir / "raw", vdir / "preds", suffix)
        print(f"[predict] {bench}: {sum(1 for _ in (vdir / 'preds').glob('*.csv'))} prediction files -> {vdir / 'preds'}")


if __name__ == "__main__":
    main()
