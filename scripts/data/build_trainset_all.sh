#!/usr/bin/env bash
# OPTIONAL full rebuild of the BioLiP2-based training/dev sets (docs/TRAINSET.md). BURROW ships the
# resulting entry lists in benchmarks/trainset/; a rebuild with a newer BioLiP2 / PDB state will not
# reproduce them exactly. Needs:
#   * a full wwPDB mmCIF mirror: BURROW_PDB_MIRROR (the package reads the entries directly)
#   * download_biolip2.sh, download_sifts_uniprot.sh, download_pdb_derived.sh, all test-set downloads,
#     install_tools.sh (MMseqs2 + Foldseek in <repo>/tools/bin, which pocketdetect.datasets uses)
#   * install_benchmarks.py manifests af_set dimer (frozen test union + AF/dimer sequences)
# The test union is frozen: it is only rebuilt with REBUILD_TEST_UNION=1.
# Logs: $BURROW_DATA/processed/train/work/*.log
source "$(dirname "$0")/_common.sh"
[[ -n "${BURROW_PDB_MIRROR:-}" ]] || { echo "set BURROW_PDB_MIRROR to a full wwPDB mmCIF mirror" >&2; exit 1; }
NP="${NPROC:-32}"
W="$DATA/processed/train/work"
mkdir -p "$W"
L="$W/run_all.log"
echo "--- full run $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$L"
if [[ "${REBUILD_TEST_UNION:-0}" == 1 ]]; then
  "$PY" -I "$SCRIPTS/build_trainset_testunion.py" --procs "$NP" > "$W/testunion.log" 2>&1; echo TESTUNION_DONE >> "$L"
fi
"$PY" -I "$SCRIPTS/build_trainset_candidates.py" > "$W/candidates.log" 2>&1; echo CANDIDATES_DONE >> "$L"
"$PY" -I "$SCRIPTS/build_trainset_split.py" --threads "$NP" > "$W/split.log" 2>&1; echo SPLIT_DONE >> "$L"
rm -rf "$DATA/processed/train/entries" "$DATA/processed/dev/entries" "$W"/clu50_*
"$PY" -I "$SCRIPTS/build_trainset_pool.py" --procs "$NP" --max-per-cluster 3 > "$W/pool.log" 2>&1; echo POOL_DONE >> "$L"
"$PY" -I "$SCRIPTS/build_trainset_asmcheck.py" --threads "$NP" > "$W/asmcheck.log" 2>&1; echo ASM_DONE >> "$L"
"$PY" -I "$SCRIPTS/build_trainset_finalcheck.py" --procs "$NP" > "$W/finalcheck.log" 2>&1; echo FINALCHECK_DONE >> "$L"
"$PY" -I "$SCRIPTS/apply_audit_exclusions.py" > "$W/audit_exclusions.log" 2>&1; echo AUDIT_EXCLUSIONS_DONE >> "$L"
"$PY" -I "$SCRIPTS/verify_trainset.py" --procs "$NP" > "$W/verify.log" 2>&1 || echo VERIFY_FAILED >> "$L"
"$PY" -I "$SCRIPTS/build_trainset_foldseek_strata.py" --procs "$NP" > "$W/foldseek_strata.log" 2>&1; echo STRATA_DONE >> "$L"
echo DONE >> "$L"
