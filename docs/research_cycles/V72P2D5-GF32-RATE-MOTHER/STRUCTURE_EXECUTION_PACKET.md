# V72P2D5-GF32-RATE-MOTHER — Structure Execution Packet (Frozen)

## 1. Sole question

The sole question for this structure execution is whether the frozen-seed
L1/L2 1000x1024 dv3 mother satisfies rank/coverage/connectivity on all
frozen prefixes.

Explicitly NOT in scope: decoder, GF32-route, real-data, FER, SKR, limit,
dim-expansion.

## 2. Objects (frozen, exactly once each)

- L1: n=1024, m_max=1000, k_min=782, seed=2026090501,
  prefixes={782, 821, 860, 938}.
- L2: n=1024, m_max=1000, k_min=686, seed=2026090502,
  prefixes={686, 720, 755, 823}.

Each layer built exactly once. Forbidden: seed-swap, retry, family change,
support modification, reorder, coefficient resample, decoder call,
data read.

## 3. Invocation (frozen)

- Command: `python scripts/v72p2d5_gf32_rate_mother.py --phase structure`
  only.
- Only after independent Pre-EXECUTE review PASS plus
  `cycle_state.yaml` `structure_execution_authorized: true`.
- Forbidden: `--phase all`, seed overrides, degree overrides, family
  overrides, retry overrides.

## 4. Per-layer checks (frozen)

- shape=(1000, 1024).
- dtype=uint8.
- total_edges=3072.
- var-deg all 3.
- zero rows 0, zero cols 0.
- triples unique.
- coeffs 0..31, support 1..31, nonsupport 0.

## 5. Per-prefix audit (21 fields + hard PASS gates)

Per-prefix audit records 21 fields. Hard PASS requires all of:

- rank == prefix_rows.
- zero rows 0.
- isolated variables 0.
- components 1.
- largest-component fraction 1.0.
- duplicate projections 0.
- coefficient nonzero true.
- variable min-degree >= 2.
- base duplicates 0.
- triple duplicates 0.

Four-cycle policy (frozen):

- four_cycles == 0 -> STRUCTURE_PASS (if all other hard gates pass).
- four_cycles > 0 with all other hard gates passing ->
  STRUCTURE_PASS_WITH_CYCLE_RISK, counts carried, no remap.
- Any other hard-gate failure -> STRUCTURE_BLOCKED, no G0.

## 6. Cost preflight (frozen, blocking)

- Rerun `py_compile` + `pytest` 60/60 PASS required before full build.
- Timing proxy only: small fixture plus n<=256 L1-like/L2-like builds,
  no decoder.
- Record build/rank wall time + RSS; extrapolate 2-layer total.
- Budget: single-layer 900 s, total 1800 s, RSS < 2 GiB.
- Exceeding budget -> STRUCTURE_RESOURCE_PROJECTION_BLOCKED, no full
  build.
- Forbidden bypasses: prefix-skip, rank-skip, m_max cut, approximate
  rank, parallel build, budget raise.

## 7. Attempt semantics (frozen)

- Preflight invocations are not counted as structure attempts.
- First full L1 construction moves `structure_execution_attempts` 0 -> 1.
- Maximum 1 invocation.
- L1 then L2 sequential; L1 fail => no L2; L1 pass => proceed to L2.
- Any exception/timeout: no retry.
- `structure_execution_completed = 1` only after L1+L2 full builds plus
  all prefix audits complete.
- Completion is not PASS: BLOCKED outcomes are retained as completed.

## 8. Outputs (frozen)

- Candidate directory: `workspace/v72p2d5_structure/20260905_r2/`.
- Must not exist before authorized execution.
- Exactly four files: `results.json`, `table.csv`, `report.md`,
  `execution_summary.json`.
- Scalars plus small histograms only.
- Forbidden artifacts: full mother arrays, support arrays, coefficient
  arrays, column vectors, raw pairs, prior outputs, syndromes,
  decoder messages, hash/checksum/tag values, absolute paths.
- `results.json` must contain: phase/structure, decoder_calls 0,
  cal_rows_read 0, val_rows_read 0, L1/L2 seeds, per-layer summaries,
  per-prefix audit fields, wall time, RSS, attempts, completed,
  decision.

## 9. Pre-EXECUTE checks PE1-PE16 (frozen)

PE1: implementation SHA equals accepted R2_DV3 candidate.
PE2: `ACCEPTED_PLAN_SHA` binding re-derived, no stale constant.
PE3: target output directory absent.
PE4: `structure_execution_authorized: true` in cycle_state.
PE5: invocation is `--phase structure` only.
PE6: L1/L2 seeds, n, m_max, k_min, prefixes match Section 2.
PE7: no seed/degree/family/retry overrides.
PE8: `py_compile` PASS.
PE9: `pytest` 60/60 PASS.
PE10: cost-preflight projection within single 900 s / total 1800 s /
  RSS < 2 GiB.
PE11: no decoder import/call path enabled.
PE12: no CAL read path enabled.
PE13: no VAL read path enabled.
PE14: output file set is exactly the four frozen files.
PE15: forbidden artifact classes excluded.
PE16: FAIL on any PE item blocks execution (revise-required).

## 10. Pre-RESULT checks PR1-PR16 (frozen)

PR1: plan thresholds match frozen R2 plan.
PR2: leakage-formula decomposition checked (no leakage claim here).
PR3: `undetected` isolated, never merged into success/FER.
PR4: per-source breakdown present where applicable.
PR5: disclosure accounting complete.
PR6: per-layer checks of Section 4 verified from artifacts.
PR7: per-prefix 21 fields present for all 8 prefixes.
PR8: hard PASS gates of Section 5 applied exactly.
PR9: four-cycle policy of Section 5 applied exactly, no remap.
PR10: decoder_calls == 0 verified.
PR11: cal_rows_read == 0 and val_rows_read == 0 verified.
PR12: full-mother/support/coeff arrays absent from outputs.
PR13: hash/checksum/tag/abs-path classes absent.
PR14: attempt/completion counters match Section 7 semantics.
PR15: decision is one of the four frozen decisions below.
PR16: FAIL on any PR item blocks solidification (rework, no G0).

## 11. Decisions (frozen, exactly four)

- STRUCTURE_PASS.
- STRUCTURE_PASS_WITH_CYCLE_RISK.
- STRUCTURE_BLOCKED.
- STRUCTURE_RESOURCE_PROJECTION_BLOCKED.

Next-gate rule:

- L1+L2 all-hard PASS (with or without cycle risk) -> G0 packet review;
  cycle-risk carries four-cycle counts forward, no remap.
- Any hard fail -> back to planner, no G0.

## 12. Authorization granted by this packet

This round grants NOTHING. All execution authorizations remain false:

- `structure_execution_authorized: false`.
- `g0_execution_authorized: false`.
- `p0_cost_execution_authorized: false`.
- `g1_execution_authorized: false`.
- `g2_execution_authorized: false`.
- `synthetic_execution_authorized: false`.
- `real_execution_authorized: false`.
- `formal_execution_authorized: false`.
- `scientific_promotion: false`.

Future authorization only via explicit `cycle_state.yaml` update after
the required independent review.
