# G1 Operator Return R1 — one authorized attempt recorded, not accepted

## 1. Verbatim user authorization and commit/base identities

Verbatim authorization:

> 我现在明确授权执行 G1：授权对冻结的 g1 命令进行且仅进行一次调用；授权由“尝试”消耗而非由“成功”消耗；不许重试、不许重跑、不许恢复、不许修改任何参数；不许执行 G2。

- Fixed baseline HEAD: `6494b623629746821d7bf445c25068ae2225c09c` (short `6494b623`)
- Accepted implementation: `cf61ee63f5b76b0223838717b1344e0e7c3867ee`
- Authorization commit: `f4d577fb6b53cc58a23ada532331a5df3fac357f` (`chore(v72p2d5): authorize one frozen G1 invocation`, 3 paths)
- This return will be committed as `result(v72p2d5): record one authorized frozen G1 invocation` (2 paths)

## 2. Exact command, count, exit, outer wall, stdout, stderr, watchdog

Exact command (cwd = repository root `D:/Code/HD-QKD_Polar_Comparison`, invoked exactly once):

```powershell
& 'C:\Program Files\Git\usr\bin\timeout.exe' -k 30 960 python scripts/v72p2d5_gf32_rate_mother.py --phase g1
```

- Invocation count: `1` (exactly once; never issued again)
- Exit code: `0` (`G1_EXIT=0`)
- Operator outer wall: `239.110 s` (`G1_WALL_S=239.110`, PowerShell stopwatch around the exact line only)
- Child stdout: empty (no lines)
- Child stderr: empty (no lines)
- Watchdog interpretation: `timeout.exe -k 30 960` did not fire (exit `0`, not `124`); no kill grace engaged; normal process completion per packet §4.4/STEP 4 mapping (`0` → continue to STEP 5)

## 3. Output-root listing

`workspace/v72p2d5_g1/20260907_r2/` exists with exactly the normal four-file bundle:

- `execution_summary.json|384|2026-09-08T02:39:50`
- `report.md|246|2026-09-08T02:39:50`
- `results.json|3210|2026-09-08T02:39:50`
- `table.csv|330|2026-09-08T02:39:50`

## 4. Literal scalar payload (normal bundle, packet §4.7)

`results.json` literals:

- `phase: g1`, `block_length: 64`, `formal_root: workspace/v72p2d5_g1/20260907_r2`
- `f_list: [1.0, 1.2]`; `frozen_rows: 1.0 → m1 49 / m2 43; 1.2 → m1 59 / m2 52`
- `seeds: 2026090600..2026090699` (100 ordered seeds, listed literally L64–L165)
- `decoder_calls: 440`; `crashes: 0`; `nonfinite: 0`; `monotonic: true`
- `outcome: G1_COMPLETED_NO_SIGNAL_FAIL`; `passed: false`
- `wall_seconds: 238.86517630005255`; `peak_rss_bytes: 115142656`
- `output_files: [results.json, table.csv, report.md, execution_summary.json]`
- per-f `1.0`: `attempted 100`, `app_exact_count 0`, `app_exact_rate 0.0`, `app_failure_fraction 1.0`, `app_syndrome_ok_count 0`, `app_iterations_total 18000`, `app_iterations_max 180`, `oracle_exact_count 0`, `oracle_syndrome_ok_count 0`, `oracle_iterations_total 1800`, `nonfinite_count 0`, `peak_rss_bytes 114167808`
- per-f `1.2`: `attempted 100`, `app_exact_count 0`, `app_exact_rate 0.0`, `app_failure_fraction 1.0`, `app_syndrome_ok_count 0`, `app_iterations_total 18000`, `app_iterations_max 180`, `oracle_exact_count 0`, `oracle_syndrome_ok_count 0`, `oracle_iterations_total 1800`, `nonfinite_count 0`, `peak_rss_bytes 115142656`

`execution_summary.json` literals: `decoder_calls 440`, `files [results.json, table.csv, report.md, execution_summary.json]`, `formal_root workspace/v72p2d5_g1/20260907_r2`, `monotonic true`, `nonfinite 0`, `outcome G1_COMPLETED_NO_SIGNAL_FAIL`, `passed false`, `peak_rss_bytes 115142656`, `phase g1`, `wall_seconds 238.86517630005255`.

`table.csv` literals:

```text
f,attempted,app_exact_count,app_exact_rate,app_failure_fraction,oracle_exact_count,app_syndrome_ok_count,app_iterations_total,app_iterations_max,oracle_syndrome_ok_count,oracle_iterations_total,nonfinite_count,peak_rss_bytes
1.0,100,0,0.0,1.0,0,0,18000,180,0,1800,0,114167808
1.2,100,0,0.0,1.0,0,0,18000,180,0,1800,0,115142656
```

`report.md` literals: `phase g1`, `outcome G1_COMPLETED_NO_SIGNAL_FAIL`, `passed False`, `monotonic True`, `nonfinite 0`, `decoder_calls 440`, `peak_rss_bytes 115142656`, `wall_seconds 238.86517630005255`, `formal_root workspace/v72p2d5_g1/20260907_r2`.

## 5. Arithmetic-only recomputation (no interpretation)

- 440 call identity: per f, APP `18000/180 = 100` calls + oracle `1800/90 = 20` calls = 220/f; `220 × 2 = 440` = stored `decoder_calls 440`. Holds.
- Failure fractions: per f `1 - 0/100 = 1.0` = stored `app_failure_fraction 1.0`; `0/100 = 0.0` = stored `app_exact_rate 0.0`. Holds.
- Attempted/count bounds: `0 ≤ 100` for every exact/syndrome count vs `attempted 100`. Holds.
- Iteration bounds: `app_iterations_max 180 = 2 mothers × max_iter 90`; `18000 = 100 × 180`; oracle `1800 = 20 × 90`. Within frozen `max_iter 90` arithmetic. Holds.
- Signal predicate: `nonfinite 0` (zero ✓) AND rates `(0.0, 0.0)` nondecreasing ✓ AND top APP exact `0 > 0` ✗ → signal FALSE.
- Stored outcome consistency: signal FALSE + normal completion + wall/RSS gates met → `G1_COMPLETED_NO_SIGNAL_FAIL`, `passed=false`; `passed=true iff G1_TREND_PASS` → false consistent. Holds.
- Stored wall vs 900 s: `238.865 ≤ 900`. Holds, no `G1_OVERRUN_900S`.
- Operator outer wall vs 900 s: `239.110 ≤ 900`. Holds.
- RSS: run peak `115142656` known (not None) and `115142656 < 2147483648`. Holds; per-f peaks `114167808`/`115142656`, run peak equals max. Holds.
- `crashes 0`, `nonfinite 0` consistent with normal completion.

## 6. Operator-override need

None. Operator outer wall `239.110 s ≤ 900 s` does not override the stored outcome. No later Pre-RESULT override of the stored outcome is required on wall grounds (outer wall exceeds stored `wall_seconds 238.865` by `0.245 s` of wrapper overhead only, far below the gate).

## 7. Absent/partial state

Not applicable: the root is a complete normal four-file bundle. Nothing is labeled VOID/BLOCKED; no value was manufactured — every scalar above is a literal file read.

## 8. Pre/post protected-root comparison and G2 absence

- VOID `workspace/v72p2d5_g1/20260906_r1/`: `execution_summary.json 267` / `report.md 146` / `results.json 2593` / `table.csv 126`, all `2026-09-07T02:35:32` — character-identical pre/post. Content never opened.
- P0 `20260906_r1`, G0 `20260905_r2`, G0-recovery `20260906_r1`, Model-F `20260907_r1` (`752` + `208467`), Structure `20260905_r2`: names/sizes/mtimes identical pre/post.
- Sole workspace change: one-time additive `workspace/v72p2d5_g1/20260907_r2` (`2026-09-08T02:39:50`) created by the authorized command.
- G2 `workspace/v72p2d5_g2`: absent pre and post (`Test-Path False`). G2 never executed.

## 9. Authorization restored and prohibitions

- `g1_execution_authorized: true→false` restored before any produced file was opened; all nine `*_execution_authorized` now false (`TRUECOUNT=0`).
- No retry/rerun/resume/second invocation (count exactly 1); no command/cwd/seed/parameter/root/budget/watchdog/env/implementation change; no P0/G2/other phase, no prepare/verify, no production decoder outside the single command; no CAL/VAL/parquet/raw read; no delete/move/rename/overwrite/normalize/hash/repair under `workspace/`; no `.py`/OpenSpec/frozen packet/existing review/decision-log/memory/unrelated edit (working `git diff --numstat` 0 lines; porcelain ` M` entries are the known pre-existing CRLF churn, informational); no `next_gate`/promotion/acceptance change (`next_gate: INDEPENDENT_G1_PRE_EXECUTE_REVIEW`, `scientific_promotion: false`); no push.

## 10. NOT_ACCEPTED / PRE_RESULT_REVIEW_REQUIRED and nonclaims

`NOT_ACCEPTED / PRE_RESULT_REVIEW_REQUIRED`: this record stores the sole authorized attempt and its literal scalars only. No result is accepted, qualified, or claimed as valid FER, leakage, key rate, or scientific performance; no G2 permission is granted or proposed. Independent Pre-RESULT review remains required before any acceptance or solidification.

(End of file)
