# D5-G1-PREEXECUTE-REVIEW-R1 — independent final review before authorization

## 0. Role, scope, and verdict

Independently review the frozen G1 execution contract and the accepted
implementation. This task is read-only except for one review report and its own
temporary test/probe directories.

Return exactly one verdict:

- `G1_PRE_EXECUTE_REVIEW_PASS` — ready for the user to consider a separate,
  explicit one-attempt authorization; or
- `G1_PRE_EXECUTE_REVIEW_FAIL` — name every blocking deviation and stop.

PASS is not authorization, execution, result acceptance, scientific
qualification, or permission for G2. The reviewer may not flip any lifecycle
or authorization field and may not invoke G1.

## 1. Frozen baseline and sources of truth

- Repository: `D:/Code/HD-QKD_Polar_Comparison`
- Branch: `formal-ir-v72p1-addendum-clean`
- Docs-freeze commit: `6494b623`
- Accepted implementation: `cf61ee63f5b76b0223838717b1344e0e7c3867ee`
- Frozen contract:
  `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/G1_PRE_EXECUTE_PACKET_R1.md`
- Implementation acceptance:
  `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/G1_IMPLEMENTATION_ACCEPTANCE_R1.md`
- Packet review:
  `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/G1_PACKET_REVIEW_R1.md`
- Code review and scope addendum:
  `G1_READINESS_CODE_REVIEW_R1.md` and
  `G1_READINESS_CODE_REVIEW_SCOPE_ADDENDUM_A1.md`
- Relevant OpenSpec change:
  `openspec/changes/v72p2d5-g1-readiness/` (use the actual accepted change name
  found in commit `d47e7da1`; a name mismatch is not permission to guess).

Read the actual files, diffs, current source, and tests. Do not accept prior
self-reported PASS text as evidence without verification.

Before any test or probe, capture:

1. branch, HEAD, recent relevant commits, and content-diff state;
2. all nine `*_execution_authorized` values, `scientific_promotion`,
   `next_gate`, P0 acceptance scope, and accepted G1 fields;
3. top-level name/size/mtime snapshots of P0, VOID-G1, proposed G1, G2, G0,
   G0-recovery, Model-F, and structure formal roots.

Required initial lifecycle:

- all nine execution authorizations false;
- `scientific_promotion: false`;
- P0 accepted only as `COST_MEASUREMENT_ONLY`;
- `next_gate: INDEPENDENT_G1_PRE_EXECUTE_REVIEW`;
- accepted G1 implementation is exactly `cf61ee63...`;
- proposed root is exactly `workspace/v72p2d5_g1/20260907_r2` and absent;
- G2 root absent;
- retained `workspace/v72p2d5_g1/20260906_r1` remains VOID and unchanged.

Any deviation in those lifecycle facts is a blocking STOP.

## 2. Hard prohibitions

- Do not invoke any CLI `--phase`, including a refusal probe.
- Do not run a production decoder or bind the historical decoder.
- Do not run Model-F prepare/verify.
- Do not read CAL/VAL/parquet/raw rows.
- Do not read or cite numbers from the retained VOID-G1 root.
- Do not create, delete, move, rename, overwrite, hash, or normalize any formal
  evidence root or file.
- Do not edit `.py`, existing `.md`, OpenSpec, `cycle_state.yaml`, decision log,
  or memory.
- Do not run git add/commit/push/reset/stash/checkout/clean/rebase/revert/amend
  or line-ending normalization.
- Do not repair findings. Any blocking deviation means STOP.
- Do not ask for or manufacture execution authorization.

The only durable new file allowed is:

`docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/G1_PRE_EXECUTE_REVIEW_R1.md`

A unique pytest basetemp under `workspace/` and external OS-temp probe files are
allowed. Resolve and verify their exact paths before deleting only those
review-owned paths.

## 3. Contract and provenance audit

Independently verify:

### P01 — provenance and scope

- `4bf2682a` introduced exactly the frozen G1 execution packet.
- `d47e7da1`, `614aab9e`, and `cf61ee63` have the documented roles and scoped
  file manifests.
- `6494b623` contains exactly the seven documented acceptance/freeze paths and
  no production code.
- Current production content for the G1 implementation equals the accepted
  `cf61ee63` content. Later docs-only commits are allowed.
- There is no real content diff outside accepted scope. Because this checkout
  has known CRLF status churn, use `git diff --numstat` and
  `git diff --cached --numstat` plus explicit path manifests; report porcelain
  counts only as informational. Do not normalize or clean the tree.

### P02 — immutable execution contract

Verify the packet and current code/tests agree on all of the following:

- phase `g1`; authorization key `g1_execution_authorized`;
- unique new root `workspace/v72p2d5_g1/20260907_r2`;
- width 64; `f` order 1.0 then 1.2;
- L1 rows 49/59 and L2 rows 43/52;
- one natural-prefix max mother per level and `f`;
- graph seeds 2026090501/2026090502;
- ordered paired block seeds 2026090600..2026090699, 100 per `f`;
- oracle first 20 per `f`, diagnostic only;
- historical GF32, cold start, `max_iter=90`, damping 1.0;
- exactly 440 decoder calls;
- Model-F fixed accepted input root;
- L1 then L2 even when L1 is not exact;
- exactly four no-overwrite scalar output files;
- scientific operator wall gate `<=900 s`;
- process watchdog 960 s with 30 s kill grace;
- run peak RSS must be known and `<2147483648` bytes;
- one attempt only after a later explicit user authorization; attempt, not
  success, consumes authorization; no retry/rerun/resume/tuning.

### P03 — signal, outcome, and claims

Verify the prospective signal is exactly:

```text
zero nonfinite
AND APP rates nondecreasing
AND top APP exact count > 0
AND (top exact count > low exact count OR both counts == attempted)
```

Verify outcome precedence and exact labels:

1. `G1_PRE_EXECUTION_BLOCKED`
2. `G1_WATCHDOG_TIMEOUT_VOID`
3. `G1_NONFINITE_OR_CRASH_BLOCKED`
4. `G1_OVERRUN_900S`
5. `G1_RESOURCE_OVERRUN`
6. `G1_TREND_PASS`
7. `G1_COMPLETED_NO_SIGNAL_FAIL`

For normal completed output, `passed=true` iff `G1_TREND_PASS`. Confirm no
50%/90% threshold, no oracle decision role, and no FER/leakage/key-rate/
qualification/promotion/G2 claim.

## 4. Fresh executable checks that do not execute G1

### E01 — compile

Compile the current core and both D5 scripts named by the accepted review. A
nonzero exit is blocking.

### E02 — exact three-file test scope

Use one fresh unique basetemp under `workspace/`, `-p no:cacheprovider`, and
run exactly these three pytest files together:

```text
comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py
comparison_bench/tests/test_v72p2d5_model_f_input.py
comparison_bench/tests/test_v72p2d4_cal_gf32_model_rate_audit.py
```

Require zero failures. The known `Unknown config option: cache_dir` warning is
benign. Record the exact command and literal summary line. Re-stat formal roots
afterward, then remove only the validated review basetemp.

### E03 — live Windows RSS

Without monkeypatching, call current `_rss_bytes()` directly. Require
`type(value) is int` and `value > 0`. Independently verify
`sizeof(PROCESS_MEMORY_COUNTERS)==72`, and that the three ctypes signatures are
set before invocation. Record the literal live value. `None`, zero, fabricated
fallback, or wrong ABI is blocking.

### E04 — watchdog rehearsal

Require this exact binary to exist:

`C:\Program Files\Git\usr\bin\timeout.exe`

Run only the harmless rehearsal using that absolute binary, `-k 30 3`, and a
Python process that sleeps for 10 seconds. Require exit 124. This is not the G1
command. Record binary stat, exact rehearsal command, and exit code.

Then verify the frozen future command character-for-character:

```powershell
& 'C:\Program Files\Git\usr\bin\timeout.exe' -k 30 960 python scripts/v72p2d5_gf32_rate_mother.py --phase g1
```

Do not run it.

### E05 — test isolation audit

Inspect every test call that sets `authorized=True` for the D5 synthetic path.
Require all three simultaneously:

1. fake/sentinel decoder explicitly supplied;
2. synthetic `counts_ab` and `p_b` explicitly injected;
3. output directed to a test-owned temporary path.

No authorized test path may bind the production decoder or formal output root.
SAFE A/B/C, TIS, and the absence-assertion tripwire must remain effective.

### E06 — true script-launch Model-F reachability probe

This probe is deliberately allowed to read only the accepted Model-F NPZ via
the production consumer. It must not decode or write formal evidence.

Create a short Python probe file outside the repository in a unique OS-temp
directory. Run it with cwd at repository root, with no `PYTHONPATH` change and
no `sys.path` insertion. The probe must:

1. print `sys.path[0]`, cwd, and whether repo root is on `sys.path`;
2. require repo root absent from `sys.path`;
3. attempt ordinary `import comparison_bench` and require
   `ModuleNotFoundError`;
4. load the G1 core by its production file-path mechanism;
5. call the synthetic G1 entry with `authorized=True`, a unique first-call
   sentinel `decode_fn`, a test-owned temp output, and **without injecting
   `counts_ab` or `p_b`**, so the accepted real Model-F input must traverse the
   production file-path consumer;
6. have the sentinel raise immediately on the first decoder call and record
   exactly one call; this proves reachability but prevents any real decoder;
7. require the exception identity/message to be the unique sentinel, not a
   loader/path/data error;
8. require the temp output directory to remain empty;
9. require proposed G1 and G2 formal roots to remain absent.

The probe may inspect only keys/shapes needed by production validation; do not
print or retain Model-F array values. Remove only the validated external probe
directory and its test output after recording literal stdout/stderr/exit.

Failure to reach the sentinel, more than one call, any historical decoder bind,
any output file, or any formal-root change is blocking.

## 5. Final root and lifecycle gate

After all checks, repeat the initial lifecycle extraction and all root stat
snapshots. Require exact equality, except that review-owned temporary paths
must be gone. In particular:

- VOID-G1 remains unchanged and uncited numerically;
- proposed G1 remains absent;
- G2 remains absent;
- all nine authorizations remain false;
- `next_gate` remains `INDEPENDENT_G1_PRE_EXECUTE_REVIEW`;
- no tracked or staged content change was introduced.

Any deviation means `G1_PRE_EXECUTE_REVIEW_FAIL` and STOP.

## 6. Review report

Create only `G1_PRE_EXECUTE_REVIEW_R1.md`, containing:

1. reviewer role, baseline, and non-authorization statement;
2. P01–P03 table with PASS/FAIL and evidence locations;
3. E01–E06 table with exact commands and literal outputs;
4. all frozen parameters, signal, outcomes, budgets, and attempt semantics;
5. live RSS value and ABI result;
6. watchdog rehearsal and frozen-command comparison;
7. full test command and literal summary;
8. reachability probe output and why it cannot call the real decoder;
9. pre/post root and lifecycle comparison;
10. blocking and non-blocking findings;
11. explicit did/did-not checklist;
12. one final verdict token.

Do not commit the report. Do not update lifecycle state. A PASS report only
allows the main thread to ask the user for a separate explicit authorization.

## 7. Stop rules

Immediately STOP, make no repair, and return the failing item plus raw output
if any of these occurs:

- baseline/lifecycle/root mismatch;
- accepted implementation content mismatch;
- compile or test failure;
- live RSS is not a positive real integer or PMC size is not 72;
- watchdog rehearsal is not 124;
- reachability sentinel is not reached exactly once;
- production decoder or any `--phase` is invoked;
- formal output appears or changes;
- unauthorized tracked/staged content appears;
- a requirement is ambiguous enough to change execution semantics.

## 8. Return format

Report:

1. verdict;
2. P01–P03 and E01–E06 status;
3. compile and pytest literal lines;
4. live RSS/PMC result;
5. watchdog rehearsal and exact frozen command verification;
6. reachability probe literal output;
7. pre/post root and lifecycle equality;
8. blocking/non-blocking findings;
9. true/false list for every prohibition;
10. the sole created review-file path and confirmation of no commit/push.

End exactly:

`G1 Pre-EXECUTE 评审不构成授权；G1 未执行；新 G1 根与 G2 根仍不存在。`

