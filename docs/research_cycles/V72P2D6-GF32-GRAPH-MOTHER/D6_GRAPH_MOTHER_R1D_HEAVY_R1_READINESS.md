# D6 R1d heavy R1 readiness and frozen exploratory batch design

Status: `D6_R1D_EXPLORE_READY_AWAITING_EXPLICIT_AUTHORIZATION` (freeze only; this
document grants no execution authorization and creates no root).
Track: `EXPLORE_HEAVY` (repository-wide two-tier workflow accepted:
`TWO_TIER_WORKFLOW_ACCEPTED_REPOSITORY_WIDE` /
`TWO_TIER_WORKFLOW_ACCEPTED`, `docs/research_cycles/WORKFLOW-TWO-TIER-R1/cycle_state.yaml`).
Authority: `.workbuddy/tasks/D6_MAINLINE_GRAPH_REDIRECT_HEAVY_R1_TASK_PACKET.md`
(H01–H35 performed in this batch opening; H41–H46 complete).
Branch: `formal-ir-v72p1-addendum-clean` (not switched; no commit, no push).

This batch resumes the accepted D6 R1d Option C eligible-only route. It changes
only the executed *route/reference* state; the frozen R1d science is unchanged
(see the accepted `D6_GRAPH_MOTHER_R1D_EXECUTION_PACKET_R1.md` §2–§5).

## 1. Predecessor route close (accepted X1–X4)

Raw-artifact re-verification (H01; read-only, nothing rerun):

| item | verified value | raw artifact + field |
|---|---|---|
| X1 | `CHECK_UPDATED`, `accepted_check_updated=true`, 1 decoder call, `writes=0`, historical identity | `/tmp/opencode/x1_r1_rerun_20260913/stdout.txt` (`provenance`, `accepted_check_updated`; md5 `b978bbd94c065b9b9c861bd46139d3e1`) |
| X2 | forward joint exact 2/16, 2/16, 1/16; reverse joint 0/16 (all 3 graph pairs, n=64, f=1.2) | `workspace/d7_r1_multigraph_20260913_r1/across_graph_summary.json` `per_graph_primary[].forward_both_count` / `reverse_both_count`; `graph_summary.csv` |
| X3 | 156 failed records; row-layered 360 rescued 1; flooding 90 rescued 0; baseline replay matched 156/156 | `workspace/d7_r1_reference_ladder_20260913_r1/paired_summary.csv` (`baseline_exact=False` → `arm_360_exact=True` count 1, `flooding_exact=True` count 0); `manifest.json` `selected_records=156` |
| X4 | 1320/1320 calls; 200 blocks per f∈{1.0,1.1,1.2}; L1/L2 exact=0; L1/L2 syndrome-valid=0; provenance/transfer 200/200; `G2_CURRENT_CONFIGURATION_FAILED`; wall 2141.9420988290076 s | `workspace/v72p2d5_g2/20260906_r1/results.json` + `execution_summary.json` (`wall_seconds`, `per_f[]`, `grade`) + `table.csv` |

Runtime-figure provenance: `2141.9420988290076 s` is the runner-measured stored
wall in `workspace/v72p2d5_g2/20260906_r1/execution_summary.json` `wall_seconds`
(repeated in `results.json` `wall_seconds` and `report.md`); the operator-owned
outer wall was 2143.83 s; `runtime_status: G2_RUNTIME_UNVERIFIED` remains the
inherited label (the X4 Pre-RESULT review recorded the measured stored wall as
authoritative). No bullet required a STOP.

Route-close record (durable entry added to `docs/decision-log.md`, one entry):

- X1–X4 accepted for route reconciliation; D5 G2 terminal
  `G2_CURRENT_CONFIGURATION_FAILED` (superseding the earlier decomposition
  terminal `DECOMPOSITION_NO_N64_RECOVERY`, retained as history).
- D5 current rate-mother configuration closed at the frozen rate mother.
- D7-H remains `NOT_AUTHORIZED / NOT_RECOMMENDED`; no D7 file was edited; D7
  historical artifacts are byte-identical.
- Next orthogonal scientific variable: graph/code construction at unchanged
  Model-F, rows, coefficients contract, decoder, schedule and estimator.

## 2. Frozen exploratory batch design

Arm set: exactly `{B0_D5_DV3_NATIVE, B1_D5_DV3_COMMON_LABELS, T1_PEG_DV3}`
(`R1D_ARMS`); B0/B1 are controls that cannot advance; T1 is the sole new arm.
T2/T3/T4/M1/M2 are structurally ineligible/outside Option C and are refused by
`assert_r1d_arm` pre-dispatch.

Frozen transition table (verbatim source: accepted
`D6_GRAPH_MOTHER_R1D_EXECUTION_PACKET_R1.md` §2; no threshold invented here):

> - Canary (mandatory): `{B0,B1,T1}` × n64 × 4 canary seeds × {f1.2 (59,52),
>   square (64,64)} × {L1 + APP-L2 + oracle-L2 diagnostic} = 72 invocations.
> - Confirmation (iff T1 advances, f1.2 APP exact ≥1/4): T1 × n64 × 16 seeds ×
>   {f1.0, f1.2, square} = 144 invocations; strong ≥12/16, partial 1..11/16,
>   both requiring f1.0 ≤ f1.2 ≤ square, zero crash/nonfinite, zero APP
>   exact/syndrome disagreement, known RSS <2 GiB.
> - Scaling (iff no new arm reaches 1/4 at n64 f1.2): T1 ONLY × 4 scaling seeds
>   × {f1.2, square} at n128 (24), then n256 (24) if silent; stop at first
>   signaling width; ≤1-arm confirmation by the same rules (144 each).
> - Worst case 552 scientific + small setup ≤ 2500 total. Every dispatched
>   `(arm,n,layer,prefix)` is asserted in `R1D_VALID_SUBSET` with live I1
>   recheck before any decoder binding; anything else is a hard failure.

Compact literal restatement (same values; seeds/rows are frozen constants):

| stage | entry condition | arms | seeds | points (n, L1 rows, L2 rows) | invocations | advance / stop rule |
|---|---|---|---|---|---|---|
| canary | always (mandatory) | B0, B1, T1 | 4 × `2026091000..2026091003` | n64 f1.2 (59,52); n64 square (64,64) | 72 | T1 advances iff n64 f1.2 APP exact ≥ 1/4 (frozen `select_advancement`) |
| confirmation | T1 advances | T1 | 16 × `2026091010..2026091025` | n64 f1.0 (49,43), f1.2 (59,52), square (64,64) | 144 | strong ≥12/16; partial 1..11/16; both require f1.0 ≤ f1.2 ≤ square, zero crash/nonfinite, zero APP exact/syndrome disagreement, known RSS <2 GiB |
| scaling canary | no new arm reaches 1/4 at n64 f1.2 | T1 | 4 × `2026091100..2026091103` | n128 f1.2 (118,104), square (128,128); then n256 f1.2 (236,208), square (256,256) | 24 per width | stop at first signaling width; silent width → next width |
| scaling confirmation | signal at a width | T1 | 16 × `2026091010..2026091025` | same three points at that width | 144 | same strong/partial rules; terminal label `N64`→`SCALING-n<w>` |

Terminal semantics (by reference): `classify_terminal`
(`D6_GRAPH_STRONG_N64_RECOVERY` / `D6_GRAPH_PARTIAL_N64_SIGNAL` /
`D6_GRAPH_SQUARE_ONLY_DIAGNOSTIC` / `D6_GRAPH_TOPOLOGY_NO_USEFUL_RECOVERY` /
`D6_GRAPH_N64_SIGNAL_INVALID`; scaling relabels `N64`→`SCALING-n<w>`), the
execution-integrity precedence (`D6_GRAPH_STRUCTURE_INVARIANT_BLOCKED` /
`D6_GRAPH_ATTEMPTED_CELL_INVALID`, accepted Option C acceptance §5) and the
resource precedence RSS > WALL > CHUNK (`D6_RSS_UNKNOWN_BLOCKED`,
`D6_RSS_LIMIT_BLOCKED`, `D6_WALL_BUDGET_BLOCKED`,
`D6_GRAPH_CHUNK_WALL_BLOCKED`).

## 3. Frozen command, root, watchdog and evidence (H32/H33)

Exact future command (repo venv; DO NOT RUN without explicit authorization):

```text
.venv/bin/python scripts/v72p2d6_graph_mother_development.py --r1d \
  --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 \
  --out-root workspace/d6_graph_mother_r1d_141730d1-5ed4-4a60-a935-50e8f24f872d/ \
  [--workers 18]
```

- Fresh root UUID: `141730d1-5ed4-4a60-a935-50e8f24f872d`
  (`workspace/d6_graph_mother_r1d_141730d1-5ed4-4a60-a935-50e8f24f872d/`);
  verified absent (H32). It must not be created before the authorized run.
- Model-F root resolution: the accepted R1d packet keeps the literal
  placeholder `<CAL-ONLY-Model-F-artifact-root>` with "explicit, no default".
  The accepted CAL-only artifact in this repo is
  `workspace/v72p2d5_model_f_input/20260907_r1` (D5 `MODEL_F_INPUT_FORMAL_ROOT`;
  `model_f_input_summary.json` `cal_only: true`, `val_rows_read: 0`; used by the
  D6 R1c-A2 execution and by accepted D7 X2/X3/X4). Flag: if the main thread
  intends a different CAL-only root, substitute it verbatim before execution.
- External watchdog and process ownership: the runner owns one dedicated
  respawnable worker process per decoder cell (pids logged in
  `manifest.json` `worker_pids` and per row `worker_pid`/`respawn_pid`); 120 s
  per-invocation watchdog (`poll=min(120s, remaining)`), terminate+respawn, no
  retry; the operator owns one foreground process, terminated only if
  positively identified as task-owned.
- Budgets (frozen): ≤2500 total setup+scientific calls; ≤12 h wall
  (`deadline=t0+12h`); aggregate RSS <2 GiB strict (no-zero) with pilot-gated
  downgrade 18→14→12→8; chunk ≥5400 s blocks dispatch; no retry; no seed
  search, no adaptive selection, no resume.
- Expected fresh-root evidence files: `manifest.json`,
  `structure_records.csv` (frozen columns + `row_degree_min`,
  `rows_below_degree_2`; marker `structure_schema=r1d-v2`,
  `eligible_semantics=frozen-AND-I1`), `selected_arms.json`,
  `decoder_records.csv`, `summary.json`, `command_log.txt`. Historical A2/VOID
  roots are refused by name; `--verify` recomputes every group on marked roots.

## 4. Early-negative semantics (H34) and claim ceiling (H35)

- Scientific canary negative (T1 n64 f1.2 APP exact < 1/4): confirmation does
  not run (frozen predicate); the frozen scaling fallback is entered only by its
  own frozen predicate ("no new arm reaches 1/4"), and the batch ends at the
  first frozen terminal. The result is recorded under the frozen terminal
  labels only and MUST NOT be described as graph-family impossibility; route
  interpretation is the main thread's, per heavy-packet §9.
- Engineering/invalid canary negative (crash, nonfinite, APP
  exact/syndrome disagreement, RSS/wall/chunk block, invariant failure):
  resource gates stop further dispatch; a crash/nonfinite/invariant failure
  forces the blocking terminal when the final terminal is composed; the frozen
  stage sequence may still run out; it is a `BLOCKED`/engineering outcome with
  no algorithm conclusion, never "graph-family impossibility".
- Claim ceiling: any positive T1 result is exploratory graph-candidate
  evidence at synthetic n64/n128/n256 under the frozen contract only. It is
  not FER, not qualification, not promotion, not real-data success, and it does
  not revive D7-H automatically. No recovery claim beyond the registered
  terminals, no SC/M/T2 claim, no performance claim beyond measured structure
  costs.

## 5. Readiness audit summary (H11–H15, H21–H24)

- `R1D_ARMS` = exactly B0/B1/T1; `R1D_VALID_SUBSET` = exactly the 22 frozen
  schedule cells; every cell passed live I1 (min check degree 2, zero rows
  below degree 2); the invalid T3 n64 L1 k59 cell is refused pre-dispatch
  (`H12` proof transcript `/tmp/opencode/d6_h12_h13_proof.out`).
- B0 support == D5 native support for all widths/layers; B1 support == B0
  support; T1 support differs (187/186/382/382/766/761 entries); B0 coefficients
  == D5 coefficient stream, B1/T1 == common stream (frozen seeds
  `202609120100+n` / `202609120200+n`); decoder contract `max_iter=90`,
  `damping_alpha=1.0`, cold (`warm_beliefs=None`, `field=None`); one Model-F
  prior, one block per `(n,seed)`, identical rows and call order L1→APP-L2→
  oracle for every arm (`H13`).
- A4/A6 equivalence: 62/62 `test_v72p2d6_gf32_graph_mother.py` passed, including
  the T2-fast-vs-reference n64/n128/n256 and A4 committed-fixture equivalence
  tests; 165/165 `test_v72p2d5_gf32_rate_mother.py` passed (`H14`; the old
  10,897-second benchmark was not rerun).
- H22 exposure: per-mode `exact`, `syndrome_ok`, `iterations`, `finite`, graph
  identity (`arm`, `n`, `matrix_id`, `rows_l1`, `rows_l2`) and residual
  syndrome weight now persist in additive R1d decoder records
  (`R1D_DECODER_FIELDNAMES`); row/I1 metrics persist in `r1d-v2`
  structure records. The frozen `DECODER_FIELDNAMES` and historical schemas are
  unchanged; non-R1d roots keep the frozen header.
- H24 guards unchanged: fresh-root existence refusal, `assert_no_formal_write`,
  `assert_r1d_out_root` (A2/VOID roots by name), ≤2500-call budget, 12 h wall,
  120 s watchdog, strict RSS, chunk block, no retry.
- Drift fixed during this batch: (a) R1d predecessor fields in
  `cycle_state.yaml` were stale; (b) the BP-compat worker tests could resolve
  the real historical decoder when two focused files reload
  `comparison_bench.*` in one pytest process (test-world-state identity
  hazard; one exploratory combined invocation reached the real bind path on
  tiny synthetic in-memory fixtures before the fix — retained in
  `EXPLORATION_LOG_R1D.md`; the fix patches the live module instance and is
  re-proved with a detector covering the importlib bind path: combined run
  28/28, `V35_DETECTED=[]` proves the real bind path was not reached — it is
  not a claim that no v35 import is reachable by any route).

## 6. State

All authorization keys remain false; `evidence_root`/`terminal` remain null; no
output root was created. Next gate: explicit user/main-thread authorization for
the frozen run (this document grants none). H41–H46 are complete; independent
readiness review verdict `PASS_WITH_FINDINGS` is recorded in
`D6_GRAPH_MOTHER_R1D_HEAVY_R1_READINESS_REVIEW.md`.

## 7. H41–H44 validation (2026-09-13; fresh task-owned basetemps, no execution)

All commands run from the repo root with `.venv/bin/python`, always passing
`-p no:cacheprovider` and a fresh
`--basetemp workspace/d6_r1d_heavy_r1_tests/<fresh-name>`; zero production
decoder/CAL/VAL/real/raw/n1024 contact, no output root created, no commit, no
push. `next_gate`, authorization keys, `evidence_root` and `terminal` are
unchanged by this section.

### H41 T0 — compile/import/constants/tiny math

- `py_compile` on the mother module, the runner and the focused
  D6/R1d/BP-compat test files → `PY_COMPILE_EXIT=0`.
- Constants/arm inventory (read-only import): `R1D_ARMS` exactly
  `[B0_D5_DV3_NATIVE, B1_D5_DV3_COMMON_LABELS, T1_PEG_DV3]`,
  `R1D_SCALING_FALLBACKS=[T1_PEG_DV3]`, `R1D_STRUCTURE_SCHEMA=r1d-v2`,
  `R1D_ELIGIBLE_SEMANTICS=frozen-AND-I1`, `R1D_VALID_SUBSET` exactly 22 cells,
  4 refused historical roots → `H41_CONSTANTS_OK`.
- Tiny-math T0 subset (`test_v72p2d6_gf32_graph_mother_r1d.py`, `-k` on the
  seven pure tests) → **7 passed, 7 deselected, 3.68 s** (designated basetemp
  `h41_t0_a1f3c9d2`; not materialized because none of those tests requests
  `tmp_path`).

### H42 T1 — focused suites (per file, fresh basetemps)

| file | result | pytest wall | basetemp |
|---|---|---|---|
| `test_v72p2d6_gf32_graph_mother_r1d.py` | 14 passed | 6.90 s | `h42_r1d_c3d8e1f2` |
| `test_v72p2d6_bp_provenance_compat.py` | 14 passed | 3.15 s | `h42_bp_compat_d4e9f3a1` (not materialized) |
| `test_v72p2d6_gf32_graph_mother.py` | 62 passed | 248.72 s | `h42_mother_b7a2c5e8` |
| `test_v72p2d5_gf32_rate_mother.py` | 165 passed | 25.45 s | `h42_rate_d5f1a8b3` |
| `test_v72p2d5_model_f_input.py` | 32 passed | 6.20 s | `h42_modelf_e6b3c9d2` |
| `test_v72p2d4_cal_gf32_model_rate_audit.py` | 30 passed | 14.12 s | `h42_d4_f2a7b1c4` |
| `test_v72p2d4r2_cal_gf32_model_rate_audit.py` | 32 passed | 32.49 s | `h42_d4r2_a8c4d2e6` |
| `test_nonbinary_v31.py` | 11 passed | 3.37 s | `h42_nbv31_b1d6e8f3` (not materialized) |
| `test_v37_degree_feasibility.py` | 11 passed | 4.68 s | `h42_v37_c9e2f4a7` (not materialized) |

- Literal seven-file non-perf suite (historical composition: graph-mother,
  rate-mother, model-f, d4, d4r2, nonbinary_v31, v37; v38 excluded) in one
  fresh process → **343 passed, 338.37 s** (basetemp `h42_seven_e4a8b2d6`).
- Combined-order hazard re-proof (`r1d` + `bp-compat` in one pytest process
  with the outside-repo `d6_v35_detect` production-decoder detector) →
  **28 passed, 7.97 s, `V35_DETECTED=[]`** (basetemp
  `h42_combined_order_f7c3d9a1`); the H15 stale module-instance fix holds; the
  detector covers the importlib bind path, so `V35_DETECTED=[]` proves the real
  bind path was not reached (not a claim that no v35 import is reachable by any
  route).
- Explicit category subset across the mother/r1d/bp-compat/model-f files
  (structural validity, control/advancement, fake decoder matrix, conditional
  transitions, crash/nonfinite/resource precedence, no-overwrite/historical
  protection) → **45 passed, 77 deselected, 11.24 s** (basetemp
  `h42_categories_9b1e4d7a`). Representative green tests:
  - 22/22 live I1: `test_r1d_every_schedule_cell_eligible`,
    `test_r1c_a5_I1_detected_and_boundary`,
    `test_r1c_a5_ineligibility_propagates_to_selection`,
    `test_r1c_a5_dispatch_guard_refuses`;
  - controls/advancement: `test_r1d_fallback_t1_only_and_controls`;
  - fake decoder call matrix: `test_r1d_invalid_cell_fails_before_decoder`,
    `test_r1d_fake_e2e_new_schema_verified_zero_decoder`,
    `test_r1d_residual_syndrome_weight_exposed`, the BP-compat
    provenance/refusal/reload tests (incl.
    `test_refused_provenance_blocks_without_crash_or_l2[...]`);
  - conditional transitions: `test_r1c_a3_scaling_stages_ordered`,
    `test_r1c_a2_sequential_three_point_consistent`,
    `test_r1c_a3_canary_isolation`,
    `test_r1c_a3_empty_confirmation_not_safety`,
    `test_r1c_a4_scaling_prunes_nonfallback`;
  - crash/nonfinite/resource precedence:
    `test_r1d_crash_nonfinite_override`,
    `test_r1c_a3_crash_overrides_topology`,
    `test_r1c_a5_execution_terminal_precedence`,
    `test_r1c_a2_rss_unknown_blocked`,
    `test_r1c_a2_single_worker_over_limit`,
    `test_r1c_a2_dual_timeout_separation`;
  - no-overwrite/historical protection:
    `test_r1d_old_schema_readable_and_immutable`,
    `test_r1d_no_a2_void_formal_reuse`, `test_formal_root_guard`,
    `test_r1c_a5_historical_verify_unchanged_and_schema_stable`,
    `test_M08_second_write_refuses_first_unchanged`.
- H12/H13 read-only no-decoder proof re-run (real builders):
  `H12_H13_PROOF_OK`; 22/22 live I1 with min check degree 2 and 0 rows below
  degree 2; T3 n64 L1 k59 refused pre-dispatch; B0/B1 support == D5 DV3
  support at all three widths/layers; B0 coefficients == D5 coefficient
  stream; T1 support differs in 6/6 cells; coefficient seeds
  `202609120100`/`202609120200`; decoder contract `max_iter=90`,
  `damping_alpha=1.0`, cold (`warm_beliefs=None`, `field=None`); raw output
  `workspace/d6_r1d_heavy_r1_tests/h42_h12_h13_proof_r1.out` (3.58 s).

### H43 bounded performance smoke (real builders only, zero decoder)

- A4/A6 fast-vs-reference equivalence subset
  (`-k "r1c_a4_equivalence_committed or r1c_a6_t2_fast_equals"`) →
  **5 passed, 237.28 s** (basetemp `h43_equiv_b3e7a2c9`). Per-test call times:
  n256 committed-fixture 211.23 s, n64 fast-vs-reference 12.70 s, n128 fixture
  8.60 s, A4 committed n64 2.51 s, A4 committed scaling-fb 1.02 s. The old
  10,897-second benchmark was not rerun.
- Bounded structure-build timing with `build_structures` /
  `build_structures_parallel` over the R1d arms (real graph builders, no
  decoder binding of any kind): n64 seq 0.074 s, n64 par (workers=2) 0.076 s,
  n128 par (workers=2) 0.204 s (18 records each).
- perf-v38 skipped (recorded choice): no scoped dependency changed — the
  v38 suite imports `v35_algorithm_development`, `v38_architecture_triage`
  and `execute_v38r1_development`, none of which is in this batch's scoped
  diff (additive D6/R1d record fields + focused-test isolation); the changed
  A4/A6 build path is instead covered by the equivalence subset above.

### H44 basetemps (all fresh, task-owned, outside legacy pytest roots)

Materialized under `workspace/d6_r1d_heavy_r1_tests/`:
`h42_r1d_c3d8e1f2`, `h42_mother_b7a2c5e8`, `h42_rate_d5f1a8b3`,
`h42_modelf_e6b3c9d2`, `h42_d4_f2a7b1c4`, `h42_d4r2_a8c4d2e6`,
`h42_seven_e4a8b2d6`, `h42_combined_order_f7c3d9a1`,
`h42_categories_9b1e4d7a`, `h43_equiv_b3e7a2c9` (+ transcript file
`h42_h12_h13_proof_r1.out`). Designated but not materialized (no `tmp_path`
requested): `h41_t0_a1f3c9d2`, `h42_bp_compat_d4e9f3a1`,
`h42_nbv31_b1d6e8f3`, `h42_v37_c9e2f4a7`, `h42_categories_list_00000000`.
Nothing was deleted. The pre-existing `t0`/`t0c`/`t1`/`t3`/`t4`/`t5`/`t6`
dirs in the same root belong to the batch-opening sweep and were not used or
modified by H41–H44. Legacy roots untouched: `workspace/tmp_pytest` mtime
2026-09-10 14:44, `workspace/.pytest_cache` mtime 2026-09-10 22:50. Historical
root `workspace/d6_graph_mother_r1c_dd8c4defe67742a8b2bc1b634c116d6b` retains
its six files with their 2026-09-09 12:59–15:17 mtimes; planned R1d root
`workspace/d6_graph_mother_r1d_141730d1-...` remains absent.

H41–H44 are complete; H45 (independent readiness review) and H46 (stop at
`D6_R1D_EXPLORE_READY_AWAITING_EXPLICIT_AUTHORIZATION`) remain. No terminal
and no authorization key was set by this validation.
