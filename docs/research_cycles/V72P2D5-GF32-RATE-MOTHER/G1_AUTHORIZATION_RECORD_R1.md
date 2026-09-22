# G1 Authorization Record R1 — one frozen attempt authorized

## 1. Verbatim user authorization

> 我现在明确授权执行 G1：授权对冻结的 g1 命令进行且仅进行一次调用；授权由“尝试”消耗而非由“成功”消耗；不许重试、不许重跑、不许恢复、不许修改任何参数；不许执行 G2。

## 2. Initial branch/HEAD/lifecycle/root evidence (STEP 1 gate literals)

- Branch: `formal-ir-v72p1-addendum-clean`
- HEAD: `6494b623629746821d7bf445c25068ae2225c09c` (short `6494b623`)
- `git log --oneline -3`: `6494b623 docs(v72p2d5): accept G1 readiness and freeze Pre-EXECUTE packet` / `cf61ee63 fix(v72p2d5): declare WinAPI ctypes signatures for live G1 RSS` / `614aab9e feat(v72p2d5): implement G1 readiness metrics, outcome, and fresh root`
- `git diff cf61ee63 -- <core + 2 tests>` empty, `LASTEXITCODE=0`; `--stat` empty
- `git diff --numstat` empty (`NUMSTAT_END EXIT=0`); `git diff --cached --numstat` empty (`CACHED_END EXIT=0`); residual CRLF warnings informational only, no normalization performed
- All nine `*_execution_authorized` false: structure/g0/g0_recovery/p0_cost/g1/g2/synthetic/real/formal
- `scientific_promotion: false`; `next_gate: INDEPENDENT_G1_PRE_EXECUTE_REVIEW`
- `g1_accepted_implementation: cf61ee63f5b76b0223838717b1344e0e7c3867ee`; `g1_formal_root: workspace/v72p2d5_g1/20260907_r2`; `model_f_input_root: workspace/v72p2d5_model_f_input/20260907_r1`
- Proposed `workspace/v72p2d5_g1/20260907_r2` absent (`Test-Path False`); G2 `workspace/v72p2d5_g2` absent (`Test-Path False`); VOID `workspace/v72p2d5_g1/20260906_r1` present (`Test-Path True`)
- Protected roots pre-stat: `v72p2d5_g1/` → `[20260906_r1]` (`2026-09-07T02:35:32`); VOID `20260906_r1/` → `execution_summary.json 267` / `report.md 146` / `results.json 2593` / `table.csv 126` (all `2026-09-07T02:35:32`); P0 `[20260906_r1]`; G0 `[20260905_r2]`; G0-recovery `[20260906_r1]`; Model-F `[20260907_r1]` (`model_f_input_summary.json 752` + `model_f_input.npz 208467`, `2026-09-07T02:07:07`); Structure `[20260905_r2]` — matches Pre-EXECUTE review §8 snapshot
- Watchdog binary `C:\Program Files\Git\usr\bin\timeout.exe` present, `Length=41752`
- No pytest/compile/probe/rehearsal rerun (frozen fresh evidence in passing review; no accepted source changed)

## 3. Accepted implementation and passing Pre-EXECUTE review

- Accepted implementation: `cf61ee63f5b76b0223838717b1344e0e7c3867ee`
- Frozen packet: `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/G1_PRE_EXECUTE_PACKET_R1.md` (`G1_PRE_EXECUTE_PACKET_FROZEN / EXECUTE_NOT_AUTHORIZED`)
- Passing review: `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/G1_PRE_EXECUTE_REVIEW_R1.md`, sole final verdict `G1_PRE_EXECUTE_REVIEW_PASS` (§11 line 98; no `G1_PRE_EXECUTE_REVIEW_FAIL`); review file uncommitted from prior turn, staged byte-for-byte unchanged with this record

## 4. Exact frozen command (cwd = repository root, run exactly once)

```powershell
& 'C:\Program Files\Git\usr\bin\timeout.exe' -k 30 960 python scripts/v72p2d5_gf32_rate_mother.py --phase g1
```

Byte-identical to packet §4.2 frozen block. No flags, parameters, seeds, output-root override, retry, rerun, resume, or tuning.

## 5. Frozen run contract

- Decoder calls: exactly `440`
- Scientific operator-wall gate: outer wall `<=900 s`
- Process watchdog: `960 s` with `30 s` kill grace (`-k 30 960`)
- RSS gate: measured run peak known and `<2147483648` bytes (`<2 GiB`); `None` fails resource gate
- Signal (packet §4.6): `zero nonfinite AND APP rates nondecreasing AND top APP exact count > 0 AND (top exact count > low exact count OR both counts == attempted)`
- Outcome precedence (packet §4.5, seven labels in frozen order): 1 `G1_PRE_EXECUTION_BLOCKED` > 2 `G1_WATCHDOG_TIMEOUT_VOID` > 3 `G1_NONFINITE_OR_CRASH_BLOCKED` > 4 `G1_OVERRUN_900S` > 5 `G1_RESOURCE_OVERRUN` > 6 `G1_TREND_PASS` > 7 `G1_COMPLETED_NO_SIGNAL_FAIL`; normal completed `passed=true iff G1_TREND_PASS`
- Four no-overwrite scalar files: `results.json`, `table.csv`, `report.md`, `execution_summary.json` under `workspace/v72p2d5_g1/20260907_r2/`

## 6. Attempt consumption and prohibitions

- This authorization is consumed by the single attempt, not by success: exit 0, 124, 3, any other exit, exception, crash, partial root, or missing/malformed evidence all consume it.
- No retry, no rerun, no resume, no reuse of a partial root (retained VOID in place), no parameter/command/cwd/seed/root/budget/watchdog/env/implementation change, no second invocation for any reason.
- No P0/G2/other phase, no prepare/verify, no production decoder outside the single frozen command. No G2 execution.

## 7. Operator obligation

- Immediately after the attempt and BEFORE opening any produced file: flip `g1_execution_authorized: true→false`, verify all nine authorizations false, then stat the proposed root and record the operator return.
- Result is recorded only, not accepted; independent Pre-RESULT review remains required; `next_gate` unchanged.

(End of file)
