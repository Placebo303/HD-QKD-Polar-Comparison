# D7-B — WSL local-source launch rework and renewed Pre-EXECUTE R1

## 0. Main-thread review and disposition

The prior authorized D7-B invocation ended before decoder binding with:

`ImportError('attempted relative import with no known parent package')`

Disposition:

`D7_B_PRE_EXECUTION_LAUNCH_BINDING_BLOCKED`

This is an environment/launch integration defect, not a decoder result and not
an easy-regime scientific outcome. The prior command invocation is spent and
will never be retried, resumed or reused. No D7-B result root exists.

The user has migrated the execution environment to WSL. This packet authorizes
only a minimal local-source import repair, tests, independent code review,
execution-packet addendum and renewed independent Pre-EXECUTE review. It does
not authorize another D7-B scientific invocation.

## 1. Baseline and preserved evidence

- Repository: `D:/Code/HD-QKD_Polar_Comparison` as seen by the current checkout;
  WSL execution must use the corresponding mounted repository path resolved at
  runtime, never a newly hard-coded `/mnt/...` default.
- Branch: `formal-ir-v72p1-addendum-clean`
- Expected HEAD: `9e41e0d`
- Authorization commit: `ce52ac5`
- Revocation commit: `9e41e0d`
- Current `d7b_execution_authorized: false`
- Attempts/completed/decoder/result fields remain 0/0/false/false
- No `workspace/d7_b_easy_regime_*` root
- R1d and G2 roots absent
- Production v35/D5/D7-A code unchanged from accepted baselines

Two uncommitted lifecycle documents from the blocked invocation must be read,
validated against the return, and preserved verbatim except for clearly marked
main-thread disposition metadata if needed:

- `D7_B_OPERATOR_RETURN_R1.md`
- `D7_B_PRE_RESULT_REVIEW_R1.md`

They are not scientific result artifacts. Land them in a docs-only provenance
commit before the repair, together with a concise launch-block disposition and
state transition to rework. Do not invent a terminal, decoder count or result.

Known unrelated dirty/CRLF and pending SOP/workbuddy administrative changes
remain out of scope. Use explicit manifests and content numstat. No clean,
reset, checkout, stash, rebase, amend, broad stage or push.

## 2. Root cause to prove before editing

Reproduce the failure without authorization and without calling a decoder:

1. the runner loads `v72p2d7_gf32_easy_regime.py` by file location;
2. the core's normal `comparison_bench.formal_ir.v35_algorithm_development`
   import is unavailable when `comparison_bench/src` is absent from `sys.path`;
3. fallback loads v35 as top-level `v35_algorithm_development`;
4. v35 executes `from .nonbinary_field import ...` without a package parent;
5. Python raises the recorded relative-import `ImportError` before decoder call
   and before output-root creation.

Use a subprocess/probe with repository package source absent from initial
`sys.path`. Do not patch `sys.path` in the probe itself. The probe must stop at
binding/import and never invoke `decode_row_layered_fftqspa`.

If the observed cause differs, STOP and report it; do not apply this repair by
analogy.

## 3. Frozen minimal repair

Use the simplest package-correct launch behavior:

1. In `scripts/v72p2d7_gf32_easy_regime.py`, derive
   `<repo>/comparison_bench/src` from the runner's resolved `__file__`.
2. Insert that exact directory into the current process's `sys.path` only when
   absent, before loading the D7-B core.
3. Import/load the D7-B core so its package imports resolve against that local
   source tree.
4. `bind_historical_decoder()` must reach v35 through the normal package name
   `comparison_bench.formal_ir.v35_algorithm_development`.

Do not hard-code a Windows drive, WSL mount, current working directory,
`PYTHONPATH`, active venv site-packages or installed package assumption.

The existing file-layout fallbacks may remain only if they are correct in their
own declared context. The preferred repair is runner-local source-path setup,
not a generalized dynamic package emulator. If a fallback is kept, ensure it
does not catch and obscure an internal dependency `ImportError` as though the
top-level package were simply absent.

Allowed production edits:

- `scripts/v72p2d7_gf32_easy_regime.py`
- if strictly necessary,
  `comparison_bench/src/comparison_bench/formal_ir/v72p2d7_gf32_easy_regime.py`
  only for precise import/fallback behavior
- `comparison_bench/tests/test_v72p2d7_gf32_easy_regime.py`

Forbidden:

- v35, D5, D7-A or field implementation changes;
- scientific fixtures, priors, seeds, cap ladder, thresholds, budgets,
  classifications, writer schema or decoder invocation semantics;
- dependency installation, packaging the repository, editable install,
  environment-wide `PYTHONPATH`, copied decoder modules or vendoring;
- decoder calls, output-root creation, or authorization changes.

## 4. WSL command addendum

Create OpenSpec addendum/delta under the existing
`v72p2d7-gf32-easy-regime` change and create:

`docs/research_cycles/V72P2D7-GF32-EASY-REGIME/D7_B_EXECUTION_PACKET_ADDENDUM_WSL_A1.md`

The addendum records that WSL is now the canonical execution environment and
freezes this exact future command shape:

```bash
timeout -k 30 1800 python scripts/v72p2d7_gf32_easy_regime.py --out-root workspace/d7_b_easy_regime_<uuid>
```

It supersedes only the Windows shell/executable spelling in the original
execution packet. Inner Python script, arguments, root pattern, UUID rule,
scientific matrix, budgets, one-attempt semantics and all prohibitions remain
unchanged.

Record interpreter identity (`sys.executable`, Python and NumPy versions), WSL
distro/kernel identity, repository path and `timeout --version` during renewed
Pre-EXECUTE. Do not freeze machine-specific absolute values as scientific
parameters.

No new UUID is generated in this rework. A future fresh authorization will
name/generate the one new UUID.

## 5. Tests L01–L12

All tests are zero-decoder and must use subprocesses where launch behavior is
the subject:

- L01 reproduce the pre-fix relative-import failure from a WSL/venv-like local
  source environment, with no decoder call and no root;
- L02 run `--help` from repo root with package not installed and no PYTHONPATH;
- L03 run `--help` from a non-repository cwd using the absolute runner path;
- L04 run `--dry-run` from both cwd contexts; exactly 64 cells, no root, no
  historical decoder binding;
- L05 import/run the runner in a subprocess whose initial `sys.path` lacks repo
  root and `comparison_bench/src`; verify it adds only the resolved local src;
- L06 call `bind_historical_decoder()` only, assert returned callable is exactly
  the package-loaded v35 row-layered function; never call it;
- L07 assert v35 module `__package__ == 'comparison_bench.formal_ir'` and its
  `nonbinary_field` resolves from the same repository source tree;
- L08 ensure a fake module earlier under an unrelated cwd is not imported;
- L09 unauthorized scientific CLI returns 3 before root creation and before
  decoder binding;
- L10 D7-B 19 tests and D7-A 14 tests remain green;
- L11 scoped regression demonstrates all frozen scientific constants/schema are
  byte/semantic unchanged;
- L12 protected roots, R1d/G2 absence and authorization false remain unchanged.

Do not claim L01 by leaving the production tree broken. Capture the original
failure in a test-local miniature module/package fixture or a pre-edit
provenance transcript, then test the repaired real runner in L02–L09.

Use a fresh task-owned basetemp. Remove only that resolved directory. Do not run
perf-v38, any `--phase`, D7-B scientific execution, R1d, G1 or G2.

## 6. Ordered work and commits

### T0 — provenance closeout

Read all named files, confirm baseline and root/authorization state, and verify
the two uncommitted blocked-return documents. Create a concise
`D7_B_LAUNCH_BLOCK_DISPOSITION_R1.md` and append a troubleshooting entry that
states the reusable Python package-context failure. Commit only blocked-run
documents, disposition, troubleshooting and factual state gate:

`docs(d7-b): retain spent launch-block attempt and enter scoped rework`

Do not mark a result accepted or completed.

### T1 — OpenSpec/addendum freeze

Before editing code, add the launch-rework tasks/design delta and WSL execution
packet addendum. Commit separately:

`docs(d7-b): freeze WSL local-source launch rework and command addendum`

### T2 — minimal implementation and tests

Implement §3 and L01–L12. Run py_compile, focused launch tests, full D7-B,
D7-A regression and the related non-perf milestone suite. Commit only the
allowed script/core/test files:

`fix(d7-b): make local-source decoder binding package-correct on WSL`

### T3 — independent code review

An independent reviewer must inspect the import mechanics, prove no scientific
contract drift, and rerun representative subprocess tests. Allowed verdict:

`D7_B_WSL_LAUNCH_REWORK_REVIEW_PASS`

One narrowly scoped repair cycle is allowed for implementation defects. Any
scientific-contract change returns to the main thread.

### T4 — renewed independent Pre-EXECUTE

Use a separate reviewer context and actual WSL environment. Run probes as
separate commands, never chained:

1. interpreter/WSL identity;
2. live RSS positive integer;
3. `timeout` existence/version;
4. `timeout -k 30 3 python -c 'import time; time.sleep(30)'` returns 124;
5. real runner `--help` from repo and external cwd;
6. real runner `--dry-run` from external cwd;
7. external no-PYTHONPATH binding probe that stops after receiving the exact
   v35 callable and proves zero decoder invocation/root creation;
8. unauthorized exact-command-shape probe returns 3 before work;
9. no D7-B/R1d/G2 target root, protected metadata unchanged, authorization
   false;
10. scoped code/tests equal reviewed implementation.

Create `D7_B_PRE_EXECUTE_REVIEW_WSL_R2.md`. Allowed PASS verdict:

`D7_B_PRE_EXECUTE_REVIEW_PASS_WSL_R2_AWAITING_FRESH_AUTHORIZATION`

This review cannot authorize execution and must not generate a scientific UUID.

### T5 — closeout

Commit review documents and append only durable launch/readiness facts to
decision log and project memory. Set the documented gate to:

`D7_B_WSL_READY_AWAITING_FRESH_EXPLICIT_AUTHORIZATION`

All authorization keys remain false; attempts/completed/decoder/result fields
remain factually unchanged. Local commits only, no push. Then STOP.

## 7. Acceptance matrix

- W01 prior invocation and authorization lifecycle preserved exactly
- W02 no scientific result/terminal inferred from launch failure
- W03 root cause reproduced as missing package context
- W04 local source path derived only from runner `__file__`
- W05 normal package import loads D7-B/v35/nonbinary_field from same checkout
- W06 no cwd, installed-package, Windows-drive or hard-coded WSL-path reliance
- W07 no v35/D5/D7-A/scientific-contract change
- W08 L01–L12 pass with zero decoder calls
- W09 import/help/dry-run/unauthorized paths create no root
- W10 external-cwd WSL binding probe reaches exact callable without invoking it
- W11 WSL command addendum changes shell spelling only
- W12 independent code review PASS
- W13 renewed independent Pre-EXECUTE PASS
- W14 protected roots unchanged, D7-B/R1d/G2 roots absent, auth false
- W15 scoped local commits only, no push, dirty tree preserved
- W16 final gate awaits a new explicit user authorization

## 8. Hard STOP rules

STOP if baseline evidence differs, root cause is not package context, repair
would require installing/moving the package or changing v35/science, any decoder
is invoked, any result root appears, any protected root/auth changes, or either
review fails after one scoped repair.

Do not reuse the spent UUID. Do not ask the operator to infer authorization.

## 9. Return

Report deltas only: commits/files, preserved blocked attempt, root-cause proof,
exact import repair, L01–L12, literal test lines, WSL interpreter/path/timeout
evidence, both review verdicts, roots/auth/state and no-push status.

End exactly:

`D7-B WSL launch binding 缺陷已完成零-decoder修复并通过 renewed Pre-EXECUTE；旧授权仍已消耗，尚无科学结果，等待新的用户明确授权，R1d、G1、G2 均未授权。`

