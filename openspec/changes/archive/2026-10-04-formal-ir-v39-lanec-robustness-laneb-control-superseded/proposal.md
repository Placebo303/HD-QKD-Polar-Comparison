# OpenSpec Proposal: formal-ir-v39-lanec-robustness-laneb-control

**Status**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`
**Domain**: Formal Information Reconciliation / Nonbinary LDPC research
**Change ID**: `formal-ir-v39-lanec-robustness-laneb-control`
**Cycle ID**: `V39P0`
**Predecessor cycle**: `V38R1`
**Predecessor terminal**: `V38_MULTIPLE_ROUTE_SIGNALS`
**Accepted predecessor result SHA**: `2416486f724f4fb7cbf1058d9dc1bb1fc5ded5ed`
**Independent acceptance commit**: `c8c5cd2e`
**Accepted predecessor implementation SHA**: `8f7bc7d8d7366772ff425528cd1080fa67ef7509`

## Why

The accepted V38R1 development result showed, on one fixed winner matrix per
lane and 15 shared development blocks: Lane C `14/15` exact L2 recoveries
(median residual 0), Lane B `9/15` (median residual 0), Lane A `0/15` (median
residual 115). This is a single-construction-seed, single-block-set signal. It
cannot distinguish a robust architecture-level effect from one lucky
construction seed or one favorable block draw, and it cannot separate Lane C
from Lane B at this sample size.

V39P0 therefore asks exactly one question: does the Lane C strong signal
reproduce across all pre-registered construction seeds and across new
empirical-count development blocks, with Lane B as the pre-registered
structural control?

## Scope

This planning change freezes the V39P0 experiment protocol only:

1. Main route: Lane C (L=8, w=2 spatially banded prototype) evaluated on all
   NINE frozen construction seeds per the existing registry (not only the
   V38 winner).
2. Control route: Lane B (eIRA-like lower-bidiagonal prototype) evaluated on
   all NINE frozen construction seeds, paired to Lane C by construction-seed
   ordinal.
3. Fifteen NEW development block seeds (5 per source), non-overlapping with
   V36/V38 blocks, sampled from the same source-specific V25 TRAIN empirical
   counts with oracle-L1 conditioning.
4. A same-block frozen V31 baseline recomputed once per block on the new
   seeds (15 decoder calls; never duplicated per construction seed).
5. A posterior-binding preflight proving the complete Bob symbol (not
   `u2_bob`) reaches `get_conditional_posterior_l2`.
6. Frozen gates C1 / B1 / CB / BASE, a six-state terminal machine with
   integrity-first precedence, and descriptive-only statistics.

No execution is performed by this planning round. The future implementation
candidate must stop at `IMPLEMENTATION_CANDIDATE / EXECUTE_NOT_AUTHORIZED`;
the single authorized run is exactly 105 real decoder calls written once to an
additive run root.

## Non-goals

- Not a parameter optimization cycle: Lane C L/w/check allocation/support
  rules, Lane B dual-diagonal structure, GF(32) polynomial 37, decoder
  schedule, max_iter=30, damping_alpha=1.0, empirical posterior semantics,
  construction seeds, source dimensions, and gate thresholds are all frozen.
- No Lane A participation: Lane A had residual improvement without exact
  recovery in V38R1 and is excluded from the V39 main experiment.
- No FER, asymptotic threshold, SKR, security, formal-qualification,
  promotion, or real-frame claim of any kind.
- No seed addition, threshold revision after results, rerun, warm start,
  iteration-cap increase, damping search, or automatic successor start.

## Affected specs

New delta spec only:
`specs/formal-ir-v39-lanec-robustness-laneb-control/spec.md`.
No existing spec, code, test, output, or memory file is modified by this
planning change.

## Lifecycle

This change ends at `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED` with
`development_execution_authorized`, `formal_execution_authorized`,
`scientific_promotion`, `implementation_started`, and
`production_outputs_created` all false. Independent ChatGPT plan review and
explicit main-thread/user authorization are required before any implementation
or execution work starts.
