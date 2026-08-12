# V9 Recommendation (recorded only because the V8 reproduction gate PASSED)

Change: `formal-nonbinary-ldpc-v8-reference-reproduction`
Date: 2026-08-04
Operator: implementation operator (coder-fast); the decision to open a V9
change belongs to the main thread.

## Reproduction result (frozen, single run)

- Published target: Müller et al. 2024, Quantum Inf Process 23, 195,
  Table 1 row "0.75": q=4, rate 0.75, DET 0.069, EEff 1.053.
- V8 threshold proxy (frozen seed 2026080418, 20000 nodes, max 200 iters,
  binary search p in [0.01, 0.12], tol 0.0025): **0.062422**.
- Delta vs published: 0.0066 <= frozen tolerance 0.015 -> **PASS**.
- Full probe trace: `evidence/v8_reproduction_trace.json`.

## Recommendation (design.md section 7 direction)

The leading V9 direction is a **paper-faithful syndrome reconciliation**:

1. Use the reproduced q-ary QSC ensemble (edge-perspective degree
   distribution, concentrated two-point check distribution implied by the
   code rate) as the basis, not another unvalidated decoder/post-processing
   permutation.
2. Follow the paper's reconciliation construction: syndrome disclosure with
   **blind puncturing/shortening** rate adaptation (paper eq. 12 and the
   blind-reconciliation protocol, Section 2.2.1), decoded in the error
   domain (`d = s + H*y = H*(x+y)`, reconstruct `x_hat = y + e_hat`).
3. Use **fresh roots** and fresh development/confirmation data.  The V8
   reference tooling (independent oracle, full-vector MC-DE) is a
   design/validation aid, not a production decoder.
4. Open a **separate OpenSpec change** for V9; this V8 change authorizes
   only drafting that proposal.

No V9 implementation, execution, or parameter adaptation is performed here.
