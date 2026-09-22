# D5-G1-CODE-REVIEW-SCOPE-ADDENDUM-A1

## Purpose

Complete one missing independent-review item. The original review ran two
pytest files (`189 passed`) after interpreting “three-file suite” as core plus
two tests. The frozen implementation packet actually named these three pytest
files:

1. `comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py`
2. `comparison_bench/tests/test_v72p2d5_model_f_input.py`
3. `comparison_bench/tests/test_v72p2d4_cal_gf32_model_rate_audit.py`

The main thread independently ran the exact set and observed
`219 passed, 1 warning in 24.22s`, but main-thread evidence does not replace the
missing independent-review run.

This addendum does not reopen C1–C8 or D/A traceability unless the full suite
finds a failure.

## Hard constraints

- No decoder, no `--phase`, no prepare/verify, no CAL/VAL/parquet-row read.
- No code, existing document, OpenSpec, state, decision-log, or memory edit.
- No git write operation and no push.
- No write to formal evidence roots.
- Use a new unique basetemp under `workspace/`; do not reuse or delete
  `workspace/d5_g1_main_verify_20260908a` if it exists—it belongs to the main
  thread and is not formal evidence.
- Only one new file is allowed:
  `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/G1_READINESS_CODE_REVIEW_SCOPE_ADDENDUM_A1.md`.

## Procedure

1. Snapshot all D5 formal roots by existence and top-level name/size/mtime.
2. Confirm proposed G1 `20260907_r2` and G2 roots are absent.
3. Run exactly:

```text
python -m pytest \
  comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py \
  comparison_bench/tests/test_v72p2d5_model_f_input.py \
  comparison_bench/tests/test_v72p2d4_cal_gf32_model_rate_audit.py \
  -p no:cacheprovider \
  --basetemp workspace/<unique-review-addendum-name> \
  -q --tb=line
```

PowerShell may place this on one line. Do not change the three paths.

4. Require zero failures. The known `Unknown config option: cache_dir` warning
   is benign.
5. Re-snapshot formal roots and require exact equality; G1/G2 new roots remain
   absent.
6. Remove only this addendum's own verified basetemp if the environment permits.
   Cleanup failure is reported and does not alter the scientific verdict if the
   path is confirmed task-specific and outside formal roots.

## Output

Create the one addendum file with:

- original review verdict and exact scope gap;
- exact command and literal pytest summary;
- pre/post root comparison;
- any cleanup residue;
- commands not executed;
- one verdict:
  - `G1_CODE_REVIEW_SCOPE_ADDENDUM_PASS`, which completes the test-scope item
    and leaves `G1_READINESS_CODE_REVIEW_PASS` effective; or
  - `G1_CODE_REVIEW_SCOPE_ADDENDUM_FAIL`, which suspends the prior PASS and
    names the failing test IDs.

Do not commit.

Final line:

`G1 代码评审测试范围已补齐；该补遗不构成授权，G1 未执行。`

