# Design: V72P2D5 P0 Model-F consumer path fix

Status: `IMPLEMENTATION_CANDIDATE_ONLY`. No execution, no authorization, no
CAL/VAL/raw read, no formal output. All constants below are frozen from the
accepted R2_DV3 plan and current core/tests; this change invents no
scientific value.

## 1. Loader resolution by file path (T1)

Anchors (verified, not re-derived):

- `Path(__file__).resolve().parents[4]` is the repository root
  (`formal_ir` -> `comparison_bench` -> `src` -> `comparison_bench` ->
  root).
- The Model-F module is the sibling file
  `Path(__file__).resolve().parent / "v72p2d5_model_f_input.py"`.

`_load_model_f_loader()` loads it with
`importlib.util.spec_from_file_location` + `module_from_spec` +
`exec_module` and returns its `load_model_f_input`, inside the helper as
now (no import-time behavior change). No `sys.path` mutation, no cwd
dependence, no directory search, no fallback chain of guesses, no
try/except around the path arithmetic.

Transitive dependency, handled minimally: the sibling module imports
`build_canonical_counts` from the contrast module
`v72p2d3_gf32_contrast.py`, whose own top-level imports are stdlib/numpy
only. The loader therefore loads the contrast module by file path first
and registers it in `sys.modules` under both dotted names the sibling
tries (`comparison_bench.formal_ir...` and
`comparison_bench.src.comparison_bench.formal_ir...`; existing entries are
kept via `setdefault`, never overwritten). The sibling's own import then
succeeds with no `sys.path` change. Without this step the sibling's
`exec_module` would raise `ImportError` under script launch and the fix
would be ineffective; this step completes T1 rather than extending it.
The sibling module itself is unmodified (outside the change allowlist).

## 2. Artifact-root resolution against the repository root (T2)

`MODEL_F_INPUT_FORMAL_ROOT` stays the frozen relative string
`"workspace/v72p2d5_model_f_input/20260907_r1"`.
`_resolve_model_f_input_root()` anchors it: relative values resolve
against the T1 repository root; absolute values resolve directly. Same
root-anchoring contract as the prepare script's path resolver (mirrored,
not imported). No cwd, no search, no fallback. Monkeypatched absolute
roots in existing tests keep working (absolute passes through).

## 3. Three-way failure separation (T3)

`MODEL_F_BLOCKED` (`MODEL_F_INPUT_BLOCKED_MISSING_CAL_TRAIN_COUNTS`) is
kept as the constant for the genuine missing-input case so existing
asserts keep their meaning. Two new distinct constants:

- `MODEL_F_LOADER_UNAVAILABLE = "MODEL_F_INPUT_LOADER_UNAVAILABLE"`:
  the Model-F module file is missing or fails to execute. An
  environment/implementation fault, never missing scientific input; the
  message never says `MISSING_CAL_TRAIN_COUNTS`.
- `MODEL_F_INPUT_INVALID = "MODEL_F_INPUT_INVALID"`: the artifact is
  present but the loader's own validation rejects it (shape, dtype, sum,
  marginal, summary, file set). Surfaces the loader's underlying error,
  never relabelled as missing input.

`_load_model_f_input_or_blocked` behavior:

1. Injected `counts_ab`+`p_b` short-circuit (unchanged, zero filesystem
   access).
2. Loader faults propagate as loader-unavailable (chained with
   `raise ... from ...`).
3. Resolved root that is not a directory raises genuine `MODEL_F_BLOCKED`
   naming the resolved absolute path.
4. `FileNotFoundError`/`NotADirectoryError` during load (files missing
   under an existing root) raise genuine `MODEL_F_BLOCKED` naming the
   resolved absolute path, chained.
5. `ValueError` from loader validation raises `MODEL_F_INPUT_INVALID`
   with the loader's error chained.
6. Any other exception propagates raw: surfaced, never relabelled as
   missing input.

No broad `except` swallows a cause; every mapped error chains the
original.

## 4. Regression tests for the real launch condition (T4, additive)

In `comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py` only, new
`M22a`--`M22e` cases using `tmp_path` artifacts; none reads the real
Model-F root:

- (a) Repo-root resolution is cwd-independent: chdir to `tmp_path`, assert
  the resolved root equals the repo-anchored formal root. Path assert
  only; no artifact load.
- (b) Loader resolves with repo root, `src`, and `''` removed from
  `sys.path` and all `comparison_bench*` entries purged from
  `sys.modules`; pointed at a `tmp_path` artifact written in the test via
  the sibling's own writer. Asserts round-tripped content, i.e. no
  loader-unavailable error.
- (c) Absent artifact gives genuine missing-input, message naming the
  resolved absolute path.
- (d) Present-but-wrong file set gives the invalid outcome, never the
  missing-input outcome.
- (e) Injected tables short-circuit with loader and resolver boomed and
  `tmp_path` left empty (zero filesystem access).
- (f) By construction: new tests call the helper directly, never a
  synthetic runner with `authorized=True`, so SAFE A/B/C and the
  `test_TIS_static_authorized_synthetic_isolation` AST guard hold
  unweakened; `T0_38` (no `def load_`, no `load_*` attribute), `T1_13`
  (import guard), `T1_14` (no data-read fragments, `open(` count), `T1_21`
  (no hash), `T1_22` (no write calls in test source), and
  `test_P0G1G2_f_no_holdout_or_file_access` all still pass.

## 5. Verification (T5)

- `py_compile` on the touched core module and the scripts CLI.
- Full focused suite (`test_v72p2d5_model_f_input.py`,
  `test_v72p2d5_gf32_rate_mother.py`,
  `test_v72p2d4_cal_gf32_model_rate_audit.py`) with a fresh `--basetemp`
  under `workspace/`; additive cases raise the count; no previously
  passing test may fail. (Known pre-existing failure:
  `test_T1_22_openspec_history_zero_mod` fails on this worktree before and
  after because unrelated `src/`/`experiments/`/`tools/` files are
  modified; it is out of this change's allowlist and stays untouched.)
- Unauthorized refusal unchanged: `python
  scripts/v72p2d5_gf32_rate_mother.py --phase p0-cost` prints a refusal and
  exits 3, creating nothing.
- `workspace/v72p2d5_p0_cost/20260906_r1` and
  `workspace/v72p2d5_g2/20260906_r1` still absent; Model-F, G0,
  G0-recovery, G1, structure roots byte-identical by stat before/after.
- End-to-end proof is impossible here: it requires a new authorized P0
  run, which is not authorized. The fix is delivered as a candidate for
  independent review, not as a proven run.

## 6. Authorization gate

`is_phase_authorized` remains the single choke; all
`*_execution_authorized` stay false; `next_gate: P0_PACKET_REVIEW`. This
change grants no authorization. The consumed 2026-09-07 P0 authorization
is wasted; a NEW P0 authorization is required before any further P0 run,
after independent review of this candidate.

## 7. Explicitly not in design

Decoder changes, prepare-script runs, CAL/VAL reads, new CLI flags, frozen
constant or threshold changes, output-root changes, retry/cache/config/
hash machinery, framework generalization, scientific claims.
