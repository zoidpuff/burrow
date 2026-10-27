#!/usr/bin/env bash
# =====================================================================================================
# BURROW reproduction driver. Steps, in the documented order:
#
#   smoke       1 min   model checksums, reference == fast backend, examples/expected/ (no data needed)
#   rescore     ~10 min re-score the shipped predictions/ on every benchmark (needs `data` step: install)
#   data        hours   download public data, install shipped manifests + frozen ground truth, build inputs
#   predict     ~10 min re-run BURROW (FREEZE v2, default preset, seed 0) on every test benchmark [GPU optional]
#   evaluate    ~10 min score the `predict` outputs (same evaluator as `rescore`)
#   trainset    [LONG]  rebuild the leakage-controlled BioLiP2 train/dev set + D6 audit exclusions
#   featurize   [LONG]  point features + labels (train incl. assemblies, dev), default and accurate designs
#   train       [LONG]  12 models: 3 seeds x {all, small} x {default, accurate}
#   freeze      [LONG]  FREEZE v1 provenance, output floor tau by train cluster-CV, FREEZE v2
#   speed       ~5 min  1-core timings of the presets on the 200 LIGYSIS speed chains
#
#   scripts/reproduce_all.sh <step> [<step> ...]      e.g. scripts/reproduce_all.sh smoke data rescore
#   scripts/reproduce_all.sh all                      every step in order (days of CPU for trainset..freeze)
#
# Environment: BURROW_DATA (default <repo>/data), BURROW_PDB_MIRROR (optional local wwPDB mirror),
# BURROW_MODELS (default <repo>/models), PYTHON (default: python of the active environment),
# DEVICE (default cpu; e.g. cuda:0 or cuda:0,1), WORKERS (default 8), OUT (default <repo>/outputs).
# Training writes to results/dev/ and data/cache/ inside the repository (git-ignored except results/).
# Seeds: pocketdetect.seeds (single source of truth). Data provenance and licenses: DATA.md.
# Hardware used for the published numbers: 64-core AMD EPYC 9554, 4x RTX 4090, ~79 GB usable RAM.
# =====================================================================================================
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${PYTHON:-python}"
DEVICE="${DEVICE:-cpu}"
WORKERS="${WORKERS:-8}"
OUT="${OUT:-outputs}"
BENCHES="ligysis ligysis_ni coach420_mlig holo4k_mlig cryptobench pocketwatch af_set dimer dimer_chains"
FF="--n-rays 30 --max-len 16 --subsample 3"     # default-preset feature design
TF="--score-floor 0.7"                          # default preset: score buried points only
log() { echo "[reproduce $(date +%H:%M:%S)] $*"; }

step_smoke() { $PY scripts/smoke.py; }

step_data() {
  bash scripts/data/build_all.sh               # see scripts/data/README.md (STEPS=... to select parts)
}

step_rescore() {                               # shipped predictions -> headline metrics (results/test/v2/SUMMARY.md)
  for b in $BENCHES; do
    $PY scripts/evaluate_benchmark.py "$b" --pred-file "predictions/$b.csv.gz" --out "$OUT/rescore/$b"
  done
}

step_predict() {
  $PY scripts/predict_benchmarks.py $BENCHES --preset default --seed 0 --device "$DEVICE" --workers "$WORKERS" \
      --out "$OUT/preds"
}

step_evaluate() {
  for b in $BENCHES; do
    v=$(ls "$OUT/preds/$b")                    # one variant per benchmark from step_predict
    $PY scripts/evaluate_benchmark.py "$b" --pred-dir "$OUT/preds/$b/$v/preds" --out "$OUT/eval/$b"
  done
}

step_trainset() {                              # docs/TRAINSET.md; needs BioLiP2 + wwPDB + MMseqs2/Foldseek
  bash scripts/data/download_biolip2.sh
  bash scripts/data/install_tools.sh
  bash scripts/data/build_trainset_all.sh
  $PY -I scripts/data/apply_audit_exclusions.py   # decision D6: drop the 186 entries flagged by the audit
  $PY scripts/burrow_relabel_biolip.py           # snapshot of the post-D6 manifests used for training
}

snapshot() { ls -td results/dev/cache/trainset_snapshot/*/ | head -1; }

step_featurize() {
  export BURROW_TRAINSET="$(snapshot)"
  $PY scripts/burrow_biolip_prep.py              # dev inputs + dev site tables (all / small)
  for cfg in "" "$FF"; do
    $PY scripts/burrow_featurize_biolip.py --split dev --jobs 16 $cfg
    $PY scripts/burrow_featurize_biolip.py --split train --assembly --jobs 16 $cfg
  done
}

step_train() {
  export BURROW_TRAINSET="$(snapshot)"
  for s in 0 1 2; do for v in all small; do
    $PY scripts/burrow_train_biolip.py --variant $v --seed-idx $s --jobs 14 --name burrow_${v}_default_s$s $FF $TF
    $PY scripts/burrow_train_biolip.py --variant $v --seed-idx $s --jobs 14 --name burrow_${v}_accurate_s$s
  done; done
}

step_freeze() {
  export BURROW_TRAINSET="$(snapshot)"
  $PY scripts/burrow_freeze.py --ranker-variant V0_base   # results/dev/freeze/ (v1: no output floor)
  # tau selection on train cluster-CV (pocket caches from --save-pockets runs of the s0 default models)
  $PY scripts/burrow_train_biolip.py --variant small --seed-idx 0 --jobs 14 --name p3_small_default_s0 --save-pockets full $FF $TF
  $PY scripts/burrow_train_biolip.py --variant all --seed-idx 0 --jobs 14 --name p3_all_default_s0 --save-pockets full $FF $TF
  $PY scripts/burrow_tau_cv.py --run p3_small_default_s0 --variant small
  $PY scripts/burrow_tau_cv.py --run p3_all_default_s0 --variant all
  $PY scripts/burrow_freeze_v2.py                         # results/dev/freeze_v2/ (v1 + floor 0.03, min_keep 3)
  log "compare results/dev/freeze_v2/models/* with models/ (trees and formation must match; meta differs)"
}

step_speed() {
  $PY scripts/verify_burrow_fast.py --n 20 --device cpu --manifest "${DEV_MANIFEST:-results/dev/biolip/inputs_audited.csv}" || \
      log "verify_burrow_fast needs the dev manifest (featurize step); skipped"
  $PY scripts/burrow_fast_preset_bench.py fast=models/burrow_all_fast_s0.json default=models/burrow_all_default_s0.json \
      accurate=models/burrow_all_accurate_s0.json
}

STEPS="smoke data rescore predict evaluate trainset featurize train freeze speed"
[ $# -eq 0 ] && set -- smoke
for target in "$@"; do
  if [ "$target" = all ]; then
    for s in $STEPS; do log "step $s"; "step_$s"; done
  elif declare -f "step_$target" > /dev/null; then
    log "step $target"; "step_$target"
  else
    echo "unknown step '$target'; steps: $STEPS all"; exit 2
  fi
done
