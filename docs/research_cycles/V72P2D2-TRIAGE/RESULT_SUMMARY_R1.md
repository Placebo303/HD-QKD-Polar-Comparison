# V72P2D2-R1 result summary (BLOCKED RESOURCE_BLOCKED, descriptive-only)

Cycle: V72P2D2-TRIAGE, R1 recovery invocation (not a new cycle).
Base `e094f7e548380db4bfcbc1fe73472e670c32379a`,
accepted plan `4592bdad357a02f8f08a880ca0036beaed3ee900`,
artifact-recorded `implementation_sha 580471cf`
(`cycle_state.yaml` R1 revision `a11cf239`),
branch `formal-ir-v72p1-addendum-clean`.
Pre-RESULT review: PASS. DESCRIPTIVE_ONLY. No FER / SKR /
information-limit / causal-graph / qualification / promotion claim.
`RESULT_SUMMARY.md` (D2 `PREP_FAILED`) is untouched; this R1 file is additive.

Scope: exactly one authorized R1 invocation, single non-fresh diagnostic block
VAL1726-1729 (session `20260123_1M_600k_0dB`), mother `9036x10240`
`nnz=49620`, 72-point ladder, `max_sweeps_per_checkpoint=10`,
`max_total_sweeps=720`, `float64`, `llr_clip=20.0`,
`convergence_tol=1e-6`, arm order A/L/I/P. Arm A read-only reuse of the
accepted D1 record (not rerun); new arms L/I/P once each. R1 authorization
consumed (`r1_execution_count_completed=1/1`,
`r1_real_execution_authorized=false` after use); no rerun, no tuning, no other
block, no promotion. `no_run_01=true`.
Command: `python scripts/v72p2d2_orthogonal_triage.py --phase real --execute-real --out-dir comparison_bench/outputs_comparison/v72p2d2r1_orthogonal_oneblock_20260904 --preflight workspace/v72p2d2_opencode_preflight/cost_preflight.json`.

## Outcome (from manifest.json / results.json / table.csv / report.md)

- `invocation_status=RESOURCE_BLOCKED`, `prep_status=PASS`,
  `fatal_error=timeout`.

| arm | status | attempted | ckpts | stop_reason | sweeps | disclosure |
|---|---|---|---|---|---|---|
| A | LADDER_EXHAUSTED | false | 72 | D1_REUSED | null (not rerun) | null (not recorded; A not rerun) |
| L | RESOURCE_BLOCKED | true | 45 | timeout | 187 | 5792 rows + 44 control = 5836 bits |
| I | NOT_ATTEMPTED | false | 0 | timeout | 0 | 0 |
| P | NOT_ATTEMPTED | false | 0 | timeout | 0 | 0 |

Normal new-arm completions: `0/3`. L ran 45 decoder calls
(`edge_updates=3135049`, `elapsed_s=602.484000000055`,
`peak_rss_bytes=277782528`); I/P never entered the decoder
(0 sweeps, 0 disclosure, empty checkpoint metrics).
`tag_bits=0`, `tag_ok=NOT_APPLICABLE`, `diagnostic=syndrome_only` for this
invocation.

## Status vocabulary (do not conflate)

- `PREP_FAILED` is the D2 base outcome only: prep-time
  `NameError: name 'Q' is not defined`, L/I/P all `NOT_ATTEMPTED` with
  0 sweeps. It is not reused for R1.
- `RESOURCE_BLOCKED` is the R1 outcome: prep passed and arm L then hit the
  per-arm 600 s soft wall (`elapsed_s=602.484000000055`). It is a resource
  stop, not a schedule / interleaver / prior route verdict.
- `NOT_ATTEMPTED` (R1 arms I/P) means the decoder never ran for that arm
  (0 checkpoints, 0 sweeps, 0 disclosure); it carries no per-arm measurement.
- `LADDER_EXHAUSTED` (arm A) is the carried D1 reuse record
  (`D1_REUSED`, not rerun), not a new R1 measurement.
- `final_syndrome_satisfied=false` (L, at `final_checkpoint_rows=5792`) is
  the in-run prefix check on the last completed checkpoint only.
- `final_oracle_exact=false` (L, `posthoc_oracle.runs_after_arm_end=true`)
  is the after-arm descriptive comparison of that same final candidate
  against Bob. It is posthoc classification only, never merged into
  undetected / protocol-accepted / verified-exact counts (all zero here).

## Arm A reuse boundary

A is `original_D1_reused` (`prior D1_M0_reused`, `schedule D1_flooding_reused`),
`attempted=false`, carried `common_metrics` only: `outcome=LADDER_EXHAUSTED`,
`iterations=334`, `candidate_vs_bob bits=3100 symbols=620`, D1 APP finite
(`max_abs=0.8002106803449582`), D1 single-edge c2v finite (`residual=1.37e-07`,
`iterations=4`). New L0/F/S/A/delta/sign/clip/syndrome fields are null with
`not_recorded_reason="D1 baseline did not record this metric; A was not rerun"`.
Baseline source recorded in artifact:
`comparison_bench/outputs_comparison/v72p2d1_parity_layout_ab/results.json`.
No quantitative A-vs-L/I/P difference is made.

## Budget (within limits, from artifacts)

- `prep_wall_s=7.765999999945052` (limit `prep_limit_s=600.0`).
- `invocation_wall_s_before_report=610.25`
  (limit `invocation_limit_s=2400.0`).
- `peak_rss_bytes=277782528` (limit `2147483648` = 2 GiB).
- Per-arm soft wall `600.0`s stopped L (`elapsed_s=602.484000000055`,
  45 checkpoints x up to 10 sweeps = 187 sweeps used); I/P stopped with
  the invocation at 0 sweeps.

## Claim boundary

One non-fresh VAL block descriptive diagnostic only. 0 protocol-accepted,
0 verified-exact, 0 undetected counted (L finished unsatisfied with a
posthoc non-exact final candidate; I/P never attempted; A reuse carries
no new acceptance). `claim_boundary` in artifacts: no protocol acceptance,
FER, SKR, information-limit, causal-graph, or promotion claim. The L
timeout is a budget stop, not a schedule / interleaver / prior verdict.

Artifacts: `comparison_bench/outputs_comparison/v72p2d2r1_orthogonal_oneblock_20260904/`
exactly four files (`manifest.json` / `results.json` / `table.csv` / `report.md`),
no `run_01`. The D2 root
`comparison_bench/outputs_comparison/v72p2d2_orthogonal_oneblock_20260904/`
(`PREP_FAILED`) is untouched.
