"""Shared locations for the data scripts (import this module before ``pocketdetect``).

Environment variables
---------------------
BURROW_DATA         data directory (default ``<repo>/data``). Layout:
                      raw/<dataset>/            third-party downloads (download_*.sh)
                      pdb/                      wwPDB entries fetched from RCSB when no mirror is set
                      processed/gt/<bench>/     ground-truth site tables (build_gt_*.py, install_benchmarks.py)
                      processed/dimer/          dimer benchmark (install_benchmarks.py + build_inputs.py)
                      processed/clusters/       30 % sequence clusters (install_benchmarks.py or build_test_clusters.py)
                      manifests/                ID lists (install_benchmarks.py)
                      inputs/<bench>/           prediction inputs (build_inputs.py)
BURROW_PDB_MIRROR   optional local wwPDB rsync mirror: the directory that contains
                    ``structures/divided/mmCIF/<xy>/<id>.cif.gz`` (the ``data/`` folder of a
                    ``rsync.wwpdb.org::ftp_data`` mirror). If unset, entries are downloaded one by one
                    from RCSB into ``$BURROW_DATA/pdb`` (same layout) by ``fetch_pdb.py``.
BURROW_PDB_DERIVED  optional wwPDB ``derived_data`` directory (pdb_entry_type.txt, index/resolu.idx,
                    pdb_seqres.txt); default ``<mirror>/../derived_data`` if present, else
                    ``$BURROW_DATA/raw/pdb_derived`` (download_pdb_derived.sh). Only the training-set /
                    AF-set rebuilds need it.
BURROW_TOOLS        directory with ``bin/mmseqs`` and ``bin/foldseek`` (default ``<repo>/tools``;
                    install_tools.sh). Falls back to the binaries on PATH.
BURROW_RCSB_URL     RCSB download base (default https://files.rcsb.org/download).

The package ``pocketdetect`` reads the PDB mirror location from ``POCKETDETECT_PDB_MIRROR``; this
module sets it to the resolved mirror so that package and scripts agree.
"""

from __future__ import annotations

import gzip
import hashlib
import io
import os
import shutil
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DATA = Path(os.path.abspath(os.path.expanduser(os.environ.get("BURROW_DATA", str(REPO / "data")))))
RAW = DATA / "raw"
PROC = DATA / "processed"
GT = PROC / "gt"
MANIFESTS = DATA / "manifests"
INPUTS = DATA / "inputs"
BENCH = REPO / "benchmarks"
TOOLS = Path(os.path.abspath(os.path.expanduser(os.environ.get("BURROW_TOOLS", str(REPO / "tools")))))
RCSB_URL = os.environ.get("BURROW_RCSB_URL", "https://files.rcsb.org/download").rstrip("/")

_mirror_env = os.environ.get("BURROW_PDB_MIRROR") or os.environ.get("POCKETDETECT_PDB_MIRROR")
HAS_MIRROR = bool(_mirror_env)
PDB_MIRROR = Path(os.path.abspath(os.path.expanduser(_mirror_env))) if _mirror_env else DATA / "pdb"
os.environ["POCKETDETECT_PDB_MIRROR"] = str(PDB_MIRROR)


def _derived_default() -> Path:
    if os.environ.get("BURROW_PDB_DERIVED"):
        return Path(os.path.abspath(os.path.expanduser(os.environ["BURROW_PDB_DERIVED"])))
    if HAS_MIRROR and (PDB_MIRROR.parent / "derived_data").is_dir():
        return PDB_MIRROR.parent / "derived_data"
    return RAW / "pdb_derived"


PDB_DERIVED = _derived_default()

# the package lives in <repo>/src
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))

# third-party dataset locations inside RAW (as produced by the download scripts)
P2RANK_DS = RAW / "p2rank_datasets" / "current"
LIGYSIS_RESULTS = RAW / "ligysis" / "lbs_comparison_results"
LIGYSIS_CODE = RAW / "ligysis" / "lbs_comparison_code"
LIGYSIS_TRANS = LIGYSIS_CODE / "LBS-comparison-v2.0.0" / "bartongroup-LBS-comparison-820714c" / "DATA" / "trans_rep_chains"
CRYPTOBENCH = RAW / "cryptobench"
POCKETWATCH = RAW / "pocketwatch" / "current"
BIOLIP = RAW / "biolip2" / "current"
SIFTS_TSV = RAW / "sifts" / "pdb_chain_uniprot.tsv.gz"
UNIPROT_HUMAN = RAW / "uniprot" / "uniprot_human_reviewed.tsv.gz"


def tool(name: str) -> str:
    """Path of mmseqs / foldseek: $BURROW_TOOLS/bin/<name>, else PATH."""
    p = TOOLS / "bin" / name
    if p.exists():
        return str(p)
    w = shutil.which(name)
    if w:
        return w
    raise FileNotFoundError(f"{name} not found in {TOOLS / 'bin'} or on PATH (run scripts/data/install_tools.sh)")


def tmpdir(prefix: str) -> Path:
    """Fresh temporary directory under $TMPDIR (or the system default)."""
    return Path(tempfile.mkdtemp(prefix=prefix))


def data_rel(p: str | os.PathLike) -> Path:
    """Resolve a path stored relative to the project (``data/...``) against BURROW_DATA."""
    s = str(p)
    if os.path.isabs(s):
        return Path(s)
    if s.startswith("data/"):
        return DATA / s[len("data/"):]
    return REPO / s


def rel_to_data(p: str | os.PathLike) -> str:
    """Inverse of data_rel for provenance strings: ``data/<path relative to BURROW_DATA>``."""
    p = Path(p)
    try:
        return "data/" + str(p.relative_to(DATA))
    except ValueError:
        return p.name


def sha256_file(path: str | os.PathLike, decompress: bool = False) -> str:
    h = hashlib.sha256()
    op = gzip.open if decompress else open
    with op(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_gz(data: bytes, path: str | os.PathLike) -> None:
    """Deterministic gzip (mtime 0, no file name)."""
    buf = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=buf, mtime=0) as g:
        g.write(data)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(str(path) + ".part")
    tmp.write_bytes(buf.getvalue())
    tmp.replace(path)


def bench_file(*parts: str) -> Path:
    """A shipped file under <repo>/benchmarks (accepts the plain or the ``.gz`` name)."""
    p = BENCH.joinpath(*parts)
    if p.exists():
        return p
    gz = p.with_name(p.name + ".gz")
    if gz.exists():
        return gz
    raise FileNotFoundError(p)


def read_bench_tsv(*parts: str):
    import pandas as pd

    return pd.read_csv(bench_file(*parts), sep="\t", dtype=str, keep_default_na=False)


# ----------------------------------------------------------------------------- wwPDB entries
def pdb_entry_path(pdb_id: str) -> Path:
    """Asymmetric-unit mmCIF in the wwPDB divided layout under PDB_MIRROR."""
    pid = pdb_id.lower()
    return PDB_MIRROR / "structures" / "divided" / "mmCIF" / pid[1:3] / f"{pid}.cif.gz"


def download(url: str, out: Path, retries: int = 4, timeout: int = 120) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_name(out.name + f".part{os.getpid()}")
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "burrow-data-scripts"})
            with urllib.request.urlopen(req, timeout=timeout) as r, open(tmp, "wb") as f:
                shutil.copyfileobj(r, f)
            tmp.replace(out)
            return
        except urllib.error.HTTPError as e:
            last = e
            if e.code == 404:
                break
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            last = e
        time.sleep(2 * (attempt + 1))
    tmp.unlink(missing_ok=True)
    raise RuntimeError(f"download failed: {url}: {last}")


def ensure_pdb_entry(pdb_id: str) -> Path:
    """Return the entry path; download it from RCSB if no mirror is configured and it is absent."""
    p = pdb_entry_path(pdb_id)
    if p.exists() or HAS_MIRROR:
        return p
    download(f"{RCSB_URL}/{pdb_id.upper()}.cif.gz", p)
    return p


def check_against_manifest(df, bench: str) -> int:
    """Compare per-structure site counts of a rebuilt site table with benchmarks/<bench>/manifest.tsv.
    Prints a summary; returns the number of structures that differ (missing, extra or other counts)."""
    import pandas as pd

    try:
        man = read_bench_tsv(bench, "manifest.tsv")
    except FileNotFoundError:
        print(f"[check] no shipped manifest for {bench}")
        return 0
    g = df.groupby("structure_id")
    got = pd.DataFrame({"n_sites": g.n_sites.first().astype(int), "n_scored": g.scored.apply(lambda s: int(pd.Series(s).astype(int).sum()))})
    ref = man.set_index("structure_id")[["n_sites", "n_scored"]].astype(int)
    missing = sorted(set(ref.index) - set(got.index))
    extra = sorted(set(got.index) - set(ref.index))
    common = ref.index.intersection(got.index)
    diff = [s for s in common if tuple(ref.loc[s]) != tuple(got.loc[s])]
    n = len(missing) + len(extra) + len(diff)
    print(f"[check] {bench}: {len(ref)} structures in the shipped manifest; missing {len(missing)} {missing[:5]}, "
          f"extra {len(extra)} {extra[:5]}, count differences {len(diff)} {diff[:5]} -> {'IDENTICAL' if n == 0 else 'DIFFERS'}")
    return n


def tool_path(name: str) -> Path:
    """Like tool() but never raises (returns the default location if the binary is not found)."""
    try:
        return Path(tool(name))
    except FileNotFoundError:
        return TOOLS / "bin" / name
