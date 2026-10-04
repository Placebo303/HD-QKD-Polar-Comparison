# Nonbinary LDPC V11 — Spatially Coupled DE Plan

Status: **plan frozen; implementation and scientific execution not yet
authorized** (2026-08-06).

OpenSpec change:
`openspec/changes/formal-nonbinary-ldpc-v11-sc-de-gate/`

## Outcome sought

V10's uncoupled GF(1024) ensemble gate missed S1 by .0047 and S3 by .0034.
V11 tests whether spatial coupling closes both gaps under a fair equal-rate
comparison. It deliberately does not retry V10 optimization and does not build
a finite code.

## Why the plan changed after literature review

The literature supports two distinct checks, which must not be conflated:

1. A published QSC spatial-coupling result can validate channel, protograph,
   and window mechanics. Ben Yacoub et al. report rate-1/2 `(3,6)`, `W=30`
   uncoupled/coupled thresholds of .0890/.0942 at q=4 and .1075/.1288 at q=16.
2. That paper uses simplified symbol-message passing, not full-vector
   FFT-QSPA. Therefore it cannot directly validate the GF(1024) decoder model.
   V11 adds separate collapse and small-field oracle checks before the
   full-vector coupled MC-DE is allowed to decide the gate.

This is stronger than importing a BEC or binary-AWGN threshold-saturation plot
and assuming it transfers to the HD-QKD QSC.

## Frozen experiment

- Strata: robust S1 (`p=.20`, `f=1.15`, gate .22) and robust S3 (`p=.30`,
  `f=1.15`, gate .32) only.
- Ensembles: reuse the frozen V10 S1/S3 variable-node distributions; no new
  degree search.
- Fairness: compensate termination rate loss so every coupled chain has the
  same effective rate and total asymptotic leakage as its uncoupled control.
- Coupling: uniform edge spreading; G1 `(w=1,L=32,W=8)`, G2
  `(w=2,L=32,W=16)`, G3 `(w=2,L=32,W=32)`.
- Statistics: five fresh, disjoint validation seeds per cell, paired with the
  uncoupled control; identical threshold estimator and stopping rule.
- Resources: pre-gating microbenchmark; projected formal wall time <=24 h and
  peak RSS <=3 GiB.
- Lifecycle: prepare -> independent read-only review -> one execute -> one
  strict replay -> independent gate recomputation.

## Pass/fail rule

A geometry passes only if both conservative thresholds reach .22/.32 and both
paired gains are at least .002. All seeds, rate checks, resource checks,
replay, and frozen-scope checks must also pass. Choose the passing geometry
with smallest `W`, then smallest `w`.

No pass means `failed_coupling`; do not report a “closest” candidate or tune
the grid. Reference failure means `failed_reference`. Budget failure means
`resource_blocked`. A pass means only `ready_for_finite_length`.

## Next authorization boundary

Only after `ready_for_finite_length` may a new OpenSpec change propose:

1. the selected terminated protograph and lift/PEG construction;
2. full-rank finite parity-check matrices;
3. a windowed FFT-QSPA decoder with the same leakage accounting; and
4. a fresh sacrificed 4+4 canary before any development data.

That later work remains unauthorized in V11. Target-efficiency lanes S2/S4,
real data, confirmation, qualification, promotion, and formal comparison also
remain out of scope.

## References

- Ben Yacoub et al., AEIT 2019, DOI 10.23919/AEIT.2019.8893373.
- Wei et al., ISIT 2014, DOI 10.1109/ISIT.2014.6874959,
  arXiv:1403.3583.
- Mitchell et al., IEEE TIT 2015, DOI 10.1109/TIT.2015.2453267,
  arXiv:1407.5366.
- Andriyanova and Graell i Amat, IEEE TIT 2016,
  DOI 10.1109/TIT.2016.2540800, arXiv:1311.2003.
- Zhang et al., IEEE Communications Letters 2016,
  DOI 10.1109/LCOMM.2016.2600662.
- Lyu and He, arXiv:2512.24232 (2025 preprint; supplementary only).
- Müller et al., Quantum Information Processing 23, 195 (2024),
  DOI 10.1007/s11128-024-04395-w, arXiv:2307.02225v2.
