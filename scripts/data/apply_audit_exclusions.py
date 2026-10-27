#!/usr/bin/env python
"""Apply the shipped leakage-audit exclusions to rebuilt train/dev manifests.

  python -I scripts/data/apply_audit_exclusions.py

Reads $BURROW_DATA/manifests/train_dev_audit_exclusions.tsv (shipped in benchmarks/trainset/,
installed by install_benchmarks.py; 186 entries flagged by an independent leakage audit: sequence
hits to a test set, dev-vs-train hits, UniProt overlap) and drops those entries from
$BURROW_DATA/processed/{train,dev}/manifest.csv. The pre-audit manifests are kept as
manifest_preaudit.csv. Idempotent: always filters from manifest_preaudit.csv. Finally compares the
kept entry ids with the shipped (pre-audit) benchmarks/trainset/trainset_{train,dev}_entries.tsv
minus the exclusions (BURROW: train 6,475, dev 579 entries).
"""
import csv
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _paths as P  # noqa: E402


def read_tsv(p):
    with open(p) as f:
        return list(csv.DictReader(f, delimiter="\t"))


def main(argv=None) -> int:
    import argparse

    argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter).parse_args(argv)
    excl = {r["entry_id"]: r["reason"] for r in read_tsv(P.MANIFESTS / "train_dev_audit_exclusions.tsv")}
    for split in ("train", "dev"):
        man = P.PROC / split / "manifest.csv"
        pre = man.with_name("manifest_preaudit.csv")
        if not pre.exists():
            shutil.copy(man, pre)
        with open(pre) as f:
            rows = list(csv.DictReader(f))
        kept = [r for r in rows if r["entry_id"] not in excl]
        with open(man, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(kept)
        ref = {r["entry_id"] for r in read_tsv(P.MANIFESTS / f"trainset_{split}_entries.tsv")} - set(excl)  # shipped lists are pre-audit
        got = {r["entry_id"] for r in kept}
        print(f"{split}: {len(rows)} -> {len(kept)} (dropped {len(rows) - len(kept)}); vs shipped list: "
              f"{len(got & ref)} shared, {len(got - ref)} only rebuilt, {len(ref - got)} only shipped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
