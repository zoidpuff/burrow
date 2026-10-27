# Benchmark manifests

This directory holds **identifier lists and ground-truth site tables only**. No third-party
structure files and no third-party raw data files are redistributed (the only structures in the repository are the two
examples in `examples/`: one PDB-derived file, CC0, and one AlphaFold DB model, CC-BY-4.0 with attribution in DATA.md). The site tables are the exact
(frozen) tables BURROW was scored on: our own AF-set and dimer tables, and our conversions of
LIGYSIS (CC-BY-4.0), CryptoBench (MIT) and PocketWatch (MIT), with attribution below. Every input structure is
obtained from its public source with `scripts/data/` (see `scripts/data/README.md`); every
manifest records where each input comes from and the sha256 of the file BURROW was evaluated on,
so a rebuild can be checked file by file (`build_inputs.py` prints the comparison).

Files larger than 1 MB are gzip-compressed (deterministic: mtime 0). `SHA256SUMS` lists every file.
Column `structure_id` is the name predictions must use (`<structure_id>.csv`; for COACH420 /
HOLO4K the id includes `.pdb`, so `<name>.pdb.csv`).

## Test benchmarks

| Directory | Structures | Sites (scored) | Input structures | Ground truth |
|---|---|---|---|---|
| `ligysis/` | 2,775 representative chains | 6,882 (6,721) | ligand-stripped TRANS-frame chains of the LBS-comparison code release (Zenodo 14033286, CC-BY-4.0) | **shipped** frozen `sites.tsv.gz` (derived from LIGYSIS, CC-BY-4.0); rebuild: `build_ligysis_ligands.py` + `build_gt_ligysis.py` |
| `ligysis_ni/` | 2,003 (subset) | 4,255 (4,141) | as `ligysis` | derived at install from `ligysis/sites.tsv.gz` (`ion_prop != 1`, N recomputed) |
| `coach420_mlig/` | 300 | ligands of the `.ds` | P2Rank datasets @ `0236ecb` (`coach420/*.pdb`) | upstream `coach420(mlig).ds`, read at evaluation time |
| `holo4k_mlig/` | 3,448 | ligands of the `.ds` | P2Rank datasets @ `0236ecb` (`holo4k/*.pdb`) | upstream `holo4k(mlig).ds` |
| `cryptobench/` | 222 apo structures | 270 (270) | CryptoBench apo mmCIF (OSF pz4a9, MIT), restricted to `input_chains` | **shipped** frozen `sites.tsv.gz` (MIT); rebuild: `build_gt_cryptobench.py` |
| `pocketwatch/` | 1,566 ESMFold2 folds (1,279 with scored sites) | 2,301 (1,573) | PocketWatch HF dataset @ `db7bd06` (MIT) | **shipped** frozen `sites.tsv.gz` (MIT); rebuild: `build_gt_pocketwatch.py` |
| `af_set/` | 2,526 AFDB v6 models | 6,731 (6,502) | AlphaFold DB v6 (CC-BY-4.0), `model_url` | **shipped** `sites.tsv.gz` (ours) |
| `af_set_allsites/` | 2,527 AFDB v6 models | 7,320 (6,989) | as `af_set` | **shipped** `sites.tsv.gz` (ours; sensitivity table) |
| `dimer/` | 400 assemblies (1,062 isolated-chain inputs) | 807 unique sites (J >= 0.5 grouping), 1,540 ligand copies | assembly 1 of the wwPDB entry (CC0), expanded by `build_inputs.py dimer` | **shipped** `gt.jsonl.gz` + tables (ours) |

### Manifest columns

* `ligysis/manifest.tsv`: `structure_id` (`<pdb>_<chain>`), `pdb_id`, `auth_chain`, `uniprot`,
  `n_sites` (N of top-N), `n_scored`, `n_scored_with_ligand_atoms` (C1-strict DCA denominator in
  BURROW's build), `in_ligysis_ni`, `input_file`, `input_source`
  (`zenodo:<record>:<path in archive>`), `input_sha256`, `gt_frame_entry` (the wwPDB entry whose
  asymmetric-unit frame the ground truth uses). `ligysis/pdb_entries.txt`: the 20,971 wwPDB entries
  needed to rebuild the ground truth (representative entries + every entry contributing a site ligand).
* `ligysis_ni/manifest.tsv`: `structure_id`, `n_sites`, `n_scored`, `input_file`.
* `coach420_mlig/`, `holo4k_mlig/manifest.tsv`: `structure_id` (file name), `pdb_id`, `chain`
  (COACH420 only), `ligand_codes` (upstream `(mlig)` codes, from Binding MOAD), `input_file`,
  `input_source` (`github:rdk/p2rank-datasets@<commit>:<path>`), `input_sha256`.
* `cryptobench/manifest.tsv`: `structure_id` (`<apo_pdb>_<chains>`), `apo_pdb_id`, `input_chains`
  (dash-separated), `uniprot`, `n_sites`, `n_scored`, `holo_pdb_ids`, `input_file` (`.pdb`, or
  `.cif` when a chain id has more than one character), `input_source`, `source_sha256` (the
  CryptoBench mmCIF), `input_sha256` (the chain-restricted file, written with gemmi 0.7.5).
* `pocketwatch/manifest.tsv`: `structure_id` (= UniProt accession), `n_sites` (= N = scored sites),
  `n_scored`, `n_sites_total` (incl. masked sites), `paper_excluded`, `input_file`, `input_source`
  (`hf:datasets/genesisml/PocketWatch@<revision>:<path>`), `input_sha256`.
* `af_set*/manifest.tsv`: `structure_id` (`AF-<UniProt>-F1`), `uniprot`, `afdb_version` (v6),
  `afdb_source` (AFDB v6 archive the model was taken from), `length`, `n_sites`, `n_scored`,
  `input_file`, `model_url`, `model_cif_sha256` (sha256 of the uncompressed mmCIF).
* `af_set*/sites.tsv.gz`: the site tables in `pocketdetect.sites` format without the local
  `structure_path` column (added by `install_benchmarks.py`). Centre = CA centroid of the LIGYSIS
  site residues on the AF model; `residues` in UniProt numbering (chain A); `ligand_atoms` = PDB
  ligand heavy atoms transferred onto the model (local CA RMSD <= 2 A); pLDDT strata. Built by
  `scripts/data/build_af_set.py` + `build_gt_af.py` (docs/AF_BENCHMARK.md).
* `af_set/af_sequences.fasta.gz`: AF model sequences of all 3,473 extracted proteins (test-union input).
* `dimer/`: `complexes.tsv` (one row per complex; `assembly_id` = 1), `chain_map.tsv` (assembly
  chain -> author chain + symmetry operator, entity, UniProt), `manifest_chains.tsv` (chain
  sequences), `site_copies.tsv` (one row per ligand copy: CCD, class, centre, binding residues),
  `unique_sites.tsv` (copies grouped `strict` / `j50`), `gt.jsonl.gz` (one JSON record per complex:
  the per-complex ground truth incl. ligand heavy-atom coordinates, read by `scripts/eval_dimer.py`
  after installation as `processed/dimer/gt/<pdb>.json`), `inputs_assembly.tsv` /
  `inputs_chains.tsv` (method inputs with atom counts and sha256), `pdb_entries.txt`.
  Built by `scripts/data/build_dimer_{scan,select}.py` (docs/DIMER_BENCHMARK.md).

### Frozen site tables (`ligysis/`, `cryptobench/`, `pocketwatch/`, `af_set*/` `sites.tsv.gz`)

`pocketdetect.sites` format, identical to the tables used for scoring except that the local
`structure_path` column is removed; `scripts/data/install_benchmarks.py` re-inserts it for your
data directory and checks the result against `gt_sha256.tsv` (sha256 of each table without
`structure_path`; the second hash column is the sha256 of the original scored file, as recorded
in BURROW's test ledger). LIGYSIS columns include the site centre in the wwPDB asymmetric-unit
frame, author residue ids, `residues_uniprot`, `ion_prop`, the authors' TRANS-frame centre and the
C1-strict `ligand_atoms`. Rebuilding from the upstream releases is the documented alternative
(`scripts/data/README.md`); for LIGYSIS it changes the ligand atoms of 15 of 6,882 sites.

## Shared tables

* `test_union/`: the frozen union of all test chains used for leakage control and clustering:
  `test_union.tsv.gz` (`id, sequence, source_set`; sha256 of the **uncompressed** file in
  `test_union.sha256`), `test_union_meta.tsv.gz` (PDB id, chain, UniProt per row),
  `test_union_pdb_ids.txt`, `test_union_uniprots.txt`, `test_union_counts.json`,
  `test_fold_novelty.tsv.gz` (max Foldseek TM-score of each test chain to the training set; strata).
  Sequences are public PDB / UniProt / AFDB / ESMFold-input sequences.
* `clusters/test_clusters.tsv`: 30 % MMseqs2 clusters of the test union (`id, source_set,
  cluster30, uniprot`), the bootstrap resampling units (4,846 clusters).
* `trainset/`: BioLiP2-derived training and dev entry lists before the leakage audit
  (`trainset_train_entries.tsv` 6,644, `trainset_dev_entries.tsv` 596: `entry_id, pdb, chain,
  uniprot, cluster30, group, rank_in_cluster, n_sites, assembly_status`) and the 186 entries
  removed by the independent leakage audit (`train_dev_audit_exclusions.tsv`), giving 6,475 train
  and 579 dev entries. The training inputs themselves are rebuilt from the wwPDB with
  `scripts/data/build_trainset_all.sh`.

## Licenses and attribution

* `ligysis/sites.tsv.gz` (and the LIGYSIS_NI table derived from it) is an adaptation of the LIGYSIS
  human binding-site data of the LBS-comparison results (Zenodo 14645504, 10.5281/zenodo.14645504)
  by J. Sanchez Utges and G. J. Barton, licensed under CC-BY-4.0
  (https://creativecommons.org/licenses/by/4.0/). Changes: site centres mapped from the authors'
  transformed frame to the wwPDB asymmetric-unit frame, residue ids converted to author numbering,
  redundancy flags, and ligand heavy atoms placed from the PDB (CC0). Cite Utges & Barton 2024,
  J Cheminform 16:126.
* `cryptobench/sites.tsv.gz` is derived from CryptoBench (OSF pz4a9; Skrhak et al. 2025,
  Bioinformatics 41:btae745), MIT license, Copyright (c) 2024 Vit Skrhak.
* `pocketwatch/sites.tsv.gz` is derived from PocketWatch (huggingface.co/datasets/genesisml/PocketWatch,
  revision db7bd06; zPocket paper, arXiv 2610.17696), MIT license (dataset card).
* Full license notices: `THIRD_PARTY_LICENSES.md`.

The identifiers point to third-party resources that keep their own licenses (see `DATA.md`):
wwPDB (CC0), AlphaFold DB (CC-BY-4.0), LIGYSIS / LBS-comparison (CC-BY-4.0), CryptoBench (MIT),
PocketWatch (MIT), P2Rank datasets (no license stated; cite Krivak & Hoksza 2018), BioLiP2
(freely available; cite Zhang et al. 2024), SIFTS / UniProt (CC-BY-4.0). The derived tables we
ship (`af_set*`, `dimer`, test union, clusters, entry lists) are released with this repository,
the converted third-party tables under the upstream licenses above;
please also cite the upstream resources.
