# Tasks: Binary LDPC Adjacent-Channel v4

## Phase 1: Codebook and Channel Foundation

- [x] Implement `formal_ir/codebook_v4.py` with the exact 40 deterministic
  anchored column-weight-three candidates, HGF2V4 bytes, rank/weight/cycle/
  low-weight diagnostics, complete manifest, and reconstruction verifier.
- [x] Implement `formal_ir/ldpc_v4_channel.py` with exact sacrificed
  calibration reconstruction, frozen adjacent-bin counts/model, nominal and
  1.25x stress contracts, and Bob-conditioned per-position plane
  probabilities.
- [x] Add focused tests for deterministic hashes, all structural gates,
  wrong-source/count/delta/Gray failures, exact probability formulas, clipping
  boundary, and absence of confirmation reads.

## Phase 2: Development and Formal Method

- [x] Implement deterministic 512+512 sacrificed development generation,
  40-candidate plane evaluation, retained statuses, exact candidate selection,
  q=1024 frame aggregation, and the 495/512 readiness gate.
- [x] Implement additive `ldpc_formal_v4` with the frozen product-sum
  BP+OSD-0 policy, ten fixed plane syndromes, Bob-conditioned soft inputs, one
  final 64-bit Toeplitz tag, exact 648-bit disclosure, caps, transcript, status
  precedence, and strict outcome validation.
- [x] Add tests proving decoder/Alice/tag isolation, exact ten-call order,
  selected-matrix binding, syndrome consistency, verified success/failure,
  malformed/backend/resource failures, and accounting.

## Phase 3: Immutable Development Tooling

- [x] Implement dedicated development prepare/execute CLI with the exact
  seven-file completed package, no overwrite/resume, source/code/backend hash
  binding, canonical bytes, deterministic execution order, and failure
  finalization.
- [x] Implement a strict read-only development verifier reconstructing the
  TTBIN calibration, channel model, all matrices, development frames,
  selections, frame aggregation, artifact DAG, denominators, and readiness
  gate while reporting `decoder_reexecution=false`.
- [x] Add success, non-ready, backend exception, malformed output, cap,
  partial-finalization, overwrite, hash/source/model/selection tamper, and
  verifier read-only tests.

## Phase 4: Fresh Synthetic Qualification Tooling

- [x] Implement dedicated synthetic prepare/execute CLI requiring a strictly
  verified ready development package, generating fresh domain-separated roots,
  exact 128+128 frames and Toeplitz seeds, and producing the exact eight-file
  completed package.
- [x] Implement strict read-only verification of fresh-seed isolation,
  generation/order, model/codebook/selection/development bindings,
  transcript/outcome/disclosure accounting, and both 126/128 gates with
  `decoder_reexecution=false`.
- [x] Add success, non-promotion, gate recomputation, forbidden failure,
  decoder exception, cap, partial-finalization, overwrite, old-seed collision,
  confirmation isolation, and all artifact-tamper tests.

## Phase 5: Conditional Real Qualification Tooling

- [x] Implement real lock/prepare that is impossible without the exact
  strictly verified promoted synthetic package; exclude all v3 reserved frame
  identities and select 128 new frames per registered bin width.
- [x] Implement exact 384-frame execution, nine-file package, retained
  per-stratum failures, and strict read-only verifier reconstructing the
  synthetic prerequisite, source hashes, selection, transcript/outcome/
  disclosure accounting, and three 126/128 gates.
- [x] Add synthetic-block, selection/exclusion/disjointness, exact order,
  denominator, non-promotion retention, source/lock/transcript tamper,
  overwrite, partial-finalization, and verifier read-only tests.

## Phase 6: Main-Thread Acceptance and Production Development

- [x] Main thread reviews every Phase 1-5 requirement and rejects any
  requirement drift; Terra makes no acceptance conclusion.
- [x] Run focused v4 tests, v1-v3/formal-real/nonbinary regressions,
  compilation, `git diff --check`, and frozen `src/`, `experiments/`, `tools/`,
  and `results/` difference checks.
- [x] Main thread prepares and audits one fresh production development plan.
- [x] Execute production development exactly once, verify exactly once, and
  require both 495/512 readiness gates before proceeding.

## Phase 7: Main-Thread Fresh Qualification

- [x] If and only if development is ready, main thread prepares and audits one
  fresh synthetic plan with no old/new seed overlap.
  The condition was false; no synthetic directory was created.
- [x] Execute synthetic exactly once, verify exactly once, and require at least
  126/128 in both strata with zero forbidden failures.
  The prerequisite was false, so no synthetic execution or verification ran.
- [x] If and only if synthetic is promoted, main thread creates and audits the
  fresh real lock/plan, executes exactly once, verifies exactly once, and
  requires at least 126/128 in all three strata.
  The prerequisite was false, so no real directory, lock, execution, or
  verification was created.
- [x] If a gate fails, preserve the immutable package, create no downstream
  production directory, do not tune or rerun, and record `non_promoted`.

## Phase 8: Handoff, Memory, and Successor Boundary

- [x] Update `AGENT_HANDOFF.md`, `docs/decision-log.md`,
  `AGENT_PROJECT_MEMORY.md`, and the binary/nonbinary parallel handoff with
  exact commands, hashes, results, limitations, and next action.
- [x] Perform mandatory memory triage after verified evidence.
- [x] Only after real promotion, propose a separate
  `binary-ldpc-rate-adaptive-v4-1` change for leakage optimization; do not add
  rate adaptation to this v4 implementation.
  Real promotion did not occur, so no rate-adaptive successor was proposed.
