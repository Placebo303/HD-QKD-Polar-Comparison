# Proposal: NBLDPC10-DE-PEG-FFTQSPA — DE-Optimized Irregular GF(1024) LDPC

## Status

Frozen for autonomous gated execution, subject to every pre-registered hard
stop gate in this change. This proposal authorizes bounded synthetic
engineering, sacrificed canaries, and development only. It does not authorize
qualification, confirmation, real data, N4, promotion, or a formal comparison
claim.

## Why

V9A failed at the ensemble gate: all four searches recorded zero eligible
candidates under the 8-candidate 3-term bounded enumeration. V9's frozen
budgets, 3-term lambda template, and fixed candidate pool were exhausted. V8's
q=4 reproduction proves the method machinery; GF(1024) needs a fundamentally
different ensemble family and full optimization.

V10 replaces V9's bounded enumeration with a general differential evolution
(DE) optimizer over 8-degree sparse lambda representations, consistent with
Müller et al. 2024's dense degree space. It introduces:

- A full error-domain syndrome FFT-QSPA decoder (not layered, not EMS/ADMM).
- Deterministic irregular PEG construction for n=4096.
- Pre-registered canary → development → stop lifecycle.

## Ordered Route

1. **V10-00** — Freeze and audit. Record HEAD, seed/root derivation, allowed
   files, prior evidence identities.

2. **V10-0** — Q=4 reference recovery gate. Reproduce the V8-60 Müller q=4
   R=0.75 ensemble using the DE optimizer without injecting the published
   lambda. Optimizer seeds must differ from V8 reproduction seed (2026080418)
   and all V9 seeds. Final candidate validated on independent seeds. Gate:
   |threshold − 0.069| ≤ 0.012. Failure → STOP; no GF(1024) work.

3. **V10-10** — DE + ensemble kernel engineering. Implement standard
   DE/rand/1/bin, K=8 sparse lambda representation, concentrated rho, 6-tier
   lexicographic objective, deterministic bias-free population initialization,
   mutation/crossover transcript, checkpoint/resume, fail-closed NaN/Inf.

4. **V10-20** — V10A GF(1024) ensemble search and gate. Four independent
   searches (S1–S4). Pre-registered microbenchmark → freeze pre_run_plan →
   independent review → execute exactly once → strict replay exactly once.
   Gate: S1 >= .22, S2 >= .215, S3 >= .32, S4 >= .32. Decision:
   - S1/S3 fail → ordinary irregular GF(1024) = failed_v10a, STOP.
   - S1/S3 pass but S2/S4 fail → robust_only (f=1.15 lane only).
   - All four pass → target_ready (f=1.08 finite-length, f=1.15 backup).

5. **V10-30** — V10B PEG codebook. Convert edge-view lambda to node-view
   counts. Mechanical concentrated rho. Deterministic irregular PEG: local
   girth maximization, ACE-like secondary score, deterministic seeded-RNG tie-break.
   Seeded uniform nonzero GF(1024) edge labels. Enforce n=4096, rank(H)=m,
   zero parallel edges. PEG trial cap → freeze on failure.

6. **V10-40** — V10B FFT-QSPA decoder. Error-domain syndrome-domain log-domain
   FFT-QSPA: GF(1024) edge coefficient permutations, syndrome shift, FWHT
   check convolution, stable normalization, probability floor, flooding
   schedule, per-iteration syndrome check, exact transcript, fail-closed
   NaN/Inf, no Alice truth access. Small-acyclic-graph oracle validated.

7. **V10-50** — V10B sacrificed canary. Engineering ACCEPT + independent
   review → one 4+4 canary plan → execute once → strict replay once. Gate:
   both strata >= 3/4 verified. Failure → failed_canary, STOP.

8. **V10-60** — V10C development. Only after canary pass. Fresh 16+16 frames,
   zero seed overlap. Gate: both strata >= 15/16 verified. readys → stop.

9. **V10-70** — Close-out. Final evidence, independent review, memory triage.

## Frozen Information-Theoretic Sizing

For q=1024 and QSC probability p:

```text
H_q(p) = [h_2(p) + p log2(q−1)] / log2(q)
m(f,p,n) = ceil(f · H_q(p) · n)
R = 1 − m/n
```

All m/R values computed, never hard-coded. Edge-perspective ensemble rate:

```text
R = 1 − (Σ_j ρ_j/j) / (Σ_i λ_i/i)
```

Reconstructed rate error ≤ 1e-12. Concentrated ρ solves
`Σ_j ρ_j/j = (1−R)·Σ_i λ_i/i` exactly with V8-60 formula.

Finite-length leakage: `L_recon = 10·m` (GF(1024) syndrome), fixed 64-bit
verification tag, `L_total = 10·m + 64`. Hard caps; no puncturing,
shortening, adaptive stages, or information-bearing indices.

## Hard Stop Rules

1. V10-0 fails q=4 reference recovery
2. V10A robust gates (S1/S3) fail
3. Planned or formal seed overlap detected
4. Tuning after formal results needed
5. RSS > 3 GiB
6. Single execute > 24 h predicted before plan review
7. Production decoder accesses Alice truth
8. Evidence overwritten
9. Reviewer-go REJECT
10. Canary stratum < 3/4
11. Development stratum < 15/16

Failed evidence is immutable. No rerun, tuning, sample reduction, or selective
frame deletion.

## Completion Boundary

V10 completes with final state ∈ {`failed_reference`, `failed_ensemble`,
`robust_only_failed_canary`, `target_failed_canary`, `development_not_ready`,
`development_ready_not_qualified`}. Even `development_ready_not_qualified`
authorizes only a separate V11 proposal (NB-SC-LDPC). No qualification,
confirmation, real/N4 data, promotion, or formal comparison.

## Scope

Additive V10 modules, tests, CLI, evidence, workspace outputs. Reuse V8 field
tables and V8 q=4/8 oracle (test-only imports). Do not modify frozen baseline,
V1–V9 source/evidence, or existing outputs. V9 modules are not imported except
where explicitly listed in design.md.

### Protocol Amendment (2026-08-06)

Per main-thread instruction, all defensive hash mechanisms (SHA-256 checksums,
integrity manifests with self-hash/source-hash fields, evidence-file hashes,
byte-comparison via SHA-256) are removed from V10 methodology. Replacement
mechanisms: git baseline verification (`git status --porcelain` +
`git diff --name-only` checking frozen directory manifests), direct byte
comparison (file-content equality without intermediate hashing), field-level
plan-binding validation, and semantic recomputation (gate reconstruction,
leakage accounting). `v10_seed` is retained as a deterministic RNG stream
derivation primitive, not a defensive hash — existing executed results
(V10-0, V10A) depend on its exact output.

### V10A Final Status

V10A ensemble gate: **failed_ensemble**. S1 (.2153 @ gate .22), S2 (.1984 @
gate .215), S3 (.3166 @ gate .32), S4 (zero eligible candidates) — all four
FAIL. No "closest to gate" selection. Successor: new V11 NB-SC-LDPC with
fresh everything. V10-30 through V10-60 are halted; only V10-70 close-out
executes.
