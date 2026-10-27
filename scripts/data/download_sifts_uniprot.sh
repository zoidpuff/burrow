#!/usr/bin/env bash
# EMBL-EBI SIFTS chain->UniProt residue mapping (CC-BY-4.0) and UniProt human reviewed sequences
# (CC-BY-4.0). SIFTS is needed for the LIGYSIS C1-strict ligand placement (build_ligysis_ligands.py)
# and the training-set / AF-set rebuilds; UniProt only for the AF-set rebuild. Both are updated
# continuously; BURROW used SIFTS 2026-10-18 and UniProt 2026_03 (sha256 in DATA.md).
source "$(dirname "$0")/_common.sh"
fetch "https://ftp.ebi.ac.uk/pub/databases/msd/sifts/flatfiles/tsv/pdb_chain_uniprot.tsv.gz" "$RAW/sifts/pdb_chain_uniprot.tsv.gz"
if [[ "${WITH_UNIPROT:-0}" == 1 ]]; then
  fetch "https://rest.uniprot.org/uniprotkb/stream?compressed=true&format=tsv&fields=accession,sequence_version,length,sequence&query=(organism_id:9606)%20AND%20(reviewed:true)" \
        "$RAW/uniprot/uniprot_human_reviewed.tsv.gz"
fi
