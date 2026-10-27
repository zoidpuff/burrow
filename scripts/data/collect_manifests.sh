#!/usr/bin/env bash
# Copy every $BURROW_DATA/raw/**/MANIFEST.tsv (file, sha256, bytes, retrieved_utc, url) into
# $BURROW_DATA/manifests/downloads/ so the checksums of your downloads can be compared with DATA.md.
source "$(dirname "$0")/_common.sh"
DEST="$DATA/manifests/downloads"; mkdir -p "$DEST"
find "$RAW" -name MANIFEST.tsv | sort | while read -r m; do
  rel="${m#$RAW/}"; name="$(echo "${rel%/MANIFEST.tsv}" | tr '/' '__')"
  { printf '# source manifest: raw/%s\n# file\tsha256\tbytes\tretrieved_utc\turl\n' "$rel"; cat "$m"; } > "$DEST/$name.tsv"
  echo "$DEST/$name.tsv ($(wc -l < "$m") files)"
done
