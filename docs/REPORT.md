# BURROW: fast, analytical pocket detection and ranking (final report)

Project: PROMPT.md (24 h budget, started 2026-10-26 14:54 CET). Final method version: **FREEZE v2** (commit `0d925b2`). Research record: RESEARCH_TREE.md (status summaries, decisions D0–D17). Usage: README.md. Every number below carries an invisible source tag (an HTML comment: open the Markdown source to see it). `scripts/check_report_numbers.py` checks each tagged number against the committed results files (§8). Units are percentage points unless stated otherwise. CIs are 95 % paired cluster-bootstrap intervals (30 % MMseqs2 sequence clusters, 1,000 resamples) unless stated otherwise. "s0/s1/s2" are the three pre-registered training seeds (`SEEDS[:3]`, src/pocketdetect/seeds.py).

---

## 1. Summary

### Verdict against the project goals (PROMPT.md)

| goal | verdict | evidence (details in §4) |
|---|---|---|
| "Clearly beat P2Rank and others" | **Partly.** | **Clear on LIGYSIS:** top-N+2 72.5 at 9.1 pockets/chain, vs fpocket+PRANK 60.4 (20.9 pockets/chain) and P2Rank 52.6. The robust evidence is localisation: DCA4 (C1-strict) 54.2 vs 31.6 (P2Rank 29.8), and P1K 96.1 vs 81.7. **Modest on non-ion sites:** LIGYSIS_NI +3.0 to +3.5 vs fpocket+PRANK and +5.4 to +5.9 vs P2Rank (post-hoc). COACH420/HOLO4K: non-inferior only. CryptoBench (apo) and dimer interfaces: at par or below, inconclusive. |
| "Ultra-fast" | **Fast; ultra-fast only with `--preset fast`.** | Final like-for-like timing (one session, the same 200 LIGYSIS chains, one process including start-up and I/O): default 142 ms per structure vs P2Rank 209 ms (≈ 1.5×) and fpocket 605 ms. The optional `--preset fast` takes 48 ms (≈ 4.4× P2Rank, ≈ 12.6× fpocket) at a dev cost of about 1–2 points. One core including parsing: fast 31.5 ms, default 99.2 ms. Over 10,000 structures, 3 GPUs beat 24 CPU workers: fast 646 vs 545 structures/s, default 411 vs 171/s. |
| Generalisation: unseen folds | **Supported.** | Fold-disjoint retraining (A1) is within noise on 8 of 9 test rows (8 benchmarks; LIGYSIS counted with two metrics). The exception is COACH420 (−3.2). |
| Generalisation: apo-to-holo, cryptic, allosteric | **Not shown.** | O4 (CryptoBench apo) is inconclusive. The apo→holo drop is +10.7 vs P2Rank +7.7. Allosteric sites were not evaluated. |
| `--af-mode` | **Partly.** | It removes hallucinated pockets (0.2 % on test vs fpocket+PRANK 12.8 %). On the AF test set (descriptive), AF mode vs naive input gives top-N+2 +1.0 [0.1, 2.0] and cuts top-N+2 hallucinations from 2.80 % to 0.12 %. It is **equivalent to a naive + pLDDT < 70 pocket filter**: +0.4 [−0.5, 1.3], and the filter has higher P1K (+2.4). PAE was unavailable (HTTP 403), and side-chain tolerance hurt and is off. The O5 superiority (+13.1) is an **ion effect**: +32.1 on ion sites vs +1.9 [−0.1, 3.9] on non-ion sites (post-hoc). |
| Homo-/heterodimers | **Partly.** | Native multi-chain input, and a benchmark built here (400 assemblies). Clearly better on non-interface sites in assemblies (single-chain +19.0). Not better on interface sites with full-assembly input (O6 −3.7, inconclusive; hetero-interface −6.1, n = 66). **Robust to a missing partner chain** (isolated-chain input, descriptive): interface DCC12 +14.2 [9.0, 20.1] vs P2Rank in chain mode, and −1.2 vs BURROW's own assembly mode (but DCA4 −11.1). |
| CPU and GPU backends | **Done.** | Numba CPU and Triton GPU backends are exact-equivalent to the reference (re-verified after the T1 speed-up). For large batches the GPU path now beats the CPU path for every preset (§4.8). The human proteome (20,550 proteins) ran in 129 s. |
| Robust, fair benchmarking | **Done.** | Reproduction gates, a frozen PREREG with ledger, an independent leakage audit and independent recomputation of the headline numbers. |

**What was built.** BURROW is a CPU/GPU pocket finder with no neural networks. It (i) places volume-element candidate points on a 1 Å solvent-shell grid, plus metal-coordination candidates, (ii) describes each point with cascaded multi-scale ray buriedness (full-atom and backbone-only), first-hit chemistry and local composition, (iii) scores the points with a LightGBM classifier, (iv) forms multi-scale pockets, (v) ranks them with a cross-fitted LightGBM ranker that yields comparable scores across proteins, then applies 10 Å suppression and (v2 only) a calibrated output-score floor. An `--af-mode` handles AlphaFold models (low-pLDDT pruning plus soft occlusion). The fast backend (Numba on CPU, Triton/PyTorch on GPU) reproduces the reference implementation exactly. Models were trained on a leakage-controlled, LIGYSIS-style BioLiP2 set built for this project, whose leakage control was audited independently.

**What is analytical and what is learned.** The candidates and features are analytical geometry and chemistry. The accuracy, however, comes from the learned point scorer and ranker: geometry-only ranking reaches 53.3 top-N+2 on dev vs P2Rank 54.1. What is new:
* volume-element candidates with backbone-only ray buriedness and metal candidates, giving recall of about 99 % before the floor;
* a cross-fitted, cross-protein-calibrated pocket ranker;
* the finding that the LIGYSIS closest-pocket rule rewards short output lists;
* confidence-aware AF geometry that removes hallucinated pockets;
* a dimer benchmark that handles symmetric copies.

**Pre-registered test results** (docs/PREREG.md; results/test/v{1,2}/SUMMARY.md; recomputed independently in results/verify_test/VERIFY.md):

* **Family 1 (gatekeeping) passes in full for both test versions, all 3 seeds and both comparators.**
  * C1, LIGYSIS top-N+2 at DCC ≤ 12 Å (2,775 chains, 6,721 sites):
    * v1: 64.3 / 64.5 / 64.9 vs the published fpocket+PRANK bar of 60.4. The smallest Δ is +3.9 [2.0, 6.0].
    * **v2 (final): 72.5 / 72.0 / 72.3**, Δ +11.6 to +12.1 vs published (lowest CI bound 9.4). v2 reaches this with 9.1 pockets per chain, vs 20.9 for fpocket+PRANK. P2Rank 2.5.1 scores 52.6.
    * Against our own fpocket 4.2.3+PRANK 2.4.2 re-run (59.5) the margins are larger.
  * C1-strict (closest pocket by DCA ≤ 4 Å to ligand atoms, 6,387 sites): v2 54.0–54.2 vs 31.6, Δ ≈ +22.6.
  * C2, pooled Precision1K: v2 96.1–96.9 vs 81.7. It was pre-registered as non-inferiority but is superior. The best *published* P1K (IF-SitePred-rescored-NR, 94.3) is only 1.8 points lower, and that margin is untested.
* **Family 2 (Holm, non-inferiority margin −2 vs the best of P2Rank 2.5.1 and fpocket+PRANK), v2:**
  * **Non-inferior (pre-registered "pass"):**
    * O2b HOLO4K(mlig): DCA4 top-n Δ +1.6 [−1.2, 4.3].
    * O3 PocketWatch (temporal, predicted structures): Δ +0.8 [−1.4, 2.9] vs P2Rank `-c alphafold`. PocketWatch models carry B-factor 100 everywhere, so AF mode had no pLDDT signal and was inert there. This was inconclusive in v1, and the Holm decision is narrow: p = 0.003 vs threshold 0.005, close to the 0.001 resolution of 1,000 resamples.
    * **O5 AF set: Δ +13.1 [11.0, 15.7] vs P2Rank `-c alphafold`, which is superior.** The gain is concentrated on ion sites (§4.3).
  * **Inconclusive** (CI spans the −2 margin):
    * O2a COACH420: +1.6 [−3.0, 5.8].
    * O4 CryptoBench apo: −2.6 [−8.6, 3.0].
    * O6 dimer interface sites: −3.7 [−8.7, 0.9].
  * None is significantly worse.

**Speed** (docs/PERF.md, "Final like-for-like timing" and the "Track T1" before/after table: same session, the same 200 LIGYSIS chains for every tool, shared node; T1 outputs are byte-identical to before):
* **One process, including start-up and I/O:** P2Rank 2.5.1 (batch, one JVM) 209 ms per structure and fpocket 4.2.3 605 ms, against:
  * BURROW default: 142 ms (≈ 1.5× P2Rank);
  * `--preset fast`: 48 ms (≈ 4.4× P2Rank, ≈ 12.6× fpocket);
  * `accurate`: 271 ms.
* **One core, warm, median excl. / incl. parsing:** fast 28.4 / 31.5 ms; default 96.0 / 99.2 ms; accurate 203.0 / 206.4 ms.
* **Throughput over 10,000 structures, 3 GPUs (8 workers each) vs 24 CPU workers:**
  * fast: 646.3 vs 544.7 structures/s;
  * default: 411.4 vs 171.0/s;
  * accurate: 338.1 vs 88.2/s.
  * After T1 the GPU path is no longer host-bound for large batches. On short runs (2,000 structures) the CPU workers still win for `fast`.
* The human AFDB proteome demo (20,550 proteins, 129 s in AF mode, 3 GPUs × 8 workers, default preset, before T1) is a different setting.

**Main caveats.**
1. **The C1 gain from v1 to v2 is an output-length effect, not better ranking.** The LIGYSIS closest-pocket rule penalises long lists. v2 shortens the list from 32.9 to 9.1 pockets per chain. The cost: max recall falls from 99.3 to 84.2, and any-pocket top-N+2 from 80.1 to 76.9. C1-strict is unchanged.
2. **Ion sites carry much of the C1 margin.** v2 Δ is +29.5 on ion sites, but +2.2 [0.1, 4.3] on "other" small molecules. In v1 that stratum was significantly *worse* than fpocket+PRANK: −6.8.
3. **Gaps on apo, cryptic and interface sites.** Apo/cryptic (O4) and dimer-interface (O6) performance is at par or slightly below P2Rank, and inconclusive.
4. **Low precision on AF models with the default ranker.** AF-set P1K is 58.9 vs 73.9 for P2Rank-AF. The optional `--af-ranker` reaches 73.9 (descriptive, test-informed).
5. **AF mode's geometry does not beat a simple pLDDT < 70 pocket filter on recall.** It is equivalent on dev and on the AF test set (+0.4 [−0.5, 1.3], descriptive), and the filter has the higher P1K. Its value is removing hallucinated pockets. The O5 margin is an ion effect (§4.3), and AF mode was inert on PocketWatch (no pLDDT).
6. **Deviations and test-informed steps (all disclosed).**
   * Amendments A1–A3 were made before any BURROW test prediction; the PREREG hash changed from `582b8b56…` to `59c7e41e…`.
   * The G1 gate failed and its fallback was not taken (D7).
   * FREEZE v2 was committed 70 min after the v1 test prediction files existed, but before any scoring.
   * The v3 cycle was motivated by the O6 test result and changed nothing.
   * The `--af-ranker` recommendation is informed by descriptive test rows.
   * v1 was significantly worse than P2Rank-AF on O3 (−2.7 [−4.9, −0.5]), though not beyond the margin.
   * Times are CET unless marked Z (UTC).

---

## 2. Approach

### 2.1 Pipeline

```
 PDB/mmCIF/AF model ──► polymer-only atoms (HETATM, waters, ions removed; first altloc; canonical PCA frame)
        │   [--af-mode: prune pLDDT<50 termini + internal runs ≥7 res; soft occlusion w = clip((pLDDT−40)/40,0,1)]
        ▼
 (1) candidates: 1 Å solvent-shell grid (vdW+1 Å, ≤6 Å from protein) → LIGSITE PSP cascade (PSP≥2 kept,
     coarse 3 Å sub-lattice for the rest) + metal-coordination candidates (≥2 coordinators, 1.95–2.35 Å)
        ▼
 (2) point features (84 default / 86 accurate): Fibonacci ray marching through a full-atom and a
     backbone+Cβ absorption grid → blocked fraction at 6/10/16(/24) Å, first-hit depth & chemistry,
     escape fraction; PSP; metal geometry; atom/residue-class densities 4–12 Å; WCN; protrusion
        ▼
 (3) point scorer: LightGBM 250×63 (ranker `all`: ions+ligands; `small`: non-ion ligands)
        ▼
 (4) pockets: geometric pass (single linkage of points at buriedness 0.40/0.55/0.70/0.85) ∪ score pass
     (0.15/0.30/0.50); chaining control (k-means split >20 Å), multi-scale sub-pockets (~6 Å pieces)
        ▼
 (5) pocket ranker: LightGBM (300×15) on 76 descriptors, trained on cross-fitted point scores,
     graded target clip(1 − DCC/12, 0, 1) → cross-protein-calibrated score
        ▼
 (6) suppression: centre < 10 Å, residue Jaccard ≥ 0.75 or point overlap ≥ 0.3 → ≤ 50 pockets
        ▼
 (7) v2 output floor: drop pockets with score < 0.03 once 3 are kept (--min-score none = v1 list)
        ▼
 CSV: rank, score, centre, residues  (+ pocket points)
```

Specification: docs/METHOD.md. Design and reviews: DESIGN.md v3 (§8 reviewer→change map, §9 amendments).

* **Candidates and features (novelty claim N1).** The candidates are a single volume-element point set, not fpocket alpha spheres. Ray buriedness through a second, backbone-only grid gives a feature that tolerates side-chain changes. A 3 Å sub-lattice of low-PSP points keeps shallow sites in the pool.
* **Two rankers.** `all` (ions included, the C1 headline) and `small` (P2Rank's ligand definition, used on COACH420/HOLO4K/CryptoBench/PocketWatch). Both are fixed in PREREG.
* **Presets** (two pre-registered, one optional).
  * `default` (30 rays, 3 Å sub-lattice, only points with buriedness ≥ 0.7 scored) is used for all pre-registered claims.
  * `accurate` (60 rays, 2 Å sub-lattice, all points scored) is shipped because it was more than 1 point better on non-ion dev sites (D5).
  * `fast` (added after the tests; not pre-registered; results/dev/biolip/FAST_PRESET.md) uses a 1.5 Å grid, 12 rays, a 2 Å sub-lattice and a smaller point model (100 × 31). Metal candidates are kept, because removing them cost 13 DCA4 points on ion sites. It was selected on train-CV with a pre-fixed rule (≤ 35 ms, ≤ 2-point loss) and confirmed once on dev: BioLiP dev `all` top-N+2 −0.8, DCA4 −1.7, P1K −2.3 vs default. The fast backend reproduces the reference exactly on CPU and GPU.
* **Output floor (v2, D12/D13).** τ = 0.03 and min_keep = 3 were chosen mechanically on train cluster-CV under no-loss guards (results/dev/biolip/V2_CYCLE.md §H5). The floor is reported as what it is: control of output length.
* **Optional `--output-rule region`** (v3b cycle, dev evidence only, not pre-registered; results/dev/biolip/V3b_CYCLE.md). It keeps the v2 list and adds any pocket scoring ≥ 0.005 whose centre is more than 16 Å from all kept pockets. It recovers coverage (dev max recall +7 to +10) without loss in closest top-N+2, DCA4 or P1K. It failed its gain gate (§5), so the default is unchanged.
* **AF mode (`--af-mode`, D8; docs/AF_MODE.md).** Spaghetti pruning plus soft occlusion, with the standard ranker. With uniform pLDDT ≥ 90 the output is byte-identical to standard mode (579/579 dev chains). The optional `--af-ranker` (pLDDT pocket descriptors) trades recall near disorder for calibration across proteins (§4.4). Side-chain tolerance is implemented but off (§5). PAE was unavailable: the AFDB file endpoint returned HTTP 403 (docs/AF_BENCHMARK.md §6).
* **Multimers.** Input is any number of protein chains. Candidates, features and ranking are computed on the whole assembly, so interface pockets are native. Pocket descriptors include the number of chains lining the pocket. The dimer benchmark collapses symmetric copies label-free for every method (PREREG fixed rules + A1).
* **Backends (docs/PERF.md).**
  * CPU: NumPy + Numba.
  * GPU: Triton/PyTorch kernels (fp64-exact ray marching) with tree inference free of LightGBM, one process per GPU, CPU workers for parsing and post-processing.
  * Equivalence: the output is identical to the reference on 64 random dev structures × 4 models × CPU/GPU and on 40 AF models × 2 presets × CPU/GPU in AF mode (scores, centres, residues, points).
  * A GPU fp32-argument bug at exactly pLDDT 70 was found after the freeze and fixed, with a regression test (D11). All v1 AF-mode test predictions were therefore produced on the CPU path.

### 2.2 Positioning against the literature (LITERATURE.md §2.2, §7)

* **Published LIGYSIS methods.** Before this project, fpocket+PRANK was the best method on LIGYSIS top-N+2 (60.4). Our harness reproduces every published method's numbers within ±0.5 (33/33 variants). Scored with the identical harness on the same 6,721 sites:

  | method | top-N+2 | P1K |
  |---|---|---|
  | DeepPocket-RESC | 58.1 | |
  | P2Rank+Cons | 53.9 | |
  | GrASP | 49.9 | 92.5 |
  | VN-EGNN-NR | 46.1 | |
  | IF-SitePred-rescored-NR | | 94.3 (highest published) |
  | **BURROW v2** | **72.5** | **96.1** |
  | BURROW v1 | 64.3 | |

  These comparisons are descriptive: there is no paired CI against the deep-learning methods.
* **Seq2Pocket.** Its author-reported ≈ 69 % (a fine-tuned 3B-parameter protein language model; LITERATURE §0) was not run on our harness, so it is not comparable.
* **Where the gain comes from.** Consistent with LITERATURE §7, the headroom came from high-recall candidates (v1 max recall 99.3 vs P2Rank 57.7) combined with a calibrated learned ranker. The candidates alone are not enough: shuffling the ranks of BURROW's own pockets gives tiling-level recall (§4.7).

---

## 3. Data and benchmarks

**Training and dev sets** (docs/TRAINSET.md; DATA.md):
* **Construction.** Built from BioLiP2 (snapshot 2025-11-12) in the LIGYSIS style: sites are ligands pooled across up to 20 entries per UniProt and superposed onto a representative chain; ions are included.
* **Frozen test union.** The test union was frozen *before* the training build (`data/manifests/test_union.tsv`, sha256 `27c3d793…`). It covers LIGYSIS, all polymer entities of COACH420/HOLO4K, all CryptoBench splits, PocketMiner, the PocketWatch test set, the AF set and every dimer chain.
* **Leakage rule.** A training chain is removed if it hits any test chain with MMseqs2 E < 1e-3 and identity ≥ 30 % over ≥ 50 % coverage or ≥ 80 residues. This removed 77.4 % of BioLiP2 chains.
* **Set sizes.**
  * Initial build: 6,644 train / 596 dev entries and 14,073 train sites, of which 37.7 % are ion-only.
  * 60.4 % of train entries have max Foldseek TM < 0.5 to every test chain.
* **Independent leakage audit** (results/audit/LEAKAGE_AUDIT.md, re-implemented from scratch): verdict "FAIL (marginal)".
  * Findings: 7 train assembly-partner chains violate the rule against the builder's own union; 92 primary-tier violators in total once observed-residue sequences are used (88 of them at 0.30–0.35 identity); 1 UniProt overlap.
  * Fix (D6): **every** flagged entry was dropped (186 entries), leaving 6,475 train and 579 dev chains.
  * **No full re-audit was run after D6.** The later checks were the dev reviewer's MMseqs2 search (2 borderline dev hits) and the test verifier's UniProt and PDB-ID overlap check.
  * The test verifier later found 0 of 2,565 LIGYSIS UniProts in train or dev.
* **Dev sets** (never test):
  * BioLiP2 dev (579 chains);
  * apo-dev = CryptoBench *train* folds (885 apo structures);
  * AF dev = AFDB models of dev proteins (278);
  * train-assembly out-of-fold (OOF) for multimers.

**Test benchmarks** (docs/EVALUATION.md; all frozen before any BURROW test prediction):

| benchmark | endpoint | units | inputs | source |
|---|---|---|---|---|
| LIGYSIS (C1, C1-strict, C2) | top-N+2 DCC12 (closest-pocket rule), DCA4, P1K | 2,775 chains / 6,721 sites (6,387 with ligand atoms, A2) | authors' ligand-free representative chains | Utgés & Barton 2024 |
| LIGYSIS_NI | same, ions removed (descriptive) | 2,003 chains / 4,141 sites | same | |
| COACH420(mlig), HOLO4K(mlig) (O2a/b) | DCA4 top-n, P2Rank rules (our evaluator reproduces P2Rank's to 0.1 %) | 379 / 6,874 ligands | P2Rank distribution files | Krivák & Hoksza |
| PocketWatch (O3) | top-N+2 DCC12, their mask | 1,566 structures / 1,573 sites (released ≥ 2024) | their predicted structures, `--af-mode` | zPocket paper (MIT) |
| CryptoBench test (O4) | top-N+2 DCC12 to the site-residue centroid on apo | 222 apo / 270 sites | apo structures | Škrhák et al. 2025 |
| AF set (O5) | top-N+2 DCC12 | 2,526 AFDB v6 human models / 6,502 sites | full-length models, `--af-mode` | **built here** (docs/AF_BENCHMARK.md) |
| Dimer (O6) | interface top-N+2 DCC12 on full-assembly input | all 400 assemblies scored (283 30 %-cluster bootstrap units) / 807 unique sites, 243 interface (70 minor-interface sites lie outside the endpoint) | PDB assembly 1 | **built here** (docs/DIMER_BENCHMARK.md) |

**Comparator versions.** On LIGYSIS the fpocket+PRANK comparator uses PRANK 2.4.2, as in the paper; the other benchmarks use PRANK 2.5.1. Both give identical LIGYSIS numbers (results/baselines/HEADLINES.md). PREREG's family-2 text says "the five" but lists six endpoints, because O2 counts twice; Holm used all six.

**Datasets not used as test benchmarks** (M6):
* **scPDB:** no license is stated (academic use only). It has one druggable site per entry, it is a training set for several comparators, and it overlaps LIGYSIS (9.7 % of sites; LITERATURE §2.2).
* **AF2BIND:** residue-level only, with about 65 test chains per seed-dependent split and labels pooled from homologous structures (DATA.md §7).
* **HOTPocket:** a catalogue of predicted pockets, not a benchmark. Its BioLiP2-derived known pockets were used only descriptively, in the proteome demo.

**Built benchmarks.**
* **AF set.** LIGYSIS sites transferred by UniProt numbering onto AFDB v6 models, with residue-type checks. 42 fragmented proteins (> 2,700 aa) are excluded. It is **holo-biased**: median local Cα RMSD to the PDB representative is 0.38 Å, and only 95 benchmark sites have pLDDT < 70.
* **Dimer set.** 400 complexes (274 homo / 126 hetero) taken from assembly 1 of entries of LIGYSIS UniProts: `author_and_software_defined_assembly`, X-ray/EM ≤ 3 Å. Sites are classed as single-chain / homo-interface / hetero-interface. Symmetric copies are grouped by residue-set Jaccard ≥ 0.5 (A1), and the oracle ceiling is 1.0.

**Reproduction gates (PREREG; passed before any comparison).**
* Our harness on the authors' LIGYSIS predictions reproduces all 33 published variants within ±0.5 (results/validation/ligysis_reproduction.md). The authors' own code agrees.
* Our re-runs agree with the published values (results/baselines/ligysis_gate.md):
  * P2Rank 2.4.2: 52.6 vs 51.9 published.
  * fpocket 4.2.3+PRANK: 59.5 vs 60.4.
  * A3 (fpocket 4.2.3, not 4.0.3, matches the paper's pocket counts) was adopted before any BURROW test prediction.

---

## 4. Results

### 4.1 Pre-registered families (test)

Every row comes from results/test/v{1,2}/summary.json. Ledger: results/TEST_LEDGER.md (2 versions on test; the cap was 3). An independent agent recomputed all headline numbers, C1 with the LIGYSIS authors' code, and all matched within ±0.2 (results/verify_test/VERIFY.md).

**Family 1** (fixed sequence C1 → C1-strict → C2; requirement: Δ ≥ +2 and CI > 0 vs both comparators, every seed; C2 is non-inferiority at −3):

| endpoint | seed | comparator (value) | v1 BURROW | v1 Δ [95% CI] | v2 BURROW | v2 Δ [95% CI] | pass v1 / v2 |
|---|---|---|---|---|---|---|---|
| C1 | s0 | published fpocket+PRANK (60.4) | 64.3 | +3.9 [2.0, 6.0] | 72.5 | +12.1 [9.9, 14.2] | yes / yes |
| C1 | s0 | re-run fpocket 4.2.3+PRANK 2.4.2 (59.5) | 64.3 | +4.8 [2.9, 7.0] | 72.5 | +13.0 [10.9, 15.2] | yes / yes |
| C1 | s1 | published fpocket+PRANK (60.4) | 64.5 | +4.1 [2.2, 6.2] | 72.0 | +11.6 [9.4, 13.9] | yes / yes |
| C1 | s1 | re-run fpocket 4.2.3+PRANK 2.4.2 (59.5) | 64.5 | +5.0 [3.1, 7.2] | 72.0 | +12.5 [10.3, 14.8] | yes / yes |
| C1 | s2 | published fpocket+PRANK (60.4) | 64.9 | +4.5 [2.5, 6.7] | 72.3 | +11.9 [9.6, 14.1] | yes / yes |
| C1 | s2 | re-run fpocket 4.2.3+PRANK 2.4.2 (59.5) | 64.9 | +5.4 [3.4, 7.7] | 72.3 | +12.8 [10.5, 15.1] | yes / yes |
| C1-strict | s0 | published fpocket+PRANK (31.6) | 54.4 | +22.9 [20.2, 25.9] | 54.2 | +22.6 [20.0, 25.5] | yes / yes |
| C1-strict | s0 | re-run fpocket 4.2.3+PRANK 2.4.2 (31.8) | 54.4 | +22.6 [19.8, 25.8] | 54.2 | +22.4 [19.6, 25.4] | yes / yes |
| C1-strict | s1 | published fpocket+PRANK (31.6) | 54.1 | +22.5 [19.8, 25.4] | 54.2 | +22.6 [19.9, 25.5] | yes / yes |
| C1-strict | s1 | re-run fpocket 4.2.3+PRANK 2.4.2 (31.8) | 54.1 | +22.3 [19.4, 25.4] | 54.2 | +22.4 [19.5, 25.3] | yes / yes |
| C1-strict | s2 | published fpocket+PRANK (31.6) | 54.5 | +22.9 [20.2, 25.8] | 54.0 | +22.4 [19.7, 25.3] | yes / yes |
| C1-strict | s2 | re-run fpocket 4.2.3+PRANK 2.4.2 (31.8) | 54.5 | +22.7 [19.8, 25.8] | 54.0 | +22.2 [19.3, 25.2] | yes / yes |
| C2 | s0 | published fpocket+PRANK (81.7) | 95.7 | +14.0 [10.1, 18.6] | 96.1 | +14.4 [10.2, 19.0] | yes / yes |
| C2 | s0 | re-run fpocket 4.2.3+PRANK 2.4.2 (81.7) | 95.7 | +14.0 [9.9, 18.7] | 96.1 | +14.4 [10.2, 18.9] | yes / yes |
| C2 | s1 | published fpocket+PRANK (81.7) | 96.4 | +14.7 [10.5, 18.9] | 96.5 | +14.8 [10.9, 19.1] | yes / yes |
| C2 | s1 | re-run fpocket 4.2.3+PRANK 2.4.2 (81.7) | 96.4 | +14.7 [10.5, 18.9] | 96.5 | +14.8 [10.8, 19.0] | yes / yes |
| C2 | s2 | published fpocket+PRANK (81.7) | 96.9 | +15.2 [11.1, 19.5] | 96.9 | +15.2 [10.9, 19.6] | yes / yes |
| C2 | s2 | re-run fpocket 4.2.3+PRANK 2.4.2 (81.7) | 96.9 | +15.2 [10.9, 19.5] | 96.9 | +15.2 [10.9, 19.6] | yes / yes |

**Family 2** (Holm over 6 endpoints, margin −2 vs the best of P2Rank 2.5.1 / fpocket 4.2.3+PRANK on identical inputs; "superior" = CI > 0):

| endpoint | seed | metric (n sites / units) | best comparator (value) | v1 BURROW | v1 Δ [95% CI] | v1 decision | v2 BURROW | v2 Δ [95% CI] | v2 decision |
|---|---|---|---|---|---|---|---|---|---|
| O2a | s0 | success_DCA4_topn (379 / 247) | p2rank_2.5.1 (69.4) | 71.8 | +2.4 [−2.7, 7.1] | inconclusive | 71.0 | +1.6 [−3.0, 5.8] | inconclusive |
| O2a | s1 | success_DCA4_topn (379 / 247) | p2rank_2.5.1 (69.4) | 71.2 | +1.8 [−2.9, 6.3] | inconclusive | 71.5 | +2.1 [−2.9, 6.6] | inconclusive |
| O2a | s2 | success_DCA4_topn (379 / 247) | p2rank_2.5.1 (69.4) | 73.4 | +4.0 [−0.8, 8.3] | inconclusive | 71.2 | +1.8 [−2.7, 6.0] | inconclusive |
| O2b | s0 | success_DCA4_topn (6,874 / 708) | p2rank_2.5.1 (76.6) | 78.4 | +1.8 [−1.0, 4.4] | non-inferior | 78.2 | +1.6 [−1.2, 4.3] | non-inferior |
| O2b | s1 | success_DCA4_topn (6,874 / 708) | p2rank_2.5.1 (76.6) | 78.4 | +1.8 [−0.9, 4.4] | non-inferior | 78.4 | +1.8 [−1.0, 4.6] | non-inferior |
| O2b | s2 | success_DCA4_topn (6,874 / 708) | p2rank_2.5.1 (76.6) | 78.0 | +1.4 [−1.2, 3.9] | non-inferior | 77.9 | +1.4 [−1.3, 4.1] | non-inferior |
| O3 | s0 | recall_topn2 (1,573 / 910) | p2rank_2.5.1_af (75.8) | 73.1 | −2.7 [−4.9, −0.5] | inconclusive | 76.6 | +0.8 [−1.4, 2.9] | non-inferior |
| O3 | s1 | recall_topn2 (1,573 / 910) | p2rank_2.5.1_af (75.8) | 73.9 | −2.0 [−4.0, −0.1] | inconclusive | 76.6 | +0.8 [−1.3, 2.8] | non-inferior |
| O3 | s2 | recall_topn2 (1,573 / 910) | p2rank_2.5.1_af (75.8) | 73.9 | −2.0 [−4.1, 0.2] | inconclusive | 77.1 | +1.3 [−0.7, 3.3] | non-inferior |
| O4 | s0 | recall_topn2 (270 / 203) | p2rank_2.5.1 (71.9) | 66.7 | −5.2 [−11.1, 1.0] | inconclusive | 69.3 | −2.6 [−8.6, 3.0] | inconclusive |
| O4 | s1 | recall_topn2 (270 / 203) | p2rank_2.5.1 (71.9) | 68.5 | −3.3 [−9.8, 2.3] | inconclusive | 73.0 | +1.1 [−4.9, 6.8] | inconclusive |
| O4 | s2 | recall_topn2 (270 / 203) | p2rank_2.5.1 (71.9) | 68.5 | −3.3 [−9.2, 2.3] | inconclusive | 71.1 | −0.7 [−6.3, 5.0] | inconclusive |
| O5 | s0 | recall_topn2 (6,502 / 1,691) | p2rank_2.5.1_af (51.4) | 59.2 | +7.8 [5.3, 10.3] | non-inferior (superior) | 64.5 | +13.1 [11.0, 15.7] | non-inferior (superior) |
| O5 | s1 | recall_topn2 (6,502 / 1,691) | p2rank_2.5.1_af (51.4) | 58.8 | +7.4 [4.8, 9.8] | non-inferior (superior) | 64.5 | +13.1 [10.8, 15.5] | non-inferior (superior) |
| O5 | s2 | recall_topn2 (6,502 / 1,691) | p2rank_2.5.1_af (51.4) | 59.1 | +7.7 [5.1, 10.3] | non-inferior (superior) | 64.4 | +13.0 [10.7, 15.5] | non-inferior (superior) |
| O6 | s0 | success_DCC12_topn2 (243 / 158) | p2rank_2.5.1 (87.7) | 85.6 | −2.1 [−7.1, 2.8] | inconclusive | 84.0 | −3.7 [−8.7, 0.9] | inconclusive |
| O6 | s1 | success_DCC12_topn2 (243 / 158) | p2rank_2.5.1 (87.7) | 84.4 | −3.3 [−8.6, 2.0] | inconclusive | 84.8 | −2.9 [−8.0, 2.2] | inconclusive |
| O6 | s2 | success_DCC12_topn2 (243 / 158) | p2rank_2.5.1 (87.7) | 84.4 | −3.3 [−8.4, 1.5] | inconclusive | 85.2 | −2.5 [−7.3, 2.7] | inconclusive |

**Reading the tables.**
* v1 already passes family 1 by itself. v2 passes O3 where v1 did not: v1 O3 was −2.7 [−4.9, −0.5], significantly worse though not beyond the margin.
* O6 slips slightly from v1 to v2.
* The O5 superiority holds across all seeds and both versions.

### 4.2 Output length: v1 vs v2, and the closest-pocket rule

Seed 0, default preset (results/test/v2/SUMMARY.md, "Output-length trade-off"):

| benchmark | headline metric v1 → v2 | any-pocket top-N+2 v1 → v2 | max recall v1 → v2 | P1K v1 → v2 | pockets/structure v1 → v2 |
|---|---|---|---|---|---|
| LIGYSIS (all, DCC12) | 64.3 → 72.5 | 80.1 → 76.9 | 99.3 → 84.2 | 95.7 → 96.1 | 32.9 → 9.1 |
| LIGYSIS_NI (small) | 58.7 → 66.4 | 76.6 → 71.7 | 99.2 → 79.3 | 89.5 → 89.6 | 36.0 → 7.9 |
| COACH420 (DCA4 top-n) | 71.8 → 71.0 | – | – | – | 33.0 → 5.3 |
| HOLO4K (DCA4 top-n) | 78.4 → 78.2 | – | – | – | 40.8 → 7.9 |
| CryptoBench (apo) | 66.7 → 69.3 | 81.5 → 79.6 | 100.0 → 85.6 | 40.0 → 38.5 | 36.4 → 6.2 |
| PocketWatch (AF mode) | 73.1 → 76.6 | 81.8 → 81.6 | 99.6 → 90.6 | 72.2 → 70.5 | 44.3 → 9.9 |
| AF set (AF mode) | 59.2 → 64.5 | 73.2 → 68.5 | 98.1 → 77.3 | 58.4 → 58.9 | 42.1 → 10.0 |
| Dimer interface | 85.6 → 84.0 | – | – | – | 46.4 → 14.9 |

**Mechanism** (found on dev, results/dev/biolip/V2_CYCLE.md, diagnostic): the LIGYSIS protocol credits a site only to the pocket *closest* to its centre. A low-ranked pocket that is closer than the ranked hit therefore "steals" the site.
* On apo-dev cryptic sites, v1 had any-pocket top-N+2 77.8 vs P2Rank 72.3. Yet its closest-pocket score was lower, because 403 of its misses had a pocket within 12 Å ranked beyond N+2. BURROW output ~42 pockets per structure, P2Rank 4.5.
* The floor removes this penalty. It leaves P1K and C1-strict essentially unchanged and costs coverage.
* One-to-one (Hungarian) top-N+2 on LIGYSIS *drops* from 76.0 (v1) to 71.3 (v2). v2 stays above fpocket+PRANK published (66.3).
* **Recommendation:** use the v2 default for ranked, short lists. Use `--min-score none` (v1 list, bit-identical) for exhaustive discovery.

Full LIGYSIS secondary metrics (seed 0; descriptive):

| method | pockets/chain | top-N | top-N+2 | any-pocket top-N+2 | 1:1 top-N+2 | DCA4 top-N+2 | max recall | P1K | P1K 1:1 | TP@100FP | residue MCC |
|---|---|---|---|---|---|---|---|---|---|---|---|
| BURROW v2 all default s0 | 9.1 | 62.5 | 72.5 | 76.9 | 71.3 | 54.2 | 84.2 | 96.1 | 95.9 | 1561 | 29.0 |
| BURROW v2 all accurate s0 | 8.1 | 61.7 | 71.3 | 75.5 | 69.8 | 54.2 | 81.9 | 95.6 | 95.3 | 1316 | 28.3 |
| fpocket+PRANK (published) | 20.9 | 48.8 | 60.4 | 71.4 | 66.3 | 31.6 | 91.3 | 81.7 | 76.4 | 526 | – |
| fpocket 4.2.3+PRANK 2.4.2 (re-run) | 20.9 | 48.5 | 59.5 | 69.7 | 64.5 | 31.8 | 89.4 | 81.7 | 76.6 | 538 | 11.6 |

LIGYSIS_NI (non-ion sites, `small` ranker; descriptive, no paired CI in the summary):

| method | pockets/chain | top-N | top-N+2 | any-pocket top-N+2 | DCA4 top-N+2 | max recall | P1K | residue MCC |
|---|---|---|---|---|---|---|---|---|
| BURROW v2 small default s0 | 7.9 | 54.8 | 66.4 | 71.7 | 51.3 | 79.3 | 89.6 | 32.2 |
| BURROW v2 small accurate s0 | 6.9 | 53.5 | 66.1 | 70.2 | 52.1 | 76.1 | 89.8 | 32.5 |
| P2Rank 2.5.1 | 5.1 | 53.9 | 60.9 | 62.8 | 44.6 | 67.3 | 80.8 | 34.3 |
| fpocket 4.2.3+PRANK 2.4.2 | 23.4 | 52.3 | 63.4 | 72.9 | 48.2 | 91.7 | 82.7 | 16.9 |

* v2 `small` is above both baselines on LIGYSIS_NI top-N+2.
* v1 `small` was *below* fpocket+PRANK there: 58.7 vs 63.4. DCA4 and P1K favour BURROW in both versions.

Post-hoc paired Δs on LIGYSIS_NI (project bootstrap; results/test/v2/POSTHOC.md; descriptive):

| BURROW model | comparator | metric | BURROW | comparator | Δ [95% CI] |
|---|---|---|---|---|---|
| v1:burrow_small_default_s0 | fpocket_4.2.3+PRANK_2.4.2 | recall_topn2 | 58.7 | 63.4 | −4.6 [−6.3, −2.9] |
| v1:burrow_small_default_s0 | fpocket_4.2.3+PRANK_2.4.2 | recall_ldca_topn2 | 51.2 | 48.2 | +3.0 [1.5, 4.7] |
| v1:burrow_small_default_s0 | p2rank_2.5.1 | recall_topn2 | 58.7 | 60.9 | −2.2 [−4.5, 0.0] |
| v1:burrow_small_default_s0 | p2rank_2.5.1 | recall_ldca_topn2 | 51.2 | 44.6 | +6.7 [4.9, 8.5] |
| v2:burrow_small_default_s0 | fpocket_4.2.3+PRANK_2.4.2 | recall_topn2 | 66.4 | 63.4 | +3.0 [1.1, 4.7] |
| v2:burrow_small_default_s0 | fpocket_4.2.3+PRANK_2.4.2 | recall_ldca_topn2 | 51.3 | 48.2 | +3.1 [1.5, 4.8] |
| v2:burrow_small_default_s0 | p2rank_2.5.1 | recall_topn2 | 66.4 | 60.9 | +5.4 [3.5, 7.5] |
| v2:burrow_small_default_s0 | p2rank_2.5.1 | recall_ldca_topn2 | 51.3 | 44.6 | +6.7 [5.2, 8.4] |
| v2:burrow_small_default_s1 | fpocket_4.2.3+PRANK_2.4.2 | recall_topn2 | 66.8 | 63.4 | +3.5 [1.5, 5.3] |
| v2:burrow_small_default_s1 | fpocket_4.2.3+PRANK_2.4.2 | recall_ldca_topn2 | 51.7 | 48.2 | +3.5 [2.0, 5.2] |
| v2:burrow_small_default_s1 | p2rank_2.5.1 | recall_topn2 | 66.8 | 60.9 | +5.9 [3.9, 7.9] |
| v2:burrow_small_default_s1 | p2rank_2.5.1 | recall_ldca_topn2 | 51.7 | 44.6 | +7.2 [5.6, 8.8] |
| v2:burrow_small_default_s2 | fpocket_4.2.3+PRANK_2.4.2 | recall_topn2 | 66.7 | 63.4 | +3.3 [1.4, 5.1] |
| v2:burrow_small_default_s2 | fpocket_4.2.3+PRANK_2.4.2 | recall_ldca_topn2 | 51.4 | 48.2 | +3.2 [1.6, 4.9] |
| v2:burrow_small_default_s2 | p2rank_2.5.1 | recall_topn2 | 66.7 | 60.9 | +5.8 [3.8, 7.7] |
| v2:burrow_small_default_s2 | p2rank_2.5.1 | recall_ldca_topn2 | 51.4 | 44.6 | +6.8 [5.3, 8.5] |

### 4.3 Strata (descriptive; seed 0, default preset; * = fewer than 100 sites)

| endpoint | stratum | n sites | comparator (value) | v1 BURROW | v1 Δ [95% CI] | v2 BURROW | v2 Δ [95% CI] |
|---|---|---|---|---|---|---|---|
| C1 | max TM to train 0.5-0.7 | 921 | fpocket_4.2.3+PRANK_2.4.2 (64.7) | 66.4 | +1.7 [−2.4, 6.3] | 73.5 | +8.8 [4.7, 13.2] |
| C1 | max TM to train <0.5 | 4,544 | fpocket_4.2.3+PRANK_2.4.2 (57.5) | 64.3 | +6.8 [4.0, 9.4] | 72.8 | +15.3 [12.5, 18.0] |
| C1 | max TM to train >0.7 | 1,256 | fpocket_4.2.3+PRANK_2.4.2 (62.8<!--src:v2:descriptive/strata{endpoint=C1;kind=fold_novelty_maxTM;stratum=>0.7}/b-->) | 62.7<!--src:v1:descriptive/strata{endpoint=C1;kind=fold_novelty_maxTM;stratum=>0.7}/a--> | −0.1<!--src:v1:descriptive/strata{endpoint=C1;kind=fold_novelty_maxTM;stratum=>0.7}/diff--> [−3.6<!--src:v1:descriptive/strata{endpoint=C1;kind=fold_novelty_maxTM;stratum=>0.7}/ci_low-->, 3.9<!--src:v1:descriptive/strata{endpoint=C1;kind=fold_novelty_maxTM;stratum=>0.7}/ci_high-->] | 70.5<!--src:v2:descriptive/strata{endpoint=C1;kind=fold_novelty_maxTM;stratum=>0.7}/a--> | +7.6<!--src:v2:descriptive/strata{endpoint=C1;kind=fold_novelty_maxTM;stratum=>0.7}/diff--> [4.2<!--src:v2:descriptive/strata{endpoint=C1;kind=fold_novelty_maxTM;stratum=>0.7}/ci_low-->, 11.6<!--src:v2:descriptive/strata{endpoint=C1;kind=fold_novelty_maxTM;stratum=>0.7}/ci_high-->] |
| C1 | ligand ion | 2,580 | fpocket_4.2.3+PRANK_2.4.2 (50.5) | 72.1 | +21.6 [18.0, 25.2] | 80.0 | +29.5 [26.1, 32.7] |
| C1 | ligand nucleotide-cofactor | 795 | fpocket_4.2.3+PRANK_2.4.2 (82.9) | 82.0 | −0.9 [−3.6, 2.1] | 87.5 | +4.7 [2.0, 7.7] |
| C1 | ligand other | 3,346 | fpocket_4.2.3+PRANK_2.4.2 (60.9) | 54.1 | −6.8 [−8.7, −4.9] | 63.1 | +2.2 [0.1, 4.3] |
| O2a | max TM to train 0.5-0.7 * | 71 | p2rank_2.5.1 (77.5) | 76.1 | −1.4 [−10.0, 7.0] | 74.6 | −2.8 [−12.7, 7.1] |
| O2a | max TM to train <0.5 | 139 | p2rank_2.5.1 (59.0) | 65.5 | +6.5 [0.0, 13.9] | 66.2 | +7.2 [1.5, 13.4] |
| O2a | max TM to train >0.7 | 168 | p2rank_2.5.1 (74.4<!--src:v2:descriptive/strata{endpoint=O2a;kind=fold_novelty_maxTM;stratum=>0.7}/b-->) | 75.0<!--src:v1:descriptive/strata{endpoint=O2a;kind=fold_novelty_maxTM;stratum=>0.7}/a--> | +0.6<!--src:v1:descriptive/strata{endpoint=O2a;kind=fold_novelty_maxTM;stratum=>0.7}/diff--> [−7.6<!--src:v1:descriptive/strata{endpoint=O2a;kind=fold_novelty_maxTM;stratum=>0.7}/ci_low-->, 7.7<!--src:v1:descriptive/strata{endpoint=O2a;kind=fold_novelty_maxTM;stratum=>0.7}/ci_high-->] | 73.2<!--src:v2:descriptive/strata{endpoint=O2a;kind=fold_novelty_maxTM;stratum=>0.7}/a--> | −1.2<!--src:v2:descriptive/strata{endpoint=O2a;kind=fold_novelty_maxTM;stratum=>0.7}/diff--> [−9.6<!--src:v2:descriptive/strata{endpoint=O2a;kind=fold_novelty_maxTM;stratum=>0.7}/ci_low-->, 6.0<!--src:v2:descriptive/strata{endpoint=O2a;kind=fold_novelty_maxTM;stratum=>0.7}/ci_high-->] |
| O2b | max TM to train 0.5-0.7 | 1,278 | p2rank_2.5.1 (76.1) | 76.7 | +0.5 [−3.5, 4.9] | 76.5 | +0.4 [−3.7, 4.8] |
| O2b | max TM to train <0.5 | 2,733 | p2rank_2.5.1 (73.6) | 74.9 | +1.3 [−3.8, 6.3] | 74.9 | +1.4 [−3.8, 6.4] |
| O2b | max TM to train >0.7 | 2,853 | p2rank_2.5.1 (79.6<!--src:v2:descriptive/strata{endpoint=O2b;kind=fold_novelty_maxTM;stratum=>0.7}/b-->) | 82.6<!--src:v1:descriptive/strata{endpoint=O2b;kind=fold_novelty_maxTM;stratum=>0.7}/a--> | +3.0<!--src:v1:descriptive/strata{endpoint=O2b;kind=fold_novelty_maxTM;stratum=>0.7}/diff--> [−0.4<!--src:v1:descriptive/strata{endpoint=O2b;kind=fold_novelty_maxTM;stratum=>0.7}/ci_low-->, 5.9<!--src:v1:descriptive/strata{endpoint=O2b;kind=fold_novelty_maxTM;stratum=>0.7}/ci_high-->] | 82.2<!--src:v2:descriptive/strata{endpoint=O2b;kind=fold_novelty_maxTM;stratum=>0.7}/a--> | +2.6<!--src:v2:descriptive/strata{endpoint=O2b;kind=fold_novelty_maxTM;stratum=>0.7}/diff--> [−1.3<!--src:v2:descriptive/strata{endpoint=O2b;kind=fold_novelty_maxTM;stratum=>0.7}/ci_low-->, 6.1<!--src:v2:descriptive/strata{endpoint=O2b;kind=fold_novelty_maxTM;stratum=>0.7}/ci_high-->] |
| O3 | max TM to train 0.5-0.7 | 470 | p2rank_2.5.1_af (73.6) | 69.1 | −4.5 [−8.7, −0.6] | 74.5 | +0.9 [−3.6, 5.1] |
| O3 | max TM to train <0.5 | 258 | p2rank_2.5.1_af (64.3) | 60.5 | −3.9 [−8.4, 0.8] | 63.2 | −1.2 [−6.8, 4.2] |
| O3 | max TM to train >0.7 | 845 | p2rank_2.5.1_af (80.6<!--src:v2:descriptive/strata{endpoint=O3;kind=fold_novelty_maxTM;stratum=>0.7}/b-->) | 79.2<!--src:v1:descriptive/strata{endpoint=O3;kind=fold_novelty_maxTM;stratum=>0.7}/a--> | −1.4<!--src:v1:descriptive/strata{endpoint=O3;kind=fold_novelty_maxTM;stratum=>0.7}/diff--> [−4.4<!--src:v1:descriptive/strata{endpoint=O3;kind=fold_novelty_maxTM;stratum=>0.7}/ci_low-->, 1.5<!--src:v1:descriptive/strata{endpoint=O3;kind=fold_novelty_maxTM;stratum=>0.7}/ci_high-->] | 81.9<!--src:v2:descriptive/strata{endpoint=O3;kind=fold_novelty_maxTM;stratum=>0.7}/a--> | +1.3<!--src:v2:descriptive/strata{endpoint=O3;kind=fold_novelty_maxTM;stratum=>0.7}/diff--> [−1.6<!--src:v2:descriptive/strata{endpoint=O3;kind=fold_novelty_maxTM;stratum=>0.7}/ci_low-->, 4.1<!--src:v2:descriptive/strata{endpoint=O3;kind=fold_novelty_maxTM;stratum=>0.7}/ci_high-->] |
| O4 | max TM to train 0.5-0.7 * | 53 | p2rank_2.5.1 (77.4) | 71.7 | −5.7 [−18.5, 6.2] | 69.8 | −7.5 [−23.0, 8.2] |
| O4 | max TM to train <0.5 | 130 | p2rank_2.5.1 (63.1) | 60.0 | −3.1 [−12.5, 6.4] | 63.8 | +0.8 [−7.4, 9.4] |
| O4 | max TM to train >0.7 * | 87 | p2rank_2.5.1 (81.6<!--src:v2:descriptive/strata{endpoint=O4;kind=fold_novelty_maxTM;stratum=>0.7}/b-->) | 73.6<!--src:v1:descriptive/strata{endpoint=O4;kind=fold_novelty_maxTM;stratum=>0.7}/a--> | −8.0<!--src:v1:descriptive/strata{endpoint=O4;kind=fold_novelty_maxTM;stratum=>0.7}/diff--> [−17.1<!--src:v1:descriptive/strata{endpoint=O4;kind=fold_novelty_maxTM;stratum=>0.7}/ci_low-->, 1.1<!--src:v1:descriptive/strata{endpoint=O4;kind=fold_novelty_maxTM;stratum=>0.7}/ci_high-->] | 77.0<!--src:v2:descriptive/strata{endpoint=O4;kind=fold_novelty_maxTM;stratum=>0.7}/a--> | −4.6<!--src:v2:descriptive/strata{endpoint=O4;kind=fold_novelty_maxTM;stratum=>0.7}/diff--> [−13.6<!--src:v2:descriptive/strata{endpoint=O4;kind=fold_novelty_maxTM;stratum=>0.7}/ci_low-->, 3.3<!--src:v2:descriptive/strata{endpoint=O4;kind=fold_novelty_maxTM;stratum=>0.7}/ci_high-->] |
| O5 | max TM to train 0.5-0.7 | 1,727 | p2rank_2.5.1_af (55.0) | 59.1 | +4.1 [−0.2, 8.9] | 63.9 | +8.9 [5.2, 12.6] |
| O5 | max TM to train <0.5 | 2,215 | p2rank_2.5.1_af (47.3) | 61.9 | +14.6 [10.0, 19.0] | 67.9 | +20.7 [16.1, 24.9] |
| O5 | max TM to train >0.7 | 2,560 | p2rank_2.5.1_af (52.6<!--src:v2:descriptive/strata{endpoint=O5;kind=fold_novelty_maxTM;stratum=>0.7}/b-->) | 56.9<!--src:v1:descriptive/strata{endpoint=O5;kind=fold_novelty_maxTM;stratum=>0.7}/a--> | +4.3<!--src:v1:descriptive/strata{endpoint=O5;kind=fold_novelty_maxTM;stratum=>0.7}/diff--> [1.1<!--src:v1:descriptive/strata{endpoint=O5;kind=fold_novelty_maxTM;stratum=>0.7}/ci_low-->, 8.0<!--src:v1:descriptive/strata{endpoint=O5;kind=fold_novelty_maxTM;stratum=>0.7}/ci_high-->] | 62.1<!--src:v2:descriptive/strata{endpoint=O5;kind=fold_novelty_maxTM;stratum=>0.7}/a--> | +9.5<!--src:v2:descriptive/strata{endpoint=O5;kind=fold_novelty_maxTM;stratum=>0.7}/diff--> [6.2<!--src:v2:descriptive/strata{endpoint=O5;kind=fold_novelty_maxTM;stratum=>0.7}/ci_low-->, 12.9<!--src:v2:descriptive/strata{endpoint=O5;kind=fold_novelty_maxTM;stratum=>0.7}/ci_high-->] |
| O5 | site pLDDT 50-70 * | 76 | p2rank_2.5.1_af (28.9) | 30.3 | +1.3 [−13.6, 15.5] | 31.6 | +2.6 [−10.3, 15.0] |
| O5 | site pLDDT 70-90 | 1,566 | p2rank_2.5.1_af (46.5) | 55.0 | +8.6 [3.7, 14.0] | 60.3 | +13.9 [9.9, 18.1] |
| O5 | site pLDDT <50 * | 13 | p2rank_2.5.1_af (30.8) | 15.4 | −15.4 [−46.2, 18.2] | 7.7 | −23.1 [−53.3, 9.1] |
| O5 | site pLDDT >=90 | 4,847 | p2rank_2.5.1_af (53.4<!--src:v2:descriptive/strata{endpoint=O5;kind=site_plddt_band;stratum=>=90}/b-->) | 61.1<!--src:v1:descriptive/strata{endpoint=O5;kind=site_plddt_band;stratum=>=90}/a--> | +7.7<!--src:v1:descriptive/strata{endpoint=O5;kind=site_plddt_band;stratum=>=90}/diff--> [5.0<!--src:v1:descriptive/strata{endpoint=O5;kind=site_plddt_band;stratum=>=90}/ci_low-->, 10.4<!--src:v1:descriptive/strata{endpoint=O5;kind=site_plddt_band;stratum=>=90}/ci_high-->] | 66.6<!--src:v2:descriptive/strata{endpoint=O5;kind=site_plddt_band;stratum=>=90}/a--> | +13.2<!--src:v2:descriptive/strata{endpoint=O5;kind=site_plddt_band;stratum=>=90}/diff--> [10.6<!--src:v2:descriptive/strata{endpoint=O5;kind=site_plddt_band;stratum=>=90}/ci_low-->, 15.7<!--src:v2:descriptive/strata{endpoint=O5;kind=site_plddt_band;stratum=>=90}/ci_high-->] |
| O6 | site class hetero_interface * | 66 | p2rank_2.5.1 (92.4) | 86.4 | −6.1 [−13.0, 0.0] | 86.4 | −6.1 [−14.1, 1.7] |
| O6 | site class homo_interface | 177 | p2rank_2.5.1 (85.9) | 85.3 | −0.6 [−7.0, 5.5] | 83.1 | −2.8 [−8.8, 3.1] |
| O6 | site class minor_interface * | 70 | p2rank_2.5.1 (80.0) | 84.3 | +4.3 [−3.0, 11.9] | 85.7 | +5.7 [−2.6, 13.7] |
| O6 | site class single_chain | 494 | p2rank_2.5.1 (64.6) | 82.0 | +17.4 [11.5, 24.1] | 83.6 | +19.0 [13.2, 25.9] |

* **Fold novelty.** The evidence against fold memorisation is the **A1 fold-disjoint retraining** (§4.7), which is within noise on 8 of 9 test rows (8 benchmarks; LIGYSIS has two metrics). The strata are supportive: on C1 and O5 the gain is largest at max TM < 0.5, and the same holds on dev (Δ +19.4; results/review_dev/REVIEW.md).
* **O6 fold strata.** The O6 fold-novelty rows in SUMMARY.md were computed over all 807 dimer sites instead of the 243 interface sites, because of a stratum-filter bug in `scripts/run_prereg_analysis.py`. They are omitted above. The interface-only recomputation (post-hoc, results/test/v2/POSTHOC.md) shows BURROW slightly behind P2Rank in every fold band, so there is no fold-novelty pattern on interfaces. The bug is descriptive only; no pre-registered endpoint is affected.

| fold stratum (max TM to train) | n interface sites | BURROW v2 s0 | P2Rank 2.5.1 | Δ [95% CI] |
|---|---|---|---|---|
| 0.5-0.7 * | 36 | 83.3 | 86.1 | −2.8 [−14.7, 8.8] |
| <0.5 | 143 | 81.8 | 86.0 | −4.2 [−10.9, 2.3] |
| >0.7 * | 64<!--src:json:results/test/v2/posthoc.json#o6_interface_fold_novelty{stratum=>0.7}/n_rows--> | 89.1<!--src:json:results/test/v2/posthoc.json#o6_interface_fold_novelty{stratum=>0.7}/a--> | 92.2<!--src:json:results/test/v2/posthoc.json#o6_interface_fold_novelty{stratum=>0.7}/b--> | −3.1<!--src:json:results/test/v2/posthoc.json#o6_interface_fold_novelty{stratum=>0.7}/diff--> [−10.6<!--src:json:results/test/v2/posthoc.json#o6_interface_fold_novelty{stratum=>0.7}/ci_low-->, 3.4<!--src:json:results/test/v2/posthoc.json#o6_interface_fold_novelty{stratum=>0.7}/ci_high-->] |
* **Ligand class.**
  * Ions dominate the C1 margin.
  * v2 is significantly ahead on nucleotide/cofactor sites and only marginally ahead on "other" small molecules (CI lower bound 0.1).
  * v1 was behind on "other" (−6.8 [−8.7, −4.9]): v1's long list hurt drug-like sites most.
* **pLDDT band (O5).** The gain is concentrated at pLDDT ≥ 70. The < 70 strata have 89 sites in total and are uninformative.
* **Dimer site class (O6).** BURROW is far ahead on single-chain sites in assemblies. It trails on homo- and hetero-interface sites, with CIs that include 0. Minor-interface sites (70) are not part of the endpoint.
* **O5 by ligand class** (post-hoc, descriptive; results/test/v2/POSTHOC.md). The O5 margin is almost entirely on ion sites. Non-ion sites are at par on DCC12 and modestly ahead on DCA4. The nucleotide/cofactor class is at par (+0.1) and "other" is +2.3.

| split | ligand class | metric | n sites | BURROW v2 s0 | P2Rank `-c alphafold` | Δ [95% CI] |
|---|---|---|---|---|---|---|
| 2-class | ion | recall_topn2 | 2422 | 68.7 | 36.6 | +32.1 [28.3, 36.1] |
| 2-class | ion | recall_ldca_topn2 | 2292 | 50.2 | 5.3 | +44.9 [41.4, 48.8] |
| 2-class | non-ion | recall_topn2 | 4080 | 62.1 | 60.2 | +1.9 [−0.1, 3.9] |
| 2-class | non-ion | recall_ldca_topn2 | 3748 | 47.9 | 43.8 | +4.1 [2.5, 5.6] |
| 3-class | nucleotide-cofactor | recall_topn2 | 782 | 84.9 | 84.8 | +0.1 [−2.3, 2.5] |
| 3-class | nucleotide-cofactor | recall_ldca_topn2 | 736 | 82.6 | 82.2 | +0.4 [−2.4, 3.4] |
| 3-class | other | recall_topn2 | 3298 | 56.7 | 54.4 | +2.3 [−0.1, 4.9] |
| 3-class | other | recall_ldca_topn2 | 3012 | 39.4 | 34.4 | +4.9 [3.1, 6.8] |

Only the pre-registered strata above were computed. A UniProt-unit bootstrap sensitivity analysis and AF-set strata by template richness were not run (§7).

### 4.4 AF mode and proteome demo

**Test (O5, AF set, seed 0, v2):**

| method | pockets/structure | top-N | top-N+2 | DCA4 top-N+2 | max recall | P1K | hallucinated pockets % (all) | hallucinated % (top-N+2) |
|---|---|---|---|---|---|---|---|---|
| BURROW v2 all default s0 (AF mode) | 10.0 | 54.4 | 64.5 | 48.8 | 77.3 | 58.9 | 0.2 | 0.1 |
| BURROW v2 all accurate s0 (AF mode) | 8.9 | 54.5 | 63.8 | 48.1 | 75.5 | 58.8 | 0.0 | 0.0 |
| P2Rank 2.5.1 -c alphafold | 7.4 | 45.4 | 51.4 | 29.2 | 61.1 | 73.9 | 0.4 | 0.3 |
| P2Rank 2.5.1 | 5.3 | 42.2 | 47.3 | 27.9 | 53.0 | 71.1 | 0.3 | 0.3 |
| fpocket 4.2.3+PRANK 2.5.1 | 42.7 | 39.5 | 48.6 | 28.8 | 91.1 | 67.0 | 12.8 | 1.7 |

* **Recall and localisation.** BURROW `--af-mode` is ahead on recall and DCA4.
* **Precision.** P2Rank-AF has the higher pooled P1K with the default ranker. This precision deficit was not visible on dev, where BURROW's P1K was higher. The CHEN11-only ablation model, which has no ion labels, reaches AF-set P1K 78.2. That suggests the low pooled precision comes from the ion-heavy `all` training: many confident ion pockets are unlabelled on AF models.
* **Optional AF ranker (descriptive test rows; results/test/v2/DESCRIPTIVE.md).** `--af-ranker` uses `results/dev_af/models/afr_final_afpdb_pl.json` on the `all` default s0 base model:

| benchmark | metric | BURROW + `--af-ranker` | v2 PREREG variant | Δ vs v2 [95% CI] | P2Rank `-c alphafold` | Δ vs P2Rank-AF [95% CI] |
|---|---|---|---|---|---|---|
| af_set | recall_topn2 | 65.8 | 64.5 | +1.3 [0.5, 2.1] | 51.4 | +14.4 [12.1, 16.8] |
| af_set | recall_ldca_topn2 | 49.6 | 48.8 | +0.8 [0.3, 1.4] | 29.2 | +20.4 [18.3, 22.8] |
| af_set | P1K | 73.9 | 58.9 | +15.0 [10.7, 18.6] | 73.9 | +0.0 [−7.0, 6.4] |
| pocketwatch | recall_topn2 | 73.2 | 76.6 | −3.4 [−4.9, −1.8] | 75.8 | −2.6 [−4.6, −0.6] |
| pocketwatch | P1K | 55.9 | 70.5 | −14.6 [−17.3, −9.5] | 56.5 | −0.6 [−3.7, 7.2] |

  * **AF set.** The AF ranker lifts P1K by +15.0 to 73.9, equal to P2Rank-AF. Top-N+2 also rises slightly (+1.3). The precision gap is therefore closed without losing recall.
  * **PocketWatch.** Both top-N+2 (−3.4) and P1K (−14.6) fall. These models carry B-factor 100 on every atom, so there is **no pLDDT signal**: AF mode is a no-op there, and the AF ranker's pLDDT descriptors are uninformative. The comparison also mixes rankers (the AF ranker is tied to the `all` base model; PREREG maps PocketWatch to `small`).
  * **Recommendation** (descriptive; the default stays unchanged per D8): use `--af-ranker` for AFDB proteome screening, where real pLDDT is present and precision across proteins matters. Do not use it on predicted structures without pLDDT. This advice is **test-informed** (descriptive rows) and was not pre-registered. On PocketWatch the AF ranker lowered top-N+2 by −3.4.
* **Hallucinations.** Hallucinated pockets (mean pLDDT < 50, matching no site) are 0.2 % of BURROW pockets vs 12.8 % for fpocket+PRANK.

**Test, descriptive: AF mode vs naive input and vs the pLDDT filter** (results/test/v2/DESCRIPTIVE.md; v2 `all` default s0; paired):
* **vs naive input:** top-N+2 +1.0 [0.1, 2.0]. Top-N+2 hallucinations fall from 2.80 % to 0.12 %, and all-pocket hallucinations from 4.85 % to 0.17 %.
* **vs naive + pLDDT < 70 filter:** top-N+2 +0.4 [−0.5, 1.3] (equivalent). The filter has P1K +2.4 [0.1, 3.7] higher and no hallucinations by construction.
* **PocketWatch:** the models have no pLDDT, so AF mode and the filter are no-ops there. The rows differ only by ranker variant.
* **Conclusion.** AF mode works as hallucination control. A plain pLDDT < 70 pocket filter is an equally good, simpler alternative.

**Mechanism evidence (dev; results/dev_af/AF_DEV_RESULTS.md):**
* **Recall vs the simple filter.** On AF dev, prune+soft reaches DCC12 top-N+2 64.3, vs 63.1 for naive input, 63.4 for the "naive + drop pockets with pLDDT < 70" baseline and 56.2 for P2Rank `-c alphafold`. AF mode is therefore **equivalent to the filter on recall, not better**: on train-OOF −0.7 vs the filter.
* **Hallucinations.** Hallucinated pockets fall from 5.0 % to 0.2 %, without discarding pockets with pLDDT 50–70.
* **Controls.** Matched-random pruning costs 2.5–3.1 points. The no-op check is byte-identical.
* **Ceiling.** The PDB chains of the same proteins give 68.0, so AF mode recovers nearly all of it.
* **Optional AF ranker.** P1K improves by +6.7 (train-OOF). Recall at sites near low-confidence regions moves by −3.0 (reference base model).

**Human proteome (descriptive; results/proteome/HUMAN.md; frozen v1 default model, fast backend, 3 GPUs × 8 workers):**
* 23,586 AFDB models (20,550 proteins; fragments merged) ran with 0 errors: 169 s naive, 129 s in AF mode, peak RSS 17.5 GB.
* **Top-3 pockets with mean pLDDT < 50:**
  * all proteins: 8.0 % naive → 0.9 % in AF mode;
  * proteins with ≥ 50 % disordered residues: 34.9 % → 3.6 %.
* **P2Rank `-c alphafold` on 500 random proteins:** 1.6 % low-pLDDT top-3 pockets, at 960 structures/min vs BURROW's 2,895/min on the same subset.
* Known HOTPocket/BioLiP2 sites recovered in the top-3 (AF mode): 39.5 %. This overlaps train and test sets and is descriptive only.

### 4.5 Dimers

Dimer benchmark, full-assembly input, seed 0, v2 (O6 endpoint = interface DCC12 top-N+2):

| method | pockets/assembly | interface DCC12 top-N+2 | interface DCA4 top-N+2 | homo-interface DCC12 | hetero-interface DCC12 | all-site DCC12 top-N+2 | all-site precision top-N+2 |
|---|---|---|---|---|---|---|---|
| BURROW v2 all default s0 | 14.9 | 84.0 | 77.8 | 83.1 | 86.4 | 83.9 | 48.7 |
| BURROW v2 all accurate s0 | 13.5 | 84.8 | 77.0 | 82.5 | 90.9 | 83.8 | 49.4 |
| P2Rank 2.5.1 | 13.2 | 87.7 | 77.4 | 85.9 | 92.4 | 72.9 | 35.3 |
| fpocket 4.2.3+PRANK 2.5.1 | 50.5 | 86.8 | 74.1 | 86.4 | 87.9 | 74.8 | 38.8 |

* **Single-chain vs interface sites.** On full assemblies BURROW finds far more of *all* sites and is more precise. On interface sites it is at par or slightly behind P2Rank on DCC12 and at par on DCA4.
* **The v3 dev cycle reproduced the pattern on train-assembly OOF** (results/dev/biolip/V3_CYCLE.md, 319 interface sites):
  * interface DCC12: v2 −2.2 vs P2Rank;
  * interface DCA4: 74.9 vs 70.2;
  * all assembly sites: +12.8.
  * Interface fixes did not reach the gate (§5).
* **Isolated-chain input** (descriptive; results/test/v2/DESCRIPTIVE.md, chain mode = every chain predicted alone, same protocol as the baselines' `dimer_chains`):
  * Interface DCC12 top-N+2: BURROW v2 69.6 vs P2Rank 55.4 (+14.2 [9.0, 20.1]), and vs fpocket+PRANK 68.3 (+1.3 [−4.6, 6.7]).
  * Against BURROW's own assembly mode (site-level, any chain): DCC12 −1.2 [−7.2, 4.4], but DCA4 −11.1 [−16.2, −5.6].
  * P2Rank drops from 87.7 (assembly) to 55.4 (chain) without the partner.
  * **Interpretation.** BURROW is robust to a missing partner chain: it still places a pocket near interface sites, so the partner mostly sharpens localisation (DCA4). P2Rank depends on the partner chain.
* **Suitability as a benchmark** (the PROMPT sub-goal): no published dimer pocket benchmark exists (LITERATURE §2.8). Ours is usable and has an oracle ceiling of 1.0. All 400 assemblies were scored (the "283" in SUMMARY's denominator table counts 30 % sequence-cluster bootstrap units). Its interface stratum, however, is small (243 sites on 214 assemblies, 158 cluster units) and gives CIs of ±5 points. A larger, PISA-based, cross-entry interface set is the main follow-up (§7).

### 4.6 Apo and cryptic sites

**CryptoBench test (O4; seed 0, v2; apo structures):**

| method | pockets/structure | top-N | top-N+2 | any-pocket top-N+2 | max recall | P1K | residue MCC |
|---|---|---|---|---|---|---|---|
| BURROW v2 small default s0 | 6.2 | 45.2 | 69.3 | 79.6 | 85.6 | 38.5 | 28.7 |
| BURROW v2 small accurate s0 | 5.4 | 45.6 | 73.3 | 80.4 | 85.2 | 41.0 | 28.7 |
| P2Rank 2.5.1 | 4.2 | 50.4 | 71.9 | 74.8 | 80.0 | 30.1 | 27.0 |
| fpocket 4.2.3+PRANK 2.5.1 | 20.8 | 37.0 | 59.6 | 74.8 | 94.8 | 34.2 | 14.0 |

* **The O4 Δ varies by seed** (from −2.6 to +1.1) with CIs of about ±6, so the result is inconclusive. BURROW has higher any-pocket recall, max recall and P1K. The closest-pocket top-N is lower.
* **Holo counterparts and PocketMiner** (descriptive, test data, no tuning; results/descriptive/POCKETMINER_CRYPTOBENCH_HOLO.md):
  * **Apo→holo drop.** On 233 paired CryptoBench sites, top-N+2 drops by +10.7 [5.6, 15.9] for BURROW and +7.7 [2.7, 12.5] for P2Rank. BURROW's drop is somewhat larger, so it is, if anything, *more* sensitive to the apo state (the CIs overlap).
  * **Holo structures.** BURROW is at par on DCC12 (−0.4) and ahead on DCA4 (+6.4 [0.9, 12.1]).
  * **PocketMiner test (35 apo chains), residue ROC-AUC:**

    | method | ROC-AUC [95% CI] | AUPRC |
    |---|---|---|
    | BURROW v2 `small` | 0.792 [0.744, 0.836] | 0.714 |
    | PocketMiner (MD-trained cryptic-pocket predictor) | 0.789 [0.694, 0.872] | 0.712 |
    | P2Rank | 0.601 | |

    BURROW matches PocketMiner, a dedicated tool, at residue level. With n = 35 this is suggestive only.
* **Apo-dev history (CryptoBench train folds; results/dev_apo/APO_DEV.md, V2_CYCLE.md).**
  * v1 trailed P2Rank on cryptic DCC12: 62.1 vs 68.5. It was ahead on DCA4: 55.3 vs 50.6.
  * The deficit was traced to the closest-pocket/output-length effect (§4.2), not to apo-specific ranking. The v2 floor lifted apo-dev cryptic top-N+2 by +9.7 [8.0, 11.5].
  * Apo-specific training changes (H1–H4) did nothing (§5).

### 4.7 Ablations and controls

**Dev ablations** (seed 0, BioLiP2 dev; Δ vs frozen v1 of the same variant; results/ablations/ABLATIONS.md):

| ablation | ranker | train inputs | DCC12 top-N+2 Δ [95% CI] | DCA4 top-N+2 Δ | P1K Δ |
|---|---|---|---|---|---|
| A3 shuffled labels (negative control) | all | 8,184 | −35.6 [−40.5, −31.4] | −34.8 | −40.1 |
| A3 shuffled labels | small | 8,184 | −28.2 [−32.7, −23.7] | −30.6 | −33.4 |
| A2 CHEN11-only training (no ion labels) | all | 251 | −10.8 [−14.2, −7.6] | −15.6 | −9.2 |
| A2 CHEN11-only training | small | 251 | −3.2 [−5.9, −0.5] | −6.3 | −6.1 |
| **A1 fold-disjoint training** (TM ≥ 0.5 to test removed) | all | 4,839 | −0.3 [−2.0, 1.3] | +0.0 | −1.4 |
| A1 fold-disjoint training | small | 4,839 | −0.6 [−2.4, 1.3] | −1.2 | −2.1 |
| A4 − metal features | all | 8,184 | −2.5 [−4.4, −0.7] | −0.9 | −0.4 |
| A4 − atom-class densities | all | 8,184 | −1.7 [−3.5, −0.2] | −1.2 | −2.1 |
| A4 − ray buriedness | all | 8,184 | −0.8 [−2.4, 0.7] | +0.0 | +1.1 |
| A4 − first-hit chemistry | all | 8,184 | −0.2 [−1.9, 1.5] | −0.3 | +0.3 |
| A4 − backbone-only buriedness | all | 8,184 | −0.4 [−1.9, 1.1] | +0.9 | +0.7 |
| A4 − residue composition | all | 8,184 | −0.3 [−2.0, 1.4] | −0.6 | −0.3 |

* **Shuffled labels (negative control).** Accuracy collapses towards the surface-tiling level, as expected.
* **Fold-disjoint training.** Removing every training entry with TM ≥ 0.5 to any test chain (41 % of inputs) costs nothing measurable, so there is no evidence of fold memorisation.
* **CHEN11-only training (251 structures).** The ion-free `small` model is still competitive. Most of the `all` loss is the missing ion labels.
* **Feature groups.** No single group is essential (largest drop: metal features on `all`), so the feature set is redundant.
* **Reproducibility.** Re-training v1 reproduces the frozen models byte-for-byte.
* **Rank shuffling.** BURROW's own pockets with randomly shuffled ranks score 14.6 (dev review), the level of surface tiling, so the gain is in the learned ranking.
* **Geometric candidates alone.** Ranking them without learning (`--ranker geometry`) reaches 53.3 on dev vs P2Rank 54.1 (the DCC12 top-N+2 of the dev table).

**Test-set controls (v2):**

| benchmark | metric | oracle | protein centroid | random surface | surface tiling | BURROW v2 s0 |
|---|---|---|---|---|---|---|
| ligysis | recall_topn2 | 100.0 | 37.0 | 28.9 | 18.3 | 72.5 |
| cryptobench | recall_topn2 | 100.0 | 56.7 | 15.6 | 9.3 | 69.3 |
| pocketwatch | recall_topn2 | 100.0 | 42.8 | 12.3 | 6.9 | 76.6 |
| af_set | recall_topn2 | 100.0 | 21.6 | 17.9 | 10.8 | 64.5 |
| coach420_mlig | success_DCA4_topn | – | 14.8 | 4.2 | 2.4 | 71.0 |
| holo4k_mlig | success_DCA4_topn | – | 10.1 | 4.2 | 3.2 | 78.2 |
| dimer | recall_DCC12_topn2@interface | – | 34.2 | 17.7 | 17.7 | 84.0 |

**Fair-data control: P2Rank retrained on our training data ("P2Rank-ours"; dev only; results/baselines/P2RANK_OURS.md).**
* **Training subset.** P2Rank 2.5.1 with its default config was retrained on a random 25 % subset (1,059 liganded entries). Full and 50 % runs were OOM-killed at the ~79 GB container cap.
* **Result.** It is *worse* than stock P2Rank on BioLiP dev (`all`: −5.2; `small`: −3.5 top-N+2). BURROW v1 leads it by +16.5 (`all`) and +10.1 (`small`) top-N+2, and by +21.3 on DCA4.
* **Interpretation.** Our training set does not explain the gain; the gain is method-driven. Because of the data-volume handicap this is a lower bound.
* **Test-set rows** (descriptive; results/test/v2/DESCRIPTIVE.md). Δ are paired:

| benchmark / metric | P2Rank-ours | P2Rank 2.5.1 stock | Δ ours − stock [95% CI] | BURROW v2 s0 | Δ ours − BURROW v2 [95% CI] |
|---|---|---|---|---|---|
| LIGYSIS top-N+2 | 45.8 | 52.6 | −6.7 [−8.0, −5.3] | 72.5 | −26.6 [−29.1, −24.2] |
| LIGYSIS DCA4 top-N+2 | 28.1 | 29.8 | −1.7 [−2.4, −1.0] | 54.2 | −26.1 [−28.8, −23.6] |
| LIGYSIS_NI top-N+2 | 53.4 | 60.9 | −7.5 [−9.2, −5.9] | 66.4 | −13.0 [−15.0, −10.9] |
| COACH420 DCA4 top-n | 67.5 | 69.4 | −1.8 [−4.6, 0.7] | 71.0 | −3.4 [−7.3, 0.5] |
| HOLO4K DCA4 top-n | 78.7 | 76.6 | +2.1 [0.6, 3.6] | 78.2 | +0.5 [−1.9, 2.9] |
| CryptoBench top-N+2 | 65.6 | 71.9 | −6.3 [−10.3, −2.2] | 69.3 | −3.7 [−8.9, 1.5] |
| PocketWatch top-N+2 | 73.6 | 75.3 | −1.7 [−3.7, 0.3] | 76.6 | −3.1 [−5.6, −0.6] |
| AF set top-N+2 | 37.6 | 47.3 | −9.8 [−11.4, −8.1] | 64.5 | −27.0 [−29.5, −24.6] |
| Dimer interface top-N+2 | 84.4 | 87.7 | −3.3 [−6.8, 0.0] | 84.0 | +0.4 [−4.3, 5.0] |

  * **Vs stock P2Rank.** P2Rank-ours is significantly below stock P2Rank on LIGYSIS (both metrics), LIGYSIS_NI, CryptoBench and the AF set. It is within noise on COACH420, PocketWatch and dimer, and above stock on HOLO4K (+2.1).
  * **Vs BURROW v2.** It is far below on LIGYSIS (−26.6) and the AF set (−27.0), and below on LIGYSIS_NI and PocketWatch. It is not distinguishable on COACH420, HOLO4K, CryptoBench and the dimer interface.
  * **Interpretation.** The control is mixed but clear where BURROW's gains are large: our training data alone (at 25 % volume) does not reproduce them. On HOLO4K and the dimer interface, P2Rank with our data reaches BURROW's level.

**Test-set ablations (descriptive, run after v2 was fixed; results/test/v2/DESCRIPTIVE.md).** A1–A3 use v1 formation and are paired against v1 s0. "A1 + v2 floor" is paired against v2 s0. Single seed.

| benchmark / metric | v1 s0 | A1 fold-disjoint Δ [95% CI] | A2 CHEN11-only Δ | A3 shuffled labels Δ | v2 s0 | A1 + v2 floor Δ [95% CI] |
|---|---|---|---|---|---|---|
| LIGYSIS top-N+2 | 64.3 | +0.0 [−0.8, 0.8] | −12.7 | −28.4 | 72.5 | −0.7 [−1.5, 0.1] |
| LIGYSIS DCA4 top-N+2 | 54.4 | −0.2 [−0.8, 0.5] | −20.5 | −31.9 | 54.2 | −0.3 [−0.9, 0.4] |
| LIGYSIS_NI top-N+2 | 58.7 | −0.1 [−1.1, 0.9] | −1.6 | −22.1 | 66.4 | +0.0 [−1.1, 1.0] |
| COACH420 DCA4 top-n | 71.8 | −3.2 [−6.0, −0.3] | −1.1 | −43.5 | 71.0 | −3.4 [−6.5, −0.5] |
| HOLO4K DCA4 top-n | 78.4 | −0.7 [−1.5, 0.2] | −9.3 | −48.7 | 78.2 | −0.7 [−1.6, 0.2] |
| CryptoBench top-N+2 | 66.7 | −2.2 [−5.7, 0.7] | +0.0 | −37.0 | 69.3 | +1.1 [−2.4, 4.8] |
| PocketWatch top-N+2 | 73.1 | −0.3 [−1.8, 1.3] | −2.9 | −44.2 | 76.6 | −1.2 [−2.7, 0.1] |
| AF set top-N+2 | 59.2 | −0.7 [−1.5, 0.1] | −13.6 | −27.7 | 64.5 | +0.0 [−0.8, 0.7] |
| Dimer interface top-N+2 | 85.6 | +1.2 [−2.0, 4.6] | −0.8 | −15.6 | 84.0 | +0.0 [−2.7, 2.4] |

* **A1 (fold-disjoint training) is within noise on every benchmark except COACH420.** There the drop is −3.2 [−6.0, −0.3] with v1 formation and similar with the floor (379 ligands). On LIGYSIS it is −0.01. The test-set gains are therefore not explained by fold similarity to the training set, with a possible small COACH420 exception.
* **A2 (CHEN11-only).** Losses are large where ions count (LIGYSIS, AF set) and on HOLO4K, and small on the non-ion benchmarks.
* **A3 (shuffled labels, negative control).** It drops to about the surface-tiling or centroid level everywhere, as expected.

### 4.8 Runtime

**Final like-for-like timing** (docs/PERF.md "Final like-for-like timing"): one session, the same 200 LIGYSIS chains (median 1,803 atoms) for every tool, measured back to back. The node is shared with other users' jobs (load about 20 during the measurement).

| method | 1 core warm, median excl. / incl. parsing (ms) | 1 process on 200 chains, ms per structure (incl. start-up, I/O) | 24 CPU workers, 2,000 structures (structures/s) | 1 GPU / 3 GPUs, 8 workers each, 2,000 structures (structures/s) |
|---|---|---|---|---|
| BURROW `--preset fast` (optional) | 28.4 / 31.5 | 48 | 371.3 | 202.9 / 336.8 |
| BURROW default (pre-registered) | 96.0 / 99.2 | 142 | 149.6 | 129.4 / 236.6 |
| BURROW accurate | 203.0 / 206.4 | 271 | 79.5 | 107.7 / 195.9 |
| P2Rank 2.5.1 (batch, one JVM, 1 thread) | – (batch only) | 209 | – | – |
| fpocket 4.2.3 (1 process) | – | 605 | – | – |

* **Per process,** default is ≈ 1.5× faster than P2Rank and ≈ 4.3× faster than fpocket; `fast` is ≈ 4.4× and ≈ 12.6× faster. P2Rank's batch mode amortises a JVM start-up of several seconds over the 200 chains.
* **GPU, large batches** (T1 table, 10,000 structures, 3 GPUs vs 24 CPU workers): fast 646.3 vs 544.7/s, default 411.4 vs 171.0/s, accurate 338.1 vs 88.2/s. T1 changed the GPU feeding, parsing and model loading so that the GPU path now beats the CPU path for every preset, with byte-identical outputs and exactness re-verified. On 2,000 structures, start-up still dominates for `fast` (3 GPUs 336.8 vs 24 CPU 371.3/s).
* **Superseded measurements.** The docs/PERF.md sections below the final table, the earlier "final" session (09:33; default 157 ms per process, P2Rank 270 ms) and results/baselines/SPEED.md were taken in other sessions under heavier load and before T1. They are kept for history only; the final table and the T1 table supersede them.
* **Other settings:** proteome demo, AF mode, 3 GPUs × 8 workers: 10,996 structures/min. P2Rank `-c alphafold` with 24 threads on 500 AF models: 960/min.
* **Cold start.** The first call after installation compiles Numba code (37,210 ms). Later process starts take about 3 s.

**`--preset fast` on test (descriptive, seed 0, not pre-registered; results/test/v2/DESCRIPTIVE.md):**

| benchmark / metric | fast s0 | v2 default s0 | Δ fast − default [95% CI] |
|---|---|---|---|
| LIGYSIS top-N+2 | 72.5 | 72.5 | +0.0 [−1.0, 1.0] |
| LIGYSIS DCA4 top-N+2 | 53.4 | 54.2 | −0.8 [−1.7, 0.1] |
| LIGYSIS P1K | 97.0 | 96.1 | +0.9 [−0.7, 2.1] |
| LIGYSIS_NI top-N+2 | 66.8 | 66.4 | +0.5 [−0.8, 1.8] |
| COACH420 DCA4 top-n | 69.4 | 71.0 | −1.6 [−4.9, 1.4] |
| HOLO4K DCA4 top-n | 77.1 | 78.2 | −1.1 [−2.2, 0.1] |
| CryptoBench top-N+2 | 75.9 | 69.3 | +6.7 [2.4, 11.0] |
| PocketWatch top-N+2 | 75.8 | 76.6 | −0.8 [−2.5, 0.9] |
| AF set top-N+2 | 66.0 | 64.5 | +1.4 [0.5, 2.3] |
| AF set P1K | 60.1 | 58.9 | +1.2 [−1.6, 3.1] |
| Dimer interface top-N+2 | 85.6 | 84.0 | +1.6 [−1.5, 5.0] |

* **Accuracy.** `fast` is within noise of the default everywhere except CryptoBench (better) and the AF-set top-N+2 (slightly better). LIGYSIS top-N+2 is unchanged.
* **AF precision.** AF-set P1K is still −13.8 vs P2Rank-AF.
* **Default unchanged.** The pre-registered default stays the default. Switching it because of these test rows would be a test-driven choice. `fast` is offered as an option for throughput-bound screening.

---

## 5. What did not work (negative results, all documented)

| idea | evidence | result |
|---|---|---|
| **G1 candidate-recall gate as specified** (≥ 88 % at ≤ 40 geometric candidates) | results/dev/G1.md addendum | It passed on interim data (91.0 %), then **failed** on BioLiP dev (58.6 %). The fallback was worse (fpocket candidates 47.3 %; fpocket candidates + BURROW ranker lose about 16 on DCA4). The deviation was accepted (D7). The full pre-ranking pool is at 93.6 %. |
| AF geometric mechanisms vs the pLDDT < 70 filter | AF_DEV_RESULTS.md | No recall gain over the filter (train-OOF −0.7). The value is hallucination removal only. |
| Side-chain tolerance λ (AF mode) | AF_DEV_RESULTS.md | λ = 0.25 on all side chains: −10.9 DCC12 on AF dev. Restricting it to low pLDDT hurts the near-disorder sites. Not adopted. |
| PAE / inter-domain surrogate | AF_BENCHMARK.md §6, AF_DEV_RESULTS.md | PAE file endpoint returned 403. The structure-only surrogate (`pldom`) adds nothing. |
| Phase-3 ranker variants (relative features, pair context, LambdaRank, propensity; train cluster-CV) | results/dev/biolip/PHASE3.md | None beats V0 (criterion 70.44 vs LambdaRank 69.92). The seed ensemble was not evaluated. |
| fpocket candidates + BURROW ranker | PHASE2.md | top-N+2 at par but much worse localisation and P1K. Own candidates matter. |
| Global output floor on non-ion sites (error analysis, dev) | results/dev/biolip/NONION_ERRORS.md | v2 `small` reaches 71.2 vs fpocket+PRANK 66.0. Misses: 65 % removed by the floor, 22 % ranked > N+2, 9 % closest-pocket rule, 4 % no candidate. Candidates are not the bottleneck; the global τ is. |
| v2 apo hypotheses, apo-dev cryptic Δ vs v1 (gate +3) | V2_CYCLE.md | H1 AF-model inputs +1.9; H2 side-chain dropout +0.0; H1+H2 −1.9; H3 apo ranker features +0.3; H4 apo PDB chains +0.5. All failed. |
| v3 interface hypotheses (train-assembly OOF, gate +3 with CI > 0) | V3_CYCLE.md | min_keep × chains +1.3; interface features +0.6; both +1.9 [−0.6, 5.4]; assembly up-weighting +0.3. No FREEZE v3 (D15). |
| v3b per-protein / per-region output floors (train-CV selection, one dev confirmation; gate: non-ion top-N+2 ≥ +2 with CI > 0) | results/dev/biolip/V3b_CYCLE.md | Best rule (per region, 16 Å, ≥ 0.005): BioLiP-dev non-ion top-N+2 +1.2 [0.1, 2.4] (`small`) vs +2.0 required, so the gate was **not met**. All guards passed, including max recall +7 to +10. Shipped as the optional `--output-rule region`; no FREEZE v3 (D19). |
| AF-set precision | test v2 | BURROW P1K 58.9 < P2Rank-AF 73.9 < PUResNet 85.3. |
| NMS radius 14 Å (would raise dev top-N+2 to 72.6) | PHASE2.md, REVIEW.md | Rejected because it games the metric by spreading pockets. 10 Å was kept by one-to-one P1K. The later v2 floor was selected on train-CV under no-loss guards, not on dev top-N+2. |

---

## 6. Limitations and threats to validity

1. **Mechanism of the v2 gain.** C1 v1 → v2 (+8.2 points, s0) comes entirely from output length under the closest-pocket rule: C1-strict and P1K are unchanged, and any-pocket, max recall and one-to-one recall *fall*. The pre-registered claims do not depend on it, since v1 passes family 1 alone, but "72.5" should be quoted together with the list length (about 9 pockets per chain). The baselines were run with their default list lengths. No list-length policy was tuned for them, and fpocket+PRANK or P2Rank with a tuned floor might also gain under this rule. **C1-strict (DCA4), unchanged by the floor, is the robust evidence.**
2. **Timeline of v2 adoption.**
   * FREEZE v2 (22:09 UTC = 23:09 CET) was committed **after** v1 test prediction files were written (from 20:58 UTC) but before any v1 test score was computed (22:41 UTC).
   * The v2 mechanism and τ were derived on dev and train-CV only, and the decision (D13) is time-stamped before the v1 results. The verifier nevertheless cannot rule out that prediction files were looked at (VERIFY.md caveat 2; 70 minutes).
   * The v3 cycle was openly test-informed (motivated by O6) and changed nothing.
3. **Ion share.** About 38 % of LIGYSIS sites are ion sites (2,580 / 6,721), and that stratum carries a large share of the C1 margin. P2Rank-style tools are not trained for ions. On "other" small molecules the v2 margin is small (CI lower bound 0.1).
4. **AF set is holo-biased** (median local RMSD 0.38 Å; every protein has PDB structures; AF2 was trained on the PDB). O5 is optimistic for apo or novel proteins. Low-pLDDT strata are tiny (n = 13 and 76).
5. **CryptoBench and dimer endpoints are inconclusive** and under-powered (203 and 158 cluster bootstrap units; the dimer set has 400 scored assemblies; CI half-widths about 5–6 points). BURROW is more sensitive to apo vs holo than P2Rank (§4.6). The dimer benchmark controls cross-complex redundancy only at one complex per UniProt (docs/DIMER_BENCHMARK.md §7).
6. **Single-seed ablations** (seed 0 only). Seed-to-seed SD on dev is about 0.7 points (REVIEW.md), so Δs below about 1.5 are not interpretable individually.
7. **Speed claims are modest and noisy.**
   * Per process, on the same 200 chains including start-up and I/O, BURROW default is only ≈ 1.5× faster than P2Rank (142 vs 209 ms). The ≈ 4.4× of `--preset fast` uses a preset that was not pre-registered.
   * GPU gains need large batches.
   * The node was shared. Repeated sessions differed by up to about 1.5× (P2Rank 270 vs 209 ms), so ratios should be taken as ±30 %. Repeat timing on an exclusive node.
8. **P2Rank-ours** used 25 % of the training data (memory cap) and is a lower bound for P2Rank with our data.
9. **Deviations from PREREG and DESIGN.**
   * Amendments A1–A3 were all made before any BURROW test prediction (docs/PREREG.md).
   * G1 failed as specified, and its fallback was not taken (D7).
   * The NMS radius was fixed on CHEN11 cross-validation before BioLiP dev existed (REVIEW.md).
   * Reviews were capped at 2 rounds.
   * The speed target of ≤ 70 ms/core was missed on larger chains.
   * The `accurate` preset reuses τ without its own dev validation.
   * The PREREG sha256 changed with the amendments: frozen `582b8b56…`, amended `59c7e41e…`. Both are recorded.
10. **Benchmark-protocol dependence.** LIGYSIS sites are pooled across entries and assemblies while predictions use one chain. Interface sites are therefore judged without the partner chain, and DCC12 is lenient. C1-strict (DCA4) is the guard; BURROW's median successful DCC on dev is 3.3 Å vs 4.7 Å for P2Rank (REVIEW.md).
11. **Residue-level output.** Residue MCC on LIGYSIS beats fpocket+PRANK. On CryptoBench and PocketWatch it is at par with P2Rank, and on LIGYSIS_NI slightly below it. Pockets are small volume-element clusters, so residue lists are short.
12. **Scoring provenance.** The committed summaries were (re)generated with dirty working trees: v1 `summary.json` at scoring commit `20421b6`, v2 at `9521756`. Scoring-code sha256s are recorded in each summary.json. All family-1 and family-2 headline values are **identical** across `8b59de7`, `20421b6`, `2b367a9`, `9521756` and `HEAD` (results/test/v2/POSTHOC.md §4). The independent recomputation used no project code.

---

## 7. Follow-ups and remaining ideas

1. **Context-dependent output floor (top follow-up).** On dev, 65 % of v2's non-ion misses (151 of 232) are pockets that *were found* but dropped by the global floor (results/dev/biolip/NONION_ERRORS.md). The per-region variant (v3b) recovers coverage but only +1.2 closest-pocket top-N+2 on dev (§5). The remaining lever is the *ranking* of shallow, low-scoring sites (item 5), not the floor itself.
2. **Interfaces.** Build a PISA-based, cross-entry interface benchmark with ≥ 1,000 interface sites. Train with assembly inputs as first-class rows (the hooks `FormationConfig.min_keep` and `meta.if_feats` exist). Test AF-Multimer/AF3 complexes.
3. **Apo and cryptic sites.**
   * Cheap flexibility: normal-mode or rotamer-ensemble buriedness.
   * Training on apo–holo pairs (AHoJ/PLINDER).
   * A cryptic-specific ranker evaluated on the CryptoBench test set as descriptive only.
4. **AF mode.** Consider making `--af-ranker` the AFDB default after a pre-registered check, given its AF-set P1K result (§4.4). Retrieve PAE through another route (bulk download) for the inter-domain mechanism. Stratify the AF set by template richness and holo-likeness, and add the UniProt-unit bootstrap sensitivity analysis.
5. **Shallow, flexible and lipid sites.**
   * Dev non-ion hit rate falls from 95.4 % (buriedness ≥ 0.8) to 22.2 % (< 0.5), and lipid/detergent sites reach 48.8 %. Every method fails on these sites; P2Rank reaches 2.0 % on the least buried.
   * Remedies: exposure-aware ranker descriptors or a separate calibration for shallow candidates; label hygiene for additives and detergents in `small`; a two-head ranker (order within a protein vs score across proteins); a candidate pass that tolerates side chains in low-WCN regions.
6. **Speed.** Cut the default point-feature stage further, with fewer neighbour sums and fused ray kernels. Repeat the timings on an exclusive node.
7. **Seeds and ablations.** Repeat the ablations and the P2Rank-ours control at 3 seeds and full data (needs more than 79 GB RAM).
8. **Proteome atlas.** Publish the human AF-mode pocket atlas with calibrated scores, and compare it to HOTPocket and AF2BIND.

---

## 8. Reproducibility

* **Commits.**
  * FREEZE v1 `5e13267` (models in results/dev/freeze/models; test v1 predictions were generated from an isolated worktree at this commit, D10).
  * FREEZE v2 `0d925b2` (results/dev/FREEZE_v2.md; models in results/dev/freeze_v2/models).
  * CLI defaults to v2 from `348f26f`.
  * Test v1 first scored at `8b59de7`, test v2 at `2b367a9`, independent verification at `65cea0c`.
  * Current summaries: v1 regenerated at `20421b6`, v2 at `9521756` (descriptive rows added). Headline values are identical across these commits and HEAD (POSTHOC.md §4).
* **Model sha256** (v2, default preset; all 12 models are listed in results/test/v2/summary.json → provenance):
  * `all` s0/s1/s2: `0fa4da97…`, `317570d4…`, `3e7f1ac5…`
  * `small` s0/s1/s2: `c0b88419…`, `da798f48…`, `b770e722…`
  * The verifier matched all 96 test `run.json` files.
* **Seeds.** `SEEDS = (20261026, 1, 2, …)` and `BOOTSTRAP_SEED = 20261026` in src/pocketdetect/seeds.py. LightGBM `seed`, `bagging_seed` and `feature_fraction_seed` are all set (DESIGN §9).
* **Data.** DATA.md lists source, version, checksum and license per dataset. Restricted or large data live under `data/raw`, `data/processed` (git-ignored); manifests and checksums are committed. scPDB has no license and was not used for training.
* **Test gating.** `scripts/run_test_eval.py` (clean tree, model checksum) appends to results/TEST_LEDGER.md. `scripts/run_prereg_analysis.py` writes results/test/v{1,2}/{SUMMARY.md,summary.json}.
* **Re-running.** `scripts/reproduce_all.sh`:
  * `smoke` is a 2-minute end-to-end check: model integrity, 5 dev inputs, reference == fast, scoring.
  * Individual steps are data → benchmarks → train/dev build → audit → baselines → train/freeze → test predictions → pre-registered analysis.
  * `all` runs everything (days of CPU).
* **Usage** (README.md): `burrow predict <files|dirs|@list> --out OUT [--ranker all|small] [--preset default|accurate] [--af-mode [--af-ranker PATH]] [--min-score none|τ] [--device cpu|cuda:N[,M] --workers N]`.
* **Number check.** `.venv/bin/python scripts/check_report_numbers.py` resolves every tagged number in this file against the files committed at `HEAD` (`--worktree` to use uncommitted files) and lists the remaining placeholders for pending rows.
* **How to push.** The PI creates branch `burrow-final` at the final commit, after this revision. No git remote is configured, so add one and **push branch `burrow-final`**: `git remote add origin <url> && git push -u origin burrow-final`.

---

## Appendix

* **Decision log.** RESEARCH_TREE.md "Decisions log" D0–D17. Examples: D6 conservative audit fix; D7 G1 deviation; D8 AF-mode default; D12/D13 output floor adopted before v1 test results; D14/D15 v3 negative; D16 no further test version; D17 a ≈ 4.5 h API pause (02:40–07:10) that cost wall-clock only.
* **Process lessons** (LESSONS.md, final, 15 rules; full evidence in the file):
  * Inspect real resource caps first (79 GB, not 128 GB).
  * Only the PI commits.
  * Commit per result.
  * Keep one source of truth for constants.
  * Run long jobs detached with logs; resume rather than relaunch.
  * Kill only stored PIDs.
  * Reproduce published numbers first.
  * Require an independent re-implementation for leakage checks.
  * Pre-register gates, endpoints *and output-list-length policy*.
  * Every mechanism needs a control; never tune metric leniency.
  * Decompose headline gains by composition (ion share).
  * Select on train-CV and disclose test-informed steering.
  * Time-box exploratory branches.
  * Run test predictions from an isolated worktree and test exactness at boundary values.
