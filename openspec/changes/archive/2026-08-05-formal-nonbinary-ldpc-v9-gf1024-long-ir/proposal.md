# Proposal: Formal Nonbinary LDPC V9 GF(1024) Long-Block IR

## Status

Proposed and frozen for autonomous execution through V9C, subject to every
pre-registered stop gate in this change. This proposal authorizes bounded
synthetic engineering, sacrificed canaries, and development only. It does not
authorize qualification, confirmation, real data, N4, promotion, or a formal
comparison claim.

## Why

V8-60 independently accepted the error-domain reconciliation algebra, an
independent probability-domain oracle, full-vector q-ary QSC MC-DE, and a
corrected q=4 published reference reproduction. V7 R2 was only a scalar
surrogate and therefore did not test this route. V6/V7 finite candidates used
different ensembles or models and do not close a paper-faithful irregular
GF(1024) long-block construction.

V8's q=4 result validates the method and audit machinery only. It is not a
threshold, FER, or finite-length success result for GF(1024). V9 must first
build and validate the GF(1024) bridge.

V9A itself is a scientific evidence stage. Before any search result, one
complete plan freezes all four candidate searches, budgets, seeds, targets,
and validation rules. It then follows plan-only -> independent read-only
review -> exactly one deterministic execute containing all four searches and
multi-seed validations -> exactly one strict replay. Failed V9A evidence is
immutable and cannot be tuned or rerun.

## Ordered Route

1. **V9A — GF(1024) ensemble design.** Implement scalable length-1024
   probability-message MC-DE using FFT/WHT check updates, cross-check it
   against the V8 direct oracle, then optimize separate irregular ensembles
   for p=.20 and p=.30 at robust efficiency f=1.15 and target efficiency
   f=1.08. Robust conservative thresholds must reach .22/.32; target
   thresholds must reach .215/.32 for p=.20/.30; .215 stays below the p=.20
   f=1.08 capacity threshold (~.21827). A target failure permits robust-only
   continuation with `efficiency_target_not_met`; a robust failure stops V9.
2. **V9B — n=4096 finite-length bridge.** Only after V9A robust PASS, build
   irregular PEG/ACE (or a documented equivalent) codebooks with random
   nonzero GF(1024) edge weights and an error-domain layered log-FFT-SPA
   decoder. Complete engineering acceptance, then run one fresh sacrificed
   4+4 canary and one strict replay.
3. **V9C — long-superframe bridge.** Only after V9B PASS, test n=16384 with a
   fresh 4+4 canary. Only after that gate passes, build n=32768 from 32
   constituent 1024-symbol synthetic frames, preserve constituent provenance,
   use a fixed-rate candidate per stratum with exact syndrome/tag accounting,
   run one fresh 4+4 canary, and, on PASS, one fresh 16+16
   development package plus strict replay.

## Frozen Information-Theoretic Sizing

For q=1024 and QSC probability p, define

```text
H_q(p) = [h_2(p) + p log2(q-1)] / log2(q)
m(f,p,n) = ceil(f * H_q(p) * n)
R = 1 - m/n
```

The implementation must compute these values; rounded descriptions such as
approximately 321/458 robust and 301/430 target checks per 1024 symbols are
informative only and must never be hard-coded.

For each requested rate, the edge-perspective check distribution must satisfy

```text
sum_j rho_j/j = (1-R) * sum_i lambda_i/i
```

to absolute reconstructed-rate error at most 1e-12.

Every finite GF(1024) parity-check matrix must have full row rank
`rank(H)=m`. Rank failure is resolved before a scientific plan by bounded
deterministic reconstruction or terminates as a blocker; a rank-deficient
graph cannot be used and its effective rate cannot be repaired after data.

All n>1024 inputs are constituent superframes: n=4096 uses 4, n=16384 uses
16, and n=32768 uses 32 ordered, mutually disjoint 1024-symbol constituents.
Every plan binds their IDs, order, roots, seeds, hashes, and aggregate mapping;
constituents cannot be reused across V9 stages.

V9C is fixed-rate per stratum. With the selected tier, each plan freezes
`m=ceil(f*H_q(p)*n)`, `L_recon=10*m` bits for the GF(1024) syndrome, a separate
fixed 64-bit correctness tag, and `L_total=10*m+64`. These mechanical values
are also the hard leakage caps. V9 forbids shortened values, puncturing,
information-bearing indices/control, or any other reconciliation payload.
Blind rate adaptation is deferred to a separate future V10 change.

## Scope

Allowed changes are additive V9 modules, CLIs if required, tests, this OpenSpec
change, V9 workspace/output packages, and minimal project documentation
updates. Reuse V8 contracts without changing V8 files or evidence.

The original `src/`, `experiments/`, `tools/`, and `results/` trees and all
V1-V8 source/evidence are frozen. Existing output packages are immutable.

## Lifecycle Authority

Each scientific package follows:

```text
prepare -> independent read-only plan review -> exactly one execute
        -> exactly one strict read-only replay -> gate decision
```

Fresh roots and seed IDs must be proved disjoint from all prior evidence and
from every earlier V9 stage. Failed packages are immutable. No tuning or rerun
is permitted from failed canary/development rows.

The frozen packet authorizes automatic continuation across V9A, V9B, and V9C
without another user confirmation only when the immediately preceding gate
passes. A failed gate terminates the change at that point.

## Completion Boundary

V9 completes when either:

- V9C n=32768 development reaches at least 15/16 verified successes in each
  stratum with zero forbidden states, strict replay, median runtime no more
  than 24 hours per superframe, and peak memory no more than 3 GiB; or
- a frozen stop gate fails and the immutable evidence plus concrete blocker or
  non-promotion conclusion is recorded.

The n=32768 canary additionally has a hard 24-hour timeout per superframe and
may advance only when its median runtime is at most 16 hours. Development
retains the at-most-24-hour median gate.

Even a full V9 PASS authorizes only a new qualification proposal. It does not
authorize confirmation, real/N4 data, promotion, or comparison.
