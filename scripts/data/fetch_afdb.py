#!/usr/bin/env python
"""Download the AlphaFold DB v6 models of the AF-mode test set (O5) (AFDB, CC-BY-4.0).

  python -I scripts/data/fetch_afdb.py [--bench af_set] [--jobs 8]

Reads ``benchmarks/<bench>/manifest.tsv`` (columns structure_id, model_url, model_cif_sha256) and
writes ``$BURROW_DATA/inputs/<bench>/<structure_id>.cif.gz`` (gzip of the downloaded mmCIF). The
sha256 of the uncompressed mmCIF is compared with ``model_cif_sha256`` (the model BURROW was
evaluated on, from the AFDB v6 human-proteome / Swiss-Prot archives); mismatches are reported, not
fatal (AFDB may re-issue a model). If a v6 file URL is gone, the AFDB prediction API is queried and
the model it lists is used (with a warning).

Alternative (identical bytes, larger download): the AFDB bulk archives
``UP000005640_9606_HUMAN_v6.tar`` and ``swissprot_cif_v6.tar`` from
https://ftp.ebi.ac.uk/pub/databases/alphafold/ ; pass ``--from-tar`` to extract from local copies.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import sys
import tarfile
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _paths as P  # noqa: E402

API = "https://alphafold.ebi.ac.uk/api/prediction/{}"


def _one(row) -> tuple[str, str]:
    sid, url, want, out = row
    shared = P.INPUTS / "af_set" / out.name  # af_set_allsites reuses the af_set downloads
    if not out.exists() and shared.exists() and shared != out:
        out.symlink_to(os.path.relpath(shared, out.parent))
    if out.exists():
        got = P.sha256_file(out, decompress=True)
        return sid, "present" if got == want else "present_sha_mismatch"
    tmp = out.with_suffix(".download")
    try:
        try:
            P.download(url, tmp)
            note = ""
        except RuntimeError:
            acc = sid.split("-")[1]
            with urllib.request.urlopen(API.format(acc), timeout=60) as r:
                meta = json.load(r)
            alt = next(m["cifUrl"] for m in meta if m.get("entryId") == sid or m.get("modelEntityId", "").startswith(sid))
            P.download(alt, tmp)
            note = f"_via_api:{alt.rsplit('/', 1)[-1]}"
        data = tmp.read_bytes()
        tmp.unlink()
        P.write_gz(data, out)
        got = hashlib.sha256(data).hexdigest()
        return sid, ("downloaded" if got == want else "downloaded_sha_mismatch") + note
    except Exception as e:  # noqa: BLE001
        tmp.unlink(missing_ok=True)
        return sid, f"failed:{e}"


def from_tars(man, tars: list[Path], outdir: Path) -> dict:
    want = {f"{s}-model_v6.cif.gz": s for s in man.structure_id}
    done = {}
    for t in tars:
        with tarfile.open(t, mode="r|") as tf:
            for m in tf:
                s = want.get(Path(m.name).name)
                if s is None or s in done:
                    continue
                data = gzip.decompress(tf.extractfile(m).read())
                P.write_gz(data, outdir / f"{s}.cif.gz")
                done[s] = hashlib.sha256(data).hexdigest()
    return done


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bench", default="af_set")
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--from-tar", nargs="*", default=None, help="local AFDB v6 tar archive(s) to extract from instead")
    ap.add_argument("--limit", type=int, default=0, help="first N models only (testing)")
    a = ap.parse_args(argv)
    man = P.read_bench_tsv(a.bench, "manifest.tsv")
    if a.limit:
        man = man.head(a.limit)
    outdir = P.INPUTS / a.bench
    outdir.mkdir(parents=True, exist_ok=True)
    if a.from_tar is not None:
        done = from_tars(man, [Path(t) for t in a.from_tar], outdir)
        ref = dict(zip(man.structure_id, man.model_cif_sha256))
        bad = [s for s, h in done.items() if h != ref[s]]
        print(f"extracted {len(done)}/{len(man)}; sha mismatches {len(bad)}; missing {len(man) - len(done)}")
        return 0
    rows = [(r.structure_id, r.model_url, r.model_cif_sha256, outdir / f"{r.structure_id}.cif.gz") for r in man.itertuples()]
    status: dict[str, list[str]] = {}
    with ThreadPoolExecutor(a.jobs) as ex:
        for i, (sid, st) in enumerate(ex.map(_one, rows)):
            status.setdefault(st.split(":")[0].split("_via_api")[0], []).append(sid)
            if "mismatch" in st or st.startswith("failed") or "via_api" in st:
                print(f"  {sid}: {st}", file=sys.stderr)
            if (i + 1) % 500 == 0:
                print(f"  {i + 1}/{len(rows)}", flush=True)
    print(f"{a.bench}: " + ", ".join(f"{k}: {len(v)}" for k, v in sorted(status.items())) + f" -> {outdir}")
    return 1 if status.get("failed") else 0


if __name__ == "__main__":
    sys.exit(main())
