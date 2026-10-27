#!/usr/bin/env python
"""Cluster all test-union chains at 30 % identity (PREREG bootstrap unit).

  python -I scripts/data/build_test_clusters.py  ->  $BURROW_DATA/processed/clusters/{test_clusters.tsv,README.md}

Optional: the table ships as benchmarks/clusters/test_clusters.tsv and is installed by
install_benchmarks.py. Rebuilding needs MMseqs2 (install_tools.sh) and the installed test union.

MMseqs2 easy-cluster --min-seq-id 0.3 -c 0.5 --cov-mode 0 on the unique sequences of
$BURROW_DATA/manifests/test_union.tsv (one global clustering across all benchmarks).
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _paths as P  # noqa: E402

OUT = P.PROC / "clusters"


def main(argv=None):
    import argparse

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--threads", type=int, default=32)
    a = ap.parse_args(argv)
    OUT.mkdir(parents=True, exist_ok=True)
    MMSEQS = P.tool("mmseqs")
    tu = pd.read_csv(P.MANIFESTS / "test_union.tsv", sep="\t", dtype=str, keep_default_na=False)
    meta = pd.read_csv(P.MANIFESTS / "test_union_meta.tsv", sep="\t", dtype=str, keep_default_na=False)
    seqs = tu.drop_duplicates("sequence").reset_index(drop=True)
    seq_key = {s: f"s{i}" for i, s in enumerate(seqs.sequence)}
    tmp = P.tmpdir("burrow_mmseqs_")
    fa = tmp / "in.fasta"
    fa.write_text("".join(f">{k}\n{s}\n" for s, k in seq_key.items()))
    cmd = [MMSEQS, "easy-cluster", str(fa), str(tmp / "res"), str(tmp / "work"), "--min-seq-id", "0.3", "-c", "0.5",
           "--cov-mode", "0", "--threads", str(a.threads), "-v", "1"]
    subprocess.run(cmd, check=True)
    cl = pd.read_csv(tmp / "res_cluster.tsv", sep="\t", header=None, names=["rep", "member"])
    rep_of = dict(zip(cl.member, cl.rep))
    tu["seq_key"] = tu.sequence.map(seq_key)
    tu["cluster30"] = "c30_" + tu.seq_key.map(rep_of).fillna(tu.seq_key)
    tu = tu.merge(meta[["id", "uniprot"]], on="id", how="left")
    tu["uniprot"] = tu.uniprot.fillna("")
    tu.loc[tu.uniprot == "", "uniprot"] = "nouniprot:" + tu.seq_key  # unmapped: own unit
    out = tu[["id", "source_set", "cluster30", "uniprot"]]
    out.to_csv(OUT / "test_clusters.tsv", sep="\t", index=False)
    shutil.rmtree(tmp, ignore_errors=True)
    info = {
        "command": " ".join(["mmseqs", cmd[1]] + ["<in.fasta>", "<res>", "<tmp>"] + cmd[5:]),
        "mmseqs_version": subprocess.run([MMSEQS, "version"], capture_output=True, text=True).stdout.strip(),
        "test_union_sha256": hashlib.sha256((P.MANIFESTS / "test_union.tsv").read_bytes()).hexdigest(),
        "n_ids": len(out), "n_unique_sequences": len(seqs), "n_clusters30": int(out.cluster30.nunique()),
        "per_source_clusters": out.groupby("source_set").cluster30.nunique().to_dict(),
        "per_source_uniprots": out.groupby("source_set").uniprot.nunique().to_dict(),
    }
    (OUT / "README.md").write_text("# Test-union 30% sequence clusters\n\nBuilt by `scripts/data/build_test_clusters.py`.\n\n```\n" + json.dumps(info, indent=2) + "\n```\n")
    print(json.dumps(info, indent=2))


if __name__ == "__main__":
    main()
