# Implementation Task Packet: Nonbinary LDPC v4 IR

## Ownership

The main thread owns P0-P6, thresholds, scientific semantics, production
authorization, and final acceptance.  The implementation subagent is an
operator and must return only a complete candidate or one concrete blocker.

## Allowed files

- `comparison_bench/src/comparison_bench/formal_ir/nonbinary_v4_ir.py`
- `comparison_bench/src/comparison_bench/formal_ir/nonbinary_v4_ir_qualification.py`
- `comparison_bench/src/comparison_bench/cli/run_formal_nonbinary_v4_ir_qualification.py`
- `comparison_bench/tests/test_nonbinary_v4_ir.py`
- `comparison_bench/tests/test_nonbinary_v4_ir_qualification.py`
- this change's `tasks.md` only to check `V4-I0` through `V4-I5`

Read-only reuse is allowed from v3, `nonbinary_qspa.py`, `nonbinary_field.py`,
`nonbinary_codebook.py`, and `shared.py`.

## Forbidden

- Any v1-v3 source, test, OpenSpec, seed, artifact, output, or official plan.
- `src/`, `experiments/`, `tools/`, `results/`, `qldpc_reference`.
- Sidecars, raw `.ttbin`, real data, official v4 output, plan creation,
  production decoder execution, or external package/code copying.
- Reading existing confirmation frame arrays or using historical confirmation
  to choose behavior.

## Required implementation

- Implement `V4-I0` through `V4-I5` and the delta spec, without adding
  candidates, config knobs, fallback algorithms, dependencies, or
  unregistered statuses.
- Discard transient decoder diagnostics from qualification; strict replay
  must reject every forbidden diagnostic field in formal artifacts/transcript.
- Development seeds are one per control frame and two per IR frame.
  Confirmation material is created only after readiness and frozen in full
  before its first decode.
- Wall time is monitoring-only.  Formal statuses and replay use deterministic
  iteration/row/stage/attempt/event/memory limits.
- Test-only execute/verify requires an explicit fake runner.
- Use fresh additive `workspace/nbldpc_v4_ir_tests/<uuid>` roots and
  `pytest -p no:cacheprovider`.
- Retain invalid partial artifacts; never overwrite.

## Acceptance

- `V4-I0` through `V4-I5` complete.
- T0/T1 candidate commands and T2 fake qualification command pass.
- Return changed files, exact commands/results, artifact-free status, source
  hashes, and any blocker.  Do not mark T0-T3 or A0-A3 accepted.

## Return conditions

Return only when all implementation items are complete, or with the failing
command, exact error/traceback, remedies attempted, and the single main-thread
decision required.
