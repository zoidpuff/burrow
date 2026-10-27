# Manuscript

The manuscript describing BURROW and its benchmarks, formatted for PLOS Computational Biology. It was
written by AI agents (see the note at the top of the [repository README](../README.md) and S2 Text).
Author list, affiliations, funding and competing-interests statements are still placeholders.

| file | contents |
|---|---|
| `main.pdf` (`main.tex`, `main.md`) | main text |
| `S1_Text.*` | methods that were tried and did not work |
| `S2_Text.*` | the agent and sub-agent setup, with the human prompts verbatim |
| `S3_Text.*` | extended methods |
| `S1_Table.*` | agent roster |
| `figures/` | figures (PDF, PNG), `figure_data.csv` (the numbers plotted), `make_figures.py`, `CAPTIONS.md`; fonts: Liberation Sans (SIL OFL, license included) |
| `references.bib`, `plos2025.bst` | bibliography and the PLOS bibliography style |
| `build/` | Markdown sources (`*.src.md`) and `build.py`, which writes the `.md` and `.tex` files |
| `REVIEW.md`, `CLARITY_PASS.md`, `REFERENCES_CHECK.md`, `OPEN_ISSUES.md` | the agents' manuscript review, the clarity edit log, the reference verification and the issues that are left open |
| `AGENT_SETUP.md`, `FOLLOWUP_PROMPTS.md` | source notes for the Methods and S2 Text (copies are also at the repository root and in `prompts/`) |

Rebuild: edit `build/*.src.md`, run `python3 build/build.py`, then compile each `.tex` file with a XeTeX
engine, for example `tectonic -X compile main.tex`. Paths that the manuscript cites (for example
`results/...`, `docs/...`, `scripts/run_test_eval.py`) are relative to the repository root. Root-level
files of the private research repository (`REPORT.md`, `RESEARCH_TREE.md`, `LESSONS.md`, `DESIGN.md`,
`LITERATURE.md`) are in `docs/` and `docs/research_record/` here. `scripts/run_test_eval.py` and
`scripts/check_report_numbers.py` are included as records; they assume the layout of the research
repository.
