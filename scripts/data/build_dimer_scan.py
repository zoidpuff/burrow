#!/usr/bin/env python
"""Stage 1 of the dimer benchmark: scan every candidate PDB entry of the LIGYSIS UniProts.

Candidates = PDB entries with a BioLiP2 (snapshot $BURROW_DATA/raw/biolip2/current; BURROW used the
2025-11-12 release downloaded 2026-10-26) non-polymer ligand
row whose receptor UniProt is in the LIGYSIS benchmark set (ACCs of the 8,244 sites in
LIGYSIS_sites_DEF_TRANS.pkl, i.e. the 3,448 LIGYSIS chains) and BioLiP resolution <= 3.0 A.
Each entry is processed by ``build_dimer_common.process_entry`` (filters, assembly-1 expansion,
site classification). Holo files are written to a temporary directory and deleted; stage 2
(build_dimer_select.py) regenerates them deterministically for the selected entries.

Output: $BURROW_DATA/processed/dimer/scan/entries.jsonl.gz (one record per candidate, incl. rejection
reason; ligand atom coordinates stripped) and scan/scan_summary.json.

Usage: python -I scripts/data/build_dimer_scan.py [--jobs 60] [--limit N]

Only for a FULL rebuild of the dimer benchmark (the benchmark ships in benchmarks/dimer/). Needs a
full wwPDB mirror (BURROW_PDB_MIRROR) or many RCSB downloads, BioLiP2 and LIGYSIS. A new BioLiP2
snapshot / PDB state will not reproduce the shipped 400 complexes exactly.
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
import tempfile
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _paths as P  # noqa: E402  (sets POCKETDETECT_PDB_MIRROR, adds <repo>/src)

import pandas as pd  # noqa: E402

from build_dimer_common import MAX_RESOLUTION, BIOLIP_POLYMER_LIGANDS, load_biolip, process_entry  # noqa: E402
from safe_pickle import safe_load  # noqa: E402

BIOLIP = P.BIOLIP / "BioLiP.txt.gz"
LIGYSIS_SITES = P.LIGYSIS_RESULTS / "LIGYSIS_sites_DEF_TRANS.pkl"
OUT = P.PROC / "dimer" / "scan"


def ligysis_accessions() -> set:
    return set(safe_load(LIGYSIS_SITES)["ACC"].astype(str))


def candidate_entries(acc: set) -> list[str]:
    b = pd.read_csv(BIOLIP, sep="\t", header=None, dtype=str, usecols=[0, 2, 4, 17])
    b.columns = ["pdb", "res", "lig", "unp"]
    r = pd.to_numeric(b["res"], errors="coerce")
    m = b[b["unp"].isin(acc) & (r > 0) & (r <= MAX_RESOLUTION) & ~b["lig"].isin(BIOLIP_POLYMER_LIGANDS)]
    return sorted(set(m["pdb"].str.lower()))


_G: dict = {}


def _init(biolip, acc, tmpdir):
    _G.update(biolip=biolip, acc=acc, tmpdir=tmpdir)


def _job(pid: str) -> dict:
    p = Path(_G["tmpdir"]) / f"{pid}.pdb"
    try:
        r = process_entry(pid, _G["biolip"].get(pid, set()), _G["acc"], p)
    finally:
        p.unlink(missing_ok=True)
    for c in r.get("copies", []):
        c.pop("coords", None)
        c.pop("elements", None)
    return r


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--jobs", type=int, default=60)
    ap.add_argument("--limit", type=int, default=0, help="debug: first N candidates only")
    a = ap.parse_args(argv)
    t0 = time.time()
    acc = ligysis_accessions()
    pids = candidate_entries(acc)
    if a.limit:
        pids = pids[: a.limit]
    biolip = load_biolip(BIOLIP, set(pids))
    print(f"[scan] LIGYSIS ACCs {len(acc)}; candidate entries {len(pids)}", flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    status = Counter()
    with tempfile.TemporaryDirectory(prefix="dimer_scan_") as tmp, gzip.open(OUT / "entries.jsonl.gz.tmp", "wt") as f:
        with ProcessPoolExecutor(a.jobs, initializer=_init, initargs=(biolip, acc, tmp)) as ex:
            for i, r in enumerate(ex.map(_job, pids, chunksize=4)):
                st = r["status"] if not r["status"].startswith("error") else "error"
                status[st] += 1
                f.write(json.dumps(r, separators=(",", ":")) + "\n")
                if (i + 1) % 2000 == 0:
                    print(f"[scan] {i + 1}/{len(pids)} {dict(status)} {time.time() - t0:.0f}s", flush=True)
    (OUT / "entries.jsonl.gz.tmp").replace(OUT / "entries.jsonl.gz")
    summ = {
        "biolip": P.rel_to_data(BIOLIP.resolve()), "biolip_sha256": P.sha256_file(BIOLIP),
        "ligysis_sites": P.rel_to_data(LIGYSIS_SITES),
        "n_ligysis_acc": len(acc),
        "n_candidates": len(pids),
        "status_counts": dict(status.most_common()),
        "seconds": round(time.time() - t0, 1),
    }
    (OUT / "scan_summary.json").write_text(json.dumps(summ, indent=2))
    print(json.dumps(summ, indent=2))


if __name__ == "__main__":
    main()
