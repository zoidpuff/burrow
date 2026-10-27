# BURROW — fast protein ligand-binding pocket detection and ranking

> [!IMPORTANT]
> **This method and its benchmarking were produced by AI agents, as an experiment in testing how well
> agents can run a bioinformatics project autonomously.** A PI agent (Claude Code, Claude Opus 5.5)
> planned the project, delegated work to Claude Opus 5.5 / Claude Sonnet 5.5 sub-agents, reviewed and
> integrated their results, and kept the research record — starting from a single human prompt
> ([PROMPT.md](PROMPT.md)) with minimal human input afterwards (three questions, a time extension, "are we done?" and
> the request for a manuscript and this repository: [prompts/](prompts/)). The human did not write
> code, choose methods or edit results. The agent and sub-agent setup is described in
> [AGENT_SETUP.md](AGENT_SETUP.md). Treat the results accordingly: they were checked by independent
> agent reviewers and verifiers (described below), but not by human experts.

**BURROW** (*Buriedness-driven Ultra-fast Ranking Of pOckets, With confidence awareness*) finds and
ranks ligand-binding pockets in protein structures (PDB/mmCIF; experimental structures, AlphaFold
models, multimeric assemblies). It fills the solvent shell around the protein with 1 Å volume
elements, describes each by multi-scale ray-cast buriedness through a full-atom and a backbone-only
grid, first-hit chemistry and neighbourhood composition, scores the points with a small LightGBM
model, assembles candidate pockets at several buriedness and score levels, and ranks them with a
second LightGBM model trained on a leakage-controlled, LIGYSIS-style BioLiP2 set. There are no
neural networks. It runs on CPU (NumPy/Numba) and GPU (PyTorch/Triton) with identical output, has an
AlphaFold mode (`--af-mode`) that uses pLDDT to prune low-confidence regions, and takes multi-chain
assemblies as input. Method: [docs/METHOD.md](docs/METHOD.md); full report: [docs/REPORT.md](docs/REPORT.md);
manuscript (PLOS Computational Biology format, with supplements): [manuscript/](manuscript/).

## Headline results (test sets, pre-registered; honest caveats below)

All numbers are copied from [docs/REPORT.md](docs/REPORT.md) and [results/test/v2/SUMMARY.md](results/test/v2/SUMMARY.md)
(FREEZE v2, default preset, seed 0 unless stated; 95 % CIs from a paired bootstrap over 30 % sequence clusters).
Claims, endpoints, comparators and margins were fixed in [docs/PREREG.md](docs/PREREG.md) before any test prediction.

| benchmark (endpoint) | BURROW | comparators | verdict |
|---|---|---|---|
| LIGYSIS, 2,775 chains / 6,721 sites: top-N+2 success, DCC ≤ 12 Å (closest-pocket rule) | **72.5** (9.1 pockets/chain) | fpocket+PRANK 60.4 (published; 20.9 pockets/chain), P2Rank 2.5.1 52.6 | superior (all 3 seeds, Δ +11.6 to +12.1, lowest CI bound 9.4) |
| LIGYSIS, same, DCA ≤ 4 Å to ligand atoms (C1-strict) | **54.2** | fpocket+PRANK 31.6, P2Rank 29.8 | superior; the most robust evidence |
| LIGYSIS, Precision1K | **96.1** | fpocket+PRANK 81.7 | superior (pre-registered as non-inferiority) |
| LIGYSIS non-ion sites (post-hoc) | +3.0 to +3.5 vs fpocket+PRANK, +5.4 to +5.9 vs P2Rank | | modest |
| COACH420(mlig), HOLO4K(mlig): DCA4 top-n | 71.0 / 78.2 | P2Rank 2.5.1, fpocket+PRANK | COACH420 inconclusive (+1.6 [−3.0, 5.8]); HOLO4K non-inferior (+1.6 [−1.2, 4.3]) |
| PocketWatch (temporal, predicted structures) | 76.6 | P2Rank `-c alphafold` | non-inferior (+0.8 [−1.4, 2.9]) |
| AF set (2,526 AFDB v6 models, built here) | 64.5 | P2Rank `-c alphafold` | superior (+13.1 [11.0, 15.7]) — but an ion effect: +1.9 [−0.1, 3.9] on non-ion sites |
| CryptoBench (apo/cryptic) | 69.3 | P2Rank | inconclusive (−2.6 [−8.6, 3.0]) |
| Dimer interface sites (400 assemblies, built here) | 84.0 | P2Rank | inconclusive (−3.7 [−8.7, 0.9]) |

**Caveats (read before citing any number).**
1. **Much of the LIGYSIS margin is on ion sites** (38 % of sites; P2Rank-style tools are not trained
   for ions). The v2 margin is +29.5 on ion sites but +2.2 [0.1, 4.3] on "other" small molecules.
2. **The v1 → v2 gain on top-N+2 (64.3 → 72.5) comes from shorter output lists** (32.9 → 9.1 pockets
   per chain), which the LIGYSIS closest-pocket rule rewards; DCA4 and P1K did not change, and maximum
   recall fell from 99.3 to 84.2. Quote 72.5 together with the list length. Use `--min-score none`
   or `--output-rule region` for exhaustive pocket lists.
3. **No gain shown on apo/cryptic sites or dimer interfaces**; allosteric sites were not evaluated.
4. **AF mode removes hallucinated pockets** (0.2 % vs 12.8 % for fpocket+PRANK on test) but is
   equivalent in recall to a simple pLDDT < 70 pocket filter. With the default ranker, AF-set
   precision is low (P1K 58.9 vs 73.9 for P2Rank-AF); the optional AF ranker reaches 73.9
   (descriptive, test-informed).
5. Fold-disjoint retraining stays within noise on 8 of 9 test rows (COACH420 −3.2).

**Speed** (docs/PERF.md; same 200 LIGYSIS chains for every tool, one process including start-up
and I/O, shared node, ratios ±30 %): default 142 ms/structure vs P2Rank 2.5.1 209 ms (≈ 1.5×) and
fpocket 4.2.3 605 ms. The optional `--preset fast` takes 48 ms (≈ 4.4× P2Rank, ≈ 12.6× fpocket) at
a cost of about 1–2 points on dev; it was added after the tests and is not pre-registered. One core,
warm, including parsing: fast 31.5 ms, default 99.2 ms, accurate 206.4 ms. Over 10,000 structures,
3 GPUs (8 workers each) vs 24 CPU workers: fast 646 vs 545 structures/s, default 411 vs 171/s.
The first call after installation compiles Numba code (about 37 s; later starts about 3 s).

## Install

Tested with Python 3.12 on Linux x86-64 (versions pinned in `pyproject.toml`).

```bash
git clone <this repository> burrow && cd burrow
uv venv --python 3.12 .venv && source .venv/bin/activate
uv pip install -e ".[test]"            # or: python -m pip install -e ".[test]"
uv pip install -e ".[gpu]"             # optional GPU backend (torch 2.6 + triton 3.2, CUDA 12)
uv pip install -e ".[data]"            # optional: benchmark / training-set construction scripts
python scripts/smoke.py                # 1-minute self-check (model checksums, CPU backends, examples)
```

**Models.** The model files are in the repository's `models/` directory (they are not part of the
Python package). `burrow` looks for them in this order: `--model-dir DIR` (or a single `--model
file.json`), the `BURROW_MODELS` environment variable, `./models` in the current directory, and
`models/` next to the sources (editable install). With a regular `pip install .`, point to them
explicitly, e.g. `export BURROW_MODELS=/path/to/burrow/models`; otherwise `burrow` stops with an
error that explains this.

## Quickstart

```bash
# one structure (only protein atoms are used: ligands, waters, ions are ignored)
burrow predict examples/1a28_A.pdb --out out/

# a directory or a list of files, 16 CPU worker processes
burrow predict structures/ --out out/ --workers 16
burrow predict @my_files.txt --out out/ --workers 16

# AlphaFold / predicted model (pLDDT in the B-factor column): prunes low-confidence "spaghetti",
# soft occlusion by pLDDT. Do not use --af-mode on experimental structures (B-factors are not pLDDT).
burrow predict examples/AF-P00918-F1-model_v6.cif.gz --out out_af/ --af-mode
#   optional AF-aware ranker (better calibrated scores across proteins; reference backend):
burrow predict AF-model.cif.gz --out out_af/ --af-mode --af-ranker models/afr_final_afpdb_pl.json

# multimeric assembly (biological assembly file; pockets at interfaces are found across chains)
burrow predict 1abc-assembly1.cif.gz --out out_asm/

# presets: default (pre-registered), accurate (slower, about +1-2 points on non-ion dev sites),
# fast (about 3x faster than default, about 1-2 points lower on dev; not pre-registered)
burrow predict examples/1a28_A.pdb --out out_fast/ --preset fast
burrow predict examples/1a28_A.pdb --out out_acc/ --preset accurate

# exhaustive pocket lists: no output score floor (up to 50 pockets) ...
burrow predict examples/1a28_A.pdb --out out_all/ --min-score none
# ... or the v2 list plus the best pocket of every uncovered surface region (dev evidence only)
burrow predict examples/1a28_A.pdb --out out_region/ --output-rule region

# ligand definition: --ranker all (ions + organic ligands; default) | small (non-ion, P2Rank-style)
# | geometry (learning-free baseline)
burrow predict examples/1a28_A.pdb --out out_small/ --ranker small

# GPU: one process per GPU, CPU workers per GPU for parsing / post-processing
burrow predict proteome_dir/ --out out_gpu/ --device cuda:0,1 --workers 8
```

`--backend auto` (default) uses the fast backend (Numba on CPU, Triton on GPU) and falls back to the
reference implementation for any input it cannot handle; `--backend reference` forces the reference.
All backends produce identical files (tested in `tests/`). `burrow predict -h` lists all options.

## Output

Per input `<stem>` (file name without extension):

* `out/<stem>.csv` — one row per pocket, best first: `rank,score,center_x,center_y,center_z,residues`.
  `score` is the ranker's probability-like score, comparable across proteins; `residues` are
  space-separated `chain:resnum[icode]` in the author numbering of the input.
* `out/<stem>.points.csv` — the pocket's volume elements, `rank,x,y,z` (omit with `--no-points`).
* `out/timing.csv` — per-structure status, backend and timings.

Default list length: pockets with score < 0.03 are dropped once 3 pockets are listed (FREEZE v2
output floor; typically 6–9 pockets per chain). Example: `examples/expected/default/1a28_A.csv`
(rank 1 is the progesterone site of 1A28).

## Repository contents

| path | contents |
|---|---|
| `src/pocketdetect/` | the package: `burrow/` (method, CLI, fast CPU/GPU backend, AF mode, output rules), `geometry/` (grids, buriedness, clustering; CPU and GPU), structure I/O, evaluation (`evaluate`, `ligands`, `site_eval`, `sites`, `benchmarks`, `ligysis`, `clusters`, `controls`, `prereg`), dataset readers (`datasets/`, `importers/`) |
| `models/` | FREEZE v2 `default`/`accurate` models (`all`, `small` rankers; seeds s0–s2), `fast` preset models, optional AF ranker; `SHA256SUMS`; [models/README.md](models/README.md) |
| `predictions/` | BURROW v2 (default, seed 0) pocket predictions for every test benchmark, one `.csv.gz` per benchmark; [predictions/README.md](predictions/README.md) |
| `results/` | evaluation summaries: pre-registered analyses (`test/v1`, `test/v2`), descriptive and post-hoc rows, test ledger, baselines, ablations, dev-cycle summaries; [results/README.md](results/README.md) |
| `benchmarks/` | test-set manifests (IDs, chains, sources, checksums), our own benchmark tables (AF set, dimers), frozen site tables of LIGYSIS / CryptoBench / PocketWatch (redistributed under their licenses), cluster table, train/dev ID lists; [benchmarks/README.md](benchmarks/README.md) |
| `scripts/` | `predict_benchmarks.py`, `evaluate_benchmark.py`, training (`burrow_*`), `reproduce_all.sh`, `smoke.py`, `check_release_clean.py`; `scripts/data/` downloads and builders ([scripts/data/README.md](scripts/data/README.md)) |
| `docs/` | method, pre-registration, evaluation protocol, benchmarks, performance, the full report, and the agents' research record (`docs/research_record/`: research tree and decision log, literature review, design, process lessons) |
| `examples/` | two small structures (PDB 1A28 chain A, CC0; AFDB AF-P00918-F1, CC-BY-4.0) and expected outputs |
| `PROMPT.md`, `prompts/`, `AGENT_SETUP.md` | the human prompts (verbatim) and the agent setup |
| `manuscript/` | the manuscript (`main.pdf`), supplements S1–S3 Text and S1 Table, figures with their data and plotting script, Markdown sources and build script, and the agents' manuscript review and reference check; [manuscript/README.md](manuscript/README.md) |
| `baselines/`, `reviews/` | baseline run notes and independent review records cited by the manuscript |

**Building on BURROW:** [docs/FOR_FURTHER_DEVELOPMENT.md](docs/FOR_FURTHER_DEVELOPMENT.md) (code map, every pocket representation via `pocketdetect.burrow.export`, practical learnings).

## Reproducing the benchmarks

Data are not redistributed except identifier manifests and the ground-truth tables listed above;
[DATA.md](DATA.md) gives source, version, checksum and license for every dataset (scPDB was not used
and is not redistributed). Paths default to `data/` in the repository (`BURROW_DATA`), and a local
wwPDB mirror can be used with `BURROW_PDB_MIRROR` (otherwise entries are downloaded from RCSB).

```bash
scripts/reproduce_all.sh smoke                       # self-check, no data needed
scripts/reproduce_all.sh data                        # download public data, install manifests + ground truth, build inputs
scripts/reproduce_all.sh rescore                     # re-score the shipped predictions/ (headline numbers)
DEVICE=cuda:0 scripts/reproduce_all.sh predict evaluate   # re-run BURROW on all test sets and score it
scripts/reproduce_all.sh trainset featurize train freeze  # retrain from scratch (days of CPU; ~79 GB RAM)
```

Single benchmark: `python scripts/evaluate_benchmark.py ligysis --pred-file predictions/ligysis.csv.gz`
re-scores the shipped LIGYSIS predictions (top-N+2 72.5, DCA4 54.2, P1K 96.1). The baselines
(P2Rank, fpocket, PRANK and others) are third-party tools and are not included; their published
versions and our re-run settings are documented in `docs/EVALUATION.md` and `results/baselines/`.

Notes on provenance: the shipped model files differ from the frozen research files only in scrubbed
path strings inside their `meta` provenance fields (checksum mapping in `models/README.md`); commit
hashes in the summaries refer to the private research repository. `PROMPT.md` is verbatim except
for one redacted local file-system path.

## Citation

If you use BURROW, please cite (placeholder until publication):

```
BURROW authors (2026). BURROW: a fast protein pocket finder and ranker, designed, built and
benchmarked end to end by AI agents. Manuscript in preparation. https://github.com/zoidpuff/burrow
```

Please also cite the datasets and tools listed in [DATA.md](DATA.md) and the methods whose ideas
BURROW builds on (LIGSITE, P2Rank, fpocket/PRANK, LIGYSIS and others; see `docs/research_record/LITERATURE.md`).

## License

Code, models and predictions: MIT ([LICENSE](LICENSE)). Third-party data and tools keep their own
licenses: see [DATA.md](DATA.md) and [benchmarks/THIRD_PARTY_LICENSES.md](benchmarks/THIRD_PARTY_LICENSES.md)
(e.g. LIGYSIS CC-BY-4.0, CryptoBench and PocketWatch MIT, PDB CC0, AlphaFold DB CC-BY-4.0).
