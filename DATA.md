# DATA: datasets, sources, versions, checksums, licenses

**This repository redistributes no third-party structures and no third-party data files, except two example structures in `examples/`:** `1a28_A.pdb` (derived from PDB entry 1A28, chain A, polymer atoms only; wwPDB/RCSB PDB, CC0 1.0) and `AF-P00918-F1-model_v6.cif.gz` (unmodified AlphaFold DB v6 model of UniProt P00918; CC-BY-4.0; Jumper et al., Nature 2021; Varadi et al., Nucleic Acids Res. 2024; https://alphafold.ebi.ac.uk). It
ships (in `benchmarks/`):

* identifier manifests of every test set (PDB / UniProt / AFDB ids, chains, assembly ids, the
  upstream path of each input file and the sha256 of the file BURROW was evaluated on);
* the frozen ground-truth site tables BURROW was scored on, so evaluation reproduces the published
  numbers exactly: our own AF-set and dimer tables, and our conversions of LIGYSIS / LIGYSIS_NI
  (adapted from LIGYSIS, CC-BY-4.0, Utges & Barton), CryptoBench test (MIT) and PocketWatch test
  (MIT), with attribution and license notices in `benchmarks/README.md` and
  `benchmarks/THIRD_PARTY_LICENSES.md`;
* the frozen test union (public sequences), its 30 % sequence clusters and the training / dev
  entry lists;
* sha256 manifests of the upstream downloads (`benchmarks/download_checksums/`).

Everything else is downloaded from its public source and rebuilt with `scripts/data/`
(order and options in `scripts/data/README.md`; one driver: `scripts/data/build_all.sh`). Data go
to `$BURROW_DATA` (default `data/`). Third-party tools and data keep their own licenses; please
cite the original resources.

**scPDB is not used for training or testing and is not redistributed** (no download script is
provided). HOTPocket and AF2BIND are not BURROW train, dev or test sets.

All retrievals were on 2026-10-26 (UTC) unless noted otherwise. GitHub `codeload` tarball sha256
values are pinned in the scripts; GitHub can regenerate archives, so the **commit SHA is
authoritative**. If a pinned tarball sha256 ever mismatches, check that the commit is unchanged.

## Summary

| Dataset | Source | Version / retrieved | Checksum (sha256) | License | Role in BURROW | In this repo |
|---|---|---|---|---|---|---|
| wwPDB entries (mmCIF) | https://files.rcsb.org/download/<ID>.cif.gz (or a wwPDB rsync mirror) | snapshot of about 2026-10-16 | not pinned (live archive); dimer inputs rebuilt from RCSB on 2026-10-27 were byte-identical | CC0 | test (LIGYSIS frame + ligands, dimer), train/dev (BioLiP2 entries) | ids only |
| AlphaFold DB v6 | https://alphafold.ebi.ac.uk/files/AF-<ACC>-F1-model_v6.cif (models of `UP000005640_9606_HUMAN_v6.tar` and, for 5 accessions, `swissprot_cif_v6.tar`) | v6 | per model in `benchmarks/af_set/manifest.tsv` (`model_cif_sha256`) | CC-BY-4.0 | test (AF set, O5) | ids, URLs, sha256; derived site table |
| P2Rank datasets (COACH420, HOLO4K, + `(mlig)`) | github.com/rdk/p2rank-datasets, commit `0236ecb38cbb60b89849a1ea36fbd9ee93f3e906` (2024-11-08) | 2026-10-26 | tarball `b608bc941d12087f60c94095e822edac53a0a8ce5fd6b7cf960254a383949ad2` | no license file; structures from the PDB. Cite Krivak & Hoksza 2018, J Cheminform 10:39 | test (COACH420(mlig) O2a, HOLO4K(mlig) O2b) | ids + per-file sha256 |
| LIGYSIS / LBS-comparison results | Zenodo 14645504 (v2, 2025-01-21; v1 = 13121414, byte-identical files) | v2 | per file in `benchmarks/download_checksums/ligysis_lbs_comparison_results.tsv`; e.g. `LIGYSIS_sites_DEF_TRANS.pkl` `39a56fef7be98e3eabc93e806dfa6192abd64b363ab57dae1c7c274607a91153`, `ALL_PREDS_COMBINED_RIGHT_EXTENDED_DEF.pkl` `28099f663daf728f7daeacef2194a59dc3d3a83ff09c1322056852743defe4bd`, `LIGYSIS_human_chains_per_lig_MAY_2024.pkl` `fefcea7b36568bcf8181a008a16ba3906bb9cb705370ef4260d166ffe27b6f06` | CC-BY-4.0 | test (LIGYSIS C1, LIGYSIS_NI); site source of the AF set and of the dimer UniProt scope | ids, input sha256; adapted site table (CC-BY-4.0, attributed) |
| LBS-comparison code + input chains | Zenodo 14033286 (bartongroup/LBS-comparison v2.0.0, commit 820714c) | 2024-11-04 | `abeccd8233277b1869847060204530ed58d6485ec777dbcc3b2d1c0b056a076d` | Zenodo CC-BY-4.0; repository MIT | test inputs (ligand-stripped TRANS-frame chains) | ids + per-file sha256 |
| LIGYSIS pipeline (optional) | Zenodo 14178252 (LIGYSIS 1.0.0) | 2024-11-18 | `8fa7476e08a4589d35c1860eb7cdf377630c3ddf3f076cbc73edd5e63cf69c50` | CC-BY-4.0 | reference only | no |
| CryptoBench | OSF pz4a9 (+ github skrhakv/CryptoBench `9a3432f479325ca3c9fdc3b8612715ab5b6edecc`) | OSF node modified 2026-01-17 | `cif-files.zip` `8d15f897bfdfdf61c7d97a29f5f6ca2c5e03d73d8fb89be7da5bbc245cf56ae4`; `dataset.json` `79519369a1d32b63efd86b907013cacb5e02a68e4d711cdde20a23cdfe16ba7c`; all files verified against OSF sha256 | MIT | test (test split, apo, O4); dev (train folds 0-3) | ids, per-file sha256; derived test site table (MIT notice included) |
| PocketWatch | huggingface.co/datasets/genesisml/PocketWatch, revision `db7bd0611a14cb98e3b1d24b343565418b7193ef` (2026-10-14) | 2026-10-26 | upstream `CHECKSUMS.txt` md5 (all files except the later-edited README.md); sha256 in `benchmarks/download_checksums/` | MIT | test (temporal test split, ESMFold2 folds, O3) | ids, per-file sha256; derived test site table (MIT notice included) |
| PocketMiner set | github Mickdub/gvp branch `pocket_pred`, commit `187062df3c94127e991669768009141a08fd5d8b`, subtree `data/pm-dataset` | 2026-10-26 | per file (sha256 + git blob sha1) in `benchmarks/download_checksums/pocketminer.tsv` | MIT | test union only (leakage control); descriptive | no |
| BioLiP2 | https://zhanggroup.org/BioLiP/ (`download/BioLiP.txt.gz`, `BioLiP_nr.txt.gz`, `data/*.fasta.gz`, `data/ligand.tsv.gz`) | snapshot 2026-10-26; server Last-Modified 2025-11-12 | `BioLiP.txt.gz` `c92229bbc8c55c3bd84a9813c3e278ba62f4cfa44e6315cc98d9bf63ed64b6ec`; `BioLiP_nr.txt.gz` `594830b62f0dc368b6642958edb1a16ac66b702176c81868cedd646c1e4588f4` | "freely available", no formal license; cite Zhang et al. 2024, NAR 52:D404 | train/dev (Track A labels); dimer relevant-ligand annotation | entry ids only |
| SIFTS `pdb_chain_uniprot.tsv.gz` | https://ftp.ebi.ac.uk/pub/databases/msd/sifts/flatfiles/tsv/pdb_chain_uniprot.tsv.gz | 2026-10-18 (PDB 42.26, UniProt 2026.03) | `3ff549da37104bdd950cd78a939be55e93d7eb0279877f57d2134f58762f0f39` | CC-BY-4.0 (EMBL-EBI) | LIGYSIS ligand placement, AF set, train/dev UniProt mapping | no |
| UniProt human reviewed | https://rest.uniprot.org/uniprotkb/stream?compressed=true&format=tsv&fields=accession,sequence_version,length,sequence&query=(organism_id:9606)%20AND%20(reviewed:true) | release 2026_03 | `9507f641daa0384227b7e78311a19fdf2f316eea2fa408c2faead699a415d290` | CC-BY-4.0 | AF-set construction | no |
| wwPDB derived data | https://files.wwpdb.org/pub/pdb/derived_data/ (`pdb_entry_type.txt`, `index/resolu.idx`, `pdb_seqres.txt`) | as the PDB snapshot | not pinned | CC0 | train/dev and AF-set construction | no |
| HOTPocket (optional) | Zenodo 17653326 (v2) + github Helix-Research-Lab/HOTPocket `1ca16ce0…` | v2 | `benchmarks/download_checksums/hotpocket_*.tsv` | data CC-BY-4.0; code MIT | descriptive proteome analysis only | no |
| MMseqs2 | github soedinglab/MMseqs2 release 18-8cc5c (linux-avx2) | 2025-07-27 | `bd9b0234da5949ad528d5b5f9ea4cda9c1e23dce14b46c0791d4d919a76e61ce` | MIT | leakage filtering, clusters | no (`install_tools.sh`) |
| Foldseek | github steineggerlab/foldseek release 10-941cd33 (linux-avx2) | 2025-01-19 | `e6a3e3860e76b0b7b858736f627fe680d4d7f0fc7298301d8a92b9f711d74ac7` | GPL-3.0 | fold-novelty strata | no (`install_tools.sh`) |

## Test benchmarks

Counts, inputs and ground-truth sources per benchmark are in `benchmarks/README.md`.

| Benchmark | Endpoint | Structures / sites (scored) | Ground truth in this repo |
|---|---|---|---|
| LIGYSIS (LBS-comparison) | C1 / C1-strict / C2 | 2,775 chains / 6,882 (6,721) | **yes**, frozen (adapted from LIGYSIS, CC-BY-4.0); rebuild: `build_ligysis_ligands.py` + `build_gt_ligysis.py` |
| LIGYSIS_NI (ion_prop != 1) | descriptive | 2,003 / 4,255 (4,141) | **yes** (derived from the LIGYSIS table at install) |
| COACH420(mlig) | O2a | 300 | no: upstream `.ds` |
| HOLO4K(mlig) | O2b | 3,448 | no: upstream `.ds` |
| CryptoBench test (apo) | O4 | 222 / 270 | **yes**, frozen (MIT); rebuild: `build_gt_cryptobench.py` |
| PocketWatch test | O3 | 1,566 / 2,301 (1,573) | **yes**, frozen (MIT); rebuild: `build_gt_pocketwatch.py` |
| AF set (AFDB v6) | O5 | 2,526 / 6,731 (6,502) | **yes** (`benchmarks/af_set/sites.tsv.gz`, + all-sites sensitivity table) |
| Dimers (assembly 1) | O6 | 400 complexes (1,062 isolated chains) / 807 unique sites | **yes** (`benchmarks/dimer/`) |

Derived tables and their upstream licenses: the AF-set tables combine AFDB models (CC-BY-4.0),
LIGYSIS sites (CC-BY-4.0) and PDB ligand coordinates (CC0); the dimer ground truth combines PDB
coordinates (CC0) with BioLiP2's relevant-ligand annotation (freely available) and LIGYSIS
UniProt scope (CC-BY-4.0). The LIGYSIS table is an adaptation of the LIGYSIS data of Zenodo
14645504 (J. Sanchez Utges, G. J. Barton; CC-BY-4.0): centres mapped to the wwPDB
asymmetric-unit frame, author residue ids, redundancy flags, and PDB ligand atoms (CC0) for
C1-strict. The CryptoBench and PocketWatch tables are derived from MIT-licensed releases (notices
in `benchmarks/THIRD_PARTY_LICENSES.md`). `scripts/data/install_benchmarks.py` installs all frozen
tables and checks them against `benchmarks/gt_sha256.tsv`; COACH420/HOLO4K ground truth is the
upstream `.ds` file. Rebuilding the third-party tables from the upstream releases
(`build_all.sh` with `REBUILD_GT=1`) is the documented alternative.

## Dataset notes

### P2Rank datasets (`download_p2rank_datasets.sh`)

* The `.ds` file defines a dataset, not the directory (e.g. `holo4k/` holds 4,543 PDB files,
  `holo4k.ds` lists 4,009). `(mlig)` variants list the relevant ligand codes explicitly (from
  Binding MOAD 2013; proteins unknown to MOAD or with conflicting codes removed): COACH420(mlig)
  300 entries, HOLO4K(mlig) 3,448.
* Modified residues (MSE, SEP, LLP, ...) are HETATM records in these files and are not ligands.
* A few `(mlig)` codes are not found as HETATM in the file (COACH420(mlig) 8, HOLO4K(mlig) 70;
  mostly peptide ligands given as amino-acid names).
* No license file upstream; do not redistribute the structures.

### LIGYSIS (`download_ligysis.sh`; Utges & Barton 2024, J Cheminform 16:126)

* Human subset of LIGYSIS: per UniProt, biologically relevant ligands (BioLiP criteria) pooled
  across all PISA assemblies of all PDBe entries and clustered into sites in UniProt numbering.
  Ions are included.
* Methods are run on one ligand-stripped representative chain per protein, distributed by the
  authors in a common transformed frame (`DATA/trans_rep_chains/*.trans.pdb`). BURROW's inputs are
  these files; predictions are mapped back to the wwPDB asymmetric-unit frame of the evaluation
  (`pocketdetect.ligysis.trans_preds_to_original`).
* 3,448 chains / 8,244 sites; the evaluated set is 2,775 chains (chains with a UniProt mapping),
  6,882 sites, 6,721 scored (their redundancy filter).
* C1-strict ligand atoms: every ligand instance listed for a site (58,152 instances from 20,300
  entries) is placed on the representative chain (SIFTS-paired core CA superposition, RMSD <= 2 A).
  In BURROW's build 6,387 of 6,721 scored sites have ligand atoms.
* The pickles are read only through a restricted unpickler (numpy / pandas / builtins).
* The 3.3 GB pocket-shape dictionary is not needed and is skipped by default (`LIGYSIS_FULL=1`).

### CryptoBench (`download_cryptobench.sh`; Skrhak et al. 2025, Bioinformatics 41:btae745)

* 1,107 apo entries, 3,899 holo structures, 5,493 apo-holo pairs; folds: test 222, train-fold-0..3
  219 / 222 / 222 / 222.
* Test input = the apo entry restricted to the CryptoBench apo chain(s) (`input_chains`); sites =
  CryptoBench's merged cryptic pockets; centre = CA centroid of the pocket residues on the apo.
* The train folds are used only as a development set (`build_gt_cryptobench_trainfolds.py`).

### PocketWatch (`download_pocketwatch.sh`; zPocket paper, arXiv 2610.17696)

* Temporally held-out sites on ESMFold2 folds of canonical UniProt sequences; test = sites first
  released on or after 2024-01-01: 1,566 proteins, 2,301 sites, 1,573 scored.
* Masked sites (interface-only, pre-cutoff, subsumed) are real pockets: neither positives nor
  negatives; N = number of scored sites. Centre = their ligand-centroid transfer recipe.
* `msas_test.tar` (2.7 GB) is not downloaded.

### AF set (ours; docs/AF_BENCHMARK.md)

* All LIGYSIS sites of the LBS-benchmark UniProts mapped onto full-length AFDB v6 models (chain A,
  residue number = UniProt position): 2,526 models, 6,731 sites, 6,502 scored (LIGYSIS redundancy
  filter on the model). Proteins fragmented in AFDB (> 2,700 aa) are excluded.
* Ligand heavy atoms transferred from the PDB by local CA superposition (accepted at local RMSD
  <= 2 A; median 0.37 A).
* Models are downloaded by `fetch_afdb.py`; the sha256 of every model BURROW used is in the
  manifest. AFDB PAE files were not used.

### Dimer benchmark (ours; docs/DIMER_BENCHMARK.md)

* 400 complexes (274 homo, 126 hetero) over 450 LIGYSIS UniProts; X-ray / EM <= 3.0 A, assembly 1
  with author-and-software-defined details, 2-8 protein chains; relevant ligands from the BioLiP2
  annotation of the same entry (snapshot 2025-11-12).
* 807 unique sites (J >= 0.5 grouping): 494 single-chain, 177 homo-interface, 66 hetero-interface,
  70 minor-interface; 301 ions.
* Inputs: assembly 1 expanded from the asymmetric unit (polymer only, no CRYST1), plus every
  protein chain alone in the same frame (`build_inputs.py dimer`).

### BioLiP2 and the training / dev sets (docs/TRAINSET.md)

* Training and dev labels come from BioLiP2 (X-ray / EM, resolution <= 3.0 A, receptor >= 50
  residues, relevant ligands incl. metal ions), after removing every chain with sequence similarity
  to the frozen test union (MMseqs2: E < 1e-3 and identity >= 0.30 and coverage >= 0.5 or
  alignment >= 80), any test PDB id or test UniProt; 30 % clusters split 90 / 10 into train / dev.
* BioLiP is updated weekly and files are not versioned; a new download will differ from the
  2025-11-12 snapshot. The resulting entry lists are therefore shipped
  (`benchmarks/trainset/`), together with the 186 entries removed by an independent leakage audit.

## Reproduction checks performed for this release

With the scripts in `scripts/data/` (local copies of the downloads above, current RCSB entries):

* inputs of all test sets rebuilt (LIGYSIS 2,775, LIGYSIS_NI 2,003, COACH420(mlig) 300,
  HOLO4K(mlig) 3,448, CryptoBench 222, PocketWatch 1,566, dimer 400 assemblies + 1,062 chains from
  fresh RCSB downloads): all sha256-identical to the files BURROW was evaluated on; two AFDB v6
  models downloaded from the AFDB file service matched their recorded sha256;
* CryptoBench, PocketWatch, CryptoBench train-fold and holo-pair site tables, the installed AF-set
  and dimer tables, and the 30 % cluster table: identical to BURROW's;
* LIGYSIS site table rebuilt from scratch with the released code: identical sites, centres and
  residues; the C1-strict ligand atoms differ for 15 of 6,882 sites (6,391 instead of 6,387 scored
  sites with ligand atoms). This is why the frozen table is shipped; with it, the installed
  LIGYSIS, LIGYSIS_NI, CryptoBench and PocketWatch tables are identical to the scored ones
  (byte-identical when the same PDB mirror path is used).
