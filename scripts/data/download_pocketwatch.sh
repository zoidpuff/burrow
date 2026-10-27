#!/usr/bin/env bash
# PocketWatch (zPocket paper, arXiv 2610.17696), HF dataset genesisml/PocketWatch (MIT), pinned
# revision: labels/splits/strata/projection + ESMFold2 folds. msas_test.tar (2.7 GB) is skipped.
# Needs huggingface_hub (pip install huggingface_hub) or `uv`.
source "$(dirname "$0")/_common.sh"
REV="${POCKETWATCH_REV:-db7bd0611a14cb98e3b1d24b343565418b7193ef}"   # main @ 2026-10-14
OUT="$RAW/pocketwatch/$REV"
mkdir -p "$OUT"
HF_SNAPSHOT='
import sys
from huggingface_hub import snapshot_download
rev, out = sys.argv[1], sys.argv[2]
snapshot_download("genesisml/PocketWatch", repo_type="dataset", revision=rev, local_dir=out,
                  ignore_patterns=["msas_test.tar"], max_workers=8)
'
if "$PY" -c "import huggingface_hub" 2>/dev/null; then
  "$PY" -I -c "$HF_SNAPSHOT" "$REV" "$OUT"
else
  uv run --no-project --with "huggingface_hub==0.26.2" python -I -c "$HF_SNAPSHOT" "$REV" "$OUT"
fi
ln -sfn "$REV" "$RAW/pocketwatch/current"
cd "$OUT"
[[ -d structures_train ]] || unzip -q structures_train.zip
# upstream md5 list (skip MSA tarball contents and README.md, which was edited after CHECKSUMS.txt was generated)
grep -v -E '  ((\./)?msas_test/|README.md$)' CHECKSUMS.txt | md5sum --quiet -c - && echo "upstream CHECKSUMS.txt: OK (excluding msas_test/ and README.md)"
find . -type f ! -path './.cache/*' ! -path './structures/*.cif.gz' ! -path './structures_train/*' ! -name MANIFEST.tsv | sort | \
  while read -r f; do printf '%s\t%s\t%s\t%s\thf://datasets/genesisml/PocketWatch@%s\n' "${f#./}" "$(sha256sum "$f" | cut -d' ' -f1)" "$(stat -c %s "$f")" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$REV"; done > MANIFEST.tsv
