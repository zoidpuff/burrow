# Data scripts

Everything needed to evaluate on the BURROW test benchmarks is rebuilt from public sources by
these scripts; the repository itself ships only identifier manifests and our own derived tables
(`benchmarks/`, see `benchmarks/README.md` and `DATA.md`).

## Configuration

| Variable | Default | Meaning |
|---|---|---|
| `BURROW_DATA` | `<repo>/data` | data directory (`raw/`, `pdb/`, `processed/`, `manifests/`, `inputs/`) |
| `BURROW_PDB_MIRROR` | unset | local wwPDB mirror: the directory containing `structures/divided/mmCIF/<xy>/<id>.cif.gz` (the `data/` folder of an rsync mirror). Unset: entries are downloaded one by one from `https://files.rcsb.org/download/<ID>.cif.gz` into `$BURROW_DATA/pdb/` in the same layout. |
| `BURROW_PDB_DERIVED` | `<mirror>/../derived_data` or `$BURROW_DATA/raw/pdb_derived` | wwPDB `derived_data` (training-set / AF-set rebuild only) |
| `BURROW_TOOLS` | `<repo>/tools` | `bin/mmseqs`, `bin/foldseek` (`install_tools.sh`); falls back to `PATH` |
| `PYTHON` | `python3` | interpreter used by the shell scripts (needs the package requirements) |
| `JOBS` | 16 | worker processes in `build_all.sh` |

The Python scripts import `_paths.py`, which resolves these variables, puts `<repo>/src` on the
path and sets `POCKETDETECT_PDB_MIRROR` (read by `pocketdetect.structure`) to the resolved PDB
store, so the package and the scripts read the same entries. Run Python scripts with
`python -I scripts/data/<script>.py` from any directory.

## Order (`build_all.sh` runs steps 1-5; `STEPS="..."` selects steps)

1. **download** (third-party data -> `$BURROW_DATA/raw/`; resumable; pinned versions and sha256):
   `download_p2rank_datasets.sh` (1.9 GB), `download_ligysis.sh` (~2 GB),
   `download_cryptobench.sh` (~5 GB incl. holo mmCIF), `download_pocketwatch.sh` (~2 GB),
   `download_sifts_uniprot.sh` (SIFTS; `WITH_UNIPROT=1` adds UniProt human, AF-set rebuild only).
   `collect_manifests.sh` copies the per-download `MANIFEST.tsv` (sha256) to `manifests/downloads/`.
2. **install** `install_benchmarks.py`: test union, train/dev lists, clusters and the **frozen
   ground truth BURROW was scored on** (LIGYSIS, LIGYSIS_NI, CryptoBench test, PocketWatch test,
   AF set, dimer) from `benchmarks/` into `$BURROW_DATA/{manifests,processed}`. The site tables get
   a `structure_path` for this data directory and are checked against `benchmarks/gt_sha256.tsv`.
3. **fetch** `fetch_pdb.py --bench ligysis dimer` (20,971 + 400 wwPDB entries; checks only, if a
   mirror is set) and `fetch_afdb.py --bench af_set` / `--bench af_set_allsites` (2,527 AFDB v6
   models, sha256-checked against the manifest).
4. **gt** (documented alternative, only with `REBUILD_GT=1`; overwrites the installed tables):
   `build_ligysis_ligands.py` then `build_gt_ligysis.py` (LIGYSIS + LIGYSIS_NI),
   `build_gt_cryptobench.py`, `build_gt_pocketwatch.py`. Each builder compares per-structure site
   counts with the shipped manifest (`[check] ... IDENTICAL`). CryptoBench and PocketWatch rebuild
   identically; a LIGYSIS rebuild differs from the frozen table in the C1-strict ligand atoms of 15
   of 6,882 sites (see DATA.md). COACH420/HOLO4K use the upstream `(mlig).ds` files directly.
5. **inputs** `build_inputs.py` -> `$BURROW_DATA/inputs/<bench>/` (symlinks to the downloads, or
   `--copy`), CryptoBench chain-restricted files, dimer assembly / isolated-chain PDB files
   (`processed/dimer/inputs/`, linked as `inputs/dimer`, `inputs/dimer_chains`). Every file is
   compared with the sha256 in the manifest.
6. **verify** `verify_datasets.py` sanity checks of the downloads.
7. **clusters** (optional; shipped) `build_test_clusters.py` re-clusters the test union at 30 %
   identity with MMseqs2 (`install_tools.sh` first).

## Optional rebuilds of our own datasets

These reproduce the construction of the shipped tables and need much larger inputs. A newer
BioLiP2 / PDB / SIFTS / UniProt state will not reproduce them bit for bit; the shipped tables are
the reference.

* AF set (Track C): `download_sifts_uniprot.sh` with `WITH_UNIPROT=1`, `download_pdb_derived.sh`,
  the AFDB v6 archives `UP000005640_9606_HUMAN_v6.tar` and `swissprot_cif_v6.tar`
  (https://ftp.ebi.ac.uk/pub/databases/alphafold/) in `$BURROW_DATA/raw/afdb/`, then
  `build_af_extract.py`, `build_af_set.py`, `verify_af_set.py`, `build_gt_af.py`
  (`build_af_stress.py`: descriptive stress list; `build_af_io.py`: loader module).
* Dimer benchmark (Track D): `download_biolip2.sh`, a full mirror (`BURROW_PDB_MIRROR`), then
  `build_dimer_scan.py`, `build_dimer_select.py`, `verify_dimer_set.py` (needs
  `scripts/eval_dimer.py`; run `build_inputs.py dimer --keep-holo` to regenerate `holo/` only).
* Training / dev sets (Track A, BioLiP2): `build_trainset_all.sh` (full wwPDB mirror required;
  `download_biolip2.sh`, `download_pdb_derived.sh`, `download_pocketminer.sh`, `install_tools.sh`),
  followed by `apply_audit_exclusions.py` (shipped exclusion list), and the apo counterparts
  `build_apo_train_all.sh`. Dev-only ground truth: `build_gt_cryptobench_trainfolds.py`;
  descriptive holo pairs: `build_gt_cryptobench_test_holo.py`.
* `download_hotpocket.sh`: optional, descriptive proteome analysis only.

Not provided: scPDB is not used for training or testing and is not downloaded by these scripts and not redistributed.
The AF-model training labels for the AF-aware ranker were built from all 47 AFDB v6 proteome
archives (about 157 GB); that builder is not included.

## Helpers

`_common.sh` (shell: `fetch URL OUT [SHA256]`), `_paths.py` (Python paths / PDB access),
`zenodo_fetch.py`, `osf_fetch.py`, `github_subtree_fetch.py` (stdlib-only fetchers that verify the
upstream checksums), `safe_pickle.py` (restricted unpickler for third-party pickles: numpy, pandas
and builtins only).
