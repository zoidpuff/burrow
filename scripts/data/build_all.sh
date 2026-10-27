#!/usr/bin/env bash
# Rebuild all data needed to evaluate on the BURROW test benchmarks, from public sources.
#
#   scripts/data/build_all.sh                       # everything (about 15 GB download, ~1 h)
#   STEPS="install gt" scripts/data/build_all.sh    # selected steps only
#
# Steps (in this order; each is idempotent):
#   download  third-party datasets -> $BURROW_DATA/raw   (P2Rank datasets, LIGYSIS, CryptoBench,
#             PocketWatch, SIFTS)
#   install   shipped ID lists and the frozen site tables BURROW was scored on (LIGYSIS, LIGYSIS_NI,
#             CryptoBench, PocketWatch, AF set, dimer) -> $BURROW_DATA/{manifests,processed}
#   fetch     PDB entries (RCSB, unless BURROW_PDB_MIRROR is set) and AFDB v6 models
#   gt        REBUILD the third-party site tables from the upstream releases instead of using the
#             frozen ones (only with REBUILD_GT=1; overwrites the installed tables; LIGYSIS C1-strict
#             ligand atoms then differ for 15 of 6,882 sites, see DATA.md)
#   inputs    prediction inputs -> $BURROW_DATA/inputs/<bench>/ (+ processed/dimer/inputs)
#   verify    sanity checks of the downloads -> $BURROW_DATA/raw/VERIFY_REPORT.json
#
# Environment: BURROW_DATA (default <repo>/data), BURROW_PDB_MIRROR (optional local wwPDB mirror),
# PYTHON (default python3, needs the package requirements), JOBS (default 16).
# The 30 % sequence-cluster table ships pre-built (install step); build_test_clusters.py rebuilds
# it (needs install_tools.sh). Training-set rebuild: build_trainset_all.sh (optional, heavy).
source "$(dirname "$0")/_common.sh"
STEPS="${STEPS:-download install fetch gt inputs verify}"
JOBS="${JOBS:-16}"
has() { [[ " $STEPS " == *" $1 "* ]]; }
echo "BURROW_DATA=$DATA  steps: $STEPS"

if has download; then
  "$SCRIPTS/download_p2rank_datasets.sh"
  "$SCRIPTS/download_ligysis.sh"
  "$SCRIPTS/download_cryptobench.sh"
  "$SCRIPTS/download_pocketwatch.sh"
  "$SCRIPTS/download_sifts_uniprot.sh"
  "$SCRIPTS/collect_manifests.sh"
fi
if has install; then
  "$PY" -I "$SCRIPTS/install_benchmarks.py"
fi
if has fetch; then
  # wwPDB entries: ligysis = frame entries of the ground truth + ligand sources (only needed with
  # REBUILD_GT=1; the frozen table's structure_path points to the representative entries)
  "$PY" -I "$SCRIPTS/fetch_pdb.py" --bench ligysis dimer --jobs 8
  "$PY" -I "$SCRIPTS/fetch_afdb.py" --bench af_set --jobs 8
  "$PY" -I "$SCRIPTS/fetch_afdb.py" --bench af_set_allsites --jobs 8
fi
if has gt && [[ "${REBUILD_GT:-0}" == 1 ]]; then
  "$PY" -I "$SCRIPTS/build_ligysis_ligands.py" --jobs "$JOBS"
  "$PY" -I "$SCRIPTS/build_gt_ligysis.py" --jobs "$JOBS"
  "$PY" -I "$SCRIPTS/build_gt_cryptobench.py"
  "$PY" -I "$SCRIPTS/build_gt_pocketwatch.py"
  # af_set, af_set_allsites, dimer: installed from benchmarks/ (install step)
  # coach420_mlig, holo4k_mlig: ground truth = the upstream (mlig) .ds files, read at evaluation time
fi
if has inputs; then
  "$PY" -I "$SCRIPTS/build_inputs.py" --jobs "$JOBS"
fi
if has verify; then
  "$PY" -I "$SCRIPTS/verify_datasets.py" p2rank ligysis cryptobench pocketwatch || echo "verify_datasets reported failures (see above)"
fi
