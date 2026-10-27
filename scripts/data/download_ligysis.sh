#!/usr/bin/env bash
# LIGYSIS (human subset) reference sites + per-method predictions (Utges & Barton 2024,
# J Cheminform 16:126), CC-BY-4.0:
#  - Zenodo 14645504 "LBS-Comparison results" v2 (pickles: sites, transforms, predictions); v1 = 13121414
#  - Zenodo 14033286 bartongroup/LBS-comparison v2.0.0 (code + ligand-stripped TRANS-frame input chains)
#  - Zenodo 14178252 JavierSanchez-Utges/LIGYSIS v1.0.0 pipeline (optional, code only; set LIGYSIS_PIPELINE=1)
# ~0.9 GB results + 1 GB code/structures (4.2 GB with LIGYSIS_FULL=1). Pickles are read only through the restricted unpickler (safe_pickle.py / pocketdetect.ligysis).
source "$(dirname "$0")/_common.sh"
OUT="$RAW/ligysis"
# The 3.3 GB pocket-shape dict (volumetric overlap of the authors' methods) is not needed by BURROW's
# evaluation; it is skipped unless LIGYSIS_FULL=1.
if [[ "${LIGYSIS_FULL:-0}" == 1 ]]; then
  "$PY" -I "$SCRIPTS/zenodo_fetch.py" 14645504 "$OUT/lbs_comparison_results"
else
  "$PY" -I "$SCRIPTS/zenodo_fetch.py" 14645504 "$OUT/lbs_comparison_results" --exclude '^MASTER_POCKET_SHAPE_DICT_EXTENDED_TRANS\.pkl$'
fi
"$PY" -I "$SCRIPTS/zenodo_fetch.py" 14033286 "$OUT/lbs_comparison_code"
if [[ "${LIGYSIS_PIPELINE:-0}" == 1 ]]; then
  "$PY" -I "$SCRIPTS/zenodo_fetch.py" 14178252 "$OUT/ligysis_pipeline"
fi
for z in "$OUT"/lbs_comparison_code/*.zip "$OUT"/ligysis_pipeline/*.zip; do
  [[ -e "$z" ]] || continue
  d="${z%.zip}"; [[ -d "$d" ]] || { mkdir -p "$d"; unzip -q "$z" -d "$d"; }
done
