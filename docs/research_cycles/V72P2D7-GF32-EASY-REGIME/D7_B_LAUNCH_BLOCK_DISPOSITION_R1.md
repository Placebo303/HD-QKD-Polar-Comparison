# D7-B launch-block disposition R1 (spent attempt; scoped rework entry)

## Disposition

`D7_B_PRE_EXECUTION_LAUNCH_BINDING_BLOCKED`

The single authorized D7-B invocation (UUID
`0f1ad3ec-f9e0-463f-a7dd-d9880ff7230c`, spent, never retried/resumed/reused)
ended before decoder binding with:

`ImportError('attempted relative import with no known parent package')`

This is an environment/launch integration defect, NOT a decoder result and
NOT an easy-regime scientific outcome. No terminal, decoder count, or result
is inferred. No result is accepted; nothing is marked completed.

## Preserved lifecycle (verbatim, unchanged)

- Authorize `ce52ac5` (record + `cycle_state.yaml` false→true) → exactly one
  invocation (exit 3, wall 0 s, stdout is the ImportError line above, stderr
  empty) → revoke `9e41e0d` (`cycle_state.yaml` true→false). Both commits
  local-only, no push.
- Current: `d7b_execution_authorized: false`; attempts/completed 0/0;
  `decoder_executed: false`; `result_created: false`.
- Target root `workspace/d7_b_easy_regime_0f1ad3ec-f9e0-463f-a7dd-d9880ff7230c`
  ABSENT; zero `workspace/d7_b_easy_regime_*` roots; R1d/G2 roots absent.
- Blocked-run documents preserved: `D7_B_OPERATOR_RETURN_R1.md`
  (`NOT_ACCEPTED / PRE_RESULT_REVIEW_REQUIRED`) and
  `D7_B_PRE_RESULT_REVIEW_R1.md` (`D7_B_PRE_RESULT_REVIEW_BLOCKED`;
  R01–R03/R14–R16 PASS, R04–R13 BLOCKED for missing evidence). Both validated
  against the return and the lifecycle commits; both consistent.
- `cycle_state.yaml` intentionally untouched: every key is already factually
  correct, so there is no factual state change to stage.

## Root cause (zero-decoder probe, this WSL checkout)

Reproduced in a subprocess with repo package source absent from initial
`sys.path` and no `sys.path` patching in the probe; stopped at
binding/import; `decode_row_layered_fftqspa` never invoked:

1. runner loads `v72p2d7_gf32_easy_regime.py` by file location;
2. core's normal `comparison_bench.formal_ir.v35_algorithm_development`
   import is unavailable (`ModuleNotFoundError: No module named
   'comparison_bench'`);
3. fallback file-loads v35 as top-level `v35_algorithm_development`;
4. v35 executes `from .nonbinary_field import ...` with no package parent;
5. `ImportError('attempted relative import with no known parent package')`
   raised before any decoder call and before output-root creation.

Probe output (literal): `REPRODUCED ImportError:
ImportError('attempted relative import with no known parent package')`.

## Gate

Entering scoped WSL local-source launch rework per
`.workbuddy/tasks/D7_B_WSL_LAUNCH_REWORK_PRE_EXECUTE_R1_TASK_PACKET.md`.
No new UUID is generated here; any future scientific run needs a fresh
explicit user authorization. R1d, G1, G2 remain unauthorized.

(End of file.)
