#!/usr/bin/env bash
# PocketMiner cryptic-pocket val/test set (Meller et al. 2023, Nat Commun 14:1177), MIT. Only
# data/pm-dataset of github.com/Mickdub/gvp (branch pocket_pred) is fetched. Used only to build the
# test union for leakage control (build_trainset_testunion.py) and descriptive analyses.
source "$(dirname "$0")/_common.sh"
COMMIT="${POCKETMINER_COMMIT:-187062df3c94127e991669768009141a08fd5d8b}"  # pocket_pred @ 2023-07-21
OUT="$RAW/pocketminer"
"$PY" -I "$SCRIPTS/github_subtree_fetch.py" Mickdub/gvp "$COMMIT" data/pm-dataset "$OUT"
for f in README.md LICENSE LICENSE.txt; do
  curl -fsSL "https://raw.githubusercontent.com/Mickdub/gvp/$COMMIT/$f" -o "$OUT/repo_$f" 2>/dev/null || rm -f "$OUT/repo_$f"
done
