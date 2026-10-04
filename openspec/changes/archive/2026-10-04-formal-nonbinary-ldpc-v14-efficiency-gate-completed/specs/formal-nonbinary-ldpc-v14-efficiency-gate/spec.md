# Delta spec: formal-nonbinary-ldpc-v14-efficiency-gate

## ADDED Requirements

### Requirement: Structured channel model is frozen and cross-fitted

The gate SHALL use a structured GF(1024) symbol-difference distribution
derived read-only from the V13 characterization frames (128 bw200 frames),
smoothed with a frozen mixing parameter λ=1e-3 toward uniform, normalized,
and persisted as a public aggregate (`v14_structured_channel_model.json`,
schema `nbldpc_v14_channel_model_v1`). The fit SHALL use characterization
frames only; development/audit frames and audit truth SHALL NOT enter the
fit.

### Requirement: Gate decides before construction

The gate SHALL evaluate a frozen candidate set of three edge-perspective
variable-degree profiles (λ = {2:0.25, 3:0.30, 4:0.45};
λ = {2:0.20, 3:0.25, 5:0.55}; λ = {3:0.3, 4:0.7}) at the four frozen rate
points m ∈ {15, 16, 17, 18} (n=256, q=1024; R = 1 − m/256;
f = (m·10/256)/H(w') ∈ {1.071, 1.143, 1.214, 1.286}), with the check-side
degree distribution fixed per rate by the harmonic-exact concentrated
distribution. The gate SHALL emit exactly one `gate_state` of
`{pass, fail, mechanism_unverified}`. `pass` requires the Stage-0 mechanism
regression to pass AND at least one of the twelve frozen points whose DE
message entropy converges below the frozen threshold within the frozen
iteration budget AND whose f ≤ 1.3. `fail` freezes the route to
fresh-confirmation-only; no retry, no tuning, no post-measurement rule
change, no "closest" continuation.

### Requirement: Mechanism regression gate Stage 0

The extended DE machinery SHALL reproduce the accepted V8-60 reference
(Müller et al. 2024 Table 1 row 0.75: q=4, R=0.75, published threshold
0.069, computed proxy within |δ| ≤ 0.012) in QSC mode before the
structured-channel stages may run. A regression failure SHALL emit
`mechanism_unverified` (or `failed_reference`) and forbid Stage 2.

### Requirement: Claim boundary

DE convergence is an asymptotic-ensemble statement only. The gate SHALL NOT
emit or imply finite-length FER, qualification, promotion, or
`observed_fresh_correction`. Gate evidence SHALL be additive under
`openspec/changes/formal-nonbinary-ldpc-v14-efficiency-gate/evidence/` and
SHALL NOT touch official qualification roots, V13 artifacts, or the frozen
baseline directories.
