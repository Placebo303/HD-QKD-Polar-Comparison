# Polar Paper-Grade Qualification V2

Date frozen: 2026-08-11 (Asia/Shanghai)

## Objective

Produce a reproducible, paper-citable binary Polar reconciliation result from the existing cached sidecars without overwriting historical evidence. The qualification separates decoder performance, correctness verification, and QKD security-model claims.

## Frozen scientific choices

- Main decoder: frozen-value-aware ordinary SCL with list size 4.
- Final SCL path: minimum path metric. CRC-aided path selection is excluded from the main route because the experimental sifted keys are not CRC-precoded.
- Legacy CA-SCL remains comparison-only and cannot supply main-route rates or replay metadata.
- Polar construction: the existing polarization-weight order is retained for V2; changing the construction is a separate study.
- Correctness check: one uniformly random Toeplitz matrix, sampled independently after the cached input strings are fixed, recorded once, and reused across the fixed batch. The union bound is taken over all invoked blocks.
- Main verification tag length: 64 bits. The full Toeplitz seed and sampling rule must be stored with the result package. The earlier 32-bit canary is retained as a failed correctness-budget precheck because its batch union bound exceeded `eps_cor=1e-10`.
- Historical `results/authoritative/` trees are immutable. Every V2 run writes to a new ignored output root.

## Evidence tracks

1. **Reconciliation result:** actual kept information, public frozen-bit leakage, decoder FER, verification leakage, runtime, and deterministic replay metadata. This is the paper-grade target of V2.
2. **Calibrated security estimate:** existing visibility/finite-size model, clearly labelled as a model-dependent estimate.
3. **Composable HD-QKD security:** out of scope until the observables required by a strict Zhong/Niu-style proof are available. V2 must not promote the calibrated estimate into this category.

## Qualification ladder

### Q0 — Unit correctness

- Exhaustive/small randomized Polar transform checks.
- Arbitrary-key ordinary SCL checks with nonzero frozen values.
- A discriminating case proving that legacy CRC selection and ordinary SCL are not interchangeable.
- Random-seed Toeplitz API checks and fail-closed input checks.
- Metric aggregation and effective-sample-size invariants.

### Q1 — Reproducibility

- Same input and frozen simulation seed produce byte-equivalent scientific CSV values.
- Worker count and task completion order do not change selected rates.
- Changing only the verification seed changes verification tags, not decoder outputs or FER.

### Q2 — Canary replay

- Use cached sidecars only.
- Run predeclared representative points from all four loss settings into a fresh output root.
- Require no blocked decoder rows, no CRC budget on the main SCL route, internally consistent per-layer and point metrics, and explicit provenance for every parameter.

### Q3 — Full cross-loss back-half

- Rebuild Polar layer selection if required by the corrected decoder qualification.
- Replay all 4 losses x 121 points into a new V2 result root.
- Run read-only validation over decoder mode, leakage, random-seed provenance, correctness bound, schema completeness, and cross-table identities.
- Preserve failures; no confirmation-data tuning or rerun-to-pass.

## Statistical rule

The selection rule and simulation seeds must be fixed before Q2. A raw `FER < 0.05` decision from 100 frames is not sufficient by itself. V2 must use a deterministic one-sided uncertainty rule or a predeclared boundary extension, and report trials, errors, point estimate, and acceptance statistic.

## Acceptance boundary

V2 is paper-citable only when:

- Q0-Q3 pass without changing frozen rules after seeing Q2/Q3 outcomes;
- ordinary SCL is used consistently in simulation and actual replay;
- the verification seed is genuinely random, independent of the fixed messages, and recorded;
- reported point-level PIE equals the sum of the selected layer configurations;
- effective sample sizes do not count decoder rejection twice;
- the result package states which claims are measured, simulated, calibrated, and not supported.

## Minimal implementation rule

No new framework, database, package layer, checksum scheme, or raw-data rerun is required. Reuse the existing scripts and cached sidecars; add only the decoder mode, random verification input, invariants, and qualification tests needed above.
