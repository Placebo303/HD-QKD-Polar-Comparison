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
