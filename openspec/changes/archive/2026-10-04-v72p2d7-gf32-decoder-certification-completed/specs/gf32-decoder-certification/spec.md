# Spec delta — `gf32-decoder-certification`

## New capability: independent GF32 decoder oracle (D7-owned)

- The oracle module MUST NOT import or copy production derived tables,
  FFT/Walsh helper, check-update helper, syndrome-offset helper, or
  row-layered update code. It MAY import field/alphabet-size constants
  after independently checking declared values.
- Field multiplication MUST be implemented from the declared GF(2^5)
  primitive polynomial by bitwise polynomial reduction.
- Direct check-SP MUST explicitly enumerate assignments for degree-2 and
  degree-3 checks. Tiny exact posteriors MUST enumerate all assignments
  satisfying `H x = s`.
- Tree acceptance: normalized posterior max-abs error ≤ 1e-10 vs exact
  enumeration. MAP equality is secondary evidence only.
- Loopy acceptance: matched same-schedule per-sweep/per-iteration
  recurrence comparison ONLY. Finite-BP-vs-MAP comparison is forbidden.
- `final_beliefs` representation MUST be established from code and tested;
  the L1→L2 conversion MUST be verified against an explicit probability
  calculation (softmax correctness, axis order, Bob/U1 conditioning,
  positivity, normalization, absent-belief fallback).
- D7-A tests MUST call the historical decoder only on tiny synthetic
  in-memory fixtures; MUST NOT touch Model-F, CAL/VAL, real/raw, formal
  roots, or VOID contents; MUST NOT invoke `--phase`, R1d, G1, or G2.
