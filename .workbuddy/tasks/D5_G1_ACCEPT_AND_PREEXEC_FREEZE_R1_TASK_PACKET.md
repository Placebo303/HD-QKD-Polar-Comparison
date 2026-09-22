# D5-G1-ACCEPT-AND-PREEXEC-FREEZE-R1 — docs-only acceptance and packet freeze

## 0. Objective

Perform one documentation-only lifecycle transition:

1. land the independent code review and its scope addendum;
2. accept the G1 readiness **implementation only** at `cf61ee63`;
3. freeze the G1 Pre-EXECUTE packet;
4. move `next_gate` to `INDEPENDENT_G1_PRE_EXECUTE_REVIEW`.

This task does not authorize or execute G1 and accepts no G1 result.

## 1. Baseline and STOP conditions

Verify before writing:

- branch `formal-ir-v72p1-addendum-clean`;
- HEAD `cf61ee63` or a documentation-only descendant;
- `G1_READINESS_CODE_REVIEW_R1.md` says
  `G1_READINESS_CODE_REVIEW_PASS`;
- `G1_READINESS_CODE_REVIEW_SCOPE_ADDENDUM_A1.md` says
  `G1_CODE_REVIEW_SCOPE_ADDENDUM_PASS` and reports the exact three pytest files
  with `219 passed`;
- P0 cost accepted only; `next_gate: G1_PACKET_REVIEW`;
- all nine authorizations false and promotion false;
- retained G1 `20260906_r1` unchanged;
- fresh G1 `20260907_r2` and G2 roots absent;
- live `_rss_bytes()` returns a positive integer without decoder execution.

Any deviation is STOP. Do not repair code or evidence.

## 2. Allowed changes

Land unchanged:

- `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/G1_READINESS_CODE_REVIEW_R1.md`
- `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/G1_READINESS_CODE_REVIEW_SCOPE_ADDENDUM_A1.md`

Create:

- `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/G1_IMPLEMENTATION_ACCEPTANCE_R1.md`
- `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/G1_PRE_EXECUTE_PACKET_R1.md`

Modify only:

- `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/cycle_state.yaml`
- `docs/decision-log.md` (append only)
- `AGENT_PROJECT_MEMORY.md` (append only)

No other path.

## 3. Implementation acceptance record

`G1_IMPLEMENTATION_ACCEPTANCE_R1.md` must state:

- accepted implementation: `cf61ee63`, including predecessor `614aab9e` and
  specification/review commit `d47e7da1`;
- review chain: packet review PASS, readiness code review PASS, scope addendum
  PASS (`219 passed`), live Windows RSS positive;
- accepted functionality: fresh root, Windows RSS ABI and 200-sample peak
  semantics, aggregate exact/syndrome/iteration/RSS fields, prospective signal
  rule, outcome precedence, fail-loud writers, no-subdirectory guard, and
  test-only reachability/isolation;
- accepted scope is implementation readiness only;
- no decoder/G1 result/FER/leakage/key-rate/qualification/G2 claim;
- real external-file Model-F sentinel remains mandatory in Pre-EXECUTE;
- watchdog semantics remain mandatory in Pre-EXECUTE;
- implementation acceptance grants no authorization.

Record these disclosed boundaries:

- process wall can exceed stored entrypoint wall; operator outer wall controls
  the 900 s final classification during Pre-RESULT review;
- `app_iterations_max<=180` is asserted/recomputed, not clamped by production;
- Python exception, watchdog timeout, and pre-exec refusal remain operator-side
  labels and do not manufacture a normal four-file result;
- G1 remains synthetic trend evidence, never real FER or qualification.

## 4. Freeze `G1_PRE_EXECUTE_PACKET_R1.md`

### 4.1 Status and immutable run contract

Status:

`G1_PRE_EXECUTE_PACKET_FROZEN / EXECUTE_NOT_AUTHORIZED`

Freeze:

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

### 4.2 Exact command

Freeze exactly, with cwd at repository root:

```powershell
& 'C:\Program Files\Git\usr\bin\timeout.exe' -k 30 960 python scripts/v72p2d5_gf32_rate_mother.py --phase g1
```

No flags, parameters, seeds, output-root override, retry, rerun, resume, or
tuning.

### 4.3 Mandatory independent Pre-EXECUTE checks

The independent reviewer must freshly verify all of these after this packet is
committed and before authorization:

1. branch and scoped code/OpenSpec/review provenance;
2. `cf61ee63` is the implementation under review;
3. all nine authorizations false; promotion false; next gate is the independent
   G1 review;
4. retained VOID root unchanged; fresh G1 root and G2 root absent;
5. accepted Model-F root exists and remains accepted;
6. core and both scripts compile;
7. exact three pytest files pass with a fresh basetemp under `workspace/`;
8. live unpatched `_rss_bytes()` returns positive int; PMC size 72;
9. watchdog path exists and a harmless 3-second rehearsal returns 124;
10. no content diff outside the explicitly accepted implementation/docs scope;
11. test isolation: every authorized synthetic test call has fake decoder,
    injected arrays, and tmp output;
12. true script-launch reachability probe from a Python file outside the repo,
    with cwd at repo root and **no sys.path insertion**:
    - repo root absent from `sys.path`;
    - `import comparison_bench` fails;
    - accepted real Model-F input loads through the file-path consumer;
    - first-call sentinel fires exactly once before any real decoder call;
    - tmp output stays empty;
    - fresh G1 and G2 roots remain absent;
13. re-stat all formal roots after checks and require exact equality.

No Pre-EXECUTE reviewer may flip authorization or run G1.

### 4.4 Authorization protocol

Only after `G1_PRE_EXECUTE_REVIEW_PASS`, the user must explicitly authorize one
attempt in a new message. The execution session then:

1. records the exact user authorization;
2. creates a scoped authorization record;
3. flips only `g1_execution_authorized: false→true` and commits it;
4. runs the exact command once under an operator stopwatch;
5. immediately flips only that key back to false, records exit code and outer
   wall, and commits the consumed-attempt return;
6. never retries, regardless of refusal, exception, timeout, nonfinite, resource
   failure, partial root, or no-signal result.

### 4.5 Terminal outcome precedence

Freeze the seven labels and order from packet review:

1. `G1_PRE_EXECUTION_BLOCKED`
2. `G1_WATCHDOG_TIMEOUT_VOID`
3. `G1_NONFINITE_OR_CRASH_BLOCKED`
4. `G1_OVERRUN_900S`
5. `G1_RESOURCE_OVERRUN`
6. `G1_TREND_PASS`
7. `G1_COMPLETED_NO_SIGNAL_FAIL`

For normally completed output, `passed=true` iff `G1_TREND_PASS`. Operator
outer wall over 900 s overrides a stored pass. Any partial root is retained
in place and marked VOID; no deletion, overwrite, normalization, or reuse.

### 4.6 Signal and claims

Freeze signal:

```text
zero nonfinite
AND APP rates nondecreasing
AND top APP exact count > 0
AND (top exact count > low exact count OR both counts == attempted)
```

No 50%/90% threshold belongs to G1. Oracle is diagnostic. No outcome is FER,
real-data performance, leakage, key rate, qualification, promotion, or G2
authorization.

### 4.7 Required operator return

Require exact command, invocation count, exit code, operator outer wall,
watchdog result, output-root listing/stat, full `results.json` scalar payload,
per-f exact/syndrome/iteration/nonfinite/RSS values, run peak RSS, stored wall,
outcome/passed, arithmetic recomputation, pre/post roots, authorization restored
false, and true/false no-rerun/no-data/no-G2/no-push checklist.

No result acceptance before independent Pre-RESULT review.

## 5. Cycle state change

Keep every existing authorization and promotion value unchanged. Add:

```yaml
g1_packet_review: PASS_R1
g1_implementation_candidate: true
g1_implementation_accepted: true
g1_accepted_implementation: cf61ee63f5b76b0223838717b1344e0e7c3867ee
g1_formal_root: workspace/v72p2d5_g1/20260907_r2
```

Change only:

```yaml
next_gate: G1_PACKET_REVIEW
```

to:

```yaml
next_gate: INDEPENDENT_G1_PRE_EXECUTE_REVIEW
```

Do not add attempts/completed/result fields yet.

## 6. Decision log and memory append

Append a concise durable entry recording implementation-only acceptance,
review chain, new root, frozen signal/outcomes/resources, and next gate. State
explicitly that G1 remains unauthorized/unexecuted and G2 remains unauthorized.

No percentages and no scientific performance claim.

## 7. Verification and commit

No pytest is required in this docs-only task; cite the independent 219-pass
addendum. Run only compile/read-only stat if desired.

Before committing:

- pre/post root snapshots identical;
- fresh G1/G2 roots absent;
- all nine authorization keys false;
- only the seven allowed paths differ;
- `.py` content diff empty;
- existing review files are staged byte-for-byte unchanged;
- decision-log and memory changes are append-only;
- staged list exactly seven paths.

Commit:

```text
docs(v72p2d5): accept G1 readiness and freeze Pre-EXECUTE packet

Co-Authored-By: OpenAI Codex <codex@openai.com>
```

Do not push.

## 8. Return

Report baseline/state, seven staged paths, created/modified files, root
equality, authorization lines, lifecycle delta, commit SHA/status, and
true/false prohibitions.

End:

`G1 readiness 实现已接受且 Pre-EXECUTE 包已冻结；G1 仍未授权、未执行；等待独立 Pre-EXECUTE 评审。`
