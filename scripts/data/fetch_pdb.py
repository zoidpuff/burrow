#!/usr/bin/env python
"""Fetch wwPDB asymmetric-unit mmCIF entries (CC0) from RCSB into the local entry store.

  python -I scripts/data/fetch_pdb.py --bench ligysis dimer [--jobs 8]
  python -I scripts/data/fetch_pdb.py --ids-file my_ids.txt

Entry lists: ``benchmarks/<bench>/pdb_entries.txt`` (ligysis: 20,971 entries = representative chains
+ every entry that contributes a LIGYSIS site ligand; dimer: 400). Files are written as
``$BURROW_DATA/pdb/structures/divided/mmCIF/<xy>/<id>.cif.gz`` (wwPDB divided layout, which is what
``pocketdetect`` reads via POCKETDETECT_PDB_MIRROR). If BURROW_PDB_MIRROR is set, nothing is
downloaded: the script only reports entries missing from the mirror.

Note: RCSB serves the current version of each entry. BURROW used a wwPDB snapshot of about
2026-10-16; entries remediated since then can differ slightly (the build scripts report it).
"""

from __future__ import annotations

import argparse
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _paths as P  # noqa: E402


def _one(pid: str) -> tuple[str, str]:
    p = P.pdb_entry_path(pid)
    if p.exists():
        return pid, "present"
    if P.HAS_MIRROR:
        return pid, "missing_in_mirror"
    try:
        P.ensure_pdb_entry(pid)
        return pid, "downloaded"
    except Exception as e:  # noqa: BLE001
        return pid, f"failed:{e}"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bench", nargs="*", default=[], help="benchmarks whose pdb_entries.txt to fetch (ligysis, dimer)")
    ap.add_argument("--ids-file", action="append", default=[], help="file with one PDB id per line")
    ap.add_argument("--ids", nargs="*", default=[])
    ap.add_argument("--jobs", type=int, default=8, help="parallel downloads (be polite to RCSB)")
    a = ap.parse_args(argv)
    ids = {i.lower() for i in a.ids}
    files = [P.bench_file(b, "pdb_entries.txt") for b in a.bench] + [Path(f) for f in a.ids_file]
    for f in files:
        ids |= {line.split()[0].lower() for line in Path(f).read_text().splitlines() if line.strip()}
    if not ids:
        ap.error("no ids given")
    print(f"{len(ids)} entries; store {P.PDB_MIRROR} ({'mirror, check only' if P.HAS_MIRROR else 'RCSB download'})", flush=True)
    status: dict[str, list[str]] = {}
    with ThreadPoolExecutor(a.jobs) as ex:
        for i, (pid, st) in enumerate(ex.map(_one, sorted(ids))):
            status.setdefault(st.split(":")[0], []).append(pid)
            if st.startswith("failed"):
                print(f"  {pid}: {st}", file=sys.stderr)
            if (i + 1) % 1000 == 0:
                print(f"  {i + 1}/{len(ids)} " + ", ".join(f"{k} {len(v)}" for k, v in status.items()), flush=True)
    print(", ".join(f"{k}: {len(v)}" for k, v in sorted(status.items())))
    bad = status.get("failed", []) + status.get("missing_in_mirror", [])
    if bad:
        print("not available: " + " ".join(sorted(bad)[:50]) + (" ..." if len(bad) > 50 else ""))
        print("(a few entries may be obsolete; the build scripts report and skip them)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
