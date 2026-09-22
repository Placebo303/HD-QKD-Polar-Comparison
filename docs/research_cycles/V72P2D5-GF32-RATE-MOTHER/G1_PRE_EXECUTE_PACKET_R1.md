# G1 Pre-EXECUTE Packet R1 — frozen, not authorized

Status:

`G1_PRE_EXECUTE_PACKET_FROZEN / EXECUTE_NOT_AUTHORIZED`

## 4.1 Immutable run contract

| Item | Value |
| --- | --- |
| phase | `g1` |
| authorization key | `g1_execution_authorized` |
| implementation | `cf61ee63` |
| output root | `workspace/v72p2d5_g1/20260907_r2/` |
| width | 64 |
| f | 1.0 then 1.2 |
| rows | L1 49/59; L2 43/52 |
| graph seeds | 2026090501 / 2026090502 |
| block seeds | 2026090600..2026090699, same ordered 100 for both f |
| oracle | first 20 per f, diagnostic only |
| decoder | historical GF32, cold, max_iter 90, damping 1.0 |
| calls | 440 |
| scientific wall gate | operator outer wall `<=900 s` |
| process watchdog | 960 s, kill grace 30 s |
| RSS gate | measured run peak `<2147483648`; None fails resource gate |
| outputs | exactly four no-overwrite scalar files |
| attempts | exactly one after explicit user authorization; attempt consumes authorization |

## 4.2 Exact command

Freeze exactly, with cwd at repository root:

```powershell
& 'C:\Program Files\Git\usr\bin\timeout.exe' -k 30 960 python scripts/v72p2d5_gf32_rate_mother.py --phase g1
```

No flags, parameters, seeds, output-root override, retry, rerun, resume, or tuning.

## 4.3 Mandatory independent Pre-EXECUTE checks

The independent reviewer must freshly verify all of these after this packet is committed and before authorization:

1. branch and scoped code/OpenSpec/review provenance;
2. `cf61ee63` is the implementation under review;
3. all nine authorizations false; promotion false; next gate is the independent G1 review;
4. retained VOID root unchanged; fresh G1 root and G2 root absent;
5. accepted Model-F root exists and remains accepted;
6. core and both scripts compile;
7. exact three pytest files pass with a fresh basetemp under `workspace/`;
8. live unpatched `_rss_bytes()` returns positive int; PMC size 72;
9. watchdog path exists and a harmless 3-second rehearsal returns 124;
10. no content diff outside the explicitly accepted implementation/docs scope;
11. test isolation: every authorized synthetic test call has fake decoder, injected arrays, and tmp output;
12. true script-launch reachability probe from a Python file outside the repo, with cwd at repo root and **no sys.path insertion**:
    - repo root absent from `sys.path`;
    - `import comparison_bench` fails;
    - accepted real Model-F input loads through the file-path consumer;
    - first-call sentinel fires exactly once before any real decoder call;
    - tmp output stays empty;
    - fresh G1 and G2 roots remain absent;
13. re-stat all formal roots after checks and require exact equality.

No Pre-EXECUTE reviewer may flip authorization or run G1.

## 4.4 Authorization protocol

Only after `G1_PRE_EXECUTE_REVIEW_PASS`, the user must explicitly authorize one attempt in a new message. The execution session then:

1. records the exact user authorization;
2. creates a scoped authorization record;
3. flips only `g1_execution_authorized: false→true` and commits it;
4. runs the exact command once under an operator stopwatch;
5. immediately flips only that key back to false, records exit code and outer wall, and commits the consumed-attempt return;
6. never retries, regardless of refusal, exception, timeout, nonfinite, resource failure, partial root, or no-signal result.

## 4.5 Terminal outcome precedence

Frozen seven labels and order from packet review:

1. `G1_PRE_EXECUTION_BLOCKED`
2. `G1_WATCHDOG_TIMEOUT_VOID`
3. `G1_NONFINITE_OR_CRASH_BLOCKED`
4. `G1_OVERRUN_900S`
5. `G1_RESOURCE_OVERRUN`
6. `G1_TREND_PASS`
7. `G1_COMPLETED_NO_SIGNAL_FAIL`

For normally completed output, `passed=true` iff `G1_TREND_PASS`. Operator outer wall over 900 s overrides a stored pass. Any partial root is retained in place and marked VOID; no deletion, overwrite, normalization, or reuse.

## 4.6 Signal and claims

Frozen signal:

```text
zero nonfinite
AND APP rates nondecreasing
AND top APP exact count > 0
AND (top exact count > low exact count OR both counts == attempted)
```

No 50%/90% threshold belongs to G1. Oracle is diagnostic. No outcome is FER, real-data performance, leakage, key rate, qualification, promotion, or G2 authorization.

## 4.7 Required operator return

Require exact command, invocation count, exit code, operator outer wall, watchdog result, output-root listing/stat, full `results.json` scalar payload, per-f exact/syndrome/iteration/nonfinite/RSS values, run peak RSS, stored wall, outcome/passed, arithmetic recomputation, pre/post roots, authorization restored false, and true/false no-rerun/no-data/no-G2/no-push checklist.

No result acceptance before independent Pre-RESULT review.
