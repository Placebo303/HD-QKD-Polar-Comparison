---
slug: "formal-nonbinary-ldpc-v5-multistage-ir"
createdAt: "2026-07-31T07:48:03.699Z"
---

# Proposal: Formal Nonbinary LDPC v5 Multistage IR

## Why

The immutable v4 package (`20260731_v4_nbldpc_ir_synthetic`) passed strict
replay but missed promotion by eight p=.30 confirmation frames: 128/128 at
p=.20 and 120/128 at p=.30 against the frozen 128/128 gates.  All eight misses
were `decode_failed` after the single 40→48 extension and 12 iterations; there
were zero prohibited failures.  The frozen diagnosis is that one eight-row
extension is insufficient in the p=.30 tail under the v3 codebook and
layered-FFT-QSPA decoder.

This change pre-registers four improvement routes and executes them **in
order until one succeeds**: (A) three-level 40→48→56 rate-compatible
incremental redundancy; (B) a redesigned nested-prefix mother code; (C) a
stronger bounded decoder (improved FFT-QSPA / EMS); (D) bounded list/ADMM
post-processing.  Each route is an independent, freshly isolated synthetic
qualification with its own method identity, data roots, package, and the same
pre-registered promotion gate.  A route that earns synthetic promotion ends
the change; a non-promoted route is frozen immutably and the next route runs
on wholly fresh data.  Current v4 confirmation rows are diagnostic context
only and are never used as tuning data.

## Scope

- **Route A** — `nbldpc_formal_v5a_multistage`: exact v3 48-row codebook plus
  one deterministic 8-row extension block (56-row mother), three-level warm IR
  40→48→56 at p=.30 and two-level 32→40 at p=.20, with a two-level control
  policy on the same data.
- **Route B** — `nbldpc_formal_v5b_mother`: a newly designed deterministic
  56-row nested-prefix mother code (40/48/56) selected by a frozen structural
  proxy that targets the p=.30 tail distance spectrum, used by the same
  three-level warm IR state machine.
- **Route C** — `nbldpc_formal_v5c_decoder`: stronger bounded decoders —
  log-domain FFT-QSPA with a fixed damping schedule and an EMS decoder with
  truncated nm-symbol messages — compared on the best frozen 56-row codebook,
  inside the same three-level IR framework.
- **Route D** — `nbldpc_formal_v5d_post`: bounded list post-processing
  (top-K belief candidates checked against the disclosed syndrome) followed by
  bounded GF(q) ADMM/proximal post-processing, applied only to frames that the
  best frozen decoder leaves `decode_failed`.

Each route: 64 sacrificed development frames per stratum, one frozen plan,
one execution, one strict read-only replay, readiness at 63/64 in both
development strata, and promotion at 128/128 verified successes in both
confirmation strata with zero prohibited failures.  The routes share the v4
eight-artifact naming, identity-freshness checks, leakage/transcript
accounting, diagnostic exclusion, and no-overwrite semantics.

## Out of Scope

- Modifying v1-v4 source, plans, data, policies, results, seeds, or artifacts.
- External decoder/codebook dependencies; confirmation-driven tuning; rerunning
  any route; continuing to tune a non-promoted route.
- Real sidecars, raw `.ttbin`, N4, real-data claims, or method-comparison
  claims.
- More than one route after a promotion: the change stops at the first
  promoted route.  If all four routes are non-promoted, the change terminates
  as four immutable non-promoted packages.

## Affected Specs

- Add `formal-nonbinary-ldpc-v5-multistage`.
