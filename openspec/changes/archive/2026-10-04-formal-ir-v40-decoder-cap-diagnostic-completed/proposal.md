# OpenSpec Proposal: formal-ir-v40-decoder-cap-diagnostic

**Status**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`
**Domain**: Formal Information Reconciliation / Nonbinary LDPC research
**Change ID**: `formal-ir-v40-decoder-cap-diagnostic`
**Cycle ID**: `V40P0`
**Predecessor cycle**: `V39P0` (`formal-ir-v39-lanec-robustness-laneb-control`)
**Predecessor terminal**: `V39_NO_ROBUST_ROUTE_SIGNAL` (lifecycle
`DEVELOPMENT_RESULT_ACCEPTED`)
**Predecessor result SHA**: `940bfc996a0bd87d60e958150c4f770ee35f16b8`
**Predecessor implementation/execution SHA**:
`90d2d834c136833000ad612adfd8e09bf815d5d2`
**Predecessor accepted plan SHA**: `8efb626ba0eaa6b031abd934ed583739ba70065b`

## Why

The V39P0 authorized run produced Lane C 33/45 and Lane B 31/45 exact-L2
recoveries; both robustness gates failed, with all six `NEITHER_EXACT`
paired failures concentrated in source `1M`. One confounder was never
tested: the frozen decoder ran at `max_iter=30`. Before spending further
budget on Lane B/C, one cheap diagnostic must answer a single question:

**How much of the V39 failure is attributable to the decoder iteration cap,
and does that justify retaining Lane B/C at a fixed extended setting — or
should the budget move to protograph/MET structure design?**

This change freezes that diagnostic: at most 30 real decoder calls
(Phase A 12 + conditional Phase B 12 + conditional probe 6), exactly once,
additive outputs, with a closed-form terminal decision that either fixes
one extended decoder setting for a future confirmation cycle or stops the
Lane B/C decoder-parameter direction immediately.

## Scope

This planning change freezes the V40P0 diagnostic protocol only:

1. **Phase A (exactly 12 calls)**: all six Lane C and all six Lane B
   instances underlying V39 run_01's six `NEITHER_EXACT` pairs, re-decoded
   at `max_iter=90, damping_alpha=1.0`; every other protocol element frozen
   to V39P0 (GF(32) polynomial 37, V25 TRAIN empirical counts, oracle-L1,
   complete-Bob posterior binding, success = `exact_l2`).
2. **Phase B (conditionally exactly 12 calls)**: same 12 instances at
   `max_iter=90, damping_alpha=0.7`; runs only when Phase A produced zero
   wrong codewords, at most 1 exact rescue (out of 12), and residual
   improvement >= 25%.
3. **Probe (conditionally exactly 6 calls)**: three never-used TRAIN
   development blocks (one per source) x two frozen representative
   matrices (one per lane at its representative construction-seed
   ordinal), at the single fixed setting selected by Phase A/B.
4. A deterministic signal/terminal machine covering every judgment branch,
   budget accounting with planned/completed/started actuals, integrity-
   first invalidation, and additive evidence outputs.

No execution is performed by this planning round. Any future implementation
candidate stops at `IMPLEMENTATION_CANDIDATE / EXECUTE_NOT_AUTHORIZED`;
the diagnostic run requires an independent plan ACCEPT plus an explicit
user `EXECUTE_AUTH` bound to the exact implementation SHA.

## Non-goals

- Not a parameter search: exactly two decoder settings are tested
  (90/1.0, 90/0.7); no iteration grid, no damping grid, no warm start, no
  third setting under any outcome.
- Diagnostic rescues SHALL NOT be counted as Lane B/C route successes,
  SHALL NOT retroactively alter the V39 terminal state
  (`V39_NO_ROBUST_ROUTE_SIGNAL`) or any historical B/C conclusion, and
  SHALL NOT automatically start any successor work.
- No Lane A participation; no constructor, loader, evaluator, or decoder
  modification; no FER, asymptotic threshold, SKR, security,
  qualification, promotion, or real-frame claim of any kind.
- No rerun, resume, post-result threshold edit, or post-result seed
  addition. A partial run is terminal evidence, never resumed.

## Affected specs

New delta spec only:
`specs/formal-ir-v40-decoder-cap-diagnostic/spec.md`.
No existing spec, code, test, output, or memory file is modified by this
planning change.

## Lifecycle

This change ends at `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED` with
`development_execution_authorized`, `formal_execution_authorized`,
`scientific_promotion`, `implementation_started`, and
`production_outputs_created` all false. Independent ChatGPT plan review
and explicit main-thread/user authorization are required before any
implementation or execution work starts. The V39P0 run_01 evidence is
already accepted (lifecycle `DEVELOPMENT_RESULT_ACCEPTED`, result SHA
`940bfc996a0bd87d60e958150c4f770ee35f16b8`); no V39 review step remains
open. V40 itself stays unauthorized: execution authorization requires
only this change's independent plan ACCEPT plus an explicit user
`EXECUTE_AUTH` bound to the exact implementation SHA.
