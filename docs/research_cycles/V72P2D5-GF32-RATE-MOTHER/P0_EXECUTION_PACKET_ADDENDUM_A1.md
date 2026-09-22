# Addendum A1 to the frozen P0 execution packet — standing reachability precondition

This is an ADDENDUM. The frozen `P0_EXECUTION_PACKET.md` stays byte-identical;
nothing in it is edited by this file.

## The R1 attempt (2026-09-07, authorization consumed, no run)

Under the R1 authorization, the single frozen invocation
`python scripts/v72p2d5_gf32_rate_mother.py --phase p0-cost` refused in
0.376 s with a false `MODEL_F_INPUT_BLOCKED_MISSING_CAL_TRAIN_COUNTS`.

## Verified root cause

The Model-F consumer reached the accepted Model-F artifact through a package
import (`comparison_bench...`), which fails when the CLI is launched as a
script (`python scripts/...`, where the repository root is absent from
`sys.path`). A present, valid artifact was therefore reported as missing
input. The defect was in the consumer path, not in the artifact, the frozen
command, or the authorization.

## The fix

`D5_P0_LOADER_FIX_R1`, landed as commit `299416ae`
(`fix(v72p2d5): resolve Model-F consumer input by file path, not sys.path`):
the consumer now resolves the Model-F artifact by file path anchored at
`__file__`, independent of `sys.path` and cwd. Independently reviewed:
`LOADER_FIX_REVIEW_R1` = `LOADER_FIX_REVIEW_PASS`.

## Standing precondition (rule for this and every later stage)

> Before any `*_execution_authorized` is flipped for a stage, that stage's
> authorized path MUST be shown to reach its first decoder call under the real
> launch condition, using an explicit tmp `out_dir` and a probe decoder that
> raises on first invocation. Test-suite green is not sufficient evidence: the
> suite injects tables and monkeypatches roots, so it cannot exercise this path.

For P0 this was discharged by STEP 2' (R3 A.2): probe script outside the
repository (so `sys.path[0]` is not the repo root and the repo root is absent
from `sys.path`), repo as cwd, no `sys.path` insertion, no `python -c`,
with `repo_root_on_sys_path= False` and
`package_import_available= False ModuleNotFoundError` proving the real launch
condition, yielding `REACH_OK REACHED_FIRST_DECODER_CALL probe_calls 1` with
empty tmp contents and untouched formal roots. Full literal output is in
`P0_AUTHORIZATION_RECORD_R2.md`.
