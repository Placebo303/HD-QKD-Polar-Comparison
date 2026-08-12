# Tasks: Binary LDPC Long-Frame v3

These tasks are frozen for the first implementation work package. Requirement
ambiguity is a stop condition; the implementation operator must not reinterpret
or extend them.

## Phase 1: Candidate Codebook Foundation

- [x] Add only
  `comparison_bench/src/comparison_bench/formal_ir/codebook_long_v3.py`.
- [x] Implement the exact frozen domain, deterministic four-candidate nested
  construction, canonical HGF2V3 encoder/parser, and fail-closed validation
  from `design.md`.
- [x] Implement structural diagnostics and label every score as a proxy, never
  as FER, decoding success, or qualification evidence.
- [x] Implement a complete deterministic in-memory candidate manifest with a
  compact-JSON SHA256 and full reconstruction-based verification.
- [x] Add only
  `comparison_bench/tests/test_ldpc_codebook_long_v3.py`, covering
  deterministic construction, all prefix shapes/nesting, actual rank at all
  three lengths, no zero/duplicate columns, canonical mutation rejection,
  manifest completeness/hash/tamper rejection, candidate-only status, and
  absence of writes to production output roots.

## Required Tests

- [x] Run:
  `python -m pytest comparison_bench/tests/test_ldpc_codebook_long_v3.py -q -p no:cacheprovider`
- [x] Run:
  `python -m pytest comparison_bench/tests/test_ldpc_codebook_v2.py comparison_bench/tests/test_ldpc_formal_v2.py -q -p no:cacheprovider`
- [x] Run `python -m py_compile` on the new module and test.
- [x] Run `git diff --check` and confirm
  `git diff --name-only -- src experiments tools results` is empty.

Main-thread acceptance evidence (2026-07-26): focused 4 passed in 10.88 s;
v2 regression 7 passed and 1 skipped in 81.41 s; `py_compile` and scoped
`git diff --check` exited 0; frozen-directory diff was empty. This accepts
Phase 1 engineering only and is not FER, decoding, qualification, or promotion
evidence.

## Phase 2: Sacrificed-Development FER Kernel

- [x] Add only
  `comparison_bench/src/comparison_bench/formal_ir/long_v3_development.py`.
- [x] Implement the exact canonical policy, sacrificed generator, incremental
  candidate evaluation, fail-closed backend/input statuses, retained
  per-frame outcomes, and four-candidate selection tuple from `design.md`.
- [x] Keep runtime and structural proxies diagnostic-only; do not implement
  confirmation, real-data, qualification, or promotion behavior.
- [x] Add only
  `comparison_bench/tests/test_ldpc_long_v3_development.py`, independently
  covering exact data generation/hash/provenance, policy hash and decoder
  kwargs, nested-disclosure accounting, early success, inexact continuation,
  syndrome inconsistency, decoder/backend/input failures, exact four-candidate
  selection/no runtime oracle, malformed-grid rejection, and no file writes.

## Phase 2 Required Tests

- [x] Run:
  `python -m pytest comparison_bench/tests/test_ldpc_long_v3_development.py -q -p no:cacheprovider`
- [x] Run:
  `python -m pytest comparison_bench/tests/test_ldpc_codebook_long_v3.py comparison_bench/tests/test_ldpc_codebook_v2.py comparison_bench/tests/test_ldpc_formal_v2.py -q -p no:cacheprovider`
- [x] Run `python -m py_compile` on both Phase 2 files.
- [x] Run scoped `git diff --check` and confirm
  `git diff --name-only -- src experiments tools results` is empty.

Main-thread acceptance evidence (2026-07-26): focused 5 passed in 0.53 s;
Phase 1/v2 regression 11 passed and 1 skipped in 92.68 s; `py_compile`,
scoped `git diff --check`, and frozen-directory diff passed. Selection tests
independently prove the exact policy/data/hash contracts, incremental leakage,
status validation, no runtime oracle, and the frozen lexicographic priority.
No pinned-backend development sweep was run.

## Phase 3A: Bounded Pinned-Backend Pilot

- [x] Run exactly the single n=256/plane0/candidate0/p001 in-memory pilot from
  `design.md` with a 120-second external process timeout and no file writes.
- [x] Record the exact compact JSON stdout, exit code, and elapsed time.
- [x] Main thread reviews the diagnostic and decides whether/how to freeze a
  full development sweep. The operator SHALL NOT make that decision.

Observed once on 2026-07-26: exit 0, empty stderr, 1.0 s external wall,
0.3227008000249043 s process elapsed, pinned `ldpc==2.4.1`, 16/16
`development_exact_success`, terminal prefixes p050=15 and p0625=1, total
syndrome bits 2080. This authorizes planning the full sacrificed-development
sweep only; it is not candidate selection, FER qualification, or promotion.

## Phase 3B: Runner, Artifact DAG, and Verifier

- [x] Add only the Phase 3B runner, verifier, and focused test named in
  `design.md`.
- [x] Implement the exact production plan, two-step no-overwrite lifecycle,
  frozen 3840-row execution order, six-artifact schema/hash DAG, accepted
  Phase 2 selection reuse, cap/exception finalization, and no-resume rule.
- [x] Implement strict read-only production verification plus the private,
  explicitly test-only reduced-domain path.
- [x] Tests SHALL prove successful reduced execution, exact reconstruction,
  failure finalization, no-overwrite/read-only behavior, tamper/extra-file
  rejection, and CLI rejection of test plans.

## Phase 3B Required Tests

- [x] Run:
  `python -m pytest comparison_bench/tests/test_ldpc_long_v3_sweep.py -q -p no:cacheprovider`
- [x] Run all long-v3 focused tests together.
- [x] Run v2 codebook/formal regression.
- [x] Run `python -m py_compile` on all three Phase 3B files.
- [x] Run scoped `git diff --check` and confirm frozen-directory diff empty.

Main-thread acceptance evidence (2026-07-26): Phase 3B focused 3 passed in
12.30 s; all long-v3 tests 12 passed in 12.94 s; v2 regression 7 passed and
1 skipped in 81.34 s; `py_compile`, scoped `git diff --check`, and frozen
directory checks passed. Explicit writable test root:
`workspace/formal_long_v3_phase3b_tests_run3`. Production prepare/execute was
not run.

## Phase 3B Explicit Non-Tasks

- Do not execute `--mode prepare` or `--mode execute` for the production run
  ID or create anything under production output roots.
- Do not alter Phase 1/2 modules, existing tests, dependencies, configs,
  v1/v2, confirmation/real data, or qualification semantics.
- Do not check tasks, update documents, archive, commit, select a scientific
  winner, or authorize the production sweep.

## Phase 3C: Production Plan Freeze and Single Development Sweep

Frozen output directory:
`comparison_bench/outputs_comparison/formal_ir_methods/20260726_v1_binary_ldpc_long_v3_development/`.

- [x] Confirm the exact output directory does not exist.
- [x] Run production `--mode prepare` exactly once. It SHALL create only
  `pre_run_plan.json` and perform zero decode calls.
- [x] Main thread independently verifies the plan self-hash, run/grid/counts,
  canonical policies, exact candidate-manifest byte hash, current code hashes,
  backend requirement, caps, and sole-artifact directory state.
- [x] Only after that review, run production `--mode execute` exactly once with
  an external 660-second timeout.
- [x] Run the strict read-only verifier exactly once after execute returns.
- [x] Retain timeout, failed package, or verified complete package without
  overwrite/retry. A successor run requires a new planner decision.
- [x] Main thread reviews outcomes/selections and records development evidence
  without making qualification or promotion claims.

Observed 2026-07-26: execute exit 0 in 28.9 s wall; six artifacts; 3840/3840
outcomes and 30/30 selections; verifier exit 0 in 11.2 s with
`decoder_reexecution=false`. All 3840 per-plane candidate outcomes were
`development_exact_success`. This remains sacrificed-development evidence.
Per-plane terminal leakage uses Alice-truth exact equality and is not directly
deployable as a formal stopping signal.

## Phase 4: Frame-Level Global-Round Development

- [x] Add only
  `comparison_bench/src/comparison_bench/formal_ir/long_v3_frame_development.py`.
- [x] Implement the exact ten-plane aggregation, global stopping/tag/leakage
  model, strict input/selection reconstruction, length aggregates, frozen
  length-selection tuple, and aggregation self-hash from `design.md`.
- [x] Add only
  `comparison_bench/tests/test_ldpc_long_v3_frame_development.py` with all
  Phase 4 required coverage and no file writes.
- [x] Run the Phase 4 focused test, all long-v3 tests, v2 regression,
  `py_compile`, scoped diff check, and frozen-directory check.
- [x] Main thread applies the accepted aggregator read-only to the immutable
  Phase 3C package and records the frame-level development result.

Main-thread evidence (2026-07-26): Phase4 focused 4 passed in 4.62 s; all
long-v3 16 passed in 17.67 s; v2 regression 7 passed/1 skipped in 80.73 s.
Read-only aggregation hash
`029e33c42f254e40725a370065d30196216501085d5def5f0f0c935aca6c933c`
selects n=256 with tuple `[-16,-32,.68125,.62265625,256]`. This is
frame-level sacrificed-development evidence, not tag execution or
qualification.

## Phase 4 Explicit Non-Tasks

- Do not modify the verified Phase 3C package or any Phase1-3 code.
- Do not implement or execute actual Toeplitz tags, formal v3 decoding,
  confirmation, real data, qualification, or promotion.
- Do not write a new result artifact, change tasks/docs, or make a scientific
  acceptance conclusion.

## Phase 5: Executable Formal Binary LDPC v3

- [x] Add only
  `comparison_bench/src/comparison_bench/formal_ir/ldpc_v3.py`.
- [x] Implement the exact n=256/q=1024 ten-plane formal protocol, frozen
  selection/calibration validation, long-frame preflight, incremental
  syndromes, locked one-tag global stopping, caps, statuses, transcript, and
  strict v3 outcome validator specified in `design.md`.
- [x] Add only `comparison_bench/tests/test_ldpc_formal_v3.py` and cover every
  Phase 5 test boundary specified in `design.md`.
- [x] Run:
  `python -m pytest comparison_bench/tests/test_ldpc_formal_v3.py -q -p no:cacheprovider`
- [x] Run:
  `python -m pytest comparison_bench/tests/test_ldpc_codebook_long_v3.py comparison_bench/tests/test_ldpc_long_v3_development.py comparison_bench/tests/test_ldpc_long_v3_frame_development.py -q -p no:cacheprovider`
- [x] Run:
  `python -m pytest comparison_bench/tests/test_ldpc_codebook_v2.py comparison_bench/tests/test_ldpc_formal_v2.py -q -p no:cacheprovider`
- [x] Run `python -m py_compile` on the two Phase 5 files.
- [x] Run scoped `git diff --check` and confirm
  `git diff --name-only -- src experiments tools results` is empty.

The implementation operator SHALL report commands, results, and any ambiguity
without checking tasks, editing OpenSpec/docs/memory, or making an acceptance,
qualification, or promotion conclusion.

Main-thread acceptance evidence (2026-07-26): focused Phase 5 tests 6 passed
in 2.15 s; long-v3 regression 13 passed in 16.12 s; v2 regression 7 passed
and 1 skipped in 81.27 s. `py_compile`, scoped whitespace checks, and the
frozen `src/experiments/tools/results` diff check passed. This accepts the
method implementation and test contract only. No qualification runner,
confirmation data, production artifact, or promotion decision exists.

## Phase 5 Explicit Non-Tasks

- Do not add a runner, CLI, config, dependency, artifact, qualification,
  confirmation, real-data execution, promotion gate, or comparison claim.
- Do not modify Phase 1-4 code, v1/v2, shared helpers, existing tests, frozen
  baseline directories, requirements, outputs, OpenSpec, or handoff documents.
- Do not use exact Alice/Bob equality as a stopping oracle.
- Do not choose a new length, candidate, decoder policy, calibration schema,
  tag length, prefix schedule, status, or accounting rule.

## Phase 6A: TTBIN-Derived Data Bridge

- [x] Add only `formal_ir/ldpc_v3_ttbin_data.py` and its focused test.
- [x] Implement exact source validation/hashing, contiguous framing,
  deterministic calibration/confirmation selection, calibration derivation,
  reconstruction verification, and read-only APIs from `design.md`.
- [x] Run the focused test, Phase 5 test, `py_compile`, scoped diff check, and
  confirm frozen baseline/output diffs are empty.
- [x] Main thread reviews and accepts Phase 6A before Phase 6B coding.

Main-thread evidence (2026-07-26): focused Phase 6A plus Phase 5 tests passed
10/10 in 2.33 s; compile/diff/frozen checks passed. A direct read-only call on
the real 20 dB main/chunk and four sidecars reconstructed 160 selected frames,
source manifest `46259251...`, lock `5f0d28e7...`, and calibration
`604aa77d...`. No production artifact was written.

## Phase 6B: Synthetic Qualification

- [x] Add only the synthetic runner, verifier, and focused qualification test
  specified in `design.md`.
- [x] Implement two-step no-overwrite preparation/execution, exact generator,
  six-artifact DAG, failure finalization, gates, and read-only verification.
- [x] Run focused qualification, Phase 5/6A, all long-v3, v2 regression,
  `py_compile`, and scoped frozen-directory checks.
- [x] Main thread reviews tooling before any production prepare.

Main-thread tooling evidence (2026-07-26): Phase 6B plus Phase 5/6A passed
13/13 in 24.33 s. Terra's full long-v3 run passed 28 tests and v2 passed
7 with 1 skipped. Compile/scoped diff/frozen checks passed. No production
prepare or execution occurred during implementation tests.
- [x] Production prepare runs once at a fresh additive output path.
- [x] Main thread audits the sole plan artifact and authorizes or rejects
  execution.
- [x] Production execute and verifier each run exactly once; retain the package
  and record whether synthetic promotion unlocks Phase 6C.

Production evidence (2026-07-26): immutable root
`comparison_bench/outputs_comparison/formal_ir_methods/20260726_v1_binary_ldpc_v3_synthetic/`.
Prepare produced only the audited plan; execute ran once and exited 0 in
11.4 s; strict verifier ran once, exited 0, and reported 64 outcomes with
`decoder_reexecution=false`. Calibrated achieved 3/32 and stress_125 1/32
verified successes; the other 60 outcomes were `verify_failed`, with zero
unclassified/internal/provenance/accounting failures. Synthetic promotion
failed, so Phase 6C remains locked and no real output directory may be
created.

## Phase 6C: Real Qualification

- [ ] If and only if Phase 6B is strictly verified and promoted, add the real
  runner, verifier, and focused test specified in `design.md`.
- [ ] Prove synthetic-gate blocking, 96-frame selection/order, seven-artifact
  DAG, failure retention, gates, source/lock tampering, and read-only verify.
- [ ] Run focused and complete Phase 1-6 regressions, compile/diff/frozen checks.
- [ ] Production real lock/prepare runs once only after the gate.
- [ ] Main thread audits the real lock and plan before execution.
- [ ] Production execute and verifier each run exactly once; retain all
  outcomes and record the bounded promotion conclusion.
- [ ] Update handoff, decision log, and project memory after final review.

Blocked by the frozen gate on 2026-07-26: Phase 6B was strictly verified but
not promoted. Do not implement, lock, prepare, or execute Phase 6C under this
change. Any binary-method improvement requires a new OpenSpec change and fresh
synthetic confirmation; the failed confirmation cannot become tuning data.

## Phase 6 Explicit Non-Tasks

- Do not reparse TTBIN, modify or run the frozen Polar pipeline, overwrite
  outputs, use real confirmation for calibration, tune after confirmation,
  retry failed production packages, or broaden the claim beyond the frozen
  20 dB acquisition.

## Explicit Non-Tasks

- Do not modify `ldpc.py`, `ldpc_v2.py`, `codebook_v2.py`, existing tests,
  runners, requirements, configs, or outputs.
- Do not install dependencies or use confirmation/real data.
- Do not implement decoder wiring, policy selection, qualification, promotion,
  qualification, promotion, or a comparison result outside the Phase 2
  development-only evaluator and its exact four-candidate selection function.
- Do not check tasks, update handoff/memory/decision documents, archive the
  change, or make an acceptance conclusion. Those remain main-thread work.
