# P0 cost-preflight execution packet — 20260907 (FROZEN, NOT AUTHORIZED)

Status: `P0_PACKET_FROZEN / EXECUTE_NOT_AUTHORIZED`.
Cycle: V72P2D5-GF32-RATE-MOTHER. Gate: `next_gate: P0_PACKET_REVIEW`.
This document freezes the intended P0 run so it can be independently reviewed.
It authorizes nothing and executes nothing.

## P01 Pre-state at freeze time

Branch formal-ir-v72p1-addendum-clean / HEAD b7540421 / ahead 4 (`## formal-ir-v72p1-addendum-clean...origin/formal-ir-v72p1-addendum-clean [ahead 4]`).
`workspace/v72p2d5_p0_cost/20260906_r1` absent: true (`ROOT workspace/v72p2d5_p0_cost/20260906_r1 exists False`).
`workspace/v72p2d5_g2/20260906_r1` absent: true (`ROOT workspace/v72p2d5_g2/20260906_r1 exists False`).
`workspace/v72p2d5_g1/20260906_r1` present, 4 files: execution_summary.json 267, report.md 146, results.json 2593, table.csv 126.
`workspace/v72p2d5_model_f_input/20260907_r1` present, 2 files: model_f_input.npz 208467, model_f_input_summary.json 752.
`p0_cost_execution_authorized`: false. `next_gate`: P0_PACKET_REVIEW.
`model_f_input_accepted`: true.

## P02 Purpose and claim boundary

P0 is a cost preflight, not an experiment. Its only outputs are wall time,
iteration counts, RSS, and a projection of G1/G2 cost. It establishes no
correctness, no rate-point performance, no FER, no leakage, no key rate, and
no verdict on NB-LDPC or the dv3 mother. A P0 PASS means "the cost is measured
and projected", nothing more.

## P03 Frozen parameters

| Item | Frozen value |
| --- | --- |
| Phase name | `p0-cost` |
| Authorization key | `p0_cost_execution_authorized` (currently `false`) |
| Block width `n_IR` | 64 |
| `f` set | `(1.0, 1.2)` |
| L1 row prefixes `m1(f)` | `{1.0: 49, 1.2: 59}` |
| L2 row prefixes `m2(f)` | `{1.0: 43, 1.2: 52}` |
| Row formula | `rows = ceil(n * CE * f / 5)` |
| `CE_L1_MEAN` | `3.814742` |
| `CE_L2_ORACLE_MEAN` | `3.347605` |
| Mother builder | `build_dv3_nested_mother`, one max mother per layer |
| Builder `k_min` | L1 `P0_L1_K_MIN = 59`, L2 `P0_L2_K_MIN = 52` |
| Graph seeds | L1 `2026090501`, L2 `2026090502` |
| Block seeds | `G0_SEEDS[:2]` = `2026090510`, `2026090511` (2 blocks) |
| Decoder calls | 12 total = per `f` (2 APP calls x 2 blocks) + (1 oracle call x 2 blocks), over 2 `f` values |
| Decoder | historical `decode_row_layered_fftqspa`, `max_iter=90`, `damping_alpha=1.0`, `warm_beliefs=None` (cold start), bound once and reused |
| Prior source | accepted Model-F artifact at `workspace/v72p2d5_model_f_input/20260907_r1/`, via `prepare_model_f_prior` reusing `build_f_model` with `LAMBDA_STAR = 137.3823795883264` |
| Output root | `workspace/v72p2d5_p0_cost/20260906_r1/` (must be absent before the run; writer refuses overwrite) |
| Output files | exactly `results.json`, `table.csv`, `report.md`, `execution_summary.json` |
| Recorded per record | `f`, `kind` (`app`/`oracle`), `wall_s`, `iterations`, `rss_bytes` |
| Returned scalars | `decoder_calls`, `projected_g1_s`, `projected_g2_s`, `projection_blocked`, `passed` |
| Projection basis | `per_call = total_wall / decoder_calls`; `projected_g1_s = per_call * (100*2 + 20*2)`; `projected_g2_s = per_call * (200*3 + 40*3)` |
| `projection_blocked` rule | `True` when `projected_g2_s > 3600.0` |
| Single-call budget | 120 s |
| Downstream budgets (context only) | G1 total `<= 900 s`, G2 total `<= 3600 s`, peak RSS `< 2 GiB` |
| Metric naming | `exact_failure_fraction`; **never** call it FER; never extrapolate to real frames |
| Frozen command | `python scripts/v72p2d5_gf32_rate_mother.py --phase p0-cost` |
| Invocation count | exactly one; no retry, no rerun, no tuning, no seed change |

## P04 Frozen command and invocation contract

Command: `python scripts/v72p2d5_gf32_rate_mother.py --phase p0-cost`
Exactly one invocation. No retry, no rerun, no seed change, no tuning, no
`max_iter`/damping change, no alternate root, no second attempt after a
failure. The authorization is consumed by the attempt, not by success.

Authorization mechanism: the CLI reads `cycle_state.yaml` and refuses with
exit 3 unless `p0_cost_execution_authorized` is `true`. Flipping that key is
the authorization act and is NOT part of this packet.

## P05 Output contract

Root `workspace/v72p2d5_p0_cost/20260906_r1/`, which MUST be absent before the
run; the writer refuses to overwrite an existing root. Exactly four files:
`results.json`, `table.csv`, `report.md`, `execution_summary.json`. Scalar
payloads only. No raw rows, no matrices, no beliefs, no priors, no paths, no
checksums.

## P06 Carried residual risks

- `R-R1`: `run_p0_cost_synthetic(authorized=True)` with no injected arguments binds the **production** decoder and writes to the **formal** root by default. The guard against an accidental trigger is test-side only.
- `R-R2`: `M24`/`P12` no longer assert global formal-root absence; an unexpected new formal output would be caught only by per-test snapshot comparison.

## P07 Open questions for the reviewer

- `OQ-P0-1` — Total wall cap for P0. The frozen source pins a 120 s single-call budget but no P0 total. Worst case is 12 x 120 s = 1440 s. Should the packet carry an explicit P0 total cap, and if so what value, and is exceeding it an abort or a recorded overrun?
- `OQ-P0-2` — Watchdog. The CLI docstring says a hanging historical call needs an outer-process watchdog and that no such machinery lives in the script. What is the required outer guard for this run, and who stops it?
- `OQ-P0-3` — `projection_blocked` semantics. If `projected_g2_s > 3600`, is P0 itself still a PASS with a recorded `RESOURCE_PROJECTION_BLOCKED` flag for G2, or does it block G1 as well?
- `OQ-P0-4` — Pre-authorization isolation re-verification. Given `R-R1`, what exact evidence must be produced immediately before authorization to show no test or import path can trigger a bare authorized P0 run?
- `OQ-P0-5` — Failure disposition. If the run crashes, hangs, or produces non-finite values, is the partial output root retained (as with the voided G1 root) or is the authorization simply consumed with a recorded failure?

## P08 What this packet does not do

It does not authorize P0. It does not execute P0. It does not change any
`*_execution_authorized`. It does not change `next_gate`. It does not create
the P0 formal root. It does not resolve the open questions. It makes no
scientific claim.

## P09 Required next steps, in order

1. Independent Pre-EXECUTE review of this packet against the source, including
   a decision on every open question in P07.
2. Only if that review passes: a separate, explicit authorization act that
   flips `p0_cost_execution_authorized` to `true`.
3. Only then: the single frozen invocation in P04.
4. Then an independent Pre-RESULT review before any acceptance.

None of these may be merged, reordered, or performed by the same session that
wrote this packet.
