# D7-B operator return R2 (literal facts; NOT_ACCEPTED / PRE_RESULT_REVIEW_REQUIRED)

## Status

`NOT_ACCEPTED / PRE_RESULT_REVIEW_REQUIRED`

This document records literal facts only. It accepts nothing. Independent
Pre-RESULT R2 (R01–R18) is required before any result root/return is committed
as a result.

## 1. Execution provenance and exact process evidence

- Sole R2 UUID: `c605d1e6-8577-4c52-a865-12500fc8c964` (single
  `/proc/sys/kernel/random/uuid` read; old UUID
  `0f1ad3ec-f9e0-463f-a7dd-d9880ff7230c` permanently dead, never reused).
- Exact child argv (preserved exactly; no added args/PYTHONPATH/pipes/tee):

```bash
timeout -k 30 1800 python scripts/v72p2d7_gf32_easy_regime.py --out-root workspace/d7_b_easy_regime_c605d1e6-8577-4c52-a865-12500fc8c964
```

- Interpreter resolution (R1-documented wrapper equivalence, not a science
  change): bare `python` absent on default PATH; timing harness spawned the
  child with PATH prepended by the project venv bin, so `python` resolved to
  the reviewed interpreter (CPython 3.12.3, NumPy 2.4.4). No PYTHONPATH, no
  science env vars, no argv change.
- CWD: repo root derived at runtime (current WSL checkout), branch
  `formal-ir-v72p1-addendum-clean`.
- `command_invocations: 1` (exactly one scientific invocation; E12 disposable
  probe and E11 bind probe invoked zero decoder calls and created zero roots).
- `scientific_attempt_consumed: true` (64 invoked decoder calls evidenced in
  `decoder_records.csv`; see §4).
- Timing (harness-captured):
  - Start local: `2026-09-10 20:33:32 CST`; start UTC: `2026-09-10 12:33:32 UTC`.
  - End local: `2026-09-10 20:33:38 CST`; end UTC: `2026-09-10 12:33:38 UTC`.
  - Outer wall: `5.396` s. 124-timeout flag: NO (exit 0, not the watchdog).
- Process exit code: `0`.
- Literal stdout (complete):

```
terminal=D7_B_RESOURCE_OVERRUN out=workspace/d7_b_easy_regime_c605d1e6-8577-4c52-a865-12500fc8c964
```

- Literal stderr (complete): empty.
- Authorization lifecycle: authorize `0327c65` (record + state false→true) →
  exactly one invocation (exit 0, wall 5.396 s) → revoke `3fe63ef` (state
  true→false, committed alone before this return was written). Current
  `d7b_execution_authorized: false`. Both commits local-only, no push.

## 2. Root inventory (new R2 root only; immutable post-exit)

- Root: `workspace/d7_b_easy_regime_c605d1e6-8577-4c52-a865-12500fc8c964/`
  (fresh, was ABSENT before launch and after the authorization commit).
- Exactly five files, zero subdirectories (`find -mindepth 1 -type d | wc -l`
  → 0):

| file | size (bytes) | mtime |
|---|---|---|
| `command_log.txt` | 111 | 2026-09-10 20:33 |
| `decoder_records.csv` | 44743 | 2026-09-10 20:33 |
| `manifest.json` | 1008 | 2026-09-10 20:33 |
| `report.md` | 80 | 2026-09-10 20:33 |
| `summary.json` | 449 | 2026-09-10 20:33 |

- No-subdirectory check: PASS. No other `workspace/d7_b_easy_regime_*` root
  exists (exactly one D7-B result root: this R2 root). R1d/G2 roots absent
  (`workspace/*v72p2d7*` → no such file besides this root's own prefix match;
  this root is the sole match).
- `command_log.txt` literal: `scripts/v72p2d7_gf32_easy_regime.py --out-root
  workspace/d7_b_easy_regime_c605d1e6-8577-4c52-a865-12500fc8c964`.
- No R1d, formal, VOID, Model-F, CAL, VAL, or real/raw contents were read
  (metadata-only directory checks plus frozen D7-B code/packet/prereg reads).

## 3. Frozen manifest identity

`manifest.json` matches the frozen R1+A1 contract:

- `change: v72p2d7-gf32-easy-regime`, `contract: R1+A1`.
- tiers `["SINGLE_CHECK_D3","TREE_6","CYCLE_8","FULL_RANK_64"]`.
- priors `["P99","P90","P60","PAIR"]`.
- seeds `[2026091200,2026091201,2026091202,2026091203]`.
- caps `[1,2,4,8,16,32,90]`; `call_budget: 420`.
- `per_call_watchdog_s: 120.0`; `run_wall_limit_s: 1500.0`;
  `outer_watchdog_s: 1800.0`; `rss_limit_bytes: 2147483648`.
- `post_tol: 1e-10`.
- `tree_6_active` rows `[3,3,2]`, c0 `[0,1,2]`, c1 `[2,3,4]`, c2 `[4,5]`,
  coeffs `[[1,7,13],[29,1,7],[13,29]]` (A1 replacement; superseded `[2,3,2]`
  retained under `superseded_rejected` with proof `7<8`).

## 4. Scheduled / invoked / not-needed / budget arithmetic

- `decoder_records.csv`: 448 data rows (header + 448) = 64 cells × 7 caps.
- `summary.json`: `cells_scheduled: 64`, `calls_invoked: 64`,
  `calls_not_needed: 384`, `cells_budget_not_reached: 0`,
  `budget_exhausted: false`.
- Recomputed from CSV: INVOKED 64, `NOT_NEEDED_AFTER_EXACT` 384;
  64 + 384 = 448. `budget_exhausted` false consistent with 64 ≤ 420.
- Budget NOT reached (64 calls vs 420-call global stop). No
  `D7_B_CALL_BUDGET_EXHAUSTED` terminal.
- Per-cell caps present: `[1,2,4,8,16,32,90]` in all 64 cells (7 rows each).

## 5. Stored terminal and aggregate flags

- Stored terminal: `D7_B_RESOURCE_OVERRUN` (summary + report agree; stdout
  agrees).
- Aggregate flags: `resource_overrun: true`, `tractable_violation: true`;
  `budget_exhausted/confirmed/crash_nonfinite/p99_fail/partial/pre_blocked/
  watchdog_timeout` all false.
- Terminal priority (frozen T1–T9): resource-overrun outranks the tractable
  violation signal; no success/confirmation verdict is stored (`confirmed:
  false`).

## 6. Per-tier / per-prior / per-seed outcomes (first-exact-cap + exact/syndrome)

- 64/64 invoked calls `exact: True`, `syndrome_ok: True`, status
  `converged_exact` (64/64). Zero `finite: False`.
- First-exact-cap distribution over 64 cells: cap 1 → 64 cells (all cells
  exact at the first rung; higher caps all `NOT_NEEDED_AFTER_EXACT`).
- Per tier (16 invoked each: 4 priors × 4 seeds, all at cap 1):
  - SINGLE_CHECK_D3: 16/16 exact, 16/16 syndrome_ok.
  - TREE_6: 16/16 exact, 16/16 syndrome_ok.
  - CYCLE_8: 16/16 exact, 16/16 syndrome_ok.
  - FULL_RANK_64: 16/16 exact, 16/16 syndrome_ok.
- `unsat` nonzero: 0. `sym_err` nonzero: 0. Iterations: all invoked rows
  report numeric iterations with exact convergence (status
  `converged_exact`).

## 7. Tractable posterior / MAP errors

- Tractable tiers (exact posteriors stored): SINGLE_CHECK_D3, TREE_6.
  CYCLE_8 / FULL_RANK_64 carry no `post_err` (empty, as frozen).
- SINGLE_CHECK_D3 (n=16): `post_err` min `1.16e-16`, max `0.50033`;
  `map_agree` False count 0.
- TREE_6 (n=16): `post_err` min `0.00689`, max `0.39966`; `map_agree`
  False count 0.
- Frozen tolerance `1e-10`: maxima exceed tolerance → `tractable_violation:
  true` is consistent with the stored rows (recomputed, not trusted from
  summary).

## 8. Crash / nonfinite / status accounting

- Status counter over invoked: `converged_exact: 64`. No crash/exception
  strings (0). `finite: False` count 0. `crash_nonfinite: false` consistent.
- No watchdog rows; `watchdog_timeout: false` consistent.

## 9. Call, wall, watchdog, and RSS comparisons

- Stored run wall: `4.970117854000819` s (limit 1500 s) — within budget.
- Outer wall (harness): `5.396` s (outer 1800 s + 30 s grace) — far below;
  exit 0, not 124.
- Max per-call `wall_s` over invoked: `0.00431` s (limit 120 s/call) — within
  budget, no per-call watchdog event.
- RSS: all 64 invoked rows have empty `rss_bytes` (venv has no psutil; frozen
  `_rss_bytes()` returns null). `RSS_NONEMPTY: 0`. Per frozen code, null RSS
  rows set `resource_overrun: true`, mapping to terminal
  `D7_B_RESOURCE_OVERRUN` under frozen T1–T9 priority (environment fact
  pre-recorded in the R1 record §2 and preserved here; never repaired).
  Limit `<2GiB` (2147483648) never evaluated against a known value.

## 10. Boundary compliance

- Exactly one scientific invocation and exactly one read-only verifier
  invocation (§11).
- No R1d, no `--phase`, no G1/G2, no Model-F/CAL/VAL/real/raw/VOID/formal
  content reads.
- No edits to v35/D5/D7-A/D7-B code, tests, OpenSpec, or frozen packets.
- Result root unmodified post-exit (read-only inspection only).
- No broad git operations, no push. Pre-existing unrelated dirty/CRLF paths
  outside scope preserved untouched.

## 11. Verifier (§7 outcome)

- One read-only non-decoder invocation (the sole verifier invocation):

```bash
python scripts/v72p2d7_gf32_easy_regime.py --verify workspace/d7_b_easy_regime_c605d1e6-8577-4c52-a865-12500fc8c964
```

- Literal output (complete):

```
VERIFY_OK {'ok': True, 'problems': [], 'records': 448, 'invoked': 64, 'terminal': 'D7_B_RESOURCE_OVERRUN'}
```

- Exit: `0`. Root sizes/mtimes unchanged after verify (read-only; see §2
  table — identical before/after).
- Verifier limits (disclosed): the verifier recomputes schema/terminal/
  accounting from the stored five files; it does not re-run the decoder, does
  not attest to scientific correctness beyond internal consistency, and does
  not convert the resource terminal into a pass.

## 12. Forbidden claims (explicitly NOT claimed)

- No FER, leakage, key-rate, qualification, or actual-channel recovery claim.
- No easy-regime confirmation/partial/alert success verdict (`confirmed:
  false`; terminal is a resource terminal, not a scientific pass).
- No decoder certification or performance conclusion of any kind.
- The `D7_B_RESOURCE_OVERRUN` terminal is a frozen-code resource mapping on
  this host (null RSS), not a scientific observation about the decoder.

(End of file — uncommitted; awaits independent Pre-RESULT R2 review.)
