# Proposal: V72P2D5 G1 information-recovery R2 (candidate backoff prior path)

- Change: `v72p2d5-g1-information-recovery-r2`
- Predecessor: `formal-ir-v72p2d5-model-f-input-preparation` (accepted input) + D4R2 nested-CV selection (`lambda*=137.3823795883264`) + R1 attribution (`FINITE_LENGTH_DISCLOSURE_INSUFFICIENT`) + R2 wide attribution (`LAMBDA_APPLICATION_CONTRACT_DEFECT`)
- Cycle: `V72P2D5-GF32-RATE-MOTHER`
- Lifecycle: `CANDIDATE / READY_FOR_INDEPENDENT_REVIEW / EXECUTE_NOT_AUTHORIZED`
- Branch: `formal-ir-v72p1-addendum-clean`

## Goal

Add a review-ready, nonformal candidate prior path that applies the frozen
`lambda*` under its selected contract (total per-column concentration with
global-marginal backoff, D4R2 `build_f`), replacing nothing frozen.

## Why

R2 wide attribution (evidence root
`workspace/d5_g1_wide_attribution_r2_5c38a20ae60b41ceb0b6a0d7757aa2aa/`)
proves the accepted consumer `build_f_model` applies `lambda*` as a per-cell
pseudocount (`counts+lam` on 1,048,576 cells: 140,680 added per Bob column vs
~256 observed, 99.82% prior, MI ~0.0004 bits), while D4R2 selected it as a
total per-column concentration (`P(a|b)=(counts+lam*p_global[a])/(n_b+lam)`:
137 added per column, 34.9% prior, MI ~2.48 bits, held-out joint CE 7.16).
The same counts through the same channel-CE functional return to the D4
family (7.51) only under the backoff contract; the accepted consumer yields
~10.0. The defect explains the D4-vs-consumer gap, the APP+oracle double
zero, and the C0-vs-C1 square split (C0 0/4, C1 oracle-L2 4/4 at `m=n=64`).

## Scope

- Add `build_f_model_concentration` (D4R2-F backoff on injected counts) and
  `prepare_model_f_prior_candidate` (candidate `(p_b, p_f)` source) in
  `comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py`.
- Additive only: frozen `build_f_model`, `prepare_model_f_prior`, constants,
  rows formula, seeds, thresholds, authorizations, and all accepted artifacts
  stay byte-identical. No formal rerun, no G2, no VAL, no new CLI flags.
- Tests for the exact defect, numerical limits, axis/normalization,
  deterministic CAL-only selection basis, and formal-root isolation.

## Non-goals

- No change to any frozen function, constant, seed, threshold, authorization,
  accepted artifact, historical packet, or formal root.
- No G2/n256/n1024/real IR, no VAL read/use, no seed search, no new
  dependency/framework/retry/abstraction/integrity machinery.
- No claim that the candidate yields a useful operating point: L1 still fails
  at every disclosure ≤64 with C1 priors (binding constraint, carried
  secondary); L2 recovers only at 52–64 rows (near-zero rate).

## Acceptance

- Candidate reproduces D4R2 `build_f` cell-for-cell (maxerr < 1e-12) on
  injected counts; frozen consumer untouched (per-cell behavior pinned).
- Column normalization within 1e-12; chain-split equivalence within 1e-12;
  invalid shapes/negative lam rejected fail-closed.
- Candidate path reads no files and references no formal root when injected.
- Compile + focused tests + exact three-file D5 suite + candidate development
  diagnostics green; logical commits; no push.
