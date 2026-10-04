# Proposal: V11 Nonbinary Spatially Coupled DE Gate

## Status

Proposed and plan-frozen on 2026-08-06. This change is documentation-only at
creation time. Scientific execution requires a separate independent freeze
review of the complete V11 packet.

## Why

V10 terminated at `failed_ensemble`: its uncoupled GF(1024) density-evolution
search missed the robust S1 and S3 gates and therefore never authorized a
finite codebook or decoder. Published nonbinary spatially coupled LDPC work
shows threshold improvement and windowed-decoding behavior, including a
direct q-ary symmetric-channel (QSC) reference. V11 will test one narrow
hypothesis: whether spatial coupling, at equal effective rate and with the
same frozen V10 variable-node ensembles, closes the robust threshold gaps.

## Scope

- Reproduce published uncoupled and coupled QSC thresholds at q=4 and q=16
  using the paper's symbol-message-passing (SMP) density evolution.
- Implement and validate an additive full-probability-vector coupled MC-DE
  kernel for GF(1024), reusing V8/V10 field and DE semantics.
- Compare coupled and uncoupled controls with identical effective rate,
  ensemble, seeds, stopping rule, and threshold estimator.
- Evaluate only the robust S1 (`p_gate=.22`) and S3 (`p_gate=.32`) strata.
- Produce a read-only gate decision: `ready_for_finite_length`,
  `failed_reference`, `failed_coupling`, or `resource_blocked`.

## Out of scope

- Reopening, tuning, or overwriting V10 evidence.
- Target-efficiency S2/S4 optimization (`f=1.08`).
- Protograph lifting/PEG, finite parity-check matrices, FFT-QSPA decoder,
  canary/development/confirmation data, real data, qualification, promotion,
  or formal method comparison.
- Treating SMP results as evidence for full-vector FFT-QSPA performance.

If V11 returns `ready_for_finite_length`, protograph/lifting, windowed
FFT-QSPA, and a fresh 4+4 canary require a new successor OpenSpec change.

## Affected areas

- Future additive code: `comparison_bench/src/comparison_bench/methods/`
- Future additive tests: `comparison_bench/tests/`
- V11 evidence: this change's `evidence/` directory and a fresh
  `workspace/nbldpc_v11_*` root
- Frozen baseline: `src/`, `experiments/`, `tools/`, and `results/` remain
  untouched

## Decision requested

Approve only the engineering/reference implementation after an independent
freeze review. No scientific execute is authorized by this proposal alone.
