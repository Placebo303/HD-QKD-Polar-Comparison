# Design: NBLDPC10-DE-PEG-FFTQSPA

## 1. Scientific Contract

Alice holds `x`, Bob holds `y`. Alice publishes syndrome `s_x = Hx`. Bob derives
error-domain syndrome `s_e = s_x + Hy = H(x+y) = He`. Decoder operates on
`y`, QSC error prior (P(e=0)=1−p, P(e=a)=p/1023 ∀a≠0), `H`, `s_e`, frozen
`p`, and public configuration. No Alice truth or real `e` may enter the
production decoder.

Success requires ALL of:
1. `H·e_hat = s_e`
2. `x_hat = y + e_hat`
3. `H·x_hat = s_x`
4. Independent 64-bit verification tag matches

Any step failure → `decode_failed`. No fallback to success.

## 2. Ensemble Representation

### 2.1 Edge-Perspective Lambda

`lambda(x) = Σ_d λ_d · x^{d−1}` where degree d variable nodes have edge-fraction
weight `λ_d`. Off-by-one convention: exponent `d−1` ↔ degree `d`.

**K=8 sparse representation** (deterministic, frozen):

Each candidate is an ordered 8-tuple of `(degree, weight_logit)` pairs:
- degrees: `d ∈ [2, 40]`, all 8 unique, sorted ascending.
- weight_logits: unconstrained reals.
- Normalization: `λ_d = softmax(weight_logits)_d` applied only to those 8
  degrees; all other degrees have `λ_d = 0`.
- Constraint violation → soft-rejected in DE objective (penalty magnitude
  1e6 + violation amount) AND fail-closed by validator:
  - `Σ_d λ_d` must be 1.0 within 1e-12.
  - Each `λ_d ≥ 0.01` (minimum edge-fraction weight).
  - Degrees must be sorted ascending.
  - Weights must be finite; logits must be finite.

Node-view conversion (mechanical, never bypassed):
```text
L_d = (λ_d / d) / Σ_j (λ_j / j)
```
Edge-view weights must NEVER be used as node proportions.

### 2.2 Concentrated Check Distribution (Rho)

From the V8-60 harmonic-exact formula:
```text
integral_lambda = Σ_i λ_i / i
target          = (1 − R) · integral_lambda
dc              = 1 / target
d_lo = floor(dc), d_hi = d_lo + 1    (d_lo >= 2 required)

integer dc → regular {d_lo: 1.0}
otherwise  → w_lo = (target − 1/d_hi) / (1/d_lo − 1/d_hi)
              w_hi = 1 − w_lo
              ρ = {d_lo: w_lo, d_hi: w_hi}
```

Reconstructed rate check: `|1 − (Σ ρ_j/j)/(Σ λ_i/i) − R| ≤ 1e-12`. All `m`
computed by formula, never hard-coded.

## 3. Differential Evolution Optimizer

### 3.1 Variant

DE/rand/1/bin (Storn & Price 1997), standard deterministic implementation,
NumPy-only (no SciPy).

Frozen parameters:
- Population size: `pop_size` (to be frozen in pre_run_plan)
- Generations: `max_gen` (ditto)
- Mutation factor: `F` (scalar)
- Crossover: `CR`
- All population members initialized with deterministic, bias-free
  degree/logit generators seeded from the search seed.
- Candidate encoding: 16 reals (8 degrees + 8 logits). Degrees are
  quantized: the encoded real is mapped to `round(max(2, min(40, x + 2.0)))`
  — this constrains the floating degree component to [2,40] with discrete
  mutation.

### 3.2 Deterministic Mutation / Crossover

Mutation: `v_i = x_r1 + F · (x_r2 − x_r3)` with `r1 ≠ r2 ≠ r3 ≠ i`.
Crossover: binomial. Tie-breaking: in DE selection, replace only on
strictly better objective; equal objective → retain incumbent (deterministic).

### 3.3 Checkpoint / Resume

- Save population and generation state after every generation.
- Resume from exact saved state.
- No-overwrite: refuse to resume into an existing completed run.

### 3.4 Transcript

Record per-generation: best objective, best degrees, best weights, F,
CR, mutation/crossover indices, objective component values.

### 3.5 Fail-Closed

On NaN/Inf in any objective component or message → record as invalid
evaluation, impose a large penalty (`1e12`), retain population member
in the death pool, and continue.

### 3.6 Evaluation Caps

Hard cap: `max_evaluations` per search (frozen in pre_run_plan).

## 4. Optimization Objective (Hierarchical Lexicographic)

Each TIE round (at the gate `p_gate`) evaluates a candidate lambda and
returns an **eligible** flag plus a 6-component tuple:

| Tier | Component | Direction | Meaning |
|------|-----------|-----------|---------|
| 1 | entropy_converged | maximize (bool) | Converged at gate p (entropy < 0.01 base-q, 20-iter streak) |
| 2 | converged_iter | minimize | Iterations to convergence (lower better) |
| 3 | final_entropy | minimize | Mean base-q entropy at convergence or final iteration |
| 4 | error_prob | minimize | P(e≠0) ≡ 1 − P(e=0) at final iteration |
| 5 | threshold_proxy | maximize | Coarse binary-search threshold (optional, computed post-screen) |
| 6 | canonical_tuple | minimize | Deterministic tie-break: `(d0, d1, …, d7, λ0, …, λ7)` as lexicographic ascending compare |

Only candidates that pass Tier 1 (`entropy_converged = True`) are considered
**eligible**. A non-converged candidate receives an objective of all sentinel
maxima and is excluded from the gate screen.

### Gate Screen Protocol

1. Each candidate evaluated once at gate p with full budget.
2. Eligible candidates (converged) enter binary search for threshold proxy.
3. Refinement candidates ≤ 12, selected by best threshold proxy.
4. Validation on at least 3 independent seeds → conservative threshold =
   min(per-seed threshold proxy).
5. Winner = max conservative threshold among refined candidates; ties broken
   by canonical tuple.

Only eligible candidates that pass the entropy gate enter the binary search.

## 5. Budget Freeze Process

### 5.1 Microbenchmark (engineering-only, non-scientific)

Before any formal result, one microbenchmark run:
- Non-scientific seed (NOT from S1–S4 formal root range).
- Small population, few generations, q=1024 MC-DE at a single p.
- Purpose: estimate wall-clock per evaluation, confirm memory bounds.
- Output labelled `engineering_only_non_scientific`.
- Must not produce threshold, winner, or gate claims.

### 5.2 pre_run_plan.json

Frozen after microbenchmark and before any formal execution. Must contain:

```json
{
  "de_variant": "DE/rand/1/bin",
  "pop_size": <int>,
  "max_gen": <int>,
  "F": <float>,
  "CR": <float>,
  "K": 8,
  "degree_range": [2, 40],
  "min_weight": 0.01,
  "screen_n_samples": <int>,
  "screen_max_iter": <int>,
  "refinement_n_samples": <int>,
  "refinement_max_iter": <int>,
  "threshold_p_tol": <float>,
  "search_seeds": {"S1": <int>, "S2": <int>, "S3": <int>, "S4": <int>},
  "validation_seeds": [<int>, ..., <int>],
  "max_total_evaluations": <int>,
  "peak_rss_cap_b": 3221225472,
  "workers": 1,
  "objective": "hierarchical_6tier_lexicographic",
  "hard_stop_rules": [...],
  "output_paths": {...}
}
```

Hard caps: screen evaluations ≤ 600 per search; refinement candidates ≤ 12;
peak RSS ≤ 3 GiB; workers = 1. After formal results arrive, budget must NOT
change. If predicted execute > 24 h, return budget blocker before plan review.

## 6. V10 State Machine

```
V10-00 (freeze) → V10-0 (q=4 reference gate)
   ├─ PASS → V10-10 (DE kernel engineering)
   │          → V10-20 (V10A — 4 searches + gate)
   │             ├─ S1/S3 FAIL → STOP (failed_ensemble)
   │             ├─ S1/S3 PASS, S2/S4 FAIL → robust_only
   │             └─ ALL PASS → target_ready
   │                → V10-30 (PEG codebook)
   │                   → V10-40 (FFT-QSPA decoder)
   │                      → V10-50 (4+4 canary)
   │                         ├─ FAIL → STOP (failed_canary)
   │                         └─ PASS → V10-60 (16+16 development)
   │                                    → V10-70 (close-out)
   └─ FAIL → STOP (failed_reference)
```

## 7. V10-0 Q=4 Reference Recovery Gate

### Contract

Use the V8-60 Müller q=4 R=0.75 specification:
- Published lambda edge-weights: degrees {2,4,7,10,19,26,28}.
- DET published: 0.069.
- V10-0 checks: can the DE optimizer find this ensemble WITHOUT injecting
  the published lambda?

### Gate Rules

- Optimization seeds ≠ V8 seed (2026080418) and ≠ all V9 seeds.
- Validation seeds independent from optimization seeds.
- Gate: |candidate threshold − 0.069| ≤ 0.012 (same V8-60 tolerance).
- Reconstructed rate error ≤ 1e-12.
- At least 2 independent validation seeds must pass.
- Replay: same plan, same winner, same scientific payload.

### Failure Protocol

Freeze evidence, STOP, do not enter GF(1024). No tuning, no rerun.

## 8. V10A GF(1024) Ensemble Search

### Four Independent Searches

| ID | p | f | Tier | Gate | R ≈ | Deleted path m/n |
|----|---|---|------|------|-----|-----------------|
| S1 | .20 | 1.15 | robust | .22 | — | computed |
| S2 | .20 | 1.08 | target | .215 | — | computed |
| S3 | .30 | 1.15 | robust | .32 | — | computed |
| S4 | .30 | 1.08 | target | .32 | — | computed |

All `m` computed from `m(f,p,n) = ceil(f·H_q(p)·1024)`, `R = 1 − m/1024`.

### Conservative Threshold

For each search, run the (up to 12) refinement candidates on at least 3
independent validation seeds. The **conservative threshold** is the minimum
among per-seed threshold proxies. Search winner = candidate with max
conservative threshold.

### Gate Decision

```text
p_conservative_20 = min(validation thresholds at p=.20)
p_conservative_30 = min(validation thresholds at p=.30)

if S1 < .22 OR S3 < .32:
    ALL stop; ordinary_irregular_GF1024 = failed_v10a
    NO finite codebook, NO PEG, NO decoder, NO canary
    Successor: new V11 NB-SC-LDPC change (fresh everything)

elif S2 < .215 OR S4 < .32:
    robust_only
    Finite-length lane uses f=1.15 only
    Label all artifacts efficiency_target_not_met
    Forbid target_efficiency claims

else:
    target_ready
    Finite-length lane uses f=1.08
    f=1.15 backup frozen (not run)
```

### Search Outputs

Per-search: eligibility evidence (all candidates, entropy at gate p),
threshold proxy per refinement candidate, per-validation-seed threshold,
conservative threshold, winner identity, timing/RSS.

Do NOT select a "closest to gate" candidate from a failed search.

## 9. V10B Finite-Length PEG Construction (n=4096)

### 9.1 Node-View Conversion

From selected edge-view λ: compute node-view degree counts:
```text
L_d = (λ_d / d) / Σ_j (λ_j / j)    (node fraction at degree d)
count_d = round(L_d · n)            (integer variable nodes at degree d)
```
Adjust counts to sum to exactly `n` while preserving weight ordering.

### 9.2 Check Degrees

From concentrated ρ: compute check degree counts mechanically:
```text
count_j = round(ρ_j · m)            (integer check nodes at degree j)
```
Adjust to sum to `m`.

### 9.3 Socket Consistency

```text
Σ_d (count_d · d) = Σ_j (count_j · j) = total_edges
```
Assert equality; mismatch → blocker.

### 9.4 Deterministic Irregular PEG

Algorithm:
1. For each variable node `v = 0..n−1` in order, place `d_v` sockets.
2. For each socket, select the check node `c` among available candidates
   that maximizes **local girth** (length of shortest cycle via current
   partial graph).
3. Tie-break level 1: maximize **ACE score** (approximate cycle EMD/ACE).
4. Tie-break level 2: **deterministic seeded RNG tie-break**: a local
   `numpy.random.default_rng` seeded with `common.v10_seed(f"peg_tie:{seed}:v:{v}:s:{socket}")`,
   then the tied candidate group is randomized via `rng.permutation`,
   and the first element after permutation is selected. This is
   deterministic for a fixed seed, avoids SHA-256 dependency, and
   consumes a negligible number of RNG draws per socket.
   Upgrade path: if per-socket RNG overhead becomes measurable for
   large n, switch to a precomputed tie-break order via one global
   RNG draw per variable node.
5. If no eligible check node exists, record failure, increment trial counter.
6. Frozen trial cap `max_peg_trials` → exceed → frozen failure, STOP.

### 9.5 Edge Labels

After PEG completes: for each edge, sample uniformly from GF(1024)\{0}
using seeded RNG. Verify zero parallel edges, no zero labels.

### 9.6 Structural Verification

- No parallel edges.
- Degree sequences exact: checks verify actual row/column counts.
- `rank_GF1024(H) == m` (Gaussian elimination over GF(1024)).
- Syndrome round-trip test: random x, compute s=Hx, check agreement.
- Manifest: construction parameters only (n, m, seed, edge_label_seed,
  max_trials, trials_used, status, rank, parallel_edges, total_sockets,
  var_counts, check_counts, triples_count). No self-hash or source-hash
  fields; integrity is verified by parameter-level assertion and by git
  baseline (`git status --porcelain` + `git diff --name-only` against
  the frozen source-file manifest).

PEG trial cap exhausted without success → frozen failure, STOP.

## 10. V10B Decoder: Error-Domain FFT-QSPA

### 10.1 Syndrome Formulation

Error-domain: decoder receives `y`, `s_e = s_x + Hy`, `H`, frozen `p`.

Priors:
```text
P(e=0) = 1 − p
P(e=a) = p / 1023    ∀ a ∈ GF(1024)\{0}
```

### 10.2 Log-Domain Message Schedule

**Flooding schedule** (Müller reference semantics; layered deferred to future
performance optimization; V10 scientific lane must not select between flooding
and layered by result).

Per iteration:
1. **Variable → Check messages**: product of prior, re-scaled by edge
   coefficient, plus incoming check messages (excluding target check).
2. **Coefficient permutation**: message element `s` at edge coefficient `c`
   maps to position `c ⊗ s` (field multiplication lookup) before FWHT.
3. **Check → Variable messages**: FWHT convolution of coefficient-permuted
   messages, syndrome-shift, inverse FWHT (`÷ q`).
4. **Syndrome shift**: outgoing message `[s_c XOR c ⊗ s]` from the
   syndrome-offset convolution.
5. **Normalization**: subtract log-sum-exp (stable), probability floor
   `1e-15` in log-domain.
6. **Belief update**: product of prior + all check messages → decide
   `e_hat` at max probability.
7. **Syndrome check**: `H·e_hat == s_e` → early stop (success).
8. **Convergence check**: `e_hat` stable for `streak` consecutive iterations.

### 10.3 FWHT Convention

Use V9's accepted XOR-order non-normalized WHT with `/q` inverse transform,
consistent with the GF(1024) additive group structure. Do not re-derive or
change the GF(1024) field tables or WHT convention.

### 10.4 Resource Bounds

- `max_iter` frozen (one value per decoder instance).
- Allocation: pre-allocate all message and workspace arrays; do not grow.
- RSS guard: monitor process-tree RSS, abort if > 3 GiB.
- NaN/Inf: fail-closed, return `decode_failed`, no recovery attempt.
- Exact iteration transcript: per-iteration entropy, syndrome check result,
  e_hat stability.

### 10.5 Oracle Validation

Using V8's `nonbinary_v8_reference` (test-only import):
- q=4, q=8: exhaustive comparison with brute-force MAP/convolution oracle.
- Bounded GF(1024): small acyclic graphs with nonzero syndrome and non-unit
  edge coefficients.
- Verification of error-domain reconstruction `x_hat = y + e_hat`.

Reference-only: may read Lcrypto/gfq_ldpc source for algorithm reference but
the production implementation must be this project's own independent code.

### 10.6 Forbidden

- EMS, ADMM, list decoding, post-processing.
- Alice-truth fallback or callback.
- Layered schedule (V10 science lane flooding only).
- Adaptive iteration count.
- Implicit syndrome injection (must verify each iteration).

## 11. V10B Canary

### Plan

After engineering T0–T3 and independent ACCEPT: prepare one canary plan.
- n = 4096.
- 4 frames at p = .20, 4 frames at p = .30.
- Fresh roots (no overlap with canary/development/V8/V9 seeds).
- Chosen tier (robust_only or target_ready, frozen).
- max_iter, RSS cap, runtime cap pre-registered.

### Gate

Both strata ≥ 3/4 verified success. Each frame: decode success, syndrome
identity, 64-bit tag match, no Alice truth access, no forbidden state,
`L_recon = 10·m`, `L_total = 10·m + 64`. Any stratum < 3/4 → `failed_canary`,
STOP, no lambda/PEG seed/iteration/damping tuning.

## 12. V10C Development

Only after canary gate passes. Fresh plan:
- 16 frames at p = .20, 16 frames at p = .30.
- Zero overlap with canary, V8, V9 all seeds/roots.

Gate: both strata ≥ 15/16 verified. Readiness reached → STOP. No
confirmation, qualification, real data, N4, promotion, comparison. V10
ends at development readiness.

## 13. Leakage Formulas

```text
L_recon = 10 · m                (GF(1024) syndrome bits)
L_total = 10 · m + 64           (syndrome + verification tag)
```

These are exact hard caps. The 64-bit tag is a separate independent
Toeplitz verification tag, not embedded in the syndrome.

## 14. Testing and Evidence Tiers

- **T0**: compile/import, GF(1024) field identities, lambda exponent-degree
  mapping, rate/rho exactness, DE deterministic mutation, small oracle.
- **T1**: optimizer unit, objective/tie-break, resume/no-overwrite, PEG
  structure/rank, FFT-QSPA syndrome/edge-label, NaN/Inf/memory bounds,
  no-Alice-truth guards.
- **T2**: complete fake lifecycle (plan → review → fake execute → strict
  replay), all tamper layers, production runner never entered. Replay
  consistency verified by direct byte comparison (file-content equality,
  no intermediate SHA-256 layer). Tamper coverage uses direct byte
  comparison for raw-byte drift, field-level JSON recomputation for
  semantic tamper (gate reconstruction, leakage accounting rederivation,
  winner reconstruction), and plan-binding field validation.
- **T3**: frozen V8/V9 regression verified by git baseline
  (`git status --porcelain` + `git diff --name-only` checking that frozen
  directories and allowed file manifest are unchanged). No unauthorized
  output present.

Tamper coverage: raw byte drift (direct comparison), semantic JSON tamper
(gate reconstruction disagreement, leakage accounting recomputation failure,
winner reconstruction mismatch), plan-binding field validation rejection,
seed separation verification, fake promotion detection via gate
reconstruction. No SHA-256 manifest, self-hash, or source-hash evidence
fields.

## 15. Module Division (Additive)

V10 modules under `comparison_bench/src/comparison_bench/formal_ir/`:

| Module | Purpose | Imports |
|--------|---------|---------|
| `nonbinary_v10_common.py` | Sizing, rho, rate, constants, seed derivation | stdlib, numpy, `nonbinary_field.GF2mField` |
| `nonbinary_v10_de.py` | DE optimizer, objective, gate screen, own full-vector MC-DE evaluator | stdlib, numpy, numba (njit hot kernels), `nonbinary_v10_common`, `nonbinary_field.GF2mField` |
| `nonbinary_v10_peg.py` | Irregular PEG + edge labels | stdlib, numpy, `nonbinary_v10_common`, `nonbinary_field.GF2mField` |
| `nonbinary_v10_fftqspa.py` | FFT-QSPA decoder | stdlib, numpy, `nonbinary_field.GF2mField`, `nonbinary_v8_reference` (test-only) |

**Import discipline**:
- V8 modules (`nonbinary_v8_mcde`, `nonbinary_v8_reference`, `nonbinary_v8_error_domain`): test-only imports; production code must not import them.
- V9 modules: NOT imported except where design explicitly allows (none by default).
- numba (already a root `requirements.txt` dependency, NOT a new install): allowed for
  `nonbinary_v10_de.py` hot-loop kernels only (WHT butterfly, check convolution,
  variable/belief updates, normalization), per amendment
  `evidence/v10_budget_amendment.json` (2026-08-05, main-thread approved after the
  V10-S06 budget blocker). njit kernels MUST be bit-identical to the numpy
  reference semantics (tests assert allclose <= 1e-12 and a known-answer
  butterfly regression case). No SciPy, no `ldpc`, no external decoder library.

Tests under `comparison_bench/tests/`:
- `test_nonbinary_v10_de.py`
- `test_nonbinary_v10_peg.py`
- `test_nonbinary_v10_fftqspa.py`
- `test_nonbinary_v10_common.py`

## 16. Literature Crosswalk

See `evidence/v10_literature_crosswalk.md` for detailed mapping of each
literature source to V10 implementation. Key references:
- Müller et al. 2024 (arXiv:2307.02225) — ensemble representation, QSC,
  MC-DE, DE optimization, concentrated rho, PEG, FFT-SPA.
- Storn & Price 1997 (DOI 10.1023/A:1008202821328) — DE/rand/1/bin variant.
- Declercq & Fossorier 2007 (DOI 10.1109/TCOMM.2007.894088) — FFT-QSPA,
  GF(q) edge-label permutations.
- Bennatan & Burshtein (arXiv:cs/0511040) — random nonzero edge labels.
- Hu et al. (DOI 10.1109/TIT.2004.839541) — PEG construction.
- Wei (arXiv:1403.3583) & Huang (arXiv:1408.2621) — V11 successors only
  (spatially-coupled NB-LDPC; BEC/BIAWGNC not GF(1024) QSC evidence).

## 17. Resource and Process Controls

- workers = 1 for all scientific execution.
- Peak process-tree RSS ≤ 3 GiB (frozen cap).
- No dependency installation, clone, vendor, or external code copy.
- No Glob or recursive enumeration.
- At most two concurrent agents.
- No Git stage, commit, push, reset, or cleanup of unrelated changes.
- Record and own every long-running process ID.
- Test roots: `workspace/<v10-stage>/<uuid>`, `pytest -p no:cacheprovider`.

## 18. v10_seed Retention (Deterministic RNG Primitive)

`nonbinary_v10_common.v10_seed(tag)` is **retained** as a deterministic RNG
stream derivation primitive. It is not classified as a defensive hash mechanism
under AGENTS.md §5.7 because:

1. Its sole purpose is to derive reproducible RNG streams from tagged string
   keys, serving the same role as `np.random.default_rng(seed)` with a
   deterministic mapping from tag → integer.
2. Executed and verified scientific results (V10-0 q=4 reference recovery,
   V10A ensemble search) depend on its exact output for population
   initialization (`nonbinary_v10_de.py` L594) and mutation/crossover RNG
   streams (L821). Changing `v10_seed` would break byte-reproducibility of
   completed evidence.
3. It uses `hashlib.sha256` for its internal digest, but only to obtain a
   32-bit integer from a variable-length string tag — it is not used as a
   file integrity check, manifest field, evidence hash, or tamper-detection
   mechanism.

If `hashlib` availability becomes a concern, `v10_seed` can be reimplemented
via `int.from_bytes(zlib.crc32(tag.encode()).to_bytes(4, 'little'), 'little')`
without changing scientific semantics, but this is deferred to a separate
change after V10 close-out.
