# V72P2D2-TRIAGE result summary (BLOCKED PREP_FAILED, descriptive-only)

Cycle: V72P2D2-TRIAGE. Base `e094f7e548380db4bfcbc1fe73472e670c32379a`,
accepted plan `4592bdad357a02f8f08a880ca0036beaed3ee900`,
implementation `580471cf`, branch `formal-ir-v72p1-addendum-clean`.
Pre-RESULT review: PASS. DESCRIPTIVE_ONLY. No FER / SKR /
information-limit / qualification / promotion claim.

Scope: exactly one authorized invocation, single non-fresh diagnostic block
VAL1726-1729 (session `20260123_1M_600k_0dB`), mother `9036x10240`
`nnz=49620`, 72-point ladder, `max_sweeps_per_checkpoint=10`,
`max_total_sweeps=720`, `float64`, `llr_clip=20.0`,
`convergence_tol=1e-6`, arm order A/L/I/P. Arm A read-only reuse of the
accepted D1 record (not rerun); new arms L/I/P once each. Authorization
consumed (`execution_count_completed=1/1`); no rerun, no tuning, no other
block, no promotion. `no_run_01=true`.

## Outcome (from manifest.json / results.json / table.csv / report.md)

- `invocation_status=PREP_FAILED`, `prep_status=FAILED`.
- `fatal_error=NameError: name 'Q' is not defined`.
- Command: `python scripts/v72p2d2_orthogonal_triage.py --preflight workspace/v72p2d2_opencode_preflight/cost_preflight.json --execute-real --phase real`.

| arm | status | attempted | ckpts | stop_reason | sweeps | disclosure |
|---|---|---|---|---|---|---|
| A | LADDER_EXHAUSTED | false | 72 | D1_REUSED | null (not rerun) | null (not recorded; A not rerun) |
| L | NOT_ATTEMPTED | false | 0 | NameError: name 'Q' is not defined | 0 | 0 |
| I | NOT_ATTEMPTED | false | 0 | NameError: name 'Q' is not defined | 0 | 0 |
| P | NOT_ATTEMPTED | false | 0 | NameError: name 'Q' is not defined | 0 | 0 |

Normal new-arm completions: `0/3`. No L/I/P decoder sweeps, no edge updates,
no checkpoint metrics, no `graph_id`/`prior_id`/`schedule_id` for L/I/P.
`tag_bits=0`, `tag_ok=NOT_APPLICABLE`, `diagnostic=syndrome_only` for this
invocation.

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

- `prep_wall_s=0.43700000003445894` (limit `prep_limit_s=600.0`).
- `invocation_wall_s_before_report=0.4529999999795109`
  (limit `invocation_limit_s=2400.0`).
- `peak_rss_bytes=174399488` (limit `2147483648` = 2 GiB).
- Per-arm soft wall `600.0`s not reached: L/I/P stopped at prep with 0 sweeps.

## Claim boundary

One non-fresh VAL block descriptive diagnostic only. 0 protocol-accepted,
0 verified-exact, 0 undetected counted (L/I/P never attempted; A reuse carries
no new acceptance). `claim_boundary` in artifacts: no protocol acceptance,
FER, SKR, information-limit, causal-graph, or promotion claim. L/I/P failure
is a prep-time `NameError`, not a schedule / interleaver / prior route verdict.

Artifacts: `comparison_bench/outputs_comparison/v72p2d2_orthogonal_oneblock_20260904/`
exactly four files (`manifest.json` / `results.json` / `table.csv` / `report.md`).
