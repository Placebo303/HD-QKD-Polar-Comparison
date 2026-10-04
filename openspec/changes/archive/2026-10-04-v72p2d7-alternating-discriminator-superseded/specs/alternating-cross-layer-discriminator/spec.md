## ADDED Requirements

### Requirement: Minimal alternating code-extrinsic schedule

A D7-H arm SHALL run the frozen minimal schedule per `(f, seed)`: a cold L1
marginal decode (STAGE 0; the only unconditional mandatory call, covering all
identities), then a forward `L1→L2` code-extrinsic transfer and cold L2 decode
(STAGE 1) invoked only if STAGE 0 yields finite, shape-valid, non-crashed,
exact `CHECK_EXTRINSIC`, then a backward `L2→L1` code-extrinsic transfer and
cold L1 return decode (STAGE 2) invoked only if STAGE 1 yields the same
admissible extrinsic. No `>2-stage` alternating SHALL be run: D7-E/D7-F block
`>2-stage` alternating pending a cavity/extrinsic-message contract, and no
accepted contract implies more than two transfers.

#### Scenario: Reference and candidate endpoints

- **WHEN** a `(f, seed)` arm completes
- **THEN** the reference `both_layers_exact` is `L1_exact AND L2_exact` and
  the candidate `both_layers_exact` is `L2_exact AND L1_return_exact`
- **AND** a blocked STAGE 1 or STAGE 2 is recorded as a non-invocation, all
  downstream stages for that identity are blocked, and nothing is
  synthesized, replaced, retried, or resumed.

#### Scenario: Call cap

- **WHEN** the run executes
- **THEN** it issues at most `32 × 3 = 96` decoder calls, with 1 unconditional
  mandatory call per identity (STAGE 0; minimum 32 actual calls) plus up to 2
  gated calls (STAGE 1 gated on STAGE 0, STAGE 2 gated on STAGE 1)
- **AND** no concurrency, retry, rerun, or resume occurs.

### Requirement: Code-extrinsic-only transfer

The cross-layer transfer message SHALL be only the certified explicit
`CHECK_EXTRINSIC` code-factor extrinsic `L_code_ext = L_post − log(p_in)`,
stored row-normalized by log-sum-exp and transported through
`require_check_extrinsic_for_transfer`. Posterior `softmax(final_beliefs)`
SHALL NOT be a transfer message, and no consumer SHALL reconstruct a prior by
subtracting an unknown/reconstructed value.

#### Scenario: Non-CheckExtrinsic provenance

- **WHEN** a stage's `extrinsic_provenance` is `NO_CHECK_EVIDENCE` (including
  iteration-0 hard/syndrome success), `WARM_START_UNSPECIFIED`,
  `None`/missing/unknown, or the array is nonfinite or shape-mismatched
- **THEN** the dependent transfer is a blocked non-invocation before any
  cross-layer prior is computed and all downstream stages for that identity
  are blocked
- **AND** nothing is synthesized, replaced, retried, or resumed; source hard
  exact is not an eligibility gate.

### Requirement: No returned evidence and no double count

The backward prior SHALL be a function of L2's code-factor extrinsic only,
never L2's posterior, so that the forward stage's L1 incoming evidence is not
returned to L1. Each decode invocation SHALL consume its designated syndrome
once: L1 is decoded twice across STAGE 0 and STAGE 2, but STAGE 1's outgoing
code extrinsic removes its entire incoming prior, including STAGE 0's L1
evidence, before STAGE 2 consumes L1 syndrome again. No target posterior SHALL
be fed back, blended, multiplied, or reused. Posterior back-transfer SHALL be
explicitly forbidden.

#### Scenario: Decisive cavity demonstration

- **WHEN** the implementation is tested on tiny two-layer fixtures
- **THEN** it SHALL demonstrate that the forward-stage L1 evidence is excluded
  from the backward prior, that the returned prior is invariant to the removed
  STAGE 0 incoming-message component while remaining sensitive to STAGE 1's
  own check evidence, that iteration-0 neutral extrinsic cannot create a false
  lift, and that warm/unknown provenance is rejected
- **AND** a posterior-based back-transfer double-count SHALL never be reached.

### Requirement: Frozen matrix, decoder and estimator

The implementation SHALL use only the frozen matrix and decoder: `f ∈ [1.0,
1.2]`; seeds `2026091300..2026091315` (16 per `f`); `n=64`; L1 rows 49/59 and
L2 rows 43/52 (`f=1.0`/`f=1.2`); the frozen D5-native mothers; the accepted
Model-F root `workspace/v72p2d5_model_f_input/20260907_r1`; row-layered GF(32)
poly 37, cold start, `max_iter=90`, damping `1.0`. The joint SHALL be obtained
only through `prepare_model_f_prior_candidate` / `build_f_model_concentration`
(per-Bob-column `(counts[:,b] + lambda*p_global)/(n_b[b] + lambda)`); the
historical per-cell `counts + lambda` builder is forbidden.

#### Scenario: Estimator identity

- **WHEN** the implementation is inspected or tested
- **THEN** a static and a behavioral check SHALL fail if the legacy per-cell
  builder is referenced or reached on any path.

### Requirement: Frozen labels, terminal and budgets

The implementation SHALL compute the paired labels
(`COVERAGE_BLOCKED`, `ALTERNATING_REGRESSION`, `STRONG_ALTERNATING_LIFT`,
`WEAK_ALTERNATING_LIFT`, `NO_ALTERNATING_LIFT`), where a complete paired
outcome requires all three stages invoked and finite/shape-valid, per `f` one
complete-chain coverage count is recorded together with explicit
blocked-at-stage1 and blocked-at-stage2 counts, and `COVERAGE_BLOCKED` applies
when complete-chain coverage is below 12/16. It SHALL also compute the
first-applicable run terminal (`D7_H_PRE_EXECUTION_BLOCKED`,
`D7_H_WATCHDOG_TIMEOUT_VOID`,
`D7_H_NONFINITE_OR_CRASH_BLOCKED`, `D7_H_RESOURCE_OVERRUN`,
`D7_H_INCOMPLETE_MATRIX_BLOCKED`, `D7_H_PROVENANCE_COVERAGE_BLOCKED`,
`D7_H_ALTERNATING_STRONG_LIFT`, `D7_H_ALTERNATING_WEAK_LIFT`,
`D7_H_ALTERNATING_REGRESSION`, `D7_H_NO_USEFUL_ALTERNATING_LIFT`), with the
frozen budgets (96-call cap with minimum 32 actual calls, 120 s per-call
watchdog, stored wall <=1500 s, outer `timeout -k 30 1800`, VmHWM `< 2 GiB`
fail-closed, one fresh root).

#### Scenario: Scalar-only evidence root

- **WHEN** the future root is written
- **THEN** it contains exactly the seven scalar text files and no belief,
  prior, symbol, syndrome, block-vector, or extrinsic-array payloads
- **AND** no overwrite or subdirectory is created.

### Requirement: D7-H stays frozen and unauthorized

This change SHALL freeze the D7-H packet only. It SHALL NOT implement,
authorize, or execute D7-H, any decoder call, any Model-F/real read, or any
promotion. All execution authorization fields SHALL remain false and no
`workspace/d7_h_alternating_discriminator_<uuid>` root or identifier SHALL
exist.

#### Scenario: D7-H execution is requested

- **WHEN** an implementer or runner asks to execute D7-H
- **THEN** the answer is that D7-H requires a separate explicit authorization
  bound to one identifier, and this freeze grants nothing.
