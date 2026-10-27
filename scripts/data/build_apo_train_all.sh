#!/usr/bin/env bash
# OPTIONAL: apo counterparts of the train/dev entries (Track A2), after build_trainset_all.sh. Same
# requirements (full wwPDB mirror, derived_data, BioLiP2, MMseqs2). The leakage audit outputs under
# <repo>/results/audit/ are used if present (optional extra filters).
# Logs: $BURROW_DATA/processed/apo_train/work/*.log
source "$(dirname "$0")/_common.sh"
[[ -n "${BURROW_PDB_MIRROR:-}" ]] || { echo "set BURROW_PDB_MIRROR to a full wwPDB mmCIF mirror" >&2; exit 1; }
NP="${NPROC:-24}"
W="$DATA/processed/apo_train/work"; mkdir -p "$W"; L="$W/run.log"
echo "--- run $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$L"
if [[ ! -f "$DATA/processed/apo_train/candidates.parquet" || "${REUSE_SEARCH:-0}" != 1 ]]; then
  "$PY" -I "$SCRIPTS/build_apo_train_search.py" --threads "$NP" > "$W/search.log" 2>&1; echo SEARCH_DONE >> "$L"
fi
rm -rf "$DATA/processed/apo_train/train/entries" "$DATA/processed/apo_train/dev/entries"
"$PY" -I "$SCRIPTS/build_apo_train_pool.py" --procs "$NP" > "$W/pool.log" 2>&1; echo POOL_DONE >> "$L"
"$PY" -I "$SCRIPTS/build_apo_train_leakcheck.py" --threads "$NP" > "$W/leakcheck.log" 2>&1; echo LEAK_DONE >> "$L"
"$PY" -I "$SCRIPTS/verify_apo_train.py" --procs "$NP" > "$W/verify.log" 2>&1 || echo VERIFY_FAILED >> "$L"
echo VERIFY_DONE >> "$L"
