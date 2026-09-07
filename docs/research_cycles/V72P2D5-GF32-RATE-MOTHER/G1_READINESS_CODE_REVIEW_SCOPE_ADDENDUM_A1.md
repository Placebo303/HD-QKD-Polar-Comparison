# G1 Readiness Code Review Scope Addendum A1

- Original review verdict: `G1_READINESS_CODE_REVIEW_PASS` (`docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/G1_READINESS_CODE_REVIEW_R1.md`).
- Exact scope gap: original review interpreted "three-file suite" as core + two test files and ran two pytest files (`189 passed`). The frozen implementation packet names three pytest files; the third (`test_v72p2d4_cal_gf32_model_rate_audit.py`) was not independently run. This addendum runs exactly that frozen three-file set. It does not reopen C1–C8 or D/A traceability (no failure found).

## Exact command

```text
python -m pytest comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py comparison_bench/tests/test_v72p2d5_model_f_input.py comparison_bench/tests/test_v72p2d4_cal_gf32_model_rate_audit.py -p no:cacheprovider --basetemp workspace/d5_g1_scope_addendum_a1_9d8fe5a5593f4d66bc1e5ebd0c971f20 -q --tb=line
```

Workdir: `D:\Code\HD-QKD_Polar_Comparison`. Basetemp is a new unique review-addendum name; `workspace/d5_g1_main_verify_20260908a` was neither reused nor deleted.

## Literal pytest summary

```text
........................................................................ [ 32%]
........................................................................ [ 65%]
........................................................................ [ 98%]
...                                                                      [100%]
============================== warnings summary ===============================
..\..\software\Miniforge3\Lib\site-packages\_pytest\config\__init__.py:1434
  D:\software\Miniforge3\Lib\site-packages\_pytest\config\__init__.py:1434: PytestConfigWarning: Unknown config option: cache_dir

    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
219 passed, 1 warning in 23.61s
```

Zero failures. Known `Unknown config option: cache_dir` warning is benign.

## Pre/post root comparison

- Pre: `workspace/v72p2d5_g1/` → `[20260906_r1]` (2026/9/7 2:35:32); `20260906_r1/` → `execution_summary.json` 267 B / `report.md` 146 B / `results.json` 2593 B / `table.csv` 126 B (same mtime); `20260907_r2` absent (`False`); `v72p2d5_g2/` absent (`False`).
- Post: names/sizes/mtimes character-identical to pre; both new G1/G2 roots still absent (`False`, `False`).
- Equality holds. No workspace-evidence hashing; VOID/Model-F contents never read.

## Cleanup residue

None. Own basetemp resolved (`D:\Code\HD-QKD_Polar_Comparison\workspace\d5_g1_scope_addendum_a1_9d8fe5a5593f4d66bc1e5ebd0c971f20`), prefix-verified under `workspace/`, removed via `Remove-Item -Recurse -Force`; post `Test-Path False`. `workspace/d5_g1_main_verify_20260908a` untouched (`True` before and after).

## Commands not executed

No decoder; no `--phase` of any kind; no prepare/verify; no CAL/VAL/parquet-row read; no real Model-F artifact or VOID-root content read; no write to any formal root; no edit to code/existing docs/OpenSpec/state/decision-log/memory; no git write or push; no real external-file probe.

## Verdict

`G1_CODE_REVIEW_SCOPE_ADDENDUM_PASS`

(Completes the test-scope item; leaves `G1_READINESS_CODE_REVIEW_PASS` effective. Authorizes nothing; G1 unexecuted.)
