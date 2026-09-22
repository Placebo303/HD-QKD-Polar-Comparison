# D6 R1d renewed Pre-EXECUTE review BP-compat A1 (Track A R06)

Authority: `.workbuddy/tasks/D7_E_CROSS_LAYER_READINESS_AND_D6_COMPAT_R1_TASK_PACKET.md` §2 (R06 only).
Role: independent renewed-R1d-Pre-EXECUTE reviewer, separate context from the Track A
implementer and the R05 reviewer. Code/readiness review only: no Model-F content,
no decoder invocation, no roots, no authorization. Reviewer ran zero decoder calls,
created zero roots, and performed read-only inspection plus `ls`/`grep`/`git` status
checks only. Sole write is this document. No commits, no edits.

Branch `formal-ir-v72p1-addendum-clean`, HEAD `4a5206fbb1d933262f7f51b1855a152985fc508e`
(`git rev-parse HEAD`), matching the R05 review's verified entry HEAD.

## 1. R05 PASS is genuine and in force — CONFIRMED

- `D6_R1D_BP_COMPAT_IMPLEMENTATION_REVIEW_R1.md` line 3 carries exactly
  `D6_R1D_BP_COMPAT_IMPLEMENTATION_REVIEW_PASS` under Track A R05 authority, scoped to the
  uncommitted working tree at entry HEAD `4a5206fbb1d933262f7f51b1855a152985fc508e`.
- HEAD is still `4a5206fb`; no commits exist after it, and no superseding R05 FAIL exists.
- The review is independent on its face (states the reviewer did not write the repair),
  source-pinned (six-tuple at `v72p2d5_gf32_rate_mother.py:1026-1060`, BP tokens and
  `require_check_updated_provenance` at `v35_algorithm_development.py:523-551`), and
  reproduces all suites literally (14 + 62 + 13 + 25 + 23 = 137 passed, 0 failed,
  separate processes, fresh basetemps, `-p no:cacheprovider`, fake decoders only).
- The compat test file it cites exists with 11 `def test` functions, one parametrized
  over refused tokens, yielding the reported 14 cases. Genuine and in force.

## 2. Prior R1d Pre-EXECUTE is stale and superseded — CONFIRMED

- `D6_GRAPH_MOTHER_PRE_EXECUTE_REVIEW_R1D.md`
  (`D6_R1D_PRE_EXECUTE_REVIEW_PASS_AWAITING_EXPLICIT_AUTHORIZATION`) reviewed the
  five-unpacking, provenance-ungated code. It no longer describes the working tree.
- The addendum `D6_GRAPH_MOTHER_R1D_EXECUTION_PACKET_ADDENDUM_BP_COMPAT_A1.md` §1 declares
  it stale and superseded after repair, retained as history only: "no longer describes
  the code", "retained as history", "grants no execution"; "no claim, selection, or
  terminal may cite it as a live readiness verdict." Status
  `R1D_PRE_EXECUTE_STALE_SUPERSEDED_AFTER_REPAIR_NOT_AUTHORIZED`.
- No live readiness verdict predates this review. This document is the only renewed gate.

## 3. Repaired matrix / dispatch / budgets / terminals equal the frozen R1d contract — CONFIRMED

- `git diff -- scripts/v72p2d6_graph_mother_development.py` shows hunks only in:
  (a) `_worker_main` warmup shape validation + `ready` flag, (b) six-value unpack +
  `"belief_provenance"` IPC, (c) `run_cell` provenance pop + `CHECK_UPDATED` gate +
  deterministic blocked record, (d) `invoke` provenance threading,
  (e) the `PROVENANCE_BLOCKED_NOTE` const. Zero hunks elsewhere.
- Untouched by inspection: `R1D_ARMS`/`R1D_VALID_SUBSET` (imported, line 39-41, never
  redefined), `POINTS == ("f1.0","f1.2","square")`, `MODES == ("L1","L2-APP","L2-oracle")`,
  `CALL_BUDGET = 2500`, `WALL_BUDGET = 12*3600`, RSS/chunk/wall terminals
  (`D6_GRAPH_CHUNK_WALL_BLOCKED`, `D6_RSS_UNKNOWN_BLOCKED`, `D6_RSS_LIMIT_BLOCKED`,
  `D6_WALL_BUDGET_BLOCKED`), A3 invariant terminals, `--r1d`/`--workers`/`--out-root`
  CLI, `assert_r1d_out_root`/`assert_no_formal_write`/overwrite-refusal order.
- Exact frozen future command, dispatch set (22 cells), science (§3), budgets/watchdog/
  stop rules (§4), evidence schema r1d-v2 (§5), and no-reuse rule (§6) of
  `D6_GRAPH_MOTHER_R1D_EXECUTION_PACKET_R1.md` are unaltered by the repair diff.

## 4. Warmup ready-gating holds by code inspection — CONFIRMED

- `scripts/v72p2d6_graph_mother_development.py:115-130`: warmup stores the decode result,
  requires `len(tuple(wres)) == 6` naming
  `decoder-result-shape-incompatible: want 6 ..., got %d`, sets `ready=True`/`warmup="ok"`
  only on compatible shape, and sends `{"event":"ready","ready":ready,...,"warmup":warm}`
  with `ready=False`/`warmup="fail:<reason>"` on any exception. Shape-blind `ok` is gone.

## 5. Fail-closed APP semantics hold by code inspection — CONFIRMED

- `run_cell` (L795-829): pops both `beliefs` and `belief_provenance`; `q` starts `None`;
  only a non-crash L1 with beliefs reaches the gate; the accepted helper
  `require_check_updated_provenance(prov, consumer="D6 run_cell L1->APP-L2")` is called
  via lazy import (no V35 edit). Exactly `CHECK_UPDATED` falls to the `else` branch whose
  `softmax(bel)` → `app_fed_l2_prior` lines are the pre-repair numerics re-indented.
- Every other token (`PRIOR_ONLY`, `WARM_START_UNSPECIFIED`, `None`, unknown, missing key
  → `None`) sets `prov_blocked_error` (`provenance-blocked:belief_provenance=<repr>:`
  `want-CHECK_UPDATED:no-L2-APP-decode`, truncated to 300), constructs no `q`, calls no
  mixer, dispatches no L2-APP decode (`skip=True` placeholder, `call_idx=-1`, no budget),
  and overwrites the slot to `crash=False`, `finite=True`, named `error` + in-memory
  `note == PROVENANCE_BLOCKED_NOTE`. Never a crash cell, never an L2 APP decode.
- L1-crash path keeps the legacy `app-undefined-l1-unavailable` skip record unchanged.
- Both worker `except` clauses are textually unchanged (`except Exception as ex:  # noqa:
  BLE001`, task path retaining `- crash consumes the cell`); arity errors keep the loud
  `ValueError` signature in `error`. The exception surface is not broadened.

## 6. Dry-run / help / verify paths create no roots — CONFIRMED

- `main` order (L1864-1883): `parse_args` → `--verify` exits before any filesystem write
  → missing `--model-f-root` errors via `ap.error` → `assert_no_formal_write` →
  `assert_r1d_out_root` guard → exists-refusal (`sys.exit(2)`) → `mkdir(parents=True)`.
  `--help`, `--verify`, and missing-arg exits all precede `mkdir`. Reviewer created no
  roots and passed no `--phase`/R1d flags.

## 7. D6/R1d roots absent; all authorization false — CONFIRMED

- `ls workspace | grep -E "^d6_graph_mother_r1d_"` → no match (exit 1); no R1d result root.
- `ls workspace | grep -E "^d7_e_cross_layer"` → no match (exit 1); no D7-E root.
- `workspace/d6_r1d_tests_*` entries contain only `test_*` pytest basetemp subdirs, not
  result roots. No new root was created by the repair or by this review.
- `cycle_state.yaml`: every execution/promotion key false
  (`implementation_authorized`, `structure_execution_authorized`, `g0/g1/g2`,
  `synthetic/real/formal_execution_authorized`, `development_decoder_authorized`,
  `scientific_promotion` all false); `evidence_root: null`, `terminal: null`;
  `next_gate: D6_GRAPH_MOTHER_R1D_FROZEN_AWAITING_EXPLICIT_AUTHORIZATION`. No UUID anywhere.

## 8. Every cross-layer path fails closed — CONFIRMED

- The only belief-consuming cross-layer path in R1d is L1 beliefs → APP-L2 mixing in
  `run_cell`, gated as above (§5). The L2-oracle diagnostic uses true `u1` via
  `d5.oracle_l2_prior` (no beliefs, untouched). The L1 leg itself performs no mixing.
- Setup/warmup validates decoder-result shape before reporting ready (§4). No path exists
  by which a `PRIOR_ONLY`/missing/`None`/unknown/warm return, or a five-valued return,
  can reach `app_fed_l2_prior` or an L2-APP decode.

## 9. No science drift; no D7-E files; seven-path diff intact — CONFIRMED

- `DECODER_FIELDNAMES` 23-name list is byte-identical (const added after it; schema
  untouched; CSV writer at L983-986 still projects through it, so transient
  `beliefs`/`belief_provenance` keys cannot persist).
- `git diff --name-only HEAD | grep -iE "d7_e|cross_layer"` and the same over
  `git status --short` both return nothing; `ls scripts | grep cross_layer/d7_e` and the
  `formal_ir` equivalent return nothing. No D7-E files exist or were touched (R14-R19
  not started).
- In-scope repair set is exactly seven paths: modified
  `scripts/v72p2d6_graph_mother_development.py` + new
  `comparison_bench/tests/test_v72p2d6_bp_provenance_compat.py` + four OpenSpec paths
  (`proposal.md`, `design.md`, `tasks.md`, `specs/d6-r1d-bp-provenance-compat/spec.md`)
  + `D6_GRAPH_MOTHER_R1D_EXECUTION_PACKET_ADDENDUM_BP_COMPAT_A1.md`. Other tracked
  modifications in the working tree (hand-off/memory/readme/mainline/decision-log/sop/
  v35-report/pytest-evidence files) are pre-existing unrelated dirty state preserved
  untouched per packet §1 prohibitions; no V35/D5/D6-module file is modified.

## Verdict

`D6_R1D_PRE_EXECUTE_REVIEW_PASS_BP_COMPAT_A1_AWAITING_EXPLICIT_AUTHORIZATION`

R1d remains `PAUSED_OPTIONAL_LOCAL_CONFIRMATION_NOT_MAINLINE_GATE`. This review grants
no execution, no UUID, and no authorization flip: no R1d/`--phase`/G1/G2/VAL/real/raw
execution is authorized here or anywhere in Track A R01-R06, and a separate explicit
main-thread execution authorization naming packet, branch, widths, arms, and budget
remains required before any R1d call.

Review doc: `docs/research_cycles/V72P2D6-GF32-GRAPH-MOTHER/D6_R1D_PRE_EXECUTE_REVIEW_BP_COMPAT_A1.md`
(sole reviewer write; uncommitted; no code edited; HEAD still `4a5206fbb1d93...`).

Blockers: none.
