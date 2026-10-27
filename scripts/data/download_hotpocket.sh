#!/usr/bin/env bash
# OPTIONAL. HOTPocket (Carpenter & Altman, J Cheminform 2025): proteome-wide pocket catalogue with
# BioLiP2-derived known pockets. Not a train/dev/test set of BURROW; used only for the descriptive
# proteome analysis. Zenodo 17653326 (data v2, CC-BY-4.0) + github Helix-Research-Lab/HOTPocket (MIT).
source "$(dirname "$0")/_common.sh"
OUT="$RAW/hotpocket"
"$PY" -I "$SCRIPTS/zenodo_fetch.py" 17653326 "$OUT/zenodo_v2"
for t in "$OUT"/zenodo_v2/*.tar.gz; do
  case "$t" in *model_inputs*|*model_checkpoints*) continue;; esac  # large feature arrays / NN weights: keep archive only
  b=$(basename "$t" .tar.gz); [[ -d "$OUT/extracted/$b" ]] || { mkdir -p "$OUT/extracted/$b"; tar -xzf "$t" -C "$OUT/extracted/$b"; }
done
COMMIT="${HOTPOCKET_COMMIT:-1ca16ce0c9c902568f1e9a1c83fd6978ec91acd8}"  # main @ 2026-03-17
fetch "https://codeload.github.com/Helix-Research-Lab/HOTPocket/tar.gz/$COMMIT" "$OUT/github/HOTPocket-$COMMIT.tar.gz" "$([[ -z "${HOTPOCKET_COMMIT:-}" ]] && echo 0575c1639cee0af6b487727e0ba9ccb41d4015505f429bfa34ed11226ca81c07)"
[[ -d "$OUT/github/HOTPocket-$COMMIT" ]] || tar -xzf "$OUT/github/HOTPocket-$COMMIT.tar.gz" -C "$OUT/github"
