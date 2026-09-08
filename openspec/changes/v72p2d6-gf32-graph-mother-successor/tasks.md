# Tasks — V72P2D6 GF32 graph/mother successor

- [x] T1 Baseline gate D6-B01: branch `formal-ir-v72p1-addendum-clean`, HEAD
  `821388d6`, appendix single-file, D5 stopped/`DECOMPOSITION_NO_N64_RECOVERY`/
  `D5_GRAPH_MOTHER_SUCCESSOR_PROPOSAL`, nine auth keys false + promotion false,
  G2 absent, protected-root metadata snapshot (no content reads), numstat 0/0,
  exact allowlist.
- [x] T2 Phase A: this OpenSpec (proposal/design/tasks/specs) +
  `cycle_state.yaml` + `D6_GRAPH_MOTHER_PREREG_R1.md` + baseline record; commit
  1 only those paths. No implementation or decoder calls before commit 1.
- [x] T3 Implement `v72p2d6_gf32_graph_mother.py`: 8 arms, common
  coefficients, girth + M-cycle-rank + replay diagnostics, structural
  selection, blind finalist/fallback freeze, scalar evidence writers,
  formal-root no-write guards, call/wall/RSS accounting, terminal truth
  tables. Reuse D5 by import; no D5 edits. (+ structural_rank_list /
  select_advancement gap-fill; verified 2026-09-08.)
- [x] T4 Implement `comparison_bench/tests/test_v72p2d6_gf32_graph_mother.py`
  covering the packet §7 ten items (replay + inventory; hard gates on small
  and n=64 fixtures; coefficient identity; M forest-cycle detection incl.
  injected failing cycle; prefix nesting + rank; explicit injection;
  exact/syndrome/oracle separation; formal-root guards; budget/accounting +
  terminal truth tables). Explicit fakes + task-owned basetemps only.
  (+ rank/advancement truth-table test; 10/10 pass.)
- [x] T5 Implement `scripts/v72p2d6_graph_mother_development.py`: explicit
  `--model-f-root` + `--out-root` (fresh UUID, no formal default), watchdog
  worker (120 s/call, pid log), single-sample-per-`(n, seed)` reuse, six
  evidence files + scalar provenance. (+ full §8 pipeline: blind freeze,
  canary, confirmation/conditional scaling, --verify recomputation.)
- [x] T6 Run focused tests, then the frozen eight-file suite with a fresh
  UUID basetemp (packet §10 literal command). Repair only before decoder
  calls; after calls start, any production-code failure is STOP.
  (Focused 10/10; seven-file 291/291; v38 38/38 with src path fix;
  literal-command v38 collection error is pre-existing path-only.)
- [x] T7 Independent code review (`reviewer-go`, read-only): one-axis
  contract, arm formulas, gates, isolation, accounting, tests →
  `D6_GRAPH_MOTHER_IMPLEMENTATION_REVIEW_R1.md` (PASS required).
  (PASS 2026-09-08, fresh post-gap-fill read-only pass; no reviewer-go
  spawn tool in environment — function performed without modification.)
- [x] T8 Independent Pre-EXECUTE review (read-only): scope, frozen
  arms/seeds/rows, output-root absence, protected-root metadata, tests,
  forwarded-prompt authorization, watchdog →
  `D6_GRAPH_MOTHER_PRE_EXECUTE_REVIEW_R1.md` (PASS required before any call).
  Max two implement/review cycles, then BLOCKER. (PASS 2026-09-08.)
- [ ] T9 Structure + blind selection: build all arms (n=64; n=128/n=256
  structures on demand), write `structure_records.csv` +
  `selected_arms.json` (decoder set ≤ 6 + two prereg fallbacks). No decoder
  calls before this freeze.
- [ ] T10 n=64 canary per §8.2; advancement decision per frozen ordering.
- [ ] T11 Confirmation (§8.3) and/or conditional scaling (§8.4) per frozen
  rules; terminal classification (§8.3–§8.5).
- [ ] T12 Independent scalar recomputation from saved scalars (coverage,
  counts, separation, extrema, advancement, classification).
- [ ] T13 Independent Pre-RESULT review (read-only; only its review file may
  be created) → `D6_GRAPH_MOTHER_PRE_RESULT_REVIEW_R1.md` (PASS required
  before solidification).
- [ ] T14 Delivery: `D6_GRAPH_MOTHER_RESULT_R1.md`, D6 state update, D5 state
  linkage + `next_gate` only, append-only decision-log/memory; commit 4.
  Route strong → `D6_GRAPH_MOTHER_CANDIDATE_ACCEPTANCE_REVIEW`, partial →
  `D6_GRAPH_MOTHER_PARTIAL_SIGNAL_ROUTE_REVIEW`, square-only/no-recovery →
  `D6_DECODER_DYNAMICS_SUCCESSOR_PROPOSAL`, blocked →
  `D6_GRAPH_MOTHER_REWORK_REQUIRED`. No decoder-dynamics work.
