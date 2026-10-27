#!/usr/bin/env python
"""Build the prediction inputs of every test benchmark from the shipped manifests
(``benchmarks/<bench>/manifest.tsv``) and the upstream downloads:

  python -I scripts/data/build_inputs.py [bench ...] [--copy] [--jobs 8]      (default: all)

  $BURROW_DATA/inputs/<bench>/<input_file>   one file per structure; the file stem is the
                                             structure_id that predictions must be named after
                                             (<structure_id>.csv; COACH420/HOLO4K: <name>.pdb.csv)

Benchmarks and sources:
  ligysis, ligysis_ni  LBS-comparison v2.0.0 ligand-stripped TRANS-frame representative chains
                       (download_ligysis.sh). Predictions in this frame are mapped to the evaluation
                       frame with pocketdetect.ligysis.trans_preds_to_original.
  coach420_mlig,       P2Rank datasets @ pinned commit (download_p2rank_datasets.sh), files as listed
  holo4k_mlig          in the (mlig) .ds; ligands are stripped by the method wrappers.
  cryptobench          CryptoBench apo mmCIF (download_cryptobench.sh) restricted to the benchmark's
                       ``input_chains`` (written as PDB, or mmCIF if a chain id is longer than 1 char).
  pocketwatch          PocketWatch ESMFold2 folds (download_pocketwatch.sh).
  af_set,              AFDB v6 models (fetch_afdb.py; this script only checks them).
  af_set_allsites
  dimer                assembly 1 of 400 PDB entries, expanded from the asymmetric unit (RCSB or a
                       mirror; build_dimer_common.expand_assembly), polymer only:
                       $BURROW_DATA/processed/dimer/inputs/{assembly/<pdb>.pdb, chains/<pdb>_<C>.pdb}
                       with links $BURROW_DATA/inputs/dimer and $BURROW_DATA/inputs/dimer_chains.

Every input is compared with the sha256 recorded in the manifest (``input_sha256``; for files we
write, BURROW used gemmi 0.7.5) and a summary is printed. Default: symlinks to the downloaded
files (``--copy`` for copies).
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _paths as P  # noqa: E402

COPY = False


def place(src: Path, dst: Path) -> None:
    if dst.is_symlink() or dst.exists():
        dst.unlink()
    if not src.exists():
        raise FileNotFoundError(src)
    if COPY:
        shutil.copyfile(src, dst)
    else:
        os.symlink(os.path.abspath(src), dst)


def report(bench: str, outdir: Path, man, sha_col: str = "input_sha256", decompress: bool = False) -> None:
    ok = bad = missing = 0
    bad_ids = []
    for r in man.itertuples():
        p = outdir / r.input_file
        if not p.exists():
            missing += 1
            continue
        want = getattr(r, sha_col, "")
        if not want:
            continue
        if P.sha256_file(p, decompress=decompress) == want:
            ok += 1
        else:
            bad += 1
            bad_ids.append(r.structure_id)
    print(f"{bench}: {len(man)} inputs in {outdir}; sha256 identical {ok}, different {bad} {bad_ids[:5]}, missing {missing}", flush=True)


def _source_rel(s: str) -> str:
    """Path inside the upstream archive from an ``input_source`` string ``<scheme>:<id>:<path>``."""
    return s.split(":", 2)[2]


def ligysis(name: str = "ligysis") -> None:
    man = P.read_bench_tsv(name, "manifest.tsv")
    d = P.INPUTS / name
    d.mkdir(parents=True, exist_ok=True)
    for r in man.itertuples():
        place(P.LIGYSIS_TRANS / f"{r.structure_id}.trans.pdb", d / r.input_file)
    if name == "ligysis_ni":
        man = man.merge(P.read_bench_tsv("ligysis", "manifest.tsv")[["structure_id", "input_sha256"]], on="structure_id")
    report(name, d, man)


def ds(name: str) -> None:
    man = P.read_bench_tsv(name, "manifest.tsv")
    d = P.INPUTS / name
    d.mkdir(parents=True, exist_ok=True)
    for r in man.itertuples():
        place(P.P2RANK_DS / _source_rel(r.input_source), d / r.input_file)
    report(name, d, man)


def _crypto_one(args) -> str:
    import gemmi

    src, keep, out = args
    st = gemmi.read_structure(str(src))
    m = st[0]
    for i in range(len(m) - 1, -1, -1):
        if m[i].name not in keep:
            del m[i]
    assert len(m) == len(keep), (src, keep)
    if out.suffix == ".pdb":
        st.write_pdb(str(out))
    else:
        st.make_mmcif_document().write_file(str(out))
    return out.name


def cryptobench(jobs: int) -> None:
    man = P.read_bench_tsv("cryptobench", "manifest.tsv")
    d = P.INPUTS / "cryptobench"
    d.mkdir(parents=True, exist_ok=True)
    cif = P.CRYPTOBENCH / "cif-files" / "cif-files"
    tasks = []
    for r in man.itertuples():
        src = cif / f"{r.apo_pdb_id}.cif"
        if not src.exists():
            raise FileNotFoundError(src)
        if P.sha256_file(src) != r.source_sha256:
            print(f"  warning: {src.name} differs from the CryptoBench file BURROW used", file=sys.stderr)
        fmt_pdb = all(len(c) == 1 for c in r.input_chains.split("-"))
        if fmt_pdb != r.input_file.endswith(".pdb"):
            raise RuntimeError(f"{r.structure_id}: format rule disagrees with manifest ({r.input_file})")
        tasks.append((src, set(r.input_chains.split("-")), d / r.input_file))
    with ProcessPoolExecutor(jobs) as ex:
        list(ex.map(_crypto_one, tasks, chunksize=8))
    report("cryptobench", d, man)


def pocketwatch() -> None:
    man = P.read_bench_tsv("pocketwatch", "manifest.tsv")
    d = P.INPUTS / "pocketwatch"
    d.mkdir(parents=True, exist_ok=True)
    for r in man.itertuples():
        place(P.POCKETWATCH / _source_rel(r.input_source), d / r.input_file)
    report("pocketwatch", d, man)


def af(name: str) -> None:
    man = P.read_bench_tsv(name, "manifest.tsv")
    d = P.INPUTS / name
    d.mkdir(parents=True, exist_ok=True)
    if name != "af_set":  # reuse af_set downloads
        src = P.INPUTS / "af_set"
        for r in man.itertuples():
            if not (d / r.input_file).exists() and (src / r.input_file).exists():
                place(src / r.input_file, d / r.input_file)
    report(name, d, man, sha_col="model_cif_sha256", decompress=True)
    n_missing = sum(not (d / f).exists() for f in man.input_file)
    if n_missing:
        print(f"  {n_missing} models missing: run  python -I scripts/data/fetch_afdb.py --bench {name}")


def _dimer_one(args) -> dict:
    import tempfile

    from build_dimer_common import Reject, expand_assembly, write_pdb
    from build_dimer_select import _write_polymer_only

    pid, chains, out, keep_holo = args
    holo = (out / "holo" / f"{pid}.pdb") if keep_holo else Path(tempfile.mkdtemp(prefix="burrow_dimer_")) / f"{pid}.pdb"
    try:
        st, info = expand_assembly(pid, set(), set(), select=False)
        write_pdb(st, holo)
        n = {"assembly": _write_polymer_only(holo, out / "inputs" / "assembly" / f"{pid}.pdb", None)}
        for c in chains:
            n[c] = _write_polymer_only(holo, out / "inputs" / "chains" / f"{pid}_{c}.pdb", [c])
        got = sorted(c["chain"] for c in info["chains"])
        return {"pdb": pid, "status": "ok" if got == sorted(chains) else f"chain_mismatch:{got}", "n_atoms": n}
    except Reject as e:
        return {"pdb": pid, "status": f"reject:{e}", "n_atoms": {}}
    except Exception as e:  # noqa: BLE001
        return {"pdb": pid, "status": f"error:{type(e).__name__}:{e}", "n_atoms": {}}
    finally:
        if not keep_holo:
            holo.unlink(missing_ok=True)
            holo.parent.rmdir()


def dimer(jobs: int, keep_holo: bool) -> None:
    ia = P.read_bench_tsv("dimer", "inputs_assembly.tsv")
    ic = P.read_bench_tsv("dimer", "inputs_chains.tsv")
    D = P.PROC / "dimer"
    for sub in ("inputs/assembly", "inputs/chains") + (("holo",) if keep_holo else ()):
        (D / sub).mkdir(parents=True, exist_ok=True)
    chains = ic.groupby("pdb_id").chain.apply(list).to_dict()
    tasks = [(pid, chains[pid], D, keep_holo) for pid in ia.pdb_id]
    with ProcessPoolExecutor(jobs) as ex:
        res = list(ex.map(_dimer_one, tasks, chunksize=2))
    bad = [r for r in res if r["status"] != "ok"]
    na = dict(zip(ia.pdb_id, ia.n_atoms.astype(int)))
    natom_diff = [r["pdb"] for r in res if r["status"] == "ok" and r["n_atoms"]["assembly"] != na[r["pdb"]]]
    print(f"dimer: {len(res)} complexes; failed {len(bad)} {[(r['pdb'], r['status']) for r in bad[:5]]}; "
          f"assembly atom-count differences {len(natom_diff)} {natom_diff[:5]}")
    for link, sub in (("dimer", "assembly"), ("dimer_chains", "chains")):
        P.INPUTS.mkdir(parents=True, exist_ok=True)
        dst = P.INPUTS / link
        if dst.is_symlink() or dst.exists():
            dst.unlink()
        os.symlink(os.path.relpath(D / "inputs" / sub, P.INPUTS), dst)
    report("dimer (assembly)", D / "inputs", ia)
    report("dimer (chains)", D / "inputs", ic)


def main(argv=None) -> int:
    global COPY
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("benches", nargs="*", help="subset of: ligysis ligysis_ni coach420_mlig holo4k_mlig cryptobench pocketwatch "
                                                "af_set af_set_allsites dimer (default: all)")
    ap.add_argument("--copy", action="store_true", help="copy files instead of symlinking")
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--keep-holo", action="store_true", help="dimer: also keep the holo assembly files (for verify_dimer_set.py)")
    a = ap.parse_args(argv)
    COPY = a.copy
    todo = {
        "ligysis": lambda: ligysis("ligysis"), "ligysis_ni": lambda: ligysis("ligysis_ni"),
        "coach420_mlig": lambda: ds("coach420_mlig"), "holo4k_mlig": lambda: ds("holo4k_mlig"),
        "cryptobench": lambda: cryptobench(a.jobs), "pocketwatch": pocketwatch,
        "af_set": lambda: af("af_set"), "af_set_allsites": lambda: af("af_set_allsites"),
        "dimer": lambda: dimer(a.jobs, a.keep_holo),
    }
    bad = [b for b in a.benches if b not in todo]
    if bad:
        ap.error(f"unknown benchmark(s) {bad}")
    print(f"BURROW_DATA = {P.DATA}; PDB store = {P.PDB_MIRROR}")
    for b in a.benches or todo:
        todo[b]()
    return 0


if __name__ == "__main__":
    sys.exit(main())
