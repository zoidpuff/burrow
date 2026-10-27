#!/usr/bin/env bash
# wwPDB derived_data files (CC0): entry type/method, resolution index, SEQRES sequences. Needed only
# for the training-set / AF-set rebuilds. Skipped if BURROW_PDB_DERIVED points to an existing copy.
source "$(dirname "$0")/_common.sh"
OUT="${BURROW_PDB_DERIVED:-$RAW/pdb_derived}"
fetch "https://files.wwpdb.org/pub/pdb/derived_data/pdb_entry_type.txt" "$OUT/pdb_entry_type.txt"
fetch "https://files.wwpdb.org/pub/pdb/derived_data/index/resolu.idx" "$OUT/index/resolu.idx"
fetch "https://files.wwpdb.org/pub/pdb/derived_data/pdb_seqres.txt" "$OUT/pdb_seqres.txt"
