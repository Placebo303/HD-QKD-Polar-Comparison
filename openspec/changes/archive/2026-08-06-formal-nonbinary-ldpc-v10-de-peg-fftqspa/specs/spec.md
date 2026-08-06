# Delta Specification: NBLDPC10-DE-PEG-FFTQSPA

## ADDED Requirements

### Requirement V10-1: Error-Domain Syndrome Reconciliation

The system SHALL decode in the error domain using `e = x + y`, `s_e = H·e`,
and SHALL reconstruct `x_hat = y + e_hat`. The production decoder SHALL NOT
read Alice truth `x` or real error `e`.

#### Scenario: Decoder isolation

- **WHEN** a production decoder is called
- **THEN** its public signature receives no Alice truth parameter
- **AND** tests SHALL verify that no internal call path reads x.

### Requirement V10-2: K=8 Sparse Lambda Representation

The system SHALL represent variable-node edge-perspective degree distributions
as exactly 8 `(degree, weight_logit)` pairs with degrees ∈ [2,40], unique,
sorted ascending. Weights SHALL be softmax-normalized; each retained weight
SHALL be ≥ 0.01; the sum SHALL equal 1.0 within 1e-12. Node-view conversion
SHALL use `L_d = (λ_d/d) / Σ_j(λ_j/j)` and SHALL NOT treat edge-view weights
as node proportions.

#### Scenario: Degree off-by-one

- **WHEN** lambda is represented with polynomial `λ(x) = Σ λ_d·x^{d−1}`
- **THEN** exponent `d−1` corresponds to degree `d`
- **AND** a dedicated test SHALL verify this mapping with explicit examples.

### Requirement V10-3: DE/rand/1/bin Optimizer

The system SHALL implement standard deterministic DE/rand/1/bin with frozen
population size, generations, F, CR. It SHALL support: deterministic seed,
population manifest, mutation/crossover transcript, deterministic tie-break
(strictly better only), checkpoint/resume (no-overwrite), fail-closed NaN/Inf
(penalty + continue), max evaluations cap, workers=1, and replay determinism.

#### Scenario: Deterministic replay

- **WHEN** the same seed and parameters are used
- **THEN** the optimizer SHALL produce identical population trajectories
- **AND** the winner SHALL be byte-identical.

### Requirement V10-4: Hierarchical Lexicographic Objective

The system SHALL evaluate candidates using 6 tiers, applied in order:
1. Entropy convergence at gate p (entropy < 0.01 base-q for 20 consecutive
   iterations → eligible; not converged → ineligible).
2. Fewer iterations to convergence (lower is better).
3. Lower final mean base-q entropy.
4. Lower symbol error probability.
5. Higher coarse binary-search threshold proxy.
6. Canonical degree/weight tuple deterministic tie-break.

Only Tier-1-passing eligible candidates SHALL enter binary search or
refinement.

### Requirement V10-5: V10-0 Q=4 Reference Recovery Gate

The system SHALL optimize a q=4, R=0.75 ensemble without injecting the
published Müller lambda into the initial population. The final candidate,
validated on at least 2 independent seeds, SHALL satisfy
|threshold − 0.069| ≤ 0.012 with reconstructed rate error ≤ 1e-12.

#### Scenario: Gate failure

- **WHEN** the optimized ensemble threshold deviates by more than 0.012
- **THEN** V10 SHALL stop before any GF(1024) work
- **AND** evidence SHALL be frozen without tuning or rerun.

### Requirement V10-6: Microbenchmark and Budget Freeze

The system SHALL run exactly one engineering-only microbenchmark before formal
results. It SHALL use a non-scientific seed, SHALL NOT use S1–S4 formal roots,
and SHALL NOT produce threshold/winner/gate claims. The frozen
`pre_run_plan.json` SHALL contain all budgets, caps, and paths per design
§5.2. After formal results arrive, the budget SHALL NOT change.

#### Scenario: Budget blocker

- **WHEN** predicted execute time for V10A exceeds 24 h
- **THEN** return budget blocker before plan review
- **AND** do not execute.

### Requirement V10-7: V10A GF(1024) Ensemble Gate

The system SHALL run four independent DE searches S1–S4 with frozen budgets,
disjoint optimization and validation seeds (≥3 each), and exactly one execute
plus one strict replay. Gate thresholds: S1 ≥ .22, S2 ≥ .215, S3 ≥ .32,
S4 ≥ .32.

#### Scenario: Robust failure

- **WHEN** S1 < .22 OR S3 < .32
- **THEN** ALL V10 work SHALL stop (`failed_ensemble`)
- **AND** successor SHALL be a new V11 NB-SC-LDPC change with fresh everything.

#### Scenario: Target failure only

- **WHEN** S1 ≥ .22 AND S3 ≥ .32 but (S2 < .215 OR S4 < .32)
- **THEN** SHALL continue `robust_only` with f=1.15
- **AND** SHALL label all artifacts `efficiency_target_not_met`
- **AND** SHALL forbid target efficiency claims.

#### Scenario: All gates pass

- **WHEN** all four gates pass
- **THEN** SHALL continue `target_ready` with f=1.08 finite-length lane
- **AND** f=1.15 backup SHALL be frozen but not run.

### Requirement V10-8: PEG Construction (n=4096)

The system SHALL convert edge-view λ to node-view degree counts, build
concentrated ρ with exact check degree counts, verify socket equality, and
run deterministic irregular PEG with local girth maximization, ACE-like
secondary score, and deterministic seeded RNG tie-break (a local
`np.random.default_rng` seeded from `common.v10_seed(f"peg_tie:{seed}:v:{v}:s:{socket}")`,
first element after `rng.permutation` of the tied group). Edge labels SHALL
be uniform nonzero GF(1024) samples from a frozen seed. The resulting H SHALL
satisfy: zero parallel edges, exact degree sequences, rank_GF1024(H) = m,
syndrome round-trip. PEG trial cap exhausted SHALL freeze and stop. The PEG
manifest SHALL contain construction parameters only (no self-hash or
source-hash fields).

### Requirement V10-9: Error-Domain Log-Domain FFT-QSPA Decoder

The system SHALL decode in the error domain using log-domain flood-scheduled
FFT-QSPA with GF(1024) edge coefficient permutations, coefficient-correct
FWHT check convolution (XOR-order non-normalized WHT + /q inverse), syndrome
shift, stable normalization, probability floor 1e-15 in log-domain, per-iteration
syndrome check, frozen max_iter, fail-closed NaN/Inf, and no Alice truth
access. The decoder SHALL be validated against the V8 direct oracle at q=4,
q=8, and bounded GF(1024) with nonzero syndrome and non-unit edge coefficients.

#### Scenario: Forbidden features

- **WHEN** a decoder implementation is tested
- **THEN** it SHALL NOT use EMS, ADMM, list decoding, Alice-truth fallback,
  or layered scheduling (V10 scientific lane)
- **AND** it SHALL NOT adaptively change iteration count.

### Requirement V10-10: Leakage Accounting

The system SHALL account `L_recon = 10·m` syndrome bits and `L_total = 10·m + 64`
(total: syndrome + 64-bit verification tag). These values SHALL be hard caps.
No puncturing, shortening, adaptive stages, or information-bearing indices
SHALL be present.

### Requirement V10-11: V10B Sacrificed Canary

After engineering T0–T3 and independent ACCEPT, the system SHALL run one 4+4
(p=.20/.30) n=4096 canary plan reviewed once, executed once, and strict-replayed
once. Each frame SHALL verify: decode success, syndrome identity, 64-bit tag
match, no Alice truth, no forbidden state, exact leakage.

#### Scenario: Canary gate

- **WHEN** either stratum has < 3/4 verified success
- **THEN** V10 SHALL stop (`failed_canary`)
- **AND** no parameter tuning SHALL be attempted
- **AND** successor SHALL be V11 NB-SC-LDPC only.

### Requirement V10-12: V10C Development

Only after canary PASS, the system SHALL run one 16+16 (p=.20/.30) n=4096
development plan with zero seed overlap. Both strata SHALL have ≥ 15/16
verified success to reach `development_ready_not_qualified`.

#### Scenario: Development readiness

- **WHEN** ≥ 15/16 in both strata
- **THEN** V10 SHALL stop at readiness
- **AND** no confirmation, qualification, real data, N4, promotion, or
  comparison SHALL be created.

### Requirement V10-13: Evidence Integrity and Tamper Detection

Verification SHALL cover: raw byte drift (direct file-content comparison,
not SHA-256), semantic JSON tamper (field-level gate reconstruction
disagreement, leakage accounting recomputation failure, winner reconstruction
mismatch, plan-binding field validation rejection), seed separation
verification, optimizer transcript integrity, syndrome round-trip, tag
verification, and fake promotion detection via gate reconstruction.

Git baseline verification (`git status --porcelain` + `git diff --name-only`
checking that frozen directories and allowed source files are unchanged)
SHALL be used to detect unauthorized modifications to frozen baseline files.

No evidence file SHALL contain SHA-256 hash fields. New evidence files
produced after the 2026-08-06 protocol amendment SHALL use parameter-level
assertion, field-level validation, and git baseline instead of hash-based
integrity manifests.

Tests SHALL use explicit fake runners; production decoder paths SHALL NOT
be entered by default. All tests SHALL use `pytest -p no:cacheprovider` with
fresh additive `workspace/<v10-stage>/<uuid>` roots.

### Requirement V10-14: Resources and Budget

Peak process-tree RSS SHALL NOT exceed 3 GiB. Workers SHALL be exactly 1.
Budget SHALL be frozen in `pre_run_plan.json` and SHALL NOT change after
formal results. Hard evaluation caps: screen ≤ 600 per search, refinement
candidates ≤ 12. The budget SHALL include exact output paths.

### Requirement V10-15: Authorization Boundary

V10 SHALL NOT create or execute qualification, confirmation, real-data, N4,
promotion, or formal-comparison work. Even `development_ready_not_qualified`
SHALL only authorize a separate V11 proposal. No V10 output SHALL appear under
`comparison_bench/outputs_comparison/formal_ir_methods/`.

### Requirement V10-16: Seed Disjointness

All V10 seeds SHALL use prefix 202610xx, provably disjoint from V8
(20260804xx) and V9 (20260901xx). Optimization, validation, canary, and
development seeds SHALL all be mutually disjoint. Proof SHALL appear in
`evidence/v10_freeze_acceptance.json`.

#### Scenario: Seed overlap

- **WHEN** any V10 seed overlaps with any V8 or V9 seed
- **THEN** V10 SHALL stop immediately
- **AND** seeds SHALL be re-derived before any scientific data exist.
