# Tasks: V11 Nonbinary Spatially Coupled DE Gate

## Planning freeze

- [x] **V11-P01** Review QSC, SC-LDPC threshold-saturation, protograph edge
  spreading, windowed decoding, and HD-QKD references.
- [x] **V11-P02** Freeze the scientific question, equal-rate control, three
  geometries, resource limits, gates, and successor boundary.
- [x] **V11-P03** Record the detailed plan and acceptance IDs in OpenSpec and
  project documentation.
- [x] **V11-P04** Obtain an independent read-only freeze review before any
  implementation or scientific execution.

## Engineering/reference phase

> Gate: V11-P04 must PASS before any engineering/reference task (V11-10.1+) starts.

- [x] **V11-10.1** Add a paper-faithful QSC SMP-DE reference implementation.
- [x] **V11-10.2** Reproduce the four q=4/q=16 published thresholds and freeze
  the trace.
- [x] **V11-20.1** Add the full-vector spatially coupled MC-DE kernel outside
  frozen baseline directories.
- [x] **V11-20.2** Add collapse, oracle, normalization, noiseless-limit, and
  harmonic-rate tests.
- [x] **V11-20.3** Run T0/T1 and independent engineering review.

## Resource and formal lifecycle

- [x] **V11-30.1** Run the non-gating GF(1024) resource microbenchmark.
- [x] **V11-30.1'** AMEND-2026-08-06-01 numba budget amendment frozen (user
  approved; numba limited to nonbinary_v11_mcde.py hot kernels; scientific
  parameters unchanged).
- [x] **V11-30.2'** Microbenchmark #2 completed (post-numba predicted 66.72 h
  still over 24 h limit, judged still `resource_blocked`; user approved
  AMEND-2026-08-06-02).
- [x] **V11-30.1''** AMEND-2026-08-06-02 parallel-execution amendment frozen
  (user approved; worker-pool parallelism, seed-to-run mapping, per-run
  determinism unchanged, RSS semantics per single-run peak).
- [x] **V11-30.2''** Parallel microbenchmark re-test #3 (exactly once) and
  re-freeze the budget; stop as `resource_blocked` if still over budget.
  (Done: parallel microbenchmark #3 completed — 4 workers batch efficiency
  0.51, converted wall-clock 32.69 h over limit; the formal matrix is 60
  similar-duration tasks, so user approved switching to task-level LPT
  scheduling simulation extrapolation into Stage P; evidence
  `evidence/resource/microbenchmark3.{md,json}`.)
- [x] **V11-30.2** Stop as `resource_blocked` if the frozen budget is exceeded;
  otherwise prepare the complete formal plan.
  (Done: budget not exceeded — execute wall 15.83 h < 24 h, peak RSS 2.82 GiB
  < 3 GiB; complete formal plan prepared and frozen at
  `evidence/formal_plan.json`, schema `v11_formal_plan_v1`.)
- [x] **V11-40.1** Review the formal plan read-only and authorize exactly one
  scientific execute.
  (Done: formal plan read-only review passed — reviewer-go, 0 blockers;
  `evidence/formal_plan.{json,md}` + executor implementation + 32 tests.)
- [x] **V11-40.2** Execute the paired S1/S3 × G1/G2/G3 matrix once.
  (Done: scientific execution completed 60/60 runs, 2026-08-08; execution
  root `workspace/nbldpc_v11_execute_002d51de/`; see
  `formal_matrix_results.json` for per-run science fields.)
- [x] **V11-40.3** Strict-replay once from a fresh workspace and independently
  recompute all gate decisions.
  (Done: strict replay 60/60 byte-identical on science fields, replay_ok=true;
  `evidence/replay/replay_evidence.json`, replay root
  `workspace/nbldpc_v11_replay_8e63bf62/`.)
- [x] **V11-50.1** Record `ready_for_finite_length`, `failed_reference`,
  `failed_coupling`, or `resource_blocked`.
  (Done: final state `failed_coupling` recorded at
  `evidence/decision/final_gate_decision.json`, schema
  `v11_final_gate_decision_v1`, decided 2026-08-11.)
- [x] **V11-50.2** Run scoped regression/frozen-directory/output-root checks.
  (Done: regression 87 passed; frozen directories zero change; output root
  no new entries; A14 PASS.)
- [x] **V11-50.3** Obtain independent final acceptance and perform memory
  triage.
  (Done: reviewer-go independent final acceptance passed, 16/16 A01-A16 PASS.)

## Stop rule

Any failed reference, engineering, resource, lifecycle, replay, or scientific
gate freezes the evidence and stops V11. V11 never advances directly to a
finite codebook, decoder, canary, real data, qualification, or promotion.
