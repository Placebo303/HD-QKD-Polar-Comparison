# Proposal: formal-nonbinary-ldpc-v23-met-protograph-de

> Status: DRAFT — V23 protograph/MET DE gate for q=1024 high-rate structured channel.

## What
Implement a protograph / multi-edge-type (MET) density evolution for q=1024,
target rate ~0.9375 (f<=1.3), on the V17 structured channel. V22 showed plain
and SC-LDPC candidates do not converge; a protograph/MET ensemble may reduce
per-edge check degree while keeping high rate.

## First protograph smoke (2026-08-16)
- 2x32 all-ones protograph (rate 0.9375; variable degree 2, check degree 32).
- q=1024 structured MC-DE via V22b, n_samples=200, max_iter=50, degree_max=512.
- Result: non-converged (final base-q entropy ~0.336).
- Evidence: to be written under
  `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v22_20260816/`.

## Scope
- Design base-matrix search over small protographs (m_p=1..4, n_p=16..64).
- Derive edge-perspective lambda/rho from base matrix and run V22b structured MC-DE.
- Add MET extension only if single-edge protographs remain non-convergent.
- No finite-code construction until DE passes at target f.

## Claim boundary
`diagnostic_only`.
