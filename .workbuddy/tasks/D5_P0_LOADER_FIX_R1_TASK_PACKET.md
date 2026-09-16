# TASK PACKET — D5-P0-LOADER-FIX-R1: fix the Model-F consumer load path (code, no execution)

Target executor: implementation session (coder). Read this whole file first.
This packet changes production code. It does **not** run P0, G1, or G2.

- Repo: `D:/Code/HD-QKD_Polar_Comparison`
- Branch: `formal-ir-v72p1-addendum-clean`, HEAD at start `3ecaebb6`
- Cycle: `V72P2D5-GF32-RATE-MOTHER`, gate `next_gate: P0_PACKET_REVIEW`
- Lifecycle: `IMPLEMENTATION_CANDIDATE / EXECUTE_NOT_AUTHORIZED`
- Follow-up (not yours): independent review, then a NEW P0 authorization.

---

## 0. HARD PROHIBITIONS

You MUST NOT:

1. Run P0, G1, or G2. No `--phase p0-cost|g1|g2` invocation except the
   unauthorized-refusal check in T5, which must exit 3.
2. Run any decoder. Run `scripts/v72p2d5_prepare_model_f_input.py` at all.
3. Read CAL / VAL / raw parquet rows; `pandas.read_parquet` is forbidden.
4. Read, write, modify, delete, move, or hash anything under
   `workspace/v72p2d5_model_f_input/`, `workspace/v72p2d5_g0*/`,
   `workspace/v72p2d5_g1/`, or `workspace/v72p2d5_structure/`.
   **In particular: no test may read the real Model-F artifact.** That
   lifecycle coupling is what caused the unauthorized-G1 incident. Tests use
   `tmp_path` artifacts only.
5. Create `workspace/v72p2d5_p0_cost/...` or `workspace/v72p2d5_g2/...`.
6. Change any `*_execution_authorized`, `next_gate`, or any other
   `cycle_state.yaml` value.
7. Change any frozen scientific constant: seeds, `f` sets, `m1`/`m2` tables,
   `CE_*`, `LAMBDA_STAR`, `MAX_ITER`, damping, budgets, call counts, block
   counts, output roots, grading thresholds.
8. Refactor beyond the stated scope. No new framework, no retry logic, no
   caching, no config system, no hash/checksum machinery, no broad `except`.
9. `git push`, `git add -A`, `git add .`, `git commit -a`, `git reset`,
   `git stash`, `git checkout --`, `git clean`, `git rebase`,
   `git commit --amend`.
10. Claim any scientific result, or state that P0 will now pass.

Allowlist — you may modify only:
- `comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py`
- `comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py` (additive cases only)
- a NEW OpenSpec addendum directory (T6)

No other file. If a task is ambiguous, STOP and report; do not guess.

---

## 1. The defect (established, do not re-litigate)

On 2026-09-07 an authorized P0 invocation refused in 0.376 s with:

```
phase 'p0-cost' refused: MODEL_F_INPUT_BLOCKED_MISSING_CAL_TRAIN_COUNTS: ...
```

The message is false. The accepted artifact at
`workspace/v72p2d5_model_f_input/20260907_r1/` is present and valid — loading
it directly by file path yields `counts_ab (1024,1024)` summing to `262144`
and `p_b (1024,)` summing to `1.0`.

Root cause, verified: `_load_model_f_input_or_blocked`
(`v72p2d5_gf32_rate_mother.py:2170`) reaches the artifact through a package
import:

```python
from comparison_bench.formal_ir.v72p2d5_model_f_input import load_model_f_input
# fallback
from comparison_bench.src.comparison_bench.formal_ir.v72p2d5_model_f_input import ...
```

When the CLI is launched as `python scripts/v72p2d5_gf32_rate_mother.py`,
`sys.path[0]` is `scripts/` and the current directory is **not** on `sys.path`.
Both imports raise `ModuleNotFoundError: No module named 'comparison_bench'`.
Reproduced: with the repo root off `sys.path` the import fails; with it on
(`python -c`) it succeeds.

The CLI already solves exactly this for the core module — it derives `ROOT`
from `__file__` and loads by file path via `importlib`. The consumer did not
inherit that technique.

Second defect: the `except Exception` at line 2193 collapses import failures,
path failures, and genuine missing input into one message that names a missing
scientific input. A present, valid artifact was reported as missing. This cost
one consumed P0 authorization.

Third defect, structural: the 195-test suite passes because every test either
injects tables or monkeypatches the root, and pytest puts the rootdir on
`sys.path`. **No test exercises the real launch condition.**

## 2. T1 — Resolve the loader module by file path

In `v72p2d5_gf32_rate_mother.py`, resolve the Model-F module the way the CLI
resolves the core module: from this file's own `__file__`, not from `sys.path`.

Verified anchors (use these; do not re-derive):
- `Path(__file__).resolve().parents[4]` is the repository root.
- The Model-F module is the sibling file
  `Path(__file__).resolve().parent / "v72p2d5_model_f_input.py"`.

Load it with `importlib.util.spec_from_file_location` +
`module_from_spec` + `exec_module`, and take `load_model_f_input` from it.
Keep it module-level-importable without side effects; do not import it at
module import time if that would change existing import behaviour — load it
inside the helper, as now.

Constraints: no `sys.path` mutation, no cwd dependence, no directory search, no
fallback chain of guesses, no try/except around the path arithmetic.

## 3. T2 — Resolve the artifact root against the repository root

`MODEL_F_INPUT_FORMAL_ROOT` is the relative string
`"workspace/v72p2d5_model_f_input/20260907_r1"`. Today it is passed straight to
the loader and therefore resolves against the current directory.

Resolve it against the repository root derived in T1 when it is relative;
resolve an absolute value directly. No cwd, no search, no fallback. This is the
same contract already applied to `_resolve_parquet_path` in
`scripts/v72p2d5_prepare_model_f_input.py` (PX11); mirror that behaviour, do
not import from it.

## 4. T3 — Separate the failure modes

Replace the single collapsed message with distinct, honest outcomes. Required
distinctions:

- **Loader unavailable** — the Model-F module file is missing or fails to
  execute. This is an environment/implementation fault, NOT missing scientific
  input. It must NOT say `MISSING_CAL_TRAIN_COUNTS`.
- **Artifact absent** — the resolved root does not exist, or its files are
  missing. This is the genuine
  `MODEL_F_INPUT_BLOCKED_MISSING_CAL_TRAIN_COUNTS`, and it must name the
  resolved absolute path it looked at.
- **Artifact present but invalid** — the loader's own validation rejects it
  (shape, dtype, sum, marginal, summary). This is a distinct outcome and must
  surface the loader's underlying error, not be relabelled as missing input.

Keep `MODEL_F_BLOCKED` as the constant for the genuine missing-input case so
existing asserts on that string keep their meaning. Introduce new distinct
constants for the other two. No broad `except Exception` that swallows the
cause; chain the original exception.

## 5. T4 — Regression tests for the real launch condition (additive)

Extend `comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py` only. Tests
must use `tmp_path` artifacts; **none may read the real Model-F root.**

Required cases:

- (a) **Repo-root resolution is cwd-independent.** With the process chdir'd to
  a `tmp_path`, the resolved artifact root equals
  `<repo root>/workspace/v72p2d5_model_f_input/20260907_r1` — assert on the
  resolved path only; do not load the real artifact.
- (b) **Loader module resolves without the repo root on `sys.path`.** Simulate
  the script-launch condition (repo root and `''` removed from `sys.path`) and
  assert the helper still reaches the loader — i.e. it does not raise the
  loader-unavailable error. Point it at a `tmp_path` artifact you wrote in the
  test.
- (c) **Absent artifact gives the genuine missing-input error**, and the message
  names the resolved absolute path.
- (d) **Invalid artifact gives the invalid outcome**, not the missing-input
  outcome.
- (e) **Injected tables still short-circuit** — `counts_ab` and `p_b` passed
  explicitly must bypass all loading, with no filesystem access.
- (f) The existing SAFE A/B/C containment and the AST static guard still hold;
  do not weaken any of them to make a new test pass.

## 6. T5 — Verification

- `py_compile` on the touched module and on `scripts/v72p2d5_gf32_rate_mother.py`.
- Full focused suite with a fresh `--basetemp` under `workspace/`:
  `test_v72p2d5_model_f_input.py`, `test_v72p2d5_gf32_rate_mother.py`,
  `test_v72p2d4_cal_gf32_model_rate_audit.py`. Reference value before your
  change: `195 passed`. Your additive cases raise that count; **no previously
  passing test may fail.**
- Unauthorized refusal unchanged:
  `python scripts/v72p2d5_gf32_rate_mother.py --phase p0-cost` still prints a
  refusal and exits 3 (because the key is `false`), and creates nothing.
- Confirm `workspace/v72p2d5_p0_cost/20260906_r1` and
  `workspace/v72p2d5_g2/20260906_r1` are still absent, and that the Model-F,
  G0, G0-recovery and G1 roots are byte-identical to before your work (stat
  before and after).

**You cannot prove the real fix end-to-end without an authorized P0 run, and
you are not authorized to make one.** Do not attempt to. State this limit
explicitly in your report.

## 7. T6 — OpenSpec addendum

Create a new change directory
`openspec/changes/v72p2d5-p0-model-f-consumer-path-fix/` with `proposal.md`,
`design.md`, `tasks.md`, mirroring the style of
`openspec/changes/v72p2d5-p0-g1-g2-production-path/`. Record: the defect and
its verified root cause, the three-way failure separation, the cwd-independent
resolution contract, the test gap that let it through, the consumed-and-wasted
P0 authorization, and the explicit statement that a NEW P0 authorization is
required before any further run.

## 8. T7 — Commit (local only, NO PUSH)

Stage only the allowlisted paths, verify with
`git diff --cached --name-only` before committing, and commit once:

```
fix(v72p2d5): resolve Model-F consumer input by file path, not sys.path

The P0 consumer reached the accepted Model-F artifact through a package
import, which fails when the CLI is launched as a script because the repo
root is not on sys.path. A present, valid artifact was reported as
MODEL_F_INPUT_BLOCKED_MISSING_CAL_TRAIN_COUNTS, consuming one P0
authorization with no run.

Resolve the loader module and the artifact root from __file__ against the
repository root, cwd-independent. Separate loader-unavailable and
artifact-invalid from genuine missing input, chaining the original cause.
Add regression tests for the script-launch condition, which no existing
test exercised.

No execution, no authorization change, no frozen constant changed.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>
```

## 9. Report

Report: the diff summary; the literal pytest line before and after; the T5
refusal check; the before/after stat of the protected roots; and these as
`true`/`false` — P0/G1/G2 invoked: false; decoder run: false; CAL/VAL read:
false; real Model-F artifact read by any test: false; any frozen constant
changed: false; any `*_execution_authorized` changed: false; pushed: false.

State plainly: **the fix is not end-to-end proven; that requires a new
authorized P0 run, which is not authorized.** Then stop — the next step is an
independent review, not another run.
