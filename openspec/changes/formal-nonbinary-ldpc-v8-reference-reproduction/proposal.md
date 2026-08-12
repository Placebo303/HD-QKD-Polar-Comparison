# Change: Formal Nonbinary LDPC V8 Reference Reproduction

## Why

V7 completed its engineering ladder, but all four sacrificed canaries failed to
produce a development-ready route. This does not establish that nonbinary LDPC
is unsuitable for the project. It establishes that the implemented candidates
did not pass their frozen gates.

Two audit findings prevent a scientifically sound V8 from immediately running
another canary:

1. V7 R1B combines Bob's observation with a second independently corrupted
   observation synthesized from Alice. That is a useful algorithm diagnostic,
   but it is not the project's asymmetric reconciliation contract, where Bob
   has one paired-symbol observation and Alice discloses public information.
2. V7 R2 uses a scalar two-level density-evolution surrogate. It does not yet
   reproduce the paper's full nonbinary message distributions, exact sampled
   degrees, edge-perspective degree distributions, or channel contribution at
   every variable update.

V8 therefore creates a reference-reproduction and mathematical-audit layer
before any new scientific data are generated.

## What Changes

- Add an audit record that preserves V1-V7 evidence while correcting what
  conclusions may be drawn from R1B and R2.
- Express reconciliation in the error domain:
  `d = H*y + s = H*(x+y)`, decode the error, then reconstruct Alice.
- Add an independent, deliberately slow probability-domain oracle for small
  fields and one-check GF(1024) comparisons. It must not call production
  FFT/FWHT check-update code.
- Add full-vector Monte-Carlo density evolution for the q-ary symmetric
  channel, with edge-perspective degree distributions, exact sampled degrees,
  channel messages in variable updates, and average message entropy as the
  convergence observable.
- Reproduce at least one published q-ary reference configuration before any
  project-specific GF(1024) ensemble is proposed.
- Add T0-T3 engineering and regression evidence only.

## Non-Goals

- No canary, development, confirmation, real-data, N4, or formal comparison
  execution.
- No new production output directory under
  `comparison_bench/outputs_comparison/formal_ir_methods/`.
- No reinterpretation, overwrite, deletion, or rerun of frozen V1-V7 packages.
- No optimization of degree distributions until the reference reproduction
  gate passes.
- No external dependency, repository clone, vendored implementation, or copied
  third-party source.

## Affected Areas

- `comparison_bench/src/comparison_bench/formal_ir/` (additive V8 modules)
- `comparison_bench/tests/` (additive V8 tests)
- this OpenSpec change and its evidence directory
- `docs/nonbinary-ldpc-v7-audit-v8-plan.md`
- additive entries in project decision/handoff documents

## Authorization Boundary

Completing V8 authorizes only a proposal for a separate V9 finite-length
development change. It does not authorize V8 scientific execution or imply
promotion of any nonbinary route.

---

## V8-60 Correction Addendum (2026-08-04)

## Why

An independent audit of the accepted V8 candidate found a formula-level
approximation in `concentrated_check_distribution`: the original weights
matched the two-point *mean* check degree (`w_lo = dc_hi - dc_mean`), which
does not satisfy the edge-perspective rate condition exactly. For
edge-perspective `lambda`/`rho` the ensemble rate is

```text
R = 1 - (sum_j rho_j/j) / (sum_i lambda_i/i)
```

so the check distribution must solve `sum_j rho_j/j = (1-R) * sum_i lambda_i/i`
exactly. The mean-matched weights only approximate this (relative error
~1e-4), which biases the concentrated `rho` used by the reproduction. This is
a non-tuning formula correction, not a parameter change.

Two additional audit findings are corrected here: `REPRODUCTION_CITATION`
listed the first author with the wrong given name ("Rasmus T. Müller" instead
of "Ronny Müller"), and the frozen tolerance justification
(`0.005+0.003+0.0025 = 0.015`) is arithmetically wrong.

## What Changes

- `concentrated_check_distribution` solves the exact edge-perspective rate
  equation for adjacent check degrees `{floor(dc), ceil(dc)}` with weights
  `w_lo = (target - 1/d_hi) / (1/d_lo - 1/d_hi)`, `w_hi = 1 - w_lo`, where
  `target = (1-R) * sum_i lambda_i/i` and `dc = 1/target`; integer `dc`
  degenerates to the regular check degree.
- New `reconstructed_rate(lambda_edge, rho_edge)` helper and tests asserting
  `|reconstructed_rate - target_rate| <= 1e-12` for the reproduction config
  and additional rate/lambda configs.
- Frozen golden traces are re-recorded once under the corrected formula
  (same configs and seeds; recording, not tuning).
- `REPRODUCTION_CITATION` authors corrected to Ronny Müller et al. (matching
  the arXiv:2307.02225v2 author list).
- One corrective reference run with the paper's MC-DE budget (100000 nodes,
  max_iter 150, same frozen seed) after freezing corrected parameters and a
  corrected auditable tolerance; result in
  `evidence/v8_reproduction_trace_corrected.json`.
- `evidence/v8_reproduction_trace.json` is preserved byte-identical and
  marked (sidecar annotation) as the pre-correction approximate trace.
- Additive close-out evidence: correction record, independent-review
  acceptance, and an acceptance close-out addendum that resolves the original
  `A12 = blocked` status without rewriting `v8_engineering_acceptance.json`.

## Non-Goals (unchanged)

- No V9 implementation, no canary/development/confirmation/real-data/N4/
  comparison execution, no official output, no dependency changes, no
  staging/committing/pushing.
- No rerun of the original reproduction and no tuning of any frozen
  parameter against the published target.
