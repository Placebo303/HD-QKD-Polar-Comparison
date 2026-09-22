# D5-G1-READINESS-IMPLEMENT-R1 — implement reviewed G1 readiness deltas

## 0. Objective and lifecycle

Implement D1–D6 and acceptance items A01–A13 from
`G1_PACKET_REVIEW_R1.md`. Produce an implementation candidate only.

Status throughout this task:

- `G1_IMPLEMENTATION_CANDIDATE_ONLY`
- `G1_EXECUTION_NOT_AUTHORIZED`
- no P0/G1/G2 phase execution
- no formal G1 output creation
- `next_gate` remains `G1_PACKET_REVIEW`

The operator may implement and test with injected fake decoders, fake arrays,
and temporary output roots only. It must not accept its own work.

## 1. Required baseline and read order

Read completely before editing:

1. `AGENTS.md`
2. `AGENT_PROJECT_MEMORY.md` relevant D5 tail
3. `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/G1_EXECUTION_PACKET_R1.md`
4. `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/G1_PACKET_REVIEW_R1.md`
5. `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/P0_RESULT_ACCEPTANCE_R1.md`
6. `openspec/changes/v72p2d5-p0-g1-g2-production-path/{proposal,design,tasks}.md`
7. the current core and both D5 test files before editing them

Verify before editing:

- branch `formal-ir-v72p1-addendum-clean`;
- `4bf2682a` changes exactly one packet file;
- `G1_PACKET_REVIEW_R1.md` exists and says `G1_PACKET_REVIEW_PASS`;
- P0 accepted cost-only, `next_gate: G1_PACKET_REVIEW`;
- all nine authorization keys and promotion are false;
- retained G1 `20260906_r1` root exists unchanged;
- proposed G1 `20260907_r2` and G2 roots are absent;
- frozen watchdog binary exists and a harmless 3-second rehearsal returns 124.

If any scientific/lifecycle precondition differs, STOP. Do not repair the
baseline.

## 2. Allowed files

Modify only:

- `comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py`
- `comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py`
- `comparison_bench/tests/test_v72p2d5_model_f_input.py`

Create only:

- `openspec/changes/v72p2d5-g1-readiness-rework/proposal.md`
- `openspec/changes/v72p2d5-g1-readiness-rework/design.md`
- `openspec/changes/v72p2d5-g1-readiness-rework/tasks.md`
- `openspec/changes/v72p2d5-g1-readiness-rework/specs/spec.md`

Also land the already-created, read-only reviewer output in the final commit:

- `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/G1_PACKET_REVIEW_R1.md`

No other file may change. Do not edit the review file.

## 3. Hard prohibitions

- No decoder run and no CLI `--phase` invocation, including refusal probes.
- No Model-F prepare/verify replay.
- No CAL/VAL/parquet/raw-row read.
- No write/delete/move/rename/copy/hash/normalization under any existing
  `workspace/v72p2d5_*` evidence root.
- Tests must use explicit fake decoder, injected fake Model-F arrays, and a
  temporary output root. No test may bind the historical decoder or use a
  default formal root.
- Do not change seeds, row tables, width, `f` values, block counts, oracle
  subset, decoder parameters, budgets, G2 grading, Model-F input, or P0/G0
  behavior.
- Do not change `cycle_state.yaml`, decision-log, project memory, frozen result
  documents, baseline `src/`, `experiments/`, `tools/`, or output artifacts.
- No new dependency, process monitor, retry/resume framework, hashes, manifest,
  compatibility layer, or generic result abstraction.
- No push, reset, stash, checkout, clean, rebase, amend, or broad `git add`.

## 4. OpenSpec first

Before code edits, create the four-file change
`v72p2d5-g1-readiness-rework`. It must record the already-decided deltas, not
reopen them:

- fresh root `workspace/v72p2d5_g1/20260907_r2/`;
- Windows current-process working-set RSS via stdlib `ctypes`;
- sample RSS after every completed block result and persist per-`f` and run
  maxima;
- 2 GiB remains a hard G1 gate; `None` is resource failure;
- aggregate exact/syndrome/iteration observability;
- direct fail-loud access to `app_failure_fraction` in G1/G2 writers;
- no-subdirectory invariant in both test helpers;
- reviewed signal rule and seven terminal labels;
- real-launch sentinel remains a Pre-EXECUTE check, not run here.

Mark tasks incomplete first, then check them only after implementation evidence
exists. No code before this OpenSpec skeleton exists.

## 5. Implementation requirements

### I01 — fresh root

Set only:

```python
G1_FORMAL_ROOT = "workspace/v72p2d5_g1/20260907_r2"
```

Update tests owning this literal. Do not change or touch the old VOID root.

### I02 — RSS, stdlib only

Keep the existing Unix `resource` path. On Windows, use `ctypes` with
`GetCurrentProcess` and `GetProcessMemoryInfo` to read the current Python
process working set in bytes. Use the correctly sized
`PROCESS_MEMORY_COUNTERS` structure and fail to `None` if the API is
unavailable or returns false.

Do not add `psutil`. Do not claim process-tree RSS.

Sampling semantics:

- sample once after every completed APP block result (after any paired oracle
  call for that block);
- store `peak_rss_bytes` for each `f` as the max non-None sample;
- store run-level `peak_rss_bytes` as the max of per-`f` peaks;
- if any required sample is `None`, set run-level RSS status to unknown and
  prevent `passed=true`;
- `peak_rss_bytes >= 2*1024**3` prevents pass.

Do not call a single end reading a peak.

### I03 — aggregate observability

For each `f`, persist exactly the existing fields plus:

- `app_syndrome_ok_count`
- `app_iterations_total`
- `app_iterations_max`
- `oracle_syndrome_ok_count`
- `oracle_iterations_total`
- `nonfinite_count`
- `peak_rss_bytes`

Retain run-level `nonfinite`, `decoder_calls`, and add run-level
`peak_rss_bytes`, `wall_seconds`, `outcome`.

Required identities/bounds:

- attempted = 100 per `f`;
- APP exact and APP syndrome counts in `[0,100]`;
- oracle exact and syndrome counts in `[0,20]`;
- `app_failure_fraction == 1-app_exact_count/attempted`;
- `app_iterations_max <= 2*MAX_ITER` and totals are nonnegative;
- oracle iteration total is nonnegative;
- decoder calls = 440 on the frozen G1 path.

Do not persist raw symbols, beliefs, priors, or per-block records.

### I04 — signal rule and completed-path classification

Define the prospective signal rule using integer counts where possible:

```text
zero nonfinite
AND rates nondecreasing
AND top APP exact count > 0
AND (top APP exact count > low APP exact count
     OR both APP exact counts == attempted)
```

For a normally returned G1 run, classify in this order:

1. `G1_NONFINITE_OR_CRASH_BLOCKED` when `nonfinite > 0`;
2. `G1_OVERRUN_900S` when entrypoint wall exceeds 900 s;
3. `G1_RESOURCE_OVERRUN` when RSS is unknown or `>=2 GiB`;
4. `G1_TREND_PASS` when the signal rule holds;
5. otherwise `G1_COMPLETED_NO_SIGNAL_FAIL`.

`passed` is true iff `outcome == "G1_TREND_PASS"`.

`G1_PRE_EXECUTION_BLOCKED` and `G1_WATCHDOG_TIMEOUT_VOID` are operator-side
labels because those paths do not normally return a four-file result. A Python
exception is also fail-loud: do not catch it merely to manufacture a normal
evidence bundle. The operator may label it
`G1_NONFINITE_OR_CRASH_BLOCKED` in its return. This is the minimal boundary;
do not add recovery or partial-output machinery.

Measure `wall_seconds` from entry into `run_g1_synthetic` through completion of
model loading, decoder binding, mother construction, and decoding, immediately
before evidence writing. Evidence-writing time and process startup are reported
separately by the future operator's outer wall; an outer wall over 900 s
overrides any stored pass during Pre-RESULT review.

### I05 — fail-loud writers

In both G1 and G2 writers replace the duplicated nested fallback with direct
required-key access:

```python
float(item["app_failure_fraction"])
```

Do not rename the public field or add legacy compatibility.

G1 JSON/CSV/report/summary must include the new aggregate fields needed to
recompute the completed-path outcome. G2 receives only the fail-loud correction;
do not change G2 grading or schema otherwise.

### I06 — no-subdirectory invariant

In both test files, make each formal-root snapshot helper fail if any direct
child is a directory. Preserve the current top-level file name/size/mtime
snapshot. Add a tmp-only demonstration that absent→created directory and
present→new nested directory are caught. No recursive hashing.

### I07 — reachability contract

Add/retain static and fake tests proving the future external-file sentinel
contract can reach the first injected decoder call with accepted input while
tmp output remains empty. Unit tests must not read the real Model-F root. The
real-root external-file probe is deferred to Pre-EXECUTE.

## 6. Focused tests

Add narrowly scoped tests for:

1. new G1 root literal and old root barred from current production constant;
2. Unix RSS path preserved;
3. Windows RSS success/failure using monkeypatched/fake ctypes behavior;
4. per-block sampling count and per-`f`/run peak max;
5. RSS `None` and `>=2 GiB` prevent pass;
6. all-zero exact line → `G1_COMPLETED_NO_SIGNAL_FAIL`;
7. positive strict improvement → `G1_TREND_PASS` when resource/time gates pass;
8. saturated `1.0,1.0` → `G1_TREND_PASS`;
9. positive flat below 1.0 → no-signal fail;
10. nonfinite, >900 s, RSS over/unknown precedence;
11. exact/syndrome/iteration identities and 440 calls using fake decoder;
12. both writers fail loudly when `app_failure_fraction` is missing;
13. no-subdirectory invariant catches nested directory creation in tmp roots;
14. SAFE A/B/C and AST guards remain effective;
15. no test can invoke an authorized synthetic entrypoint without explicit fake
    decoder, injected arrays, and tmp output.

Do not weaken, skip, xfail, delete, or rewrite unrelated assertions to get
green.

## 7. Verification tiers

Use a fresh additive basetemp under `workspace/` and `-p no:cacheprovider`.

1. `py_compile` the core and both D5 scripts.
2. Run a focused selection for all new tests plus SAFE/TIS guards.
3. Run the complete three-file D5 suite:
   - `test_v72p2d5_gf32_rate_mother.py`
   - `test_v72p2d5_model_f_input.py`
   - `test_v72p2d4_cal_gf32_model_rate_audit.py`
4. Require zero failures. The benign unknown `cache_dir` warning is allowed.
5. Remove only the basetemp created by this task after verifying its resolved
   path is the intended task-specific directory.

Before and after tests, stat all formal roots. Existing roots must be identical;
new G1 `20260907_r2` and G2 roots must remain absent.

Because the worktree has known EOL stat churn, scope cleanliness by actual
content (`git diff --numstat` / `git diff --cached --numstat`) and explicit
allowlist. Do not normalize or clean the worktree.

## 8. Commit protocol

Use explicit path-by-path staging only.

Commit 1 — reviewed packet + OpenSpec:

```text
docs(v72p2d5): accept G1 packet review and specify readiness rework

Co-Authored-By: OpenAI Codex <codex@openai.com>
```

Paths: the existing review file plus the four new OpenSpec files only.

Commit 2 — code/tests:

```text
feat(v72p2d5): implement G1 readiness metrics, outcome, and fresh root

Co-Authored-By: OpenAI Codex <codex@openai.com>
```

Paths: core plus two test files only.

Before each commit, print `git diff --cached --name-only`; any out-of-scope path
is STOP. Do not self-repair the index with reset/checkout. Do not push.

## 9. Return conditions

Return only when all frozen items pass, or STOP on one concrete blocker with
the exact failing command/output and the single decision needed.

Completion report:

1. D1–D6 and A01–A13 mapping;
2. exact changed files and concise diff summary;
3. focused and full pytest literal lines;
4. RSS fake-test evidence and sampling counts;
5. five outcome test results and precedence;
6. pre/post formal-root snapshots;
7. two commit SHAs and final status;
8. true/false: decoder, phase, real Model-F root read by tests, CAL/VAL/parquet
   rows, workspace evidence changed, new G1/G2 root created, authorization
   changed, frozen constants changed beyond G1 root, push.

End with:

`G1 readiness 实现候选完成，等待独立代码评审；G1 未授权、未执行；新 G1 根与 G2 根仍不存在。`

