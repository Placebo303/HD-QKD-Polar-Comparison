# Troubleshooting

Reusable failure modes and their fixes for the HD-QKD_Polar_Comparison project.

---

## Template

```
### <Symptom>

**Observed**: <What you see>

**Root cause**: <Why it happens>

**Fix**: <Steps to resolve>

**Prevention**: <How to avoid in future>
```

---

## Known Issues

### `No module named pytest` / `No module named numpy`

**Observed**: Bare `python3 -m pytest` or `python -m ...` fails with `No module named pytest` or `No module named numpy`.

**Root cause**: System `/usr/bin/python3` has no project deps; `pytest`/`numpy` live only in repo `.venv/`. `wsl-env.sh` exports data paths but does not activate the venv.

**Fix**: Use the repo venv:
```bash
source .venv/bin/activate
.venv/bin/python -m pytest --version
```

**Prevention**: Never use bare `python3`/`python -m pytest`; always `source .venv/bin/activate` or `.venv/bin/python -m ...`. Verify with `.venv/bin/python -c "import numpy,pytest; print(numpy.__version__)"`.

---

### Permission denied on pytest cache directories

**Observed**: When globbing or grepping the repo, you get `拒绝访问 (os error 5)` on files under `pytest-cache-files-*` directories.

**Root cause**: Pytest temporary cache directories have restrictive ACLs that block traversal even with read permissions.

**Fix**: These errors are harmless. Use `--glob` patterns that exclude these directories, or use tools that handle permission errors gracefully.

**Prevention**: Add `pytest-cache-files-*/` to `.gitignore`. Do not create these directories manually.

---

### .git/index.lock permission issue

**Observed**: Git operations (commit, stage) fail with `fatal: unable to create '.git/index.lock': Permission denied`.

**Root cause**: A stale lock file from a previous interrupted git operation, or concurrent git processes.

**Fix**: Remove the lock file: `Remove-Item -LiteralPath ".git/index.lock"`. If that fails, close other git clients and try again.

**Prevention**: Avoid running multiple git operations concurrently. Ensure git commands complete fully before starting new ones.

---

### Parquet fallback to pickle

**Observed**: Output files expected as `.parquet` are written as `.pkl` instead.

**Root cause**: The `pyarrow` or `fastparquet` library is not installed, so the code falls back to pickle serialization.

**Fix**: Install the optional comparison dependencies:
```bash
pip install -r comparison_bench/requirements-comparison.txt
```

**Prevention**: Ensure `comparison_bench/requirements-comparison.txt` is installed before running benchmarks.

---

### PowerShell execution policy warnings

**Observed**: PowerShell startup emits `execution-policy` warnings.

**Root cause**: The current PowerShell profile or system policy restricts script execution.

**Fix**: These warnings are non-fatal. If needed, set `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`.

**Prevention**: This is an environment-level configuration issue, not a project issue. Ignore unless it blocks actual script execution.

---

### Legacy Windows paths in code

**Observed**: Some files (e.g., `polar_existing_bridge.py`) contain hardcoded Windows paths like `D:\Data\Raw Data\QKD_Loss\...`.

**Root cause**: Historical provenance paths baked into the code base.

**Fix**: These are **provenance only** — do not use them as execution defaults. For WSL, use POSIX paths via `/mnt/d/Data/...` or project-relative paths. Do not bake new Windows absolute paths into code.

**Prevention**: Use environment variables (`PROJECT_DATA_ROOT`, `PROJECT_RESULTS_ROOT`) or config keys instead of hardcoded paths.

---

### Report table generation fails on `bin_width_ps` NaN values

**Observed**: `make_report_tables.py` can fail while grouping or sorting report rows if `bin_width_ps` contains missing values.

**Root cause**: Imported or merged result rows may not have complete `bin_width_ps` metadata, especially when combining heterogeneous Polar/imported and comparison outputs.

**Fix**: Preserve the missing value semantics and handle NaN explicitly in report-table generation instead of coercing it into a misleading physical bin width.

**Prevention**: When adding report tables, treat `bin_width_ps` as nullable metadata and include missing-metadata checks in report-generation tests.

---

### Historical Cascade v3 sweep errors from missing `mapping`

**Observed**: An earlier v3 Cascade sweep sent all tasks to `run_errors_ir_v3.csv`.

**Root cause**: The CLI glue layer did not pass the `mapping` parameter into the Cascade sweep path.

**Fix**: Pass `mapping` through the CLI/config glue and rerun the affected sweep additively.

**Prevention**: Do not interpret `run_errors_ir_v3.csv` as the current total failure state without checking timestamps, param hashes, rerun outputs, and manifests.

---

### `ValueError: plan frozen equality` during formal execute after a source edit

**Observed**: A formal execute (`run_ldpc_v5_development.py execute`) aborts
before writing any artifacts with `ValueError: plan frozen equality` even
though the plan was prepared successfully minutes earlier.

**Root cause**: A prepared plan binds the frozen source hashes of the
implementation files. Any edit to those files (e.g., a performance refactor)
after prepare makes the plan's provenance check reject the current source,
by design — plans are immutable.

**Fix**: This is a source-changed-under-plan condition, not a retry. Record
the intended code change, then delete the stale official package directory
(no artifacts were written), re-prepare, main-review the new plan, and execute
once. Treat this as the single approved execute cycle.

**Prevention**: Freeze source files before `prepare`; if a code change is
needed, expect prepare/execute/verify to be invalidated and plan for one fresh
cycle with main-thread approval (recorded in the decision log).

---

### Robustness noise injections must match the decoder's error-channel model

**Observed**: An injected-symbol-error-rate sweep (uniform random symbol
replacement on Bob) failed 0/1152 even at SER 0.05, while real data at
SER 0.035–0.215 succeeds 100%.

**Root cause**: `plane_error_channel` builds the decoder prior from the frozen
calibration table only (Bob-conditioned, adjacent +/-1 at fixed probabilities,
nominal SER 0.243). Uniform replacement is out-of-distribution noise — the
prior is structurally mismatched, so even weak errors defeat decoding. This is
expected and diagnostic, not a capability boundary.

**Fix**: For capability-boundary questions, inject model-consistent noise:
adjacent +/-1 errors drawn at the frozen nominal probabilities (plus_one
3865/16384, minus_one 116/16384) — then the prior exactly matches the
distribution (validated 768/768 at SER 0.2430). Keep uniform-noise runs as
out-of-distribution controls.

**Prevention**: State the noise model of any SER sweep before running; check
it against `v5_plane_error_channel` (hardcoded `adjacent_nominal`) semantics.

---

### V13 D01 bursts_runs aggregate: run counter reset before the end check

**Observed** (2026-08-14): the recorded D01 `bursts_runs` aggregate said
`run_count=8`, `max_run_length=2`, `runs_per_frame_mean=0.0625` while
`error_symbol_fraction=0.0771` implies ~2525 error symbols — mathematically
inconsistent; a read-only recompute produced the same impossible numbers.

**Root cause**: in `nonbinary_v13_diagnostics._frame_channel_stats` the loop
body was

```python
run = run + 1 if value else 0      # zeroes run FIRST
if not value and run:              # now run is always 0 at a gap
    runs.append(run); run = 0
```

The conditional expression reset `run` to 0 before the run-end check, so only
runs ending at the LAST position of a frame (the trailing `if run: append`)
were ever recorded. 8 frames happened to end with an error → 8 phantom runs.

**Fix** (code only; the D01 package remains immutable evidence): explicit
branch — `if value: run += 1` / `else: if run: runs.append(run); run = 0`.
Corrected aggregates for the same 128 bw200 characterization frames: 2340
runs (mean 18.3 runs/frame), run-length histogram {1: 2169, 2: 157, 3: 14},
max run length 3, 185 adjacent error pairs (7.3% of errors have a neighbor) —
errors are isolated single-symbol perturbations, not bursts. Additionally,
99.3% (2508/2525) of nonzero Alice-Bob differences lie in [0,128), matching
the LSB-dominated bit-plane mismatch and the adjacent-symbol error structure
known from the binary V5 plane channel. The corrected numbers are recorded in
the 2026-08-14 D04 decision-log entry.

**Prevention**: never write `x = x + 1 if cond else 0` when the OLD value of
`x` is read after the assignment in the same block; use explicit branches.
Cross-check derived aggregates against each other (run counts must cover the
error-symbol count) before trusting them in reports.

---

### D7-B file-location fallback: top-level load of a relative-import module

**Observed** (2026-09-10, WSL): the D7-B runner loads its core by file
location (`spec_from_file_location`), and the core's
`bind_historical_decoder()` fell back to file-loading
`v35_algorithm_development.py` as a top-level module when the
`comparison_bench` package was not importable. The bind then failed with
`ImportError('attempted relative import with no known parent package')`
before any decoder call and before output-root creation.

**Root cause**: a module file-loaded under a top-level name has no parent
package, so its explicit relative imports (here v35's
`from .nonbinary_field import ...`) can never resolve. The fallback's
`except ModuleNotFoundError` only proved the first import failed; it could
not make the fallback context package-correct.

**Fix**: derive `<repo>/comparison_bench/src` from the runner's own resolved
`__file__` and insert it into the current process's `sys.path` (only if
absent) before loading the core, so the core and v35 resolve through the
normal package name `comparison_bench.formal_ir.*` against the local source
tree. No hard-coded drive/mount/cwd/PYTHONPATH, no install, no copies.

**Prevention**: never file-load a module that contains relative imports as a
top-level module; ensure its package is importable first. Keep
`except ModuleNotFoundError` fallbacks narrow so an internal dependency
`ImportError` is never misreported as a merely absent package.

---

### Combined pytest across D7/formal_ir suites: `No module named 'comparison_bench.formal_ir'`

**Observed** (2026-09-10/11, WSL): collecting the D7-A, D7-B and D7-C test files
together in one pytest process yields `199 collected, 1 error` with
`ModuleNotFoundError: No module named 'comparison_bench.formal_ir'`; the same
combined run without the new module yields `179 collected, 1 error`. Each suite
alone passes.

**Root cause**: pre-existing `comparison_bench` package namespace collision when
multiple `formal_ir` test modules are collected in a single process. It is not
caused by the D7 modules.

**Fix**: run each suite in its own pytest process (D7-C, D7-A, D7-B separately).
Combined multi-file collection is not a supported qualification path.

**Prevention**: treat per-suite process isolation as the baseline for D7
qualification; do not read the combined-collection error as a new regression.

---

### `python: command not found` in the default WSL shell

**Observed** (2026-09-10/11, WSL): bare `python` is absent from the default PATH
(`/bin/bash: line 1: python: command not found`, exit 127) even though the
project venv exists, so a frozen command that spells `python` fails before the
script starts.

**Root cause**: the WSL shell does not expose the project interpreter on PATH by
default.

**Fix**: prefix the accepted venv bin directory, e.g.
`PATH="$HOME/.venvs/hd-qkd-polar-comparison/bin:$PATH" python ...` (the adapter
documented for the D7-B R2 execution); review pytest runs may instead use the
repo-local `.venv/bin/python`.

**Prevention**: any future authorized D7-C run must declare the same
venv-on-PATH adapter in its command record, so a bare `python` fails safely
(exit 127) rather than silently binding a different interpreter.

---

### V35 report rewrite claimed `NB_CANDIDATE_DEVELOPMENT_READY` (rejected)

**Observed** (2026-09-11, WSL): the uncommitted working copy of
`docs/v35-algorithm-development-report.md` had been rewritten to claim a
terminal `NB_CANDIDATE_DEVELOPMENT_READY` status and a positive numerical
table.

**Root cause**: the rewrite contradicted the committed corrected report at the
cycle entry HEAD, whose bounded status is
`NO_NB_CANDIDATE_FOR_TESTED_HAND_DESIGNED_CONFIGURATION` and
`PROTOCOL_PARTIAL_A4_NOT_EXECUTED`. The rewrite was uncommitted and its numbers
were not reproducible from the accepted `run_02` evidence.

**Fix**: reject the rewrite and restore the report content exactly to the
entry-HEAD version:
`git show HEAD:docs/v35-algorithm-development-report.md > docs/v35-algorithm-development-report.md`.
No backup file was created and no false numerical table is retained as an
active report.

**Prevention**: treat the committed corrected bounded status as authoritative;
do not promote an uncommitted rewrite whose numbers cannot be recomputed from
accepted evidence.

**Recurrence** (2026-09-11, WSL): the same rejected rewrite reappeared after the
A06 restore, observed rewriting the working copy at ~10:28:58 and ~11:16:45; it
was re-restored again to the entry-HEAD version and was not committed. The
external writer remains unresolved.

---

### D6 dormant graph/mother script unpacks the pre-BP-02 `_decode_block` arity

**Observed** (2026-09-11, WSL): BP-02 changed the D5 `_decode_block` return
arity. `scripts/v72p2d6_graph_mother_development.py` is dormant and still
unpacks the old return shape, so it will crash before its cross-layer use.

**Root cause**: the D6 script was not migrated when the D5 return arity changed;
it is currently reachable only by an unauthorized D6 rerun.

**Fix / prevention**: D6 reruns are unauthorized. Fixing and migrating the
script (and adding the fail-closed provenance guard) is required under a new
scoped change before any D6 rerun. No code change is made in this packet.

---

### D7-E R22 lifecycle-test debt: ten isolated baseline tripwires (no broad cleanup)

**Observed** (2026-09-11, WSL): ten pre-existing test tripwires fail
identically at baseline (committed leftover roots / accepted-state snapshots),
unrelated to D7-E. Each was isolated with baseline proof; no skip/xfail/delete
was used.

**Inventory**:
- D7-B `test_launch_l04_dry_run_both_cwds_no_bind_no_root` and
  `test_launch_l12_roots_and_authorization_unchanged` — stale root-absence
  assertions against the accepted D7-B root.
- D7-D `test_f08_no_real_model_f_production_root_or_formal_root_read` and
  `test_s21_protected_root_lifecycle_and_d7bc_immutability` — stale
  root-absence assertions against the accepted D7-D root.
- D7-C `test_c19_protected_root_lifecycle_and_g2_r1d_absence` — root part
  already converted to snapshot invariance; residual is a stale authorization
  snapshot (`decoder_executed`/`result_created` true after the legitimate
  accepted run).
- v45–v48 five CLI/overwrite-guard failures — group reference per
  `D7_BP_INTERFACE_IMPLEMENTATION_REVIEW_R1.md` §5 (`test_t10_cli_no_fake_option`,
  `test_t10_cli_sha_rejects`, `test_cli_guards` ×3; exact full IDs
  unconfirmable from that doc and not invented here) — pre-existing accepted
  `run_01` roots trigger overwrite refusal before the asserted message.

**Rule**: repair only a test directly blocking a required scoped suite, using
snapshot invariance rather than root absence; never weaken an authorization
tripwire; no skip/xfail/delete.

---

### WSL `ru_maxrss` vs `/proc` VmHWM disagreement makes one-shot RSS gates non-deterministic (D7-E E09)

**Observed** (WSL, 2026-09-11): `resource.getrusage(...).ru_maxrss` intermittently
disagreed with `/proc/self/status` VmHWM by several GiB, making the one-shot
pre-execution RSS gate (E09) non-deterministic.

**Root cause**: `ru_maxrss` is not a stable peak-RSS source on WSL; the
kernel-reported VmHWM is authoritative for the WSL execution path.

**Fix (frozen rule)**: on Linux/WSL read current-process peak RSS only from
`/proc/self/status` field `VmHWM` (unit exactly `kB`, `bytes = value * 1024`);
never compare against or fall back to `ru_maxrss` when the status file is
present. Missing file/field, duplicate field, malformed/non-integer/
non-positive value, wrong unit, read error, or overflow returns `None` and
blocks fail-closed before scientific execution (or at the first affected call
under the existing resource terminal). Strict `< 2 GiB` limit unchanged
(equality blocks); stored key stays `rss_bytes`. Do not substitute `VmRSS`,
`statm`, psutil, or shell commands.

**Prevention**: single-probe discipline — exactly one fresh live E09 probe as
evidence; repeating probes until one passes is forbidden. Cover all parser and
edge cases with deterministic injected-text fixtures; sample the live kernel at
most once as context.

---

### Frozen decoder success contract unsatisfiable by a zero-syndrome/uniform-prior fixture (D7 X1)

**Observed** (2026-09-13, WSL): the one-shot historical-decoder provenance probe
returned `PRIOR_ONLY`, `iterations: 0`, exit 2 (`X1_PROVENANCE_PROBE_FAILED`)
although the decoder itself was healthy.

**Root cause**: the probe fixture used a zero syndrome with a uniform prior.
The historical row-layered decoder early-returns at iteration 0 whenever
`H @ argmax(beliefs) == syndrome`
(`comparison_bench/src/comparison_bench/formal_ir/v35_algorithm_development.py:835-854`);
with `argmax(uniform prior) = 0` and `syndrome = 0` that condition always
holds, so the decoder correctly returns `iterations=0` + `PRIOR_ONLY`, and a
frozen success contract requiring `CHECK_UPDATED` with `iterations >= 1` can
never pass. The fixture was unsatisfiable by construction, not the decoder.

**Fix**: use a nonzero syndrome consistent with a chosen `x_true` (X1 fix in
`_probe_fixture`: syndrome `[1, 2]`, `x_true [0, 1]`, `h = [[1, 1], [1, 2]]`,
prior unchanged), so `H @ argmax(prior) != syndrome` and at least one check
sweep runs; the authorized rerun then returned `CHECK_UPDATED`, iterations 90,
exit 0 (`X1_RERUN_VERIFIED`).

**Prevention**: before executing any frozen decoder success contract, check
fixture satisfiability against the decoder's early-exit paths; a contract that
demands updated beliefs cannot be met by a fixture that provably triggers a
zero-iteration early return.

---

### Bare `pytest -p no:cacheprovider` under WSL yields setup errors from Windows `--basetemp`

**Observed** (2026-09-18, WSL): bare `pytest -p no:cacheprovider` collected
but reported 26 passed + 7 setup errors.

**Root cause**: `pytest.ini` `addopts` carries a `--basetemp` Windows path
(`D:/Code/...`) that is invalid under WSL, so fixture setup fails before tests
run.

**Fix**: rerun with `-o addopts=""` to clear the inherited addopts →
33/33 pass. No file edited.

**Prevention**: fix-debt — portable basetemp config (deferred, non-blocking).

---

### D19 refusal-test 4-fail after authorized D19 execution is expected

**Observed**: Four refusal/root-absence tests fail after the authorized D19 execution because the D19 evidence root legitimately exists.

**Root cause**: The tests assert root absence; post-execution the accepted root is present by design.

**Fix**: Do not touch the evidence root. Treat the 4-fail as expected post-execution state; G6 readiness properly rests on its own 9/9 suite.

**Prevention**: Never delete evidence roots to green tests; convert stale absence assertions to snapshot invariance only in a scoped change.

---

### Post-execution stale root-absence failures also hit R9–R12 and D17 (same class as D19)

**Observed** (2026-09-19, WSL canonical env, suites run per file with
`-o addopts=""`): after the authorized R9/R10/R11/R12 executions the
corresponding frozen suites no longer pass:
`test_g6r9_confirm.py::test_d5_no_overwrite`,
`test_g6r10_ctrl.py::test_profile_only_fake_128_zero_calls`,
`test_g6r11_adaptive.py::test_s3_no_overwrite`,
`test_g6r12_fresh.py::test_r3_no_overwrite`,
`test_g6_decide_r2_diag.py::test_profile_fake_pool_budgets_zero_calls`
(asserted `future_root_absent is True` / `not FUTURE_ROOT.exists()`), plus
`test_v72p2d17_descaling.py::test_d16_root_absent_and_blank_predictions`.

**Root cause**: identical to the D19 entry — the assertions are pre-execution
guards; the authorized single-invocation roots
(`workspace/g6r9_confirm_3f9a1c2e-…`, `g6r10_ctrl_6f2b8c1d-…`,
`g6r11_adaptive_3c2b5b2e-…`, `g6r12_fresh_c97777aa-…`) now legitimately exist.

**Fix**: none applied. Evidence roots untouched; no rerun, no repair. Treat the
failures as expected post-execution state, exactly as the D19 precedent rules.

**Prevention**: conversion to snapshot invariance (root absent OR root equals
the frozen executed package) is a scoped change requiring its own
authorization — do not green these tests by editing asserts ad hoc or by
deleting roots.

---

### Windows default `addopts` basetemp makes root-refusal tests fail spuriously

**Observed** (2026-09-19, Windows + conda python 3.12.12): bare
`python -m pytest comparison_bench/tests/test_v72p2r7_rate_scan.py -q` gives
3 failures (`ValueError: refusing protected root …/workspace/tmp_pytest/…/root`).
The same file passes 8/8 with an out-of-repo `--basetemp`.

**Root cause**: `pytest.ini` `addopts` pins
`--basetemp=D:/Code/HD-QKD_Polar_Comparison/workspace/tmp_pytest`; that path
component starts with the protected prefix `tmp_pytest` used by
`v72p2d10_mixed_degree_l1.refuse_out_root`, so every in-test fake root is
refused as if it were a protected output root.

**Fix**: run with an external basetemp, e.g.
`-o addopts="-p no:cacheprovider" --basetemp=%TEMP%\pt_x` (Windows) or
`-o addopts=""` (WSL, where the hard-coded Windows path is invalid and produces
setup errors).

**Why not simply delete `--basetemp`**: measured, not assumed — removing it
entirely produces 12 setup errors on Windows
(`test_v72p2d17_descaling.py`: 1 failed / 32 passed / 12 errors) while WSL is
clean (3 failed / 42 passed). Portable-basetemp config therefore remains open
fix-debt; do not remove the option silently.

---

### Windows conda python and WSL `.venv` give different suite verdicts

**Observed** (2026-09-19): `test_v72p2d17_descaling.py` → Windows 8 failed /
37 passed vs WSL 3 failed / 42 passed on the same HEAD.

**Root cause**: environment divergence (conda python 3.12.12 / NumPy 2.4.0 on
Windows vs `.venv` python 3.12.3 / NumPy 2.4.4 under WSL) plus the basetemp
difference above.

**Fix**: treat WSL `.venv` as the authoritative lane for suite verdicts; use
Windows runs only for triage. No file edited.

---

### UNION-default trap: `--include-r72` returns UNION 64/8 incl r65-repeat

**Observed** (2026-09-19, R23b-0.72): granted probe 32 sci + 4 setup, but the
single invocation covered 64 rows / 8 setup (r72 0/16+0/16 plus r65-repeat
0/16+0/16, bit-identical excl wall_s/call_idx) — SCOPE BREACH, self-reported
STOP.

**Root cause**: `--include-r72` builds a UNION plan (r65-repeat + r72) with no
delta-only mode; the Pre-EXECUTE precondition missed the UNION check.

**Fix**: assert plan length == granted scope (`len(plan) == 32`) before
execution; admit only the granted half, annotate any repeat as zero-info.

**Prevention**: runner hard-gated until delta-only mode + actual-argv logging +
re-review. Manifest `command` may hold a stale FROZEN_COMMAND constant —
verify actual argv from `command_log` / `out_root` / `conditional_r72`.

---

### 0.72 SCOPE-BREACH pattern — UNION-default plan executed 64/8 vs granted 32/4

**Observed**: UNION-default plan executed 64/8 vs granted 32/4 (missed
plan-length check); self-reported STOP with evidence retained, no concealment.

**Root cause**: Pre-EXECUTE missed the plan-length check against the granted
scope (see UNION-default trap entry).

**Fix**: adjudicated — r65-repeat annotated zero-info deterministic, r72 half
admitted as probe, envelope amended 96/12 consumed-closed, both grants closed.

**Prevention**: runner hard-gated (delta-only mode + actual-argv log + re-review
required before any conditional-probe run); Pre-EXECUTE must assert
len(plan)==granted scope.

---

### Seed-disjointness scans must include D19 block ranges + packet paths — operator rg over decision-log/research_cycles/openspec/comparison_bench missed frozen D19 n128 block seeds 2026094501..4508 (packet + v72p2d19 tasks F01 + D19 READINESS_R1); picks 4501/4502 collided exactly and were rejected at main-thread review with zero tolerance for colliding provenance. Fix: scan list must explicitly include .workbuddy/tasks/*_PACKET.md + openspec/changes/v72p2d19-*/tasks.md + docs/research_cycles/V72P3*/READINESS_R1.md + numeric-range assertions (not just literal greps); reviewer re-checks collision against the frozen seed table before any Pre-EXECUTE.

---

### Zotero local-api scan returns curl RC=7 (connection refused)

**Observed**: Zotero local-api scan returns curl RC=7 (connection refused, both 127.0.0.1:23119 and localhost).

**Root cause**: Zotero desktop is not running / local API not enabled.

**Fix**: Open Zotero desktop on the Windows host (local API allowed) then retry; details in `docs/research_cycles/V80-NBLDPC-JAN21/ZOTERO_SCAN_20260920.md`.

**Prevention**: Ensure Zotero desktop is running with the local API allowed before any Zotero local-api scan.

---

### S2c _construct_gate positional wiring (arm-as-seed) → all-arms-refused

**Observed**: all arms refused `unknown arm 2026092001` with zero decodes/roots.

**Root cause**: positional call `(seed, trials)` vs production signature `(arm, seed, trials)`.

**Fix**: `construct_fn(arm, seed, trials)` + T15 production-binding test.

**Prevention**: fake-only tests must mirror real `construct_fn` arity; add one production-binding test per campaign runner.

---

### v10_peg _reconcile_check_counts fallback can invent out-of-support degrees (|delta|>1)

**Observed**: SRF-02 (socket fix review).

**Root cause**: fallback path absorbs any representable delta.

**Fix**: bound/clamp to support before any frozen/DECIDE use; the L-A bit-identity proof (sha 8a56b577) does not cover this path.

**Prevention**: bound/clamp to support before any frozen/DECIDE use.

### Silent death of nohup background launch (process group killed on shell exit)

**Observed**: nohup'd run died silently <5 min, zero-byte log, no process.

**Root cause**: background process group killed when the launching shell exited.

**Fix**: relaunch with `setsid nohup <cmd> >log 2>&1 < /dev/null &` then verify with `ps`.

**Prevention**: for long detached runs use setsid + explicit liveness check; if relaunched clean with no output contamination there is no science impact.

### L1 per-decode overrun + ledger shortfall on budget FAIL (C8 pattern)
**Observed**: block-84 per-decode 1120.7 s > 300 s cap with ledger 84 vs 85 (ledger_ok False), wall 2521.8 s; partial FER 0.071 RAW.
**Root cause**: decoder instability (max-iter exhaustion path), not a schedulable tail; budget stop leaves ledger short by design.
**Fix**: retain RAW as FAIL(budget), never promote partial FER; record overrun block idx + wall + ledger mismatch.
**Prevention**: Pre-EXECUTE must state per-decode cap + ledger_ok gate; batch-end review must check overrun block before any Stage B.

---

### `from TimeTagger import FileReader` fails although Swabian-TimeTagger is installed

**Observed** (2026-09-21, WSL repo `.venv` with `Swabian-TimeTagger==2.22.6`): bare `import TimeTagger` → `ModuleNotFoundError: No module named 'TimeTagger'`; the frozen loader `src/qkd_io/ttbin_pipeline.py:148` then raises `RuntimeError: TimeTagger package not available; cannot read .ttbin: ...`, while `from Swabian import TimeTagger` works and exposes `FileReader`.

**Root cause**: the PyPI `Swabian-TimeTagger` wheel provides ONLY the `Swabian.TimeTagger` namespace; the repo loader was written against the vendor Windows-driver layout that ships a top-level `TimeTagger` package. Permanent mismatch, not a broken install.

**Fix**: call the alias shim BEFORE any TimeTagger import — `comparison_bench/src/comparison_bench/io/ttbin_compat.py::install_timetagger_alias()` (idempotent; registers `sys.modules['TimeTagger']`). Verify: the probe error flips from the import-gate `RuntimeError` to the vendor `FileReader could not open file ...` on a nonexistent path. Never patch `src/` (frozen, AGENTS.md §5.1).

**Prevention**: every entrypoint (incl. future `scripts/`) must install the alias first AND run with repo-root `PYTHONPATH` (else `No module named 'src'`). Any future `--authorized` gate flag must be `action="store_true", default=False`.

---

### `.ttbin` pair double-count: opening `X.ttbin` + `X.1.ttbin` and concatenating counts every event twice

**Observed** (2026-09-21): both pair members return byte-identical `getConfiguration()` (Jan-12: 4913-char JSON equal), `FileWriter.filename` in BOTH points at base `X.ttbin`, no part-index field; vendor docstring: FileReader "will automatically recognize if the files were split and read them too one by one"; decisively, the 8 KB Jan-12 `X.ttbin` read ALONE spans 29.9999524 s — an 8 KB file cannot hold that, so the reader followed into `.1`.

**Root cause**: pair members are NESTED / SUPERSET via vendor auto-follow, NOT disjoint parts. Assuming disjointness and UNION-concatenating doubles the stream — pairs, counts_ab and H_full all wrong (and every downstream estimator/uncertainty/memory statistic with them).

**Fix**: open ONLY `X.ttbin` (auto-follow covers `.1`); `.1` shard-only (`FileReader("X.1.ttbin")`) is the fallback — NEVER both, NEVER concatenate. Dedup-after-concat is the wrong fix (masks the error).

**Prevention**: gate every ingest on the span-continuity assertion: span > 0 AND span consistent with mtime(`X.1`)−mtime(`X`) within tolerance, else STOP-BLOCKED (span ≈ 2× gap ⇒ doubling; span ≪ gap ⇒ truncation).

---

### Filename duration tags disagree with measured acquisition span (Jan-12 `3s` tag is wrong)

**Observed** (2026-09-21): Jan-12 `Type2PPLN_3s_2026-01-12_165236` event-span drain = 29.9999524 s but filename tag says `3s`; Jan-21 `Type2_2M_3s_2026-01-21_183657` = 2.9999997 s (tag correct). Base→`.1` mtime gaps (+30 s / +3 s) and file sizes corroborate the spans; the config carries no duration field.

**Root cause**: filename tags are stale/incorrect labels for at least one pair; nothing in the file metadata supplies duration.

**Fix**: duration MUST be measured from the stream span (first→last timestamp), NEVER taken from the filename. Record `duration_measured_s` + verbatim `filename_duration_tag` + `tag_disputed` per row; Jan-12 is quarantined as `duration_measured_s=30.0`, `filename_tag_disputed=true`, never pooled with 3 s acquisitions undeclared.

**Prevention**: any census/report schema must carry the three duration columns; pooling across durations requires explicit declaration.

---

### Plug-in-only entropy table flipped the out-of-box verdict (P3 A1): uncorrected estimator drove a route-relevant number

**Observed** (2026-09-21, `P3_A1_REVIEW.md` item 7 vs `workspace/p3_census_3954637c/DESIGN_POINT_ARITHMETIC.md`): on plug-in H_full the table reads T2-1.5M OUT@208 (f=1.306853) and T2-1M OUT@200 (f=1.301864); on the Miller–Madow-corrected H (plug-in + (K−1)/(2N·ln2)) the same arms read INDETERMINATE@208 (f=1.300573; corrected H 0.82896 sits 0.00037 below the 0.829327 threshold, INSIDE the bootstrap CI half-width 0.00221) and IN@200 (f=1.292997). Related trap (finding F-2): the sparse-histogram bootstrap CI does NOT bracket the plug-in point estimate (all three CIs sit entirely below it) — CI_hi must not be read as an upper bound on H_full.

**Root cause**: plug-in entropy is biased LOW on sparse histograms (occupancy K/1024² ≈ 0.0023; support ≈ 2400 occupied joint cells; N ≈ 0.5–1.0M coincidences). Where a verdict threshold sits within ~0.001 of a source's H, the bias alone moves the verdict across the f ≤ 1.3 line — the direction that makes a source look worse than it is.

**Fix**: compute every design-point quantity (m_max, f@m, N_req) on the CORRECTED H, reporting plug-in alongside; when |H − threshold| is inside the bootstrap CI half-width, label the verdict INDETERMINATE, not OUT/IN. Authority: `workspace/p3_census_3954637c/DESIGN_POINT_ARITHMETIC.md` (closes finding F-1; documentation completion only, no re-execution).

**Prevention**: any verdict/design-point table must state which estimator governs the verdict and print the CI half-width next to every threshold comparison; never let a plug-in-only table (or an uncorrected review reconstruction) drive a route/design-point decision.

---

### Misattributed parameter count / unit-mixed ratio in prior-cost claims (digit-substring false positive `138516`; 5-bit vs 10-bit symbol mix)

**Observed** (2026-09-21, triple-audit `docs/PRIOR_COST_ACCOUNTING_AUDIT_20260921.md` §3/§6 + `docs/PRIOR_COST_CLAIM_REVIEW_20260921.md` §6): a prior-cost claim quoted `P20Q 138,516 bits ÷ 32,768 symbols`, `PHASE4_P0_PRIOR_CONTRACT.md`, "C03 ≈ 2 parameters", "2545 parameters", and a "~1.8× quantity-order error". Audit: `P20Q`/`138516` zero hits in `docs/`+`src/` (7 repo-wide hits are digit-substrings inside unrelated floats, e.g. `0.0012013851679151025`); the named contract file does not exist; 2545 is the 1M Jan-21 joint support (2M = 2821; CAL nonzero = 139,766); C03 is a 1024-bin smoothed histogram (`nonbinary_v25_gate.py:364-371`); no repo-grounded model yields 1.8× (honest ratios 51–256× / 1.50× / 0.12–0.26× / 1.07×) — 7.84/4.23 ≈ 1.856 matches the GF(32) 5-bit-symbol vs full 10-bit-symbol unit conversion exactly.

**Root cause**: two compounding traps — (i) quoting numbers without a repo-wide existence check (digit-substring grep hits look like evidence; a missing source document goes unnoticed); (ii) the repo uses "symbol" in two senses (V80 accounting = GF(32) 5-bit unit, net 3.92 b/sym; V13/V25 channel = full 10-bit ToA symbol, net 7.84 b/sym), so dividing a V80-scale net by a V13-scale denominator fabricates a ~1.86× factor.

**Fix**: before quoting any cost/ratio number, (1) grep the exact digit string repo-wide AND confirm a prose/code/manifest source (substring-inside-float ≠ evidence); (2) state the support-count source dataset (2545/2821/139766/≈2400), bits-per-parameter basis, denominator pool + reuse model, and symbol basis (GF(32) vs full ToA); (3) never mix V80 nets with V13 denominators.

**Prevention**: any future prior/disclosure-cost arithmetic must print the four-tuple (k-source, bits/param, pool+reuse, symbol basis) alongside the ratio; treat any un-sourced "~1.8×" as a unit-mix suspect until the tuple is shown.

### Joint-entropy bias correction applied to a conditional entropy (A1 MM estimand error)

**Observed** (2026-09-21, `comparison_bench/src/comparison_bench/cli/p3_census_a1.py:349`): plug-in is conditional `Ĥ(A|B)=H_L1+H_L2` (chain rule over the F03 bijection) but the added Miller–Madow term is the joint correction `(K_AB−1)/(2N·ln2)`; correct first-order conditional term is `(K_AB−K_B)/(2N·ln2)`, so the code over-corrects by `(K_B−1)/(2N·ln2)` (optimistic: H up ⇒ f down ⇒ m_max up). `K_B` was never persisted (transient `p_b`, line 103) and is unrecoverable from the summary JSONs — max plausible over 0.82σ/0.76σ/0.65σ of CI halfwidth, no verdict flip. Authority: `docs/A1_ESTIMATOR_AND_SLOPE_VERIFICATION_20260921.md` T1–T2.

**Root cause**: Miller–Madow biases subtract across the `Ĥ(A,B)−Ĥ(B)` decomposition (joint `(K_AB−1)` minus marginal `(K_B−1)`); copying the textbook joint formula onto a chain-rule conditional plug-in silently changes the estimand.

**Fix**: state the estimand (joint vs conditional) next to every bias-correction formula; persist the marginal support (`K_B_train` minimum) so the correction is auditable without re-reading raw data.

**Prevention**: any entropy-correction code must print `(K_AB, K_B, N)` and the applied term; reviewers check the correction's K against the plug-in's estimand, not just its algebra.

---

### Bootstrap interval halfwidth presented as a sigma multiple ("~9σ")

**Observed** (2026-09-21): a threshold–H gap of 0.0257 was reported as "~9σ beyond its bootstrap CI" — but 0.00285 was the percentile-interval halfwidth, not a standard deviation, and the interval does not bracket the plug-in point estimate. Withdrawn; replaced by halfwidth-ratio form (≈9.0× CI hw). Authority: `docs/V80_BASELINE_20260921.md` §3.

**Root cause**: a percentile interval on a statistic has no σ semantics; dividing a gap by its halfwidth yields an interval multiple, which sounds like significance but is not.

**Fix**: report "gap ≈ N.N× CI halfwidth (interval multiple, NOT σ)" and state whether the interval brackets the point estimate before any significance-flavoured language.

**Prevention**: ban bare "σ" for bootstrap/resampling intervals unless a standard error was actually estimated; verdict tables print the halfwidth next to every threshold comparison.

---

### One-time calibration cost charged as a per-block cost (36-bit m≤201 overreach)

**Observed** (2026-09-21): 36 b prior-disclosure cost charged against a single block's 4.3075 b headroom ⇒ m≤201 was stated unconditionally; amortized once per same-source batch it is 36/200≈0.18 b (1M) or 36/364≈0.099 b (2M) ⇒ 0.036/0.020 rows ⇒ m≤201 does NOT follow. Authority: `docs/V80_BASELINE_20260921.md` §2(a).

**Root cause**: a one-time cost was divided by 1 block instead of by the batch it serves; the charging model (per-block vs per-batch, batch size) was never stated.

**Fix**: every cost-consequence claim states its charging model + amortization basis FIRST (bits disclosed, encoding, protocol, per-block vs per-batch); underdetermined models yield conditionals ("ONLY under per-block charging"), never headline consequences.

**Prevention**: any "cost forces design-point move" claim must show the per-block figure under both models side by side before the relocation follows.

### S0.1 batch-end F1 — 行级 status='success' 语义

**Observed**: 含 `undetected` 的失败行仍可能记为行级 `status='success'` / `decoded=1`。

**Root cause**: 行级 `status`/`decoded` 反映解码器收敛语义，不等于验证成功；summary 级 `k` 会计正确，但下游若按 `status`/`decoded` 聚合成功数会得到错误计数。

**Fix**: 成功数以权威列 `failed`/`k` 为准，且须与 FER、`undetected` 联读；严禁按 `status`/`decoded` 聚合成功数。

**Prevention**: 任何下游聚合/报表在取成功数前先确认使用 `failed`/`k` 列；证据见 `docs/research_cycles/V80-NBLDPC-JAN21/S0_1_BATCH_END_REVIEW.md` F1。

### Pre-RESULT 结稿跨源合并计数 + 授权块留空（M0 B1/B2 初审 FAIL）

**Observed** (2026-09-24): M0 (`G-M0-REALFRAME`) 独立 Pre-RESULT 初审两项 FAIL —
B1: 草稿把三源计数合并为 `103/1/910`（fails / undetected / fails_full10 的跨源总和），
违反 PREREG §3“逐源逐臂分列、禁止跨源/跨臂合并任何计数”；B2: §8 授权块空白。
返工删除合并数、按源/臂分列并补填授权后，重审 PASS。

**Root cause**: 汇总时顺手跨源求和，以及把授权块当“格式栏”留到最后填——
两类违规都只靠人眼才会暴露，首轮审稿未按字符串级检查执行。

**Fix**: 删除一切跨源合并数字，恢复逐源逐臂分列；授权块按“空 = 未授权”逐字填充；
FAIL 记录保留在案（返工史进 decision-log），不覆盖初审结论。

**Prevention**: 独立 Pre-RESULT 把两条列为 checklist 首项并做字符串级核查：
① grep 授权块/签字块是否空白；② 扫描结果表中任何“三源合计/总计”式数字；
§3 no-merge 与 §8 non-blank 未逐项确认前不得返回 PASS。

### 后端错标教训：`numpy-minsum-fallback (assumed)` 禁标真体，后端以 sidecar 为准（M2-LAYEREDBIN-SYNTH T2）

**Observed** (2026-09-24/25): 12 臂 RESULT md 把后端记为 `true binary SPA`，实际恒为 `numpy-minsum-fallback (assumed, 非ldpc.BpOsdDecoder)`。

**Root cause**: 执行记录沿用了真体标签写法，未显式标注 assumed 先验 + 非 ldpc 后端。

**Fix**: 以各臂 `backend_used.sidecar.json` 为准纠正（`BACKEND_CORRECTION.md` §1–§2）；旧三件未改（见 HASH_MANIFEST）；B4 转 retained-assumed 诊断，禁 promotion/选点/真实结论。

**Prevention**: 执行记录须显式写 `assumed` + 后端以 sidecar 为准；assumed 后端禁标真体名称。

### 展示 f 列完全不含披露项，结构上无法区分方法（M2 真实比较）

**Observed** (2026-09-27): M2 真实比较结果表同 m 下 HDC 与 LB 的 `f_notag` 完全相等（1M/m=197 两臂同为 1.20048829），而两臂实测 `leak_EC` 差 2.64x（1,707,485 vs 646,160 bits；实际去 tag 比 10.15137 vs 3.84156）。

**Root cause**: 展示列 `f_notag = 5m/(1024·H)` 与 `f_super = (5m+64)/(1024·H)` 的公式内不存在 `leak_EC`、tag 或任何族相关项——只取 `(m, H)`。同 m 同 H 基下跨族相等是机械强制的；该列在结构上无论实际发生什么都无法区分方法。初审 A-CMPE 披露 PASS 只查了列齐全，未查此一致性。

**Fix**: 凡引用效率/披露数字，先核对公式是否含泄漏（EC）项；展示 f 与实测披露并存时，一律并列实测 `leak_EC` 派生比并标注口径，不得以展示 f 代替实际披露。

**Prevention**: 独立 Pre-RESULT 把“f 公式含泄漏项？”列为披露会计首查：grep 公式定义，确认分子含 `leak_EC`/EC 实测项；凡闭式仅为 `(m, H)` 的名义列，一律标 `historical-nominal` 并禁排名。详见 `docs/research_cycles/M2-REALCOMP/`（`MAIN_ADJUDICATION_20260926.md` 发现 1、`CORRECTION_RESULT.md` §8、`CORRECTION_RECOMPUTE_CHECK.md` §E-1）。

### tag 形状错标：joint `M + 64` 把 tag 双计、每格超额虚胖恰 64 bit（C-1/C-2/C-3 机检修复；Stage 0 无错）

**Observed** (2026-09-28): `JOINT-PRICING` 把 `M(f) = ceil(1024·f·H)` 标为 “leak”，并以 `T_single = M + 64`（vs 1104）/ `T_recorded = M + 1024`（vs 2064）比预算——joint ceil 本身已是含 tag 的 TOTAL，`M + 64` 每格超额恰多算 64 bit。修正后名义总量 1100 vs 1104（余 4 bit）、`+20%` 回退总量 1319 vs 1104（超 215 bit）；原 §5.2 executed KILL 撤回为 executed-but-miscounted 证据保留，修正数落入 §5.3(a) **MARGINAL** 带。Stage 0 **未犯此错**：十块形状为十个逐面纯 parity `m_k` 加一次共享 tag（1875 / 超 771；回退 2233 / 超 1129 均 verified-standing）。

**Root cause**: 错标烘进冻结 spec 散文（“Joint leak `M(f) = ceil(1024·f·H)`”），两个脚本忠实实现；joint fake test 断言的是**错门的自我一致**（`test_joint_pricing_fake.py:42-43` `totals_single(1040) == 1104`；`:54-56` excess `== m − 1040`，且 exercised 在真值 m = 1100、1319 上）；跨阶段核对确认两阶段共用一个标签却计算不同类别——诚实总量 vs 误计总量。**没有任何检查把 total 构造锚定到 A1–A2 权威定义**（`m0_realframe_runner.py:101-106`、`S2_ACCOUNTING_MAP_20260920.md:16`）。

**Fix**: 单一权威定义落 `docs/research_cycles/PERPLANE-BINARY-LDPC/STAGE0_PACKET.md` §16.1（恒等式 I-TOTAL / I-LEAK / I-BUDGET / I-GATE / I-SHAPE：单块形状 ceil 即总量；十块形状 `Σ m_k + 64`，tag 恰好一次）；joint 包按 append-only 追加 §17（§§1–16 原样保留），撤回 executed KILL、保留修正数；JOINT-PRICING-R2 按 §16.3 机检接线重估，裁决 MARGINAL（§5.3(a)；独立批末审查 PASS with comments，案卷 `workspace/jp_46c7ab3c/BATCH_END_REVIEW.md`）。

**Prevention**: 定价/算术阶段必须把预算比较量暴露为纯函数，fake test 用**真实函数 + 手常数**断言包内声明的形状恒等式：§16.3 的 **C-1**（total/leak/预算恒等式）、**C-2**（陷阱断言：单块阶段 `Q == ceil(f·N·H) + TAG` 即 FAIL——本可在 joint 执行前抓住）、**C-3**（十块：`FRAME_TOTAL − Σ PLANE_PARITY == 64`，漏加与双加都翻车）；仅比较器式断言（如 `within_budget(1100)`）必要但不充分；Pre-EXECUTE 跑 F-1…F-4 禁用模式 grep 并由评审对每个命中书面处置。权威引用：`STAGE0_PACKET.md` §16.1/§16.3 与 `JOINT-PRICING/PREREG_AND_AUTH.md` §17。

### Scaling `I(f)` 包字面勘误：§3.1 写 disclosed set 笔误，执行按信息集 N−L 最优 Z（2026-09-29）

**Observed**: Scaling-bound 包 §3.1 把 `I(f)` 字面写成 disclosed set，与包内执行语义不一致。

**Root cause**: 冻结 spec 散文一字笔误；执行实际采用信息集读法（N−L 最优 Z），文字未同步勘误。

**Fix**: 后继包复用此界前必须先勘误该字面，执行口径以信息集读法为准；禁对“一字之差”自行解释沿用。

**Prevention**: 复用含公式散文的包前，先对关键符号定义做字面-执行一致性核对；发现字面与执行分歧时先勘误再复用。

### Residual N-R1 cross-baseline：`g_hi` 与 `g_equiv` 分母/H/设门全不同、不可通约（2026-09-29）

**Observed**: `g_hi = 0.10236`（跨 N 界，H-1，FER*=1e-3，分母≈1.27）与 `g_equiv = 0.02547`（N 内从名义锚回退至 64-bit 线，H-5，无 FER 门，分母 1.3）被置于同一标尺比较。

**Root cause**: 两数分母、H 源、设门问题均不同，属 cross-baseline；量级不可通约为增益。D-2 §4 原措辞「不同量纲」欠准。

**Fix**: 唯一许可推断是 `SCALING-BOUND-EXCLUDES`（仅对跨 N 增益门）不转移至薄边际问题；任一方向均不许可可行/增益/方法推断；D-2 措辞更正为「不同基线/不同问题；量纲齐次成立但增益不可通约」。

**Prevention**: 引用任何增益比值前，先并列分母、H 源、FER 门三元组；三元组任一不同即标 cross-baseline 并禁同标尺比较。

### TABLE 缺陷 N1：`f_star` 回显 `f_scan`、`g_synth` 列空，两列永久禁读（2026-09-29）

**Observed**: Gain-sweep TABLE 的 `f_star` 列回显 `f_scan` 输入、`g_synth` 列空，读数不可信。

**Root cause**: 表格生成列映射缺陷，输出列未填入真实计算值；§5 repair 额度已在 `KeyError: 't_pred'` 处消耗。

**Fix**: 该两列永久禁读，一律由 `f_scan`/`fer_emp` 重算；干净 TABLE 需新窄包新授权；禁二次修复。

**Prevention**: 落盘任何派生列前，先抽查列值非回显输入、非空；repair 额度消耗点留档，后续同包缺陷只记录不二次修复。
