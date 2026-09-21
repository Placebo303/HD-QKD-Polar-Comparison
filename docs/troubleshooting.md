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
