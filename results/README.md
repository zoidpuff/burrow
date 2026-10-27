# Evaluation summaries

Summaries of the BURROW development, freeze and test-set evaluations, copied from the research
repository. The test-set summaries were produced by the pre-registered pipeline
(`docs/PREREG.md`): test sets were evaluated only through `scripts/run_test_eval.py`, which checks
model checksums and appends every evaluation to `TEST_LEDGER.md`.

File paths mentioned inside these documents (e.g. `results/dev/biolip/...`, `data/processed/...`,
`baselines/...`) refer to the layout of the original research repository; files that are not shipped
here are referenced for provenance only. Absolute paths were made repository-relative and machine
host names were removed; references to the frozen model files
(`results/dev/freeze_v2/models/<name>.json`, `results/dev/freeze_fast/models/<name>.json`,
`results/dev_af/models/afr_final_afpdb_pl.json`) were rewritten to `models/<name>.json`, where the
release ships them. v1 model paths (`results/dev/freeze/models/...`) were left unchanged; v1 models
are not shipped. No numbers were changed.

## Test set

| file | content |
|---|---|
| `test/v2/SUMMARY.md`, `test/v2/summary.json` | **Main result.** Pre-registered analysis of FREEZE v2: gatekeeping family 1 (C1, C1-strict, C2 on LIGYSIS), family 2 (O2–O6, Holm), secondary/descriptive endpoints, controls |
| `test/v2/DESCRIPTIVE.md`, `test/v2/descriptive_*.json` | Descriptive rows, not part of the pre-registered families (ablation models on test, fast preset, AF-mode off, isolated dimer chains, timings) |
| `test/v2/POSTHOC.md`, `test/v2/posthoc.json` | Post-hoc descriptive analyses (not pre-registered; no claims) |
| `test/v2/<benchmark>/<method>/` | Per benchmark and method: `summary.csv` (metrics with 95% cluster-bootstrap CIs), `summary_uniprot.csv` (UniProt-level bootstrap sensitivity), `eval_info.json` (evaluation settings and headline values), `run_record.json` (commit, code/model/GT/prediction checksums, command line); `hallucination_summary.csv` (AF set) and `summary_eval_dimer_point.csv` (dimer) where applicable. Methods: `burrow_<ranker>_<preset>_s<seed>[_af]` (frozen BURROW v2), `desc.*` (descriptive variants) |
| `test/v2/comparators/<benchmark>/<method>/` | Same summaries for the baselines (P2Rank, fpocket+PRANK re-runs on identical inputs; published numbers where used) |
| `test/v2/controls/<benchmark>/<control>/` | Same summaries for the sanity controls (random, tiling, centroid, oracle) |
| `test/v1/SUMMARY.md`, `test/v1/summary.json` | Pre-registered analysis of FREEZE v1 (reported alongside v2 as required by the pre-registration) |
| `TEST_LEDGER.md` | Append-only log of every test-set evaluation (time, version, commits, checksums, headline values) |
| `verify_test/VERIFY.md` | Independent re-computation of the v1/v2 test headline numbers |
| `audit/LEAKAGE_AUDIT.md` | Independent train/dev vs test leakage audit (sequence, PDB-ID and UniProt overlap) |
| `baselines/HEADLINES.md` | Baseline headline numbers |
| `baselines/ligysis_gate.md`, `validation/ligysis_reproduction.md` | Reproduction gates: our harness and baseline re-runs vs the published LIGYSIS numbers |

Per-pocket / per-site / per-structure evaluation tables and the raw prediction files of the
baselines are not included; BURROW's test predictions are in `predictions/`.

## Development (train/dev only; no test data)

| file | content |
|---|---|
| `dev/FREEZE_v2.md` | FREEZE v2 model list with sha256 (the models evaluated in `test/v2/`) |
| `dev/FREEZE_fast.md` | Additional `--preset fast` models (not pre-registered) |
| `dev/DEV_RESULTS.md` | Phase 1 dev results |
| `dev/biolip/PHASE2.md`, `dev/biolip/PHASE3.md`, `dev/biolip/final_table.md` | BioLiP2-trained models: dev results and ranker improvements up to the feature freeze |
| `dev/biolip/V2_CYCLE.md` | v2 cycle (output score floor; apo/cryptic pockets) |
| `dev/biolip/V3_CYCLE.md`, `dev/biolip/V3b_CYCLE.md` | v3/v3b cycles (negative results; no further freeze) |
| `dev/biolip/FAST_PRESET.md` | Selection of the fast preset |
| `dev/biolip/NONION_ERRORS.md` | Error analysis of the `small` ranker on dev |
| `ablations/ABLATIONS.md`, `ablations/ablations_long.csv` | Pre-registered ablations (dev only), summary and long-format table |
