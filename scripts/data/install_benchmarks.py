#!/usr/bin/env python
"""Install the files shipped in ``benchmarks/`` into the data directory, in the layout the
evaluator (``pocketdetect.benchmarks``) and the build scripts expect.

  python -I scripts/data/install_benchmarks.py [part ...]      (default: all parts)

Parts:
  manifests   test union (+ sha256 check), train/dev entry lists, audit exclusions, fold novelty
              -> $BURROW_DATA/manifests/
  clusters    30 % MMseqs2 clusters of the test union -> $BURROW_DATA/processed/clusters/test_clusters.tsv
  af_set      AF-set site tables (ours; AFDB CC-BY-4.0 + LIGYSIS CC-BY-4.0 + PDB CC0)
              -> $BURROW_DATA/processed/gt/{af_set,af_set_allsites}/sites.tsv
              (structure_path = $BURROW_DATA/inputs/<bench>/<structure_id>.cif.gz; fetch_afdb.py)
  dimer       dimer benchmark ground truth (ours; PDB CC0 + BioLiP2 relevance annotations)
              -> $BURROW_DATA/processed/dimer/{complexes.tsv,gt/<pdb>.json,...}
              (method inputs: build_inputs.py dimer)
  gt          the FROZEN site tables BURROW was scored on, converted from third-party benchmarks:
              LIGYSIS + LIGYSIS_NI (derived from LIGYSIS, CC-BY-4.0, Utges & Barton 2024),
              CryptoBench test (MIT), PocketWatch test (MIT)
              -> $BURROW_DATA/processed/gt/{ligysis_lbs,ligysis_ni,cryptobench_test,pocketwatch_test}/sites.tsv
              ``structure_path`` is reconstructed for this data directory; the content is checked
              against benchmarks/gt_sha256.tsv (identical to the scored tables apart from that column).
              LIGYSIS_NI is derived from the LIGYSIS table exactly as build_gt_ligysis.py does.
              Alternative: rebuild them with build_ligysis_ligands.py / build_gt_*.py (LIGYSIS
              C1-strict ligand atoms then differ for 15 of 6,882 sites, see DATA.md).

COACH420/HOLO4K ground truth is the upstream (mlig) .ds file, read at evaluation time.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _paths as P  # noqa: E402


def _bytes(p: Path) -> bytes:
    return gzip.decompress(p.read_bytes()) if p.suffix == ".gz" else p.read_bytes()


def _put(src_parts: tuple, dst: Path) -> Path:
    data = _bytes(P.bench_file(*src_parts))
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(data)
    return dst


def manifests() -> None:
    M = P.MANIFESTS
    for f in ("test_union.tsv", "test_union.sha256", "test_union_meta.tsv", "test_union_counts.json", "test_union_pdb_ids.txt",
              "test_union_uniprots.txt", "test_fold_novelty.tsv"):
        _put(("test_union", f), M / f)
    want = (M / "test_union.sha256").read_text().split()[0]
    got = hashlib.sha256((M / "test_union.tsv").read_bytes()).hexdigest()
    if got != want:
        raise SystemExit(f"test_union.tsv sha256 mismatch: {got} != {want}")
    for f in ("trainset_train_entries.tsv", "trainset_dev_entries.tsv", "train_dev_audit_exclusions.tsv"):
        _put(("trainset", f), M / f)
    _put(("dimer", "manifest_chains.tsv"), M / "dimer_manifest_chains.tsv")
    _put(("af_set", "af_sequences.fasta"), M / "af_sequences.fasta")
    print(f"manifests -> {M} (test_union sha256 {got[:12]}... OK)")


def clusters() -> None:
    out = _put(("clusters", "test_clusters.tsv"), P.PROC / "clusters" / "test_clusters.tsv")
    (out.parent / "README.md").write_text(
        "# Test-union 30% sequence clusters\n\nInstalled from benchmarks/clusters/test_clusters.tsv by "
        "scripts/data/install_benchmarks.py (built with scripts/data/build_test_clusters.py: MMseqs2 18-8cc5c "
        "easy-cluster --min-seq-id 0.3 -c 0.5 --cov-mode 0 over the unique sequences of the test union).\n")
    print(f"clusters -> {out}")


def af_set() -> None:
    import pandas as pd

    # af_sequences.fasta is also read from processed/af by the training-set rebuild
    _put(("af_set", "af_sequences.fasta"), P.PROC / "af" / "af_sequences.fasta")
    for name in ("af_set", "af_set_allsites"):
        df = pd.read_csv(P.bench_file(name, "sites.tsv"), sep="\t", dtype=str, keep_default_na=False)
        df.insert(1, "structure_path", [str(P.INPUTS / name / f"{s}.cif.gz") for s in df.structure_id])
        out = P.GT / name
        out.mkdir(parents=True, exist_ok=True)
        df.to_csv(out / "sites.tsv", sep="\t", index=False)
        (out / "README.md").write_text(
            f"# {name} site table (PREREG O5)\n\nInstalled from benchmarks/{name}/sites.tsv.gz by scripts/data/install_benchmarks.py; "
            f"structure_path points to {P.INPUTS / name} (scripts/data/fetch_afdb.py --bench {name}). Built originally by "
            "scripts/data/build_gt_af.py (definitions in its docstring and docs/AF_BENCHMARK.md).\n")
        n_present = sum(Path(p).exists() for p in df.structure_path.unique())
        print(f"{name}: {df.structure_id.nunique()} structures, {len(df)} sites -> {out / 'sites.tsv'} "
              f"(model files present: {n_present})")


def dimer() -> None:
    import pandas as pd

    D = P.PROC / "dimer"
    (D / "gt").mkdir(parents=True, exist_ok=True)
    cx = P.read_bench_tsv("dimer", "complexes.tsv").drop(columns=["assembly_id"])
    cx.to_csv(D / "complexes.tsv", sep="\t", index=False)
    for f in ("chain_map.tsv", "unique_sites.tsv", "site_copies.tsv", "manifest_chains.tsv"):
        _put(("dimer", f), D / f)
    n = 0
    with gzip.open(P.bench_file("dimer", "gt.jsonl"), "rt") as fh:
        for line in fh:
            r = json.loads(line)
            cid = r.pop("complex_id")
            (D / "gt" / f"{cid}.json").write_text(json.dumps(r, separators=(",", ":")))
            n += 1
    ia = P.read_bench_tsv("dimer", "inputs_assembly.tsv")
    pd.DataFrame({"structure_id": ia.structure_id, "complex_id": ia.complex_id, "input_path": "inputs/" + ia.input_file,
                  "n_atoms": ia.n_atoms}).to_csv(D / "inputs_assembly.csv", index=False)
    ic = P.read_bench_tsv("dimer", "inputs_chains.tsv")
    pd.DataFrame({"structure_id": ic.structure_id, "complex_id": ic.complex_id, "chain": ic.chain, "is_primary": ic.is_primary,
                  "input_path": "inputs/" + ic.input_file, "n_atoms": ic.n_atoms}).to_csv(D / "inputs_chains.csv", index=False)
    print(f"dimer: {len(cx)} complexes, {n} gt json -> {D} (method inputs: build_inputs.py dimer)")


def _stripped_sha(df) -> str:
    return hashlib.sha256(df.drop(columns=["structure_path"]).to_csv(sep="\t", index=False, lineterminator="\n").encode()).hexdigest()


def gt() -> None:
    import pandas as pd

    ref = (
        pd.read_csv(P.bench_file("gt_sha256.tsv"), sep="\t", dtype=str).set_index("benchmark"))

    def rd(bench):
        return pd.read_csv(P.bench_file(bench, "sites.tsv"), sep="\t", dtype=str, keep_default_na=False)

    tables = {}
    lig = rd("ligysis")
    lig.insert(1, "structure_path", [str(P.pdb_entry_path(s.split("_")[0])) for s in lig.structure_id])
    tables["ligysis"] = lig
    ni = lig[lig.ion_prop.astype(float) != 1].copy()  # as build_gt_ligysis.py
    ni["n_sites"] = ni.groupby("structure_id").site_id.transform("size").astype(int).astype(str)
    tables["ligysis_ni"] = ni
    cb = rd("cryptobench")
    cb.insert(1, "structure_path", [str(P.CRYPTOBENCH / "cif-files" / "cif-files" / f"{p}.cif") for p in cb.apo_pdb_id])
    tables["cryptobench"] = cb
    pw = rd("pocketwatch")
    src = P.read_bench_tsv("pocketwatch", "manifest.tsv").set_index("structure_id").input_source
    pw.insert(1, "structure_path", [str(P.RAW / "pocketwatch" / src[s].split("@", 1)[1].split(":", 1)[0] / "structures" / f"{s}.cif.gz")
                                    for s in pw.structure_id])
    tables["pocketwatch"] = pw
    for bench, df in tables.items():
        got = _stripped_sha(df)
        if got != ref.loc[bench, "sha256_without_structure_path"]:
            raise SystemExit(f"{bench}: installed table differs from the frozen ground truth ({got})")
        out = P.GT / ref.loc[bench, "gt_dir"]
        out.mkdir(parents=True, exist_ok=True)
        df.to_csv(out / "sites.tsv", sep="\t", index=False, lineterminator="\n")
        (out / "README.md").write_text(
            f"# {ref.loc[bench, 'gt_dir']} site table (frozen)\n\nInstalled from benchmarks/ by scripts/data/install_benchmarks.py: "
            "the exact table BURROW was scored on, with structure_path pointing into this data directory. "
            f"sha256 of the content without structure_path: {got}. Definitions: docs/EVALUATION.md; "
            "rebuild alternative: scripts/data/build_gt_*.py.\n")
        n_present = sum(Path(p).exists() for p in df.structure_path.unique())
        print(f"{bench}: {df.structure_id.nunique()} structures, {len(df)} sites -> {out / 'sites.tsv'} "
              f"(identical to frozen GT; structure files present: {n_present})")


PARTS = {"manifests": manifests, "clusters": clusters, "af_set": af_set, "dimer": dimer, "gt": gt}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("parts", nargs="*", help=f"subset of {list(PARTS)} (default: all)")
    a = ap.parse_args(argv)
    bad = [p for p in a.parts if p not in PARTS]
    if bad:
        ap.error(f"unknown part(s) {bad}; choose from {list(PARTS)}")
    print(f"BURROW_DATA = {P.DATA}")
    for p in a.parts or PARTS:
        PARTS[p]()
    return 0


if __name__ == "__main__":
    sys.exit(main())
