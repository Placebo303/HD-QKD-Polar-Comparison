# V72P2D5 P0 Model-F consumer path fix (implementation candidate only)

- Change: `v72p2d5-p0-model-f-consumer-path-fix`
- Predecessor: `v72p2d5-p0-g1-g2-production-path` (P0/G1/G2 production-path candidate)
- Cycle: `V72P2D5-GF32-RATE-MOTHER`
- Lifecycle: `IMPLEMENTATION_CANDIDATE_ONLY` (no execution, no authorization)
- Branch: `formal-ir-v72p1-addendum-clean` (per task packet)
- Gate: `next_gate: P0_PACKET_REVIEW` (unchanged by this change)

## Goal

Fix the Model-F consumer load path so an authorized P0 run reaches the
accepted Model-F artifact instead of refusing with a false missing-input
verdict. Produce an implementation candidate only.

## Why

On 2026-09-07 an authorized P0 invocation refused in 0.376 s with:

```text
phase 'p0-cost' refused: MODEL_F_INPUT_BLOCKED_MISSING_CAL_TRAIN_COUNTS: ...
```

The message is false. The accepted artifact at
`workspace/v72p2d5_model_f_input/20260907_r1/` is present and valid:
loading it directly by file path yields `counts_ab (1024,1024)` summing to
`262144` and `p_b (1024,)` summing to `1.0`. One consumed P0 authorization
produced no run.

## Defect statement (frozen)

`_load_model_f_input_or_blocked`
(`v72p2d5_gf32_rate_mother.py:2170`) reached the artifact through a package
import:

```python
from comparison_bench.formal_ir.v72p2d5_model_f_input import load_model_f_input
# fallback
from comparison_bench.src.comparison_bench.formal_ir.v72p2d5_model_f_input import ...
```

When the CLI is launched as `python scripts/v72p2d5_gf32_rate_mother.py`,
`sys.path[0]` is `scripts/` and the current directory is **not** on
`sys.path`. Both imports raise `ModuleNotFoundError: No module named
'comparison_bench'`. Reproduced: with the repo root off `sys.path` the
import fails; with it on (`python -c`) it succeeds.

The CLI already solves exactly this for the core module: it derives `ROOT`
from `__file__` and loads by file path via `importlib`. The consumer did
not inherit that technique.

Second defect: the `except Exception` at line 2193 collapsed import
failures, path failures, and genuine missing input into one message naming
a missing scientific input. A present, valid artifact was reported as
missing.

Third defect, structural: the 195-test suite passes because every test
either injects tables or monkeypatches the root, and pytest puts the
rootdir on `sys.path`. **No test exercised the real launch condition.**

## Scope

- Resolve the Model-F loader module from `__file__` by file path
  (`importlib.util.spec_from_file_location` + `module_from_spec` +
  `exec_module`), inside the helper as now; no `sys.path` mutation, no cwd,
  no directory search, no fallback chain.
- Resolve `MODEL_F_INPUT_FORMAL_ROOT` against the repository root when
  relative; absolute values pass through (same root-anchoring contract as
  the prepare script's path resolver; not imported).
- Separate three outcomes: loader-unavailable (new constant, never the
  missing-input string), artifact-absent (genuine `MODEL_F_BLOCKED` naming
  the resolved absolute path), artifact-invalid (new constant surfacing the
  loader's validation error, chained).
- Additive regression tests for the script-launch condition using
  `tmp_path` artifacts only; no test reads the real Model-F root.
- This change consumes no authorization and grants none. A **NEW P0
  authorization is required** before any further P0 run; the consumed
  2026-09-07 authorization is wasted and cannot be reused.

## Non-Goals

- No P0/G1/G2 execution or authorization in this change. No
  `p0_cost/g1/g2_execution_authorized=true`, no decoder run, no `run_01`,
  no formal output creation.
- No CAL/VAL/raw/real-data read during implementation or tests
  (`cal_rows_read=0`, `val_rows_read=0`); no `pandas.read_parquet` anywhere.
- No change to `cycle_state.yaml` (all authorized stay false,
  `next_gate: P0_PACKET_REVIEW`).
- No change to frozen scientific constants (seeds, `f` sets, `m1`/`m2`
  tables, `CE_*`, `LAMBDA_STAR`, `MAX_ITER`, damping, budgets, call/block
  counts, output roots, thresholds).
- No out-of-scope refactor: no framework, retry, cache, config, hash, or
  broad-except machinery.
- No scientific claim; no statement that P0 will now pass. End-to-end proof
  requires a new authorized P0 run, which is not authorized here.

## Impact Scope

- Code (candidate only, no execution):
  `comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py`
- Tests (additive cases only):
  `comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py`
- Docs (this change only):
  `openspec/changes/v72p2d5-p0-model-f-consumer-path-fix/`
- Explicitly untouched: `src/`, `experiments/`, `tools/`, `results/`,
  frozen D5 plan files, `cycle_state.yaml` authorizations, formal
  `workspace/v72p2d5_*` roots (Model-F, G0, G0-recovery, G1 byte-identical;
  P0-cost/G2 still absent).

## Acceptance Criteria

- [ ] Loader module resolves from `__file__` with repo root and `''`
  removed from `sys.path` (regression test proves it against a `tmp_path`
  artifact).
- [ ] Relative formal root resolves cwd-independently against the repo root;
  absolute values pass through.
- [ ] Loader-unavailable never reports missing input; absent artifact reports
  genuine `MODEL_F_INPUT_BLOCKED_MISSING_CAL_TRAIN_COUNTS` with the resolved
  absolute path; invalid artifact reports the invalid outcome with the
  loader's error chained.
- [ ] Injected `counts_ab`+`p_b` still short-circuit with zero filesystem
  access.
- [ ] SAFE A/B/C containment and the AST static guard hold unweakened; no
  previously passing test fails.
- [ ] `py_compile` clean; unauthorized `--phase p0-cost` still refuses with
  exit 3 creating nothing; no frozen constant or authorization changed.
- [ ] Independent review happens before any new P0 authorization; this fix is
  not end-to-end proven until a newly authorized P0 run.
