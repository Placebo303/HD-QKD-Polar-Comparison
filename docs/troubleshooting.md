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
