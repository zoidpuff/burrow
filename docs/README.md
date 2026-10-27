# Documentation

| file | contents |
|---|---|
| [METHOD.md](METHOD.md) | method specification (candidates, features, point scorer, pocket formation, ranker, output rules) |
| [PREREG.md](PREREG.md) | pre-registered claims, endpoints, comparators, margins (frozen before test predictions; amendments A1–A3) |
| [EVALUATION.md](EVALUATION.md) | evaluation protocol and metrics, reproduction gates |
| [TRAINSET.md](TRAINSET.md) | construction of the leakage-controlled BioLiP2 train/dev set |
| [AF_MODE.md](AF_MODE.md), [AF_BENCHMARK.md](AF_BENCHMARK.md) | AlphaFold mode and the AF benchmark built for this project |
| [DIMER_BENCHMARK.md](DIMER_BENCHMARK.md) | dimer/multimer benchmark built for this project |
| [PERF.md](PERF.md), [GEOMETRY_BENCH.md](GEOMETRY_BENCH.md) | runtime measurements and CPU/GPU geometry benchmarks |
| [FOR_FURTHER_DEVELOPMENT.md](FOR_FURTHER_DEVELOPMENT.md) | building on BURROW: code map, pocket representations (`pocketdetect.burrow.export`), learnings |
| [REPORT.md](REPORT.md) | the agents' final report (results, negative results, limitations, follow-ups) |
| [research_record/](research_record/) | RESEARCH_TREE.md (research tree + decision log D0–D20), LITERATURE.md, DESIGN.md (design v3 after two review rounds), LESSONS.md (process lessons) |

These documents were written by the agents during the project and are reproduced as they were,
except that local file-system paths and host names were removed. They refer to files of the original
research repository (e.g. `results/dev/...`, `baselines/...`, `reviews/...`); files not shipped here
(raw logs, caches, intermediate predictions, reviews) are part of that record only. Summaries that
the report relies on are in `results/`.
