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

## R1c-A1 parallel-contract tasks (mechanics only, science frozen)

- [x] A1-1 `--workers` hard ceiling (`w <= requested`; 8/12/14 never 18).
- [x] A1-2 measured pool sizing + main/each/aggregate RSS record (no hardcode).
- [x] A1-3 atomic dispatch reservation (lock-held `call_idx` + call/wall gate).
- [x] A1-4 warmup as `setup_decoder_calls`, `setup + scientific <= 2500`.
- [x] A1-5 per-phase incremental flush + `D6_GRAPH_CHUNK_WALL_BLOCKED` on
  `wall >= 5400s` (blocking terminal, not warning-only).
- [x] A1-6 fake-worker tests (ceiling/budget/reorder/aggregate/flush/block).
- [x] A1-7 delete write-only `pair_to_mask` (equivalence via T2 replay).

## R1c-A2 execution-safety closeout (mechanics only, science frozen; old A2 void)

- [x] A2-01 three history roots verbatim `VOID_RETAINED_ZERO_REUSE`
  (923a25897087495ab4605870e561f3cc / e8ee45a4669c4738bf7e96d926ba7e5c /
  f15cfa29baa2458e804c80a9f1045140); name-only, no read/delete/move/use.
- [x] A2-02 RSS fail-closed pilot sizing + per-call/barrier aggregate+peaks +
  strict persistence (unknown→`D6_RSS_UNKNOWN_BLOCKED`,
  1+main over→`D6_RSS_LIMIT_BLOCKED`; unknown never 0).
- [x] A2-03 12h `deadline=t0+12h`, atomic remaining, `poll=min(120s,remaining)`,
  deadline `wall_timeout=true` no-respawn + `D6_WALL_BUDGET_BLOCKED`.
- [x] A2-04 records `worker_pid/respawn_pid/timeout/wall_timeout/error`,
  `watchdog_ok` separation, respawn rules.
- [x] A2-05 checkpoint-rewrite semantics + ordered flush/fsync fail-closed +
  unified finally + `chunk>=5400s` zero new dispatch.
- [x] A2-06 `workers=1` scaling-confirm indent (`cc[point]` in point loop).
- [x] A2-07 verify 15 independent rejections.
- [x] A2-08 fake/tmp-only tests + `py_compile` + D6 focused + seven-file suite
  (no perf-v38 800s), fresh `workspace/<uuid>` basetemp.
- [x] A2-09 land prereg/OpenSpec + implementation/tests, check A1/A2, STOP for
  independent review (no self-written review).

## R1c-A3 post-run verifier and terminal rework (verifier only, zero decoder)

- [x] A3-01 freeze post-run contract: `D6_GRAPH_MOTHER_PREREG_R1C_A3.md` +
  `R1C_parallel_revision.md` A3 delta + `tasks.md` A3/A4 tasks; commit
  separately (commit 1). Eight rules frozen; no code before commit 1.
- [x] A3-02 forensic reconstruction (fresh non-formal root, read-only, no
  decoder): 184-row table (old/new keys, duplicates, counts, partitions,
  recomputation, stored-vs-recomputed, degree-source attribution or
  `NOT_VERIFIABLE`) → `D6_GRAPH_MOTHER_FORENSIC_R1C_A3.md`.
- [x] A3-03 minimal verifier/classifier correction + 10 A3 fake tests
  (identity/dup/isolation/stages/empty-confirm/crash-precedence/placeholders/
  disagreement/a2-fixture/readonly); mother module + execution path untouched.
- [x] A3-04 `py_compile` + focused D6 + seven-file non-perf regression
  (perf-v38 skipped, recorded); independent code review (own file only);
  single rework max, else STOP. Commits: impl+tests+forensic, then review. No
  push.
- [x] A3-05 single read-only `--verify` on the immutable A2 root (zero
  decoder calls); capture output+exit. FAIL → STOP, no patch, no rerun.
- [x] A3-06 independent Pre-RESULT re-review
  (`D6_GRAPH_MOTHER_PRE_RESULT_REVIEW_R1C_A3.md`):
  `…_PASS_BLOCKED_RUN` (expected) / `…_PASS_SCIENTIFIC_RESULT` / `…_FAIL`.
- [x] A3-07 closeout: FAIL → stop, evidence uncommitted; PASS_* →
  append-only operator-return correction + `D6_GRAPH_MOTHER_RESULT_R1C_A3.md`
  + one scoped evidence commit (`-f` six files + docs); auth false, G2
  absent, no accepted mark, no push.

## R1c-A4 structure/scaling performance rework (after A3 closeout, zero decoder)

- [x] A4-01 structure-only profile first; frozen baseline table (no decoder).
- [x] A4-02 three equivalent optimizations (scaling-arm pruning; ≤2
  constructions per `(n,arm,layer)`; no repeated audits).
- [x] A4-03 exact-equivalence gates (eight arms × two layers × n64; scaling
  arms × n128/n256); reference path kept until gates pass.
- [x] A4-04 fresh structure-only benchmark (≤3h): scaling wall ≥3x, n64
  equal ≤10% regress, RSS <2GiB, else `PERF_TARGET_NOT_MET`.
- [x] A4-05 deliverables (`…_PERFORMANCE_R1C_A4.md` + independent review),
  separate scoped commits; final `READY_FOR_FUTURE_D6_PRE_EXECUTE_REVIEW` or
  `PERF_TARGET_NOT_MET`; no new run authorized.

## R1c-A5 validity closure, admissible repair, R1d readiness (Track A, zero decoder)

- [x] A5-00 freeze contracts: `D6_GRAPH_MOTHER_PREREG_R1C_A5.md` +
  `D6_GRAPH_MOTHER_PREREG_R1C_A6.md` + this OpenSpec delta; commit separately
  (commit 1). No code before commit 1.
- [x] A5-01 independent validity matrix (own implementation; T2 n128/n256
  structure-only): CSV + human table in `D6_GRAPH_MOTHER_VALIDITY_R1C_A5.md`;
  frozen `eligible` + A2 five-arm selection reproduced exactly.
- [x] A5-02 per-family root-cause proofs + decoder precondition inventory
  (T3/T4 window gap; M N2/two-zone/forest force; T2 n64 rank; B0/B1 bounds as
  controls, unmodified).
- [x] A5-03 land I1 (audit_extra row_degree_min/rows_below_degree_2; eligible
  AND; build/dispatch fail-closed; verify INFO vs PASS/FAIL) + fake-only
  tests; production `build_support` unchanged; historical root unchanged.
- [x] A5-04 sandbox repair study (≤3 preregistered rules/family; R1–R5 +
  frozen order; byte-identical production) or
  `STRUCTURALLY_INFEASIBLE_AS_FROZEN` + ≤3 menu (`REQUIRES_MAIN_THREAD_RULING`,
  not landed) → `D6_GRAPH_MOTHER_REPAIR_STUDY_R1C_A5.md` + CSV.
- [x] A5-06 land crash-precedence terminal + fake tests (canary/scaling/
  confirmation); no historical change.
- [x] A5-10 structure-cost projection vs chunk 5400s / 12h wall; breach routed
  to Track B or width-inadmissible.
- [x] A5-08 R1d readiness package (`NOT_AUTHORIZED`) + `cycle_state.yaml`
  `next_gate` only (all auth false, evidence_root/terminal null; no R1d root).

## R1c-A6 exact-equivalent T2 acceleration + slow-task inventory (Track B, zero decoder; starts after Track A gate commit)

- [x] A6-01 profile first, freeze baseline table (fresh roots, workers 18+1,
  T2 candidate/affected/GC/RSS + A4-shape regression).
- [x] A6-02/A6-03 staged-filter + vectorize + incremental maintenance (key
  frozen); seven equivalence gates incl. sandbox-T2 re-run; perf targets
  (n64≤5s / n128≤90s / n256≤600s / all-8≤8s / non-T2≤10% / fb-only 2x /
  RSS<2GiB / zero decoder) else `PERF_TARGET_NOT_MET` with profile, reference
  intact.
- [x] A6-04 read-only slow-task menu with measured numbers (v38, orchestration,
  D5/D6 helpers, V30R, others); no implementation.
