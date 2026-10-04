# Tasks: V72P2D5 P0 Model-F consumer path fix (coder-fast, candidate only)

Frozen packet: D5_P0_LOADER_FIX_R1. No P0/G1/G2 run except the exit-3
refusal check; no decoder; no prepare script; no CAL/VAL/parquet; no
read/write/modify/delete/move/hash under `workspace/v72p2d5_model_f_input/`,
`g0*`, `g1/`, `structure/`; no test reads the real Model-F artifact
(`tmp_path` only); no `p0_cost`/`g2` root creation; no `cycle_state.yaml`
change; no frozen-constant change; no out-of-scope refactor; no push; no
scientific claims. Implement exactly what is specified; if any task is
ambiguous, stop and report (do not guess).
Allowlist:
`comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py`,
`comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py` (additive only),
new `openspec/changes/v72p2d5-p0-model-f-consumer-path-fix/`. Nothing else.

- [x] T1 — Resolve the loader module by file path
  - In `v72p2d5_gf32_rate_mother.py`, resolve the Model-F module from this
    file's own `__file__`: repo root `Path(__file__).resolve().parents[4]`,
    sibling `parent / "v72p2d5_model_f_input.py"`.
  - Load with `importlib.util.spec_from_file_location` + `module_from_spec`
    + `exec_module`; take `load_model_f_input`; load inside the helper as
    now (no import-time behavior change).
  - Minimal completion: preload the sibling's contrast dependency
    (`v72p2d3_gf32_contrast.py`, stdlib/numpy only) by file path and
    register it in `sys.modules` under both names the sibling tries
    (`setdefault`, never overwrite), so the sibling's own import succeeds
    with no `sys.path` change. The sibling file itself is unmodified.
  - Constraints: no `sys.path` mutation, no cwd, no directory search, no
    fallback chain, no try/except around path arithmetic.
  - Verify: helper reaches the loader with repo root off `sys.path` (T4b).

- [x] T2 — Resolve the artifact root against the repository root
  - Relative `MODEL_F_INPUT_FORMAL_ROOT` resolves against the T1 repo root;
    absolute values resolve directly. Mirror the prepare script's
    root-anchoring contract; do not import it. No cwd/search/fallback.
  - Verify: cwd-independence test (T4a); existing monkeypatched absolute
    roots keep working.

- [x] T3 — Separate the failure modes
  - Loader unavailable (module missing/exec fails): new
    `MODEL_F_LOADER_UNAVAILABLE`, never the missing-input string.
  - Artifact absent (root not a dir, or files missing): genuine
    `MODEL_F_BLOCKED` (`MODEL_F_INPUT_BLOCKED_MISSING_CAL_TRAIN_COUNTS`
    kept) naming the resolved absolute path.
  - Artifact invalid (loader validation `ValueError`): new
    `MODEL_F_INPUT_INVALID` surfacing the loader's error, chained.
  - No broad except swallowing a cause; `raise ... from ...` everywhere a
    cause exists; anything else propagates raw, never relabelled.
  - Verify: T4c/T4d plus unchanged M21/i missing-isolation asserts.

- [x] T4 — Regression tests for the real launch condition (additive)
  - Extend `comparison_bench/tests/test_v72p2d5_gf32_rate_mother.py` only:
    (a) `test_M22a_model_f_root_resolves_cwd_independent`;
    (b) `test_M22b_model_f_loader_without_repo_root_on_path`;
    (c) `test_M22c_model_f_absent_reports_missing_with_absolute_path`;
    (d) `test_M22d_model_f_invalid_not_reported_missing`;
    (e) `test_M22e_model_f_injected_tables_short_circuit`.
  - Constraints: `tmp_path` artifacts only (written via the sibling's own
    writer); never the real root; helper called directly, never a
    synthetic runner with `authorized=True`, so SAFE A/B/C and the AST
    static guard hold unweakened (read first, verified by suite).
  - Verify: new cases pass; `T0_38`/`T1_13`/`T1_14`/`T1_21`/`T1_22` guards
    and `test_TIS_static_authorized_synthetic_isolation` unaffected
    (except pre-existing `T1_22` worktree-dirt failure, out of allowlist).

- [x] T5 — Verification
  - `py_compile` on the touched module and the scripts CLI.
  - Full focused suite (`test_v72p2d5_model_f_input.py`,
    `test_v72p2d5_gf32_rate_mother.py`,
    `test_v72p2d4_cal_gf32_model_rate_audit.py`) with a fresh `--basetemp`
    under `workspace/`; additive cases raise the count; no previously
    passing test fails.
  - Refusal check `python scripts/v72p2d5_gf32_rate_mother.py --phase
    p0-cost` prints refusal, exits 3, creates nothing; `p0_cost`/`g2`
    still absent; Model-F/G0/G0-recovery/G1/structure roots byte-identical
    by stat before/after.
  - End-to-end proof impossible without a new authorized P0 run; do not
    attempt; state the limit in the report.

- [x] T6 — OpenSpec addendum
  - This directory (`proposal.md`, `design.md`, `tasks.md`) in the style of
    `v72p2d5-p0-g1-g2-production-path/`: defect + verified cause, 3-way
    separation, cwd-independent contract, test gap, consumed P0
    authorization, NEW authorization required.

- [x] T7 — Commit (local only, NO PUSH)
  - Stage allowlisted paths only, `git diff --cached --name-only` verify,
    ONE commit with the packet §8 verbatim message. Local, no push.
