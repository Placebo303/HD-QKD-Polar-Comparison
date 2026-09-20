# Tasks — Astra G1–G8 Deep-Review Prep (docs-only checklist)

- [ ] **T1 Assemble 4-file manifest** — confirm presence of the §D2.5 four
  files (packet, READINESS_R1, v72p2 design.md, D18 EXPLORATION_LOG.md).
  Missing/conflicting file → STOP, report which.
- [ ] **T2 Manual Astra first-chat** — copy-paste the 4 files into a fresh chat
  with the `EVIDENCE_READ…STOP` contract; ask Q1–Q3 only. No execution, no
  repo access granted, no authorization language.
- [ ] **T3 Paste return verbatim** — record Astra's return unmodified into the
  cycle docs with OBSERVED/DERIVED/PROPOSED/UNKNOWN labels intact.
- [ ] **T4 Independent A1–A7 check** — a reviewer threads the return against
  packet §6. FAIL blocks any amendment; advisory-only, no packet conversion.
- [ ] **T5 Amendment gate** — only on PASS plus explicit user authorization:
  open a new `v72p2d19` amendment change with a fresh packet (new seed set,
  disjointness proof, re-profile, re-review). Never edit the frozen
  `v72p2d19-*` change or rewrite the old STOP.

## Stop rules (STOP prep immediately on any)

- A new frozen seed, admission rule, statistic, or budget is proposed before
  Astra's return.
- Constructor work, T=72 batches, real-data access, or decoder/DE execution is
  attempted or requested.
- STOP immutability of D19 is challenged (rewriting 4408 history).
- SKR/FER/qualification/publication/route-closure language appears.
- Astra requests beyond read-only reasoning (edits, runs, data, authorization).
- Any request to execute or edit forbidden paths
  (`src/`, `comparison_bench/src/`, `tools/`, `experiments/`, `results/`,
  `comparison_bench/outputs_comparison/`, `workspace/`, `.workbuddy/tasks/D19_*`,
  `openspec/changes/v72p2d19-*`).

On STOP: state the failing condition and the single decision needed from the
main thread. "Still incomplete" is not a completion report.
