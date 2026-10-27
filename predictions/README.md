# BURROW test-set predictions (v2, default preset, seed 0)

Pocket predictions of the frozen BURROW v2 models on every test benchmark, as produced by the
pre-registered test runs (one consolidated, gzip-compressed CSV per benchmark). Only pocket-level
output is included; per-point output (`*.points.csv`) is not shipped. Evaluation results computed
from these files are in `results/test/v2/` (see `results/README.md`).

## Files

| file | benchmark | structures | pockets | ranker | `--af-mode` | coordinate frame / residue numbering |
|---|---|---:|---:|---|---|---|
| `ligysis.csv.gz` | LIGYSIS (C1) | 2,775 | 25,142 | `all` | no | wwPDB asymmetric unit, author numbering (**scored frame**) |
| `ligysis_inputframe.csv.gz` | LIGYSIS (C1) | 2,775 | 25,142 | `all` | no | input frame: LIGYSIS TRANS-frame representative chain, label_seq numbering |
| `ligysis_ni.csv.gz` | LIGYSIS non-ion (descriptive) | 2,775 | 20,696 | `small` | no | wwPDB asymmetric unit, author numbering (**scored frame**) |
| `ligysis_ni_inputframe.csv.gz` | LIGYSIS non-ion (descriptive) | 2,775 | 20,696 | `small` | no | input frame (as `ligysis_inputframe`) |
| `coach420_mlig.csv.gz` | COACH420 (mlig) (O2) | 300 | 1,602 | `small` | no | input structure, author numbering |
| `holo4k_mlig.csv.gz` | HOLO4K (mlig) (O2) | 3,448 | 27,314 | `small` | no | input structure, author numbering |
| `cryptobench.csv.gz` | CryptoBench test, apo (O4) | 222 | 1,379 | `small` | no | input structure, author numbering |
| `pocketwatch.csv.gz` | PocketWatch temporal test (O3) | 1,566 | 15,451 | `small` | yes | input (predicted) structure |
| `af_set.csv.gz` | AF set: LIGYSIS UniProts on AFDB (O5) | 2,526 | 25,375 | `all` | yes | input AlphaFold model |
| `dimer.csv.gz` | Dimer benchmark, full-assembly input (O6) | 400 | 5,961 | `all` | no | input assembly, author numbering |
| `dimer_chains.csv.gz` | Dimer benchmark, isolated chains (descriptive only) | 1,062 | 8,799 | `all` | no | input chain, author numbering |

`MANIFEST.tsv` lists, per file: benchmark, frame, number of structures and pockets, ranker,
preset, AF mode, model file (`models/<name>.json` in this repository), model sha256, the git commit
of the prediction code, and the sha256 of the `.csv.gz` file.

Every input structure has at least 3 pockets, so every structure of each benchmark appears in its
file (the number of structures equals the number of per-structure prediction files of the original
run; no rows were dropped or altered when consolidating).

## Columns

| column | meaning |
|---|---|
| `structure_id` | input identifier = the input file name without extension (see below) |
| `rank` | 1-based pocket rank within the structure (1 = highest score) |
| `score` | ranker score of the pocket (higher = more likely ligandable); values exactly as written by the run |
| `center_x`, `center_y`, `center_z` | pocket centre (Å) in the coordinate frame given above |
| `residues` | space-separated pocket residues, each `chain:resnum[icode]` (e.g. `A:57`, `G:43A`); order within the list carries no meaning |

Rows are sorted by `structure_id`, then `rank`. Numeric values are copied verbatim from the original
per-structure output files (the LIGYSIS scored-frame files carry 4 decimals because they were
re-written after the frame transformation; all other files carry BURROW's native output precision).

`structure_id` conventions: LIGYSIS / LIGYSIS_NI and CryptoBench `<pdb>_<chain>` (e.g. `1a52_A`);
COACH420 and HOLO4K the original dataset file names including `.pdb` (e.g. `1a26A.pdb`, `121p.pdb`);
PocketWatch the UniProt accession; AF set `AF-<UniProt>-F1`; dimer the PDB ID of the assembly;
dimer_chains `<pdb>_<chain>`.

## Coordinate frames and residue ids

- Residue ids use the chain IDs and author residue numbering (`auth_seq_id` + insertion code) of
  the input structure, with one exception: the LIGYSIS `*_inputframe` files.
- **LIGYSIS / LIGYSIS_NI.** BURROW was run on the LIGYSIS authors' representative chains, which are
  provided in their superposed "TRANS" frame. `*_inputframe.csv.gz` is BURROW's raw output on those
  files (TRANS-frame coordinates; residue numbers are the files' own numbering (label_seq-based, with occasional insertion codes), and chain
  letters are those of the TRANS file, which can differ from the wwPDB author chain). This is what you
  should compare against if you re-run BURROW on the same inputs.
  `ligysis.csv.gz` / `ligysis_ni.csv.gz` are the same pockets mapped to the wwPDB asymmetric-unit
  frame and author numbering of the corresponding chain (centre x = Rᵀ x_T + c0; label_seq → author
  residue id; residues without an author mapping are dropped). This is the frame in which the
  pre-registered LIGYSIS endpoints were scored, and the same conversion was applied to all baselines.
- All other benchmarks: the frame of the input file itself (no transformation).

## Method / provenance

- Models: `models/burrow_all_default_s0.json` (sha256 `0fa4da97c64cc40fb739b87c38372813aa721d52f37a538d3c57dbc8bfc30f56`)
  and `models/burrow_small_default_s0.json` (sha256 `c0b88419a328332ed8c5c0a2dab3ee2da96aea882001d1ff6aaf20dab8ab34c4`),
  i.e. FREEZE v2, `default` preset, seed index 0 (`results/dev/FREEZE_v2.md`). These are the
  checksums of the original frozen files; the copies shipped in `models/` differ only in scrubbed
  provenance strings inside `meta` and have new checksums (mapping in `models/README.md`). The
  predictions are reproduced exactly by the shipped files (verified on `examples/`).
- Commit hashes refer to the private research repository; they are recorded for provenance only.
- Prediction code commit: `0d925b2d5bb27f4e028cf7bd2eccd9cd18d7a71d` (all files, including the
  descriptive `dimer_chains` run). Model checksums and the commit are taken from each run's record.
- Ranker per benchmark (pre-registered, `docs/PREREG.md`): `all` (ions included) for LIGYSIS,
  AF set and dimers; `small` (non-ion ligands) for LIGYSIS_NI, COACH420, HOLO4K, CryptoBench and
  PocketWatch. PocketWatch and AF set inputs are predicted structures and were run with `--af-mode`.
- v2 output rule: pockets with ranker score < 0.03 are dropped once 3 pockets have been kept
  (`formation.min_score = 0.03`, `formation.min_keep = 3`), so every structure has ≥ 3 pockets and
  pockets beyond rank 3 all have score ≥ 0.03.
- All runs used BURROW's fast backend (`python -m pocketdetect.burrow.fast predict <input dir>
  --out <dir> --model models/burrow_<ranker>_default_s0.json --ranker <ranker> --no-points
  [--af-mode]`; GPU for the experimental-structure benchmarks, CPU for the `--af-mode` runs and
  `dimer_chains`).

## Input sets

The exact input structures (identifiers, sources and counts) for each benchmark are defined in the
manifests under `benchmarks/` — see `benchmarks/README.md`. LIGYSIS and LIGYSIS_NI share the same
2,775 inputs and differ only in the ranker and in the ground-truth sites scored (ion sites excluded
for LIGYSIS_NI). The dimer benchmark is predicted on the full biological assembly (`dimer`); the
`dimer_chains` file contains the same assemblies split into isolated chains and is descriptive only.
