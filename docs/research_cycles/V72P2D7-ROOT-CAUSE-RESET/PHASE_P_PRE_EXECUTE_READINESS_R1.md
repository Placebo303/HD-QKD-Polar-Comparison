# D7 X1–X4 Phase P pre-EXECUTE readiness record R1

- Cycle: `V72P2D7-ROOT-CAUSE-RESET`
- Change: `formal-ir-d7-root-cause-and-route-reset`
- Authority: `.workbuddy/tasks/D7_X1_X4_EXECUTION_MASTER_R1_TASK_PACKET.md` (sole packet; Phase P, P01–P10)
- Branch: `formal-ir-v72p1-addendum-clean` (recorded, not switched)
- Lifecycle: `X1_READY_AWAITING_EXPLICIT_AUTHORIZATION` (Phase P independent
  readiness review: `PASS_WITH_FINDINGS`, `PHASE_P_INDEPENDENT_READINESS_REVIEW_R1.md`)
- Scope: P01–P09 implementation, fake-injected T0/T1 tests, readiness records.
  P10 independent review is **not** self-accepted. No X phase ran.
- Production decoder / CAL / VAL calls in Phase P: **0**. All execution
  flags false; **no authorization consumed**.
- No commit, no push; changes remain in the worktree.

## 1. Implemented entrypoints (P01–P09)

- `scripts/v72p2d7_consistency_multigraph.py`
  - `--historical-provenance-probe` (P01/P02): calls
    `probe_historical_decoder_provenance(decode_fn=None)` exactly once,
    prints one JSON record, writes no file, creates no root; refuses unless
    `x1_consistency_probe_authorized: true`.
  - `--consistency` relabelled `same-input synthetic consistency` (never X1)
    in help and in the printed record (`mode:
    same_input_synthetic_consistency`); behaviour unchanged.
  - `--reference-ladder --x2-root <exact> --out-root <exact>` (P07):
    requires `x3_reference_ladder_authorized: true`; refuses before reading
    X2, binding decoders, or creating a root when false.
  - `--g2` (P08/P09): requires `x4_g2_execution_authorized: true`; refuses
    unless every D5 execution flag is false.
- `comparison_bench/src/comparison_bench/formal_ir/v72p2d7_consistency_multigraph.py`
  - `historical_provenance_probe_record` (P02 JSON/exit contract).
  - X3 (P03–P06): `is_failed_f12_record` / `select_failed_x2_records`,
    `plan_x3_calls` / `_guard_x3_plan`, `validate_x3_x2_root` /
    `validate_x3_out_root`, `read_x2_root` / `validate_x2_manifest`,
    `x3_reconstruct_marginal_call` / `x3_reconstruct_transfer_call`,
    `_replay_mismatch`, `run_reference_ladder_selected`.
  - X4 (P08/P09): `run_g2_bridge`.
- No change to `v72p2d5_gf32_rate_mother.py` (existing public G2/probe API
  was sufficient; diff remains the accepted Phase-B +278/−33).

## 2. X1 readiness — historical provenance probe

- Required flag: `x1_consistency_probe_authorized` (currently false).
- Frozen command (packet §7):
  `.venv\Scripts\python.exe scripts\v72p2d7_consistency_multigraph.py --historical-provenance-probe`
- Calls exactly one historical row-layered decoder invocation on the built-in
  2x2 GF32 fixture; prints one JSON record with resolved decoder identity,
  provenance token, accepted flag, iterations, shape validity, finite status,
  `decoder_calls: 1`, `writes: 0`.
- Exit 0 only for exact `CHECK_UPDATED` + finite + shape-valid beliefs +
  `iterations >= 1`; otherwise nonzero plus `X1_PROVENANCE_PROBE_FAILED` on
  stderr. Any other return is the X1 failure terminal; no retry/repair.
- Budget: outer watchdog 120 s; RSS < 2 GiB. Writes/roots: zero.
- Caveat: exit-code contract is exit 2 for a completed failed probe; exit 3
  for a refusal (unauthorized/probe error).

## 3. X2 readiness — three-graph exploratory diagnostic (unchanged)

- Required flag: `x2_multigraph_execution_authorized` (currently false).
- Exact input `workspace/v72p2d5_model_f_input/20260907_r1`; exact fresh root
  `workspace/d7_r1_multigraph_20260913_r1` (verified absent below).
- Frozen command:
  `.venv\Scripts\python.exe scripts\v72p2d7_consistency_multigraph.py --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d7_r1_multigraph_20260913_r1 --wall-budget-s 900`
- Matrix maximally 384 calls; wall <= 900 s; per-call watchdog 120 s;
  RSS < 2 GiB. No rerun/resume/replacement.

## 4. X3 readiness — failed-record reference ladder

- Required flag: `x3_reference_ladder_authorized` (currently false).
- Exact read-only X2 root `workspace/d7_r1_multigraph_20260913_r1`; exact
  fresh root `workspace/d7_r1_reference_ladder_20260913_r1` (verified absent).
- Frozen command:
  `.venv\Scripts\python.exe scripts\v72p2d7_consistency_multigraph.py --reference-ladder --x2-root workspace/d7_r1_multigraph_20260913_r1 --out-root workspace/d7_r1_reference_ladder_20260913_r1 --wall-budget-s 3600`
- Selector (P03): every `call_records.csv` record with `f == 1.2`,
  `invoked == true`, status not `crash:*`, `finite == true`, `exact == false`;
  `(graph_idx, graph seeds, block seed, arm, role, rows, prior kind)`
  preserved exactly; no dedup/replacement.
- Call accounting (P04, reviewer-adjudicated): let S = selected records and
  R = distinct unselected-source reconstruction keys. For any X2 root produced
  by the frozen writer, each reconstruction key is not selected, so
  S ≤ 192 − R and total calls = 3S + R ≤ 576 − 2R ≤ 576. The frozen ≤576
  ceiling holds by construction (equality only when all 192 are selected,
  R = 0); the "672 total" figure was an unachievable independent-component
  bound. A selected TARGET record additionally needs its source marginal
  beliefs; when the source slot is itself selected its ladder baseline
  supplies them (slot order processes sources first), otherwise one
  deterministic `ROW_LAYERED_90` source replay is used, cached per source
  slot. Ladder and reconstruction counts are recorded in the plan before any
  decoder is bound.
- X3 Pre-EXECUTE/Pre-RESULT requirement: verify `ladder_calls +
  reconstruction_calls ≤ 576` from actual records.
- Reconstruction (P05): H/prior/syndrome/truth rebuilt deterministically from
  the immutable X2 manifest, the manifest-referenced accepted Model-F root
  and the recorded slot identity. The reconstructed `ROW_LAYERED_90` baseline
  is compared field-by-field (`exact`, `syndrome_ok`, `iterations`, `finite`,
  `symbol_errors`, `unsatisfied_checks`, `provenance`, `status`) against the
  stored X2 record; the first mismatch is
  `X3_BASELINE_REPLAY_MISMATCH_BLOCKED` and stops all later records. TARGET
  source replays are verified against the stored source record before use.
- Terminals: `X3_REFERENCE_LADDER_COMPLETED`,
  `X3_NOT_APPLICABLE_NO_FAILED_CALLS` (zero selected; zero calls; neither
  success nor failure), `X3_BASELINE_REPLAY_MISMATCH_BLOCKED`,
  `X3_ENGINEERING_BLOCKED` (stored wall budget exceeded or RSS >= 2 GiB).
  CLI exit: 0 for completed/not-applicable, 1 for mismatch, 3 for refusal.
- Evidence (P06): fresh root with exactly `manifest.json`,
  `selected_records.csv`, `ladder_records.csv`, `paired_summary.csv`,
  `summary.json`, `report.md`, `command_log.txt`; `selected_records.csv` is
  written **before** any decoder is bound; never overwrite. Claim label
  `STRONG_REFERENCE_DIAGNOSTIC` only.
- Budget: total stored wall <= 3600 s; per-call watchdog 480 s (outer
  process ownership); RSS < 2 GiB.

## 5. X4 readiness — G2 n=256 length discriminator bridge

- Required flag: `x4_g2_execution_authorized` (currently false).
- D5 preconditions asserted by the bridge: every execution flag
  (`structure`, `g0`, `g0-recovery`, `p0-cost`, `g1`, `g2`, `synthetic`,
  `real`, `formal`) false. The D5 `g2_execution_authorized` flag is never
  set or written.
- Exact fresh root `workspace/v72p2d5_g2/20260906_r1` (verified absent);
  abort if it exists. Calls `run_g2_synthetic(authorized=True)` exactly once;
  existing four-file G2 schema plus the accepted additive per-layer/wall/RSS
  fields only.
- Frozen command:
  `.venv\Scripts\python.exe scripts\v72p2d7_consistency_multigraph.py --g2`
- Matrix n=256; f = 1.0/1.1/1.2; rows L1 196/215/235, L2 172/189/206; 200
  blocks per f; oracle subset 40 per f; max 1320 calls; wall <= 3600 s;
  single call <= 120 s outer watchdog; RSS < 2 GiB. Four-state outcome only.
- Not bundled with X2/X3; no automatic n=1024/G1/D7-H/tuning.

## 6. Target-root absence evidence (2026-09-13, pre-EXECUTE check)

```text
$ for r in workspace/d7_r1_multigraph_20260913_r1 \
           workspace/d7_r1_reference_ladder_20260913_r1 \
           workspace/v72p2d5_g2/20260906_r1; do
      [ -e "$r" ] && echo "PRESENT: $r" || echo "ABSENT: $r"; done
ABSENT: workspace/d7_r1_multigraph_20260913_r1
ABSENT: workspace/d7_r1_reference_ladder_20260913_r1
ABSENT: workspace/v72p2d5_g2/20260906_r1
```

## 7. Authorization state and consumption

All flags in `cycle_state.yaml` remain false:
`x1_consistency_probe_authorized`, `x2_multigraph_execution_authorized`,
`x3_reference_ladder_authorized`, `x4_g2_execution_authorized`,
`d7h_execution_authorized`, `g1_rerun_authorized`,
`result_solidification_authorized`, `scientific_promotion`.

`implementation_accepted: true` records the main-thread acceptance of Phases
A–F (2026-09-13). `next_gate` is the Phase P readiness marker; no execution
authorization is granted or implied. Each X phase requires its own explicit
user authorization; no phase authorizes the next. Authorization is consumed
by the first process-start attempt and restored false immediately after.

## 8. Focused tests executed (fake decoders only, fresh basetemps)

All commands from the repository root with the repo venv and fresh
`workspace/v72p2d7_x1x4_test_<uuid>` basetemps:

| # | Files | Result |
|---|-------|--------|
| T0a | `py_compile` on CLI + core + new test file | exit 0 |
| T0b | CLI `--help` / `--dry-run` | exit 0, 384 slots |
| T1a | `comparison_bench/tests/test_v72p2d7_r1_x1x4_entrypoints.py` (new, 55 tests) | **55 passed** |
| T1b | `test_v72p2d7_r1_consistency_multigraph.py` (unchanged) | **36 passed** |
| T1c | `test_v72p2d7_bp_belief_provenance.py` + `test_v72p2d7_gf32_decoder_certification.py` + new file | **92 passed** |
| T1d | `test_v72p2d5_gf32_rate_mother.py` | **165 passed** |
| T1e | `test_v72p2d5_model_f_input.py` | **32 passed** |
| T1f | `test_v72p2d6_gf32_graph_mother.py` | **62 passed** |
| T1g | `test_v72p2d7_gf32_alternating_discriminator.py` | **32 passed** |

The new suite covers: X1 JSON/exit contract, exactly-one probe call with no
writes, refusal paths, synthetic-consistency relabel; X3 selector boundary +
field preservation + no dedup, call plan/guard, manifest validation,
reconstruction + baseline equality gate, mismatch stop before later records,
source-reconstruction mismatch, zero-selected terminal, wall-budget stop,
no-overwrite, exact-X2-root enforcement, injected-decoder binding isolation,
full 384-record X2 fake matrix reaching the 576 ladder ceiling; X3 CLI
gating; X4 bridge D7-flag/D5-flags/root-exists refusals, exactly-one-call and
no-flag-write; X1–X4 dormant-flag and frozen-root-absence guards.

## 9. Prior finding — reference-ladder binding coverage

Finding D-minor: `bind_reference_ladder_decoders` was unexercised. Phase P:

- wrapper/import/signature coverage proven with a fake `_load_v35` (exact
  kwargs: row-layered 90/360 with `damping_alpha=1.0`,
  `warm_beliefs=None`, `field=None`; flooding 90 with `field=None`;
  signature `(h, prior, syndrome)`);
- the real v35 import + real bind is executed in a clean subprocess with
  `PYTHONPATH=comparison_bench/src` (production CLI layout), asserting the
  three wrappers and signatures; **no wrapper is invoked**;
- the true-condition binding probe (actually invoking a production decoder
  wrapper) belongs to **X3 Pre-EXECUTE**, before the X3 authorization is
  consumed.

## 10. Stop rules

- Any branch mismatch, scoped-file drift, or missing independent review /
  explicit phase authorization: STOP.
- X1: provenance not exactly `CHECK_UPDATED`, non-finite/invalid-shape
  beliefs, or iterations < 1 -> `X1_PROVENANCE_PROBE_FAILED`; STOP, no
  retry/repair.
- X2: incomplete/resource/crash/non-finite terminal stops before X3.
- X3: first baseline-replay mismatch ->
  `X3_BASELINE_REPLAY_MISMATCH_BLOCKED`; STOP, no later records.
- X4: matrix/call ceiling/grading vocabulary/wall-RSS accounting/root
  differ -> STOP.
- Any historical result, Model-F input, frozen baseline, or unrelated dirty
  file change -> STOP. No retry/resume/seed replacement/tuning.

## 11. P10 independent readiness review entrypoint

Review exactly:

1. `.workbuddy/tasks/D7_X1_X4_EXECUTION_MASTER_R1_TASK_PACKET.md` (P01–P10,
   §7 frozen contracts).
2. `scripts/v72p2d7_consistency_multigraph.py` (mode gating, refusals,
   exit codes).
3. `comparison_bench/src/comparison_bench/formal_ir/v72p2d7_consistency_multigraph.py`
   (X1 record builder; X3 selector/plan/guard/reconstruction/replay
   gate/writers; X4 bridge).
4. `comparison_bench/tests/test_v72p2d7_r1_x1x4_entrypoints.py` (T0/T1
   evidence).
5. This record and `cycle_state.yaml`.

Independent checks required:

- zero production decoder/CAL/VAL calls; every test path fake-injected or
  injected-runner; real `workspace/d7_r1_multigraph_20260913_r1`,
  `workspace/d7_r1_reference_ladder_20260913_r1`, and
  `workspace/v72p2d5_g2/20260906_r1` remain absent;
- all execution flags false and `historical_evidence:
  RETAINED_BYTE_IDENTICAL`; lifecycle
  `X1_READY_AWAITING_EXPLICIT_AUTHORIZATION`;
- frozen command literals, budgets, stop rules, and claim label match §7;
- X3 selector preserves identity exactly and never dedups/replaces;
- X3 baseline replay gate is field-exact and stops on first mismatch;
- the X3 reconstruction-call accounting interpretation in §4 (ladder ceiling
  576 vs `<= 96` deterministic source replays) is adjudicated acceptable:
  total = 3S + R <= 576 - 2R <= 576 by construction; X3 Pre-EXECUTE and
  Pre-RESULT must verify `ladder_calls + reconstruction_calls <= 576` from
  actual records (see §4 and `PHASE_P_INDEPENDENT_READINESS_REVIEW_R1.md`).

Rerun commands:

```text
.venv/bin/python -m pytest -p no:cacheprovider -q --basetemp=<fresh workspace/v72p2d7_x1x4_test_<uuid>> \
  comparison_bench/tests/test_v72p2d7_r1_x1x4_entrypoints.py
.venv/bin/python -m pytest -p no:cacheprovider -q --basetemp=<fresh workspace/v72p2d7_x1x4_test_<uuid>> \
  comparison_bench/tests/test_v72p2d7_r1_consistency_multigraph.py
.venv/bin/python -m pytest -p no:cacheprovider -q --basetemp=<fresh workspace/v72p2d7_x1x4_test_<uuid>> \
  comparison_bench/tests/test_v72p2d7_bp_belief_provenance.py \
  comparison_bench/tests/test_v72p2d7_gf32_decoder_certification.py \
  comparison_bench/tests/test_v72p2d7_r1_x1x4_entrypoints.py
.venv/bin/python -m pytest -p no:cacheprovider -q --basetemp=<fresh workspace/v72p2d7_x1x4_test_<uuid>> \
  comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py
```

Do not run any X1–X4 command; the authorization keys are false. This record
is not execution authorization, acceptance, or promotion.
