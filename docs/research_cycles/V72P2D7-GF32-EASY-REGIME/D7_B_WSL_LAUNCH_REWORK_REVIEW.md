# D7-B WSL launch-rework code review (independent pass)

Review mode: independent pass over the committed rework (`04b7a8e`, parent
chain `9e41e0d` → `13c1c3c` → `cc387e7` → `04b7a8e`). Nothing was edited;
only this file is created. Checks were recomputed from git objects and fresh
subprocess reruns, never by quoting the operator's conclusions. Zero decoder
calls; no root created.

## Scope inspected

`git diff 9e41e0d..HEAD --name-only` yields exactly 9 files: 2 blocked-run
docs + disposition (T0), troubleshooting entry (T0), design/tasks delta +
WSL addendum (T1), runner script + D7-B test file (T2). `comparison_bench/src/`
has zero content changes.

## Import mechanics (PASS)

- Runner diff is exactly +4/−0: `_SRC` derived from the resolved `__file__`
  (`ROOT / "comparison_bench" / "src"`), inserted at `sys.path[0]` only when
  absent, before the core file-location load. No drive/mount/cwd/PYTHONPATH/
  venv-site-packages/install assumption; no hard-coded path.
- Core module byte-unchanged: `bind_historical_decoder()` now reaches v35 via
  the normal `comparison_bench.formal_ir.v35_algorithm_development` import
  against the local tree.
- Both core fallbacks (oracle line 21, v35 line 495) catch only
  `ModuleNotFoundError`; an internal dependency `ImportError` still
  propagates and cannot be misreported as a merely absent package.

## No science drift (PASS)

- Test-file diff is +294/−0: the 19 pre-existing tests are byte-untouched.
- v35, D5, D7-A, field, fixtures, priors, seeds, ladder, thresholds,
  budgets, classification, schema, and invocation semantics: zero diff.
- L11 (frozen constants/schema, core free of `sys.path`) passes.

## Reruns (representative subprocess tests, fresh)

- Full D7-B file via shim runner: `31 passed` (19 original + 12 launch).
- External-cwd (`/tmp/d7b_review_ext`), no PYTHONPATH: real runner `--help`
  exit 0 and `--dry-run` header
  `cells=64 caps=[1, 2, 4, 8, 16, 32, 90] budget=420`.
- No `workspace/d7_b_easy_regime_*`, no `workspace/*v72p2d7*` after all runs;
  `cycle_state.yaml` authorization keys untouched (verified in L12).

## Verdict

`D7_B_WSL_LAUNCH_REWORK_REVIEW_PASS`

Zero repair cycles used (one was allowed). No scientific-contract change was
found, so nothing returns to the main thread.

(End of file — uncommitted; committed at T5 closeout.)
