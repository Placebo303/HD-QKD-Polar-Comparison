# D7-B result acceptance R2 — WSL invocation `c605d1e6-8577-4c52-a865-12500fc8c964`

Scope: scoped acceptance documentation only. Zero decoder calls, zero reruns,
zero root edits, zero production-code edits. Main-thread adjudication (§0 of
`D7_B_RESULT_ACCEPT_EARLY_EXIT_AUDIT_R1_TASK_PACKET.md`) is applied without
reinterpretation.

## Baseline (verified before writing)

- Branch: `formal-ir-v72p1-addendum-clean`; HEAD `03c2e68e62646d20c7932b63a53fbd5d1f8ee0ab`
  (prefix matches expected `03c2e68e`).
- Root `workspace/d7_b_easy_regime_c605d1e6-8577-4c52-a865-12500fc8c964/`:
  exactly five files, zero subdirectories —
  `command_log.txt` (111 B), `decoder_records.csv` (44743 B),
  `manifest.json` (1008 B), `report.md` (80 B), `summary.json` (449 B).
  Read twice (task start/end); names/sizes/mtimes identical; nothing modified.
- Review: `D7_B_PRE_RESULT_REVIEW_PASS_R2` (R01–R18 consistency-only pass).
- `cycle_state.yaml`: `d7b_execution_authorized: false`,
  `d7b_execution_attempts/completed 1/1`, `decoder_executed/result true/true`,
  `d7b_r2_terminal: D7_B_RESOURCE_OVERRUN`,
  `next_gate: INDEPENDENT_D7_B_RESULT_ACCEPTANCE_R2` (pre-acceptance value).
- R1d absent (no D7 R1d root, no R1d/G1/G2 authorization); protected roots
  (`results`, `comparison_bench/outputs_comparison`,
  `workspace/v72p2d5_g0/20260905_r2`, `workspace/v72p2d5_g1/20260907_r2`)
  unchanged.

## Accepted statements (packet §3, all twelve, without reinterpretation)

1. The R2 lifecycle (authorize `0327c65` → one invocation → revoke `3fe63ef`)
   and the five-file evidence root are accepted as authentic, immutable and
   contract-faithful.
2. The stored terminal remains `D7_B_RESOURCE_OVERRUN`.
3. `resource_overrun` means RSS unknown because the WSL venv lacked psutil
   (`_rss_bytes` try/except returns `None`; all 64 invoked rows store empty
   `rss_bytes`); it is a telemetry unknown, not a measurement.
4. No measured RSS breach occurred (zero known RSS values, hence no value at
   or above 2 GiB), and no `<2GiB` PASS may be claimed.
5. All 64 invoked cells returned exact + syndrome-consistent hard decisions at
   cap 1 (`exact 64/64`, `syndrome_ok 64/64`, `status converged_exact 64/64`,
   zero crash/nonfinite/unsatisfied/symbol errors).
6. 49 cells used decoder iteration 0 and 15 used decoder iteration 1
   (recomputed from the CSV: 48 truth-centered P99/P90/P60 cells at iteration
   0; PAIR 1 at iteration 0 + 15 at iteration 1).
7. Truth-centered P99/P90/P60 priors peak uniquely at the true word, so the 48
   iteration-0 successes are an initial-MAP sanity region, not evidence of
   iterative BP gain.
8. PAIR supplies the only cells that generally required one sweep (15/16 PAIR
   at iteration 1; the single PAIR iteration-0 cell is the all-even-truth
   tie-break case).
9. The posterior tolerance failed although MAP agreement passed (tractable
   `post_err` maxima about 0.500 SINGLE / 0.400 TREE against `1e-10`;
   `map_agree` 32/32 on tractable invoked cells).
10. The accepted scope is exactly
    `HARD_DECISION_EASY_REGION_OBSERVED_WITH_RESOURCE_AND_SOFT_BELIEF_LIMITATIONS`.
11. D7-B `CONFIRMED`/`PARTIAL` (`D7_B_EASY_REGIME_CONFIRMED` /
    `D7_B_PARTIAL_EASY_REGIME`) is not accepted (`confirmed: false`,
    `partial: false` stored and recomputed).
12. No FER, leakage, key-rate, CAL-recovery, qualification, R1d/G2 permission,
    or broad NB-LDPC conclusion follows from this acceptance.

## Not authorized

R1d, D7-C/D, any `--phase`, G1/G2, Model-F, CAL, VAL, real/raw execution and
any result-root edit remain unauthorized. No push. Next gate:
`D7_B_EARLY_EXIT_SOFT_BELIEF_AUDIT` (zero-decoder soft-belief audit R1).
