# D7 root-cause and route-reset R1 — review entrypoint

- Lifecycle: `IMPLEMENTATION_CANDIDATE_AWAITING_INDEPENDENT_REVIEW`
- Operator return: `OPERATOR_RETURN_R1.md` (this folder)
- Authority: `.workbuddy/tasks/D7_ROOT_CAUSE_AND_ROUTE_RESET_R1_TASK_PACKET.md`
- OpenSpec: `openspec/changes/formal-ir-d7-root-cause-and-route-reset/`
- Claim ceiling: implementation candidate; same-input equivalence finding;
  runner/test readiness. No G1 validity, no graph/mechanism cause, no
  D7-F mechanism fact, no G2 pass/fail, no FER/leakage/SKR/qualification/
  promotion.

## Inspect exactly these scoped files

1. `comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py`
   (canonical helpers; `_run_layered_block` record mode and per-layer
   fields; `_run_rate_scan` aggregates; `write_g1_evidence` additive
   columns; B06 probe; G2 wall/RSS recording and `_grade_g2` resource
   gates; `write_g2_evidence` additive fields).
2. `comparison_bench/src/comparison_bench/formal_ir/v72p2d7_consistency_multigraph.py`
   (comparison harness, frozen matrix, statistics, terminals, writers,
   reference ladder).
3. `comparison_bench/tests/test_v72p2d7_r1_consistency_multigraph.py`
   (T0/T1 evidence).
4. `scripts/v72p2d7_consistency_multigraph.py` (dry-run / X1 / X2 gating).
5. `openspec/changes/formal-ir-d7-root-cause-and-route-reset/**`
   (frozen contract, design §§2/5–7).
6. `docs/research_cycles/V72P2D7-ROOT-CAUSE-RESET/**`.

## Frozen contracts the reviewer should re-derive

- Comparison contract (design §2): exact for `q`, syndromes, decoded
  target, counters; `atol=1e-12` (`rtol=0`) for the two probability tensors
  with recorded max absolute difference; localized first mismatch on
  failure; STOP, no compensation.
- Multi-graph matrix (design §5.1): three graph pairs in order; block
  seeds `2026091300..2026091315`; f=1.2 rows 59/52 primary and f=1.0 rows
  49/43 sanity; four arms per block; `MAX_CALLS == 384`; source-exactness
  never gates; transfer gate requires exact `CHECK_UPDATED`;
  `max_iter=90`, `damping_alpha=1.0`.
- Statistics (design §5.3): raw discordant counts per graph and f; exact
  two-sided McNemar; Wilson 95% interval; descriptive only.
- Terminals (design §5.4): sensitivity classification uses only the three
  primary f=1.2 paired vectors; incomplete coverage or crash is
  `INCONCLUSIVE`; resource stop is the engineering blocker; all carry
  `EXPLORATORY_SYNTHETIC_SINGLE_IMPLEMENTATION`.
- Additive schema (design §3): existing keys, filenames, and column order
  preserved; blocked transfers are recorded non-invocations with no mixer
  and no L2 decode.
- G2 reconciliation (design §7): matrix matches the accepted D5 plan;
  four states preserved; `G2_RUNTIME_UNVERIFIED`.

## Rerun commands (fake decoders only)

```text
.venv/bin/python -m pytest -p no:cacheprovider -q --basetemp=<fresh workspace root> \
  comparison_bench/tests/test_v72p2d7_r1_consistency_multigraph.py
.venv/bin/python -m pytest -p no:cacheprovider -q --basetemp=<fresh workspace root> \
  comparison_bench/tests/test_v72p2d7_bp_belief_provenance.py \
  comparison_bench/tests/test_v72p2d7_gf32_decoder_certification.py \
  comparison_bench/tests/test_v72p2d7_r1_consistency_multigraph.py
.venv/bin/python -m pytest -p no:cacheprovider -q --basetemp=<fresh workspace root> \
  comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py
```

Expected: 36 / 73 / 165 passed respectively. Do not run any X1–X4 command;
the authorization keys are false.

## What the reviewer must independently check

- The claimed equivalence finding against the actual harness and formulas
  (including that no tolerance was widened beyond the frozen 1e-12).
- That no production decoder, CAL/VAL, Model-F, G1, multi-graph, G2, or
  D7-H execution occurred in A–F.
- That historical evidence and unrelated dirty-worktree content were not
  modified; the scoped manifest in `OPERATOR_RETURN_R1.md` §2.
- That the frozen thresholds, seeds, arms, evidence meaning, and G2
  semantics were not redefined.
- That the known pre-existing out-of-scope D7 test failures are correctly
  excluded rather than silently accepted as this change's results.

The reviewer must not treat this file, the operator return, or the tests as
scientific acceptance, execution authorization, or promotion.

## Phase P delta (2026-09-13) — X1–X4 readiness

- Lifecycle: `X1_READY_AWAITING_EXPLICIT_AUTHORIZATION` (Phase P review
  performed, `PASS_WITH_FINDINGS`).
- New entrypoint/readiness record:
  `PHASE_P_PRE_EXECUTE_READINESS_R1.md` (frozen commands, target-root
  absence, budgets, flags, tests; P10 review performed —
  `PHASE_P_INDEPENDENT_READINESS_REVIEW_R1.md`).
- Scoped Phase P files: `scripts/v72p2d7_consistency_multigraph.py`,
  `comparison_bench/src/comparison_bench/formal_ir/v72p2d7_consistency_multigraph.py`,
  `comparison_bench/tests/test_v72p2d7_r1_x1x4_entrypoints.py`,
  `cycle_state.yaml`, the Phase P record, and the OpenSpec Phase P delta.
- Production decoder/CAL/VAL calls in Phase P: zero; all execution flags
  false; frozen roots absent; no commit, no push.
- X3 call accounting (reviewer-adjudicated): let S = selected records and R =
  distinct unselected-source reconstruction keys; each reconstruction key is
  not selected, so S ≤ 192 − R and total calls = 3S + R ≤ 576 − 2R ≤ 576. The
  frozen ≤576 ceiling holds by construction (equality only when all 192 are
  selected, R = 0); the former "672 total" figure was an unachievable
  independent-component bound. X3 Pre-EXECUTE/Pre-RESULT must verify
  `ladder_calls + reconstruction_calls ≤ 576` from actual records (see
  readiness record §4 and
  `PHASE_P_INDEPENDENT_READINESS_REVIEW_R1.md`).
