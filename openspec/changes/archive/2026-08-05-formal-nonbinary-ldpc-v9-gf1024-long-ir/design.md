# Design: V9 GF(1024) Ensemble-to-Long-Block Bridge

## 1. Scientific Contract

Alice holds x, Bob holds one correlated observation y, and Alice publishes a
syndrome s=Hx plus explicitly accounted protocol data. The decoder operates in
the error domain:

```text
d = H y + s = H(x+y) = H e
x_hat = y + e_hat
```

No Alice truth, synthesized independent observation, hidden fallback, or
unaccounted public information may enter decoding. Verification only decides
whether a candidate is accepted; it cannot repair one.

## 2. V9A: Scalable GF(1024) MC-DE

### 2.1 Kernel

- Messages remain full length-1024 probability or normalized log-probability
  vectors; a scalar reliability surrogate is forbidden.
- Check convolution uses a GF(2^10)-correct WHT/FFT implementation with edge
  coefficient permutations.
- Variable updates sample the exact edge-view degree and include a fresh QSC
  channel term.
- Numerical operations normalize and fail closed on NaN, infinity, negative
  mass, zero mass, or invalid distributions.
- Deterministic bounded q=4/q=8/q=32 cases and bounded sparse/dense q=1024
  cases are checked against the V8 direct oracle. V8 is an oracle, not a
  production dependency or a source to modify.

### 2.2 Optimization

Optimize separate edge-view lambda distributions for p=.20 and p=.30, for
both f=1.15 robust and f=1.08 target rates. Rho uses the V8-60 harmonic-exact
construction or a documented distribution satisfying the same equation.

The search space, seeds, population/iteration budgets, degree bounds,
objective, tie-break, convergence rule, and maximum evaluations must be frozen
before results are generated. At least three independent fixed validation
seeds are required after optimization; optimization and validation seeds must
be disjoint. Report per-seed threshold and the conservative minimum.

V9A uses one lifecycle package covering all four candidate searches and all
validation seeds: plan-only, independent read-only review, exactly one
deterministic execute, and exactly one strict replay. The plan freezes budgets,
seeds, targets, convergence, and gate reconstruction. No result may alter that
plan, and a failed package cannot be tuned or rerun.

Advance gate:

- p=.20 robust conservative threshold >= .22;
- p=.30 robust conservative threshold >= .32.
- p=.20 target conservative threshold >= .215;
- p=.30 target conservative threshold >= .32.

The p=.20 target gate .215 remains below the approximate f=1.08 capacity
threshold .21827, preserving a feasible target rather than an impossible gate.

If either robust condition fails, stop before any finite codebook. A target
ensemble failure does not block the robust route, but permanently labels the
downstream stage `efficiency_target_not_met` and forbids target claims.

## 3. V9B: n=4096 Finite-Length Bridge

### 3.1 Codebook

For each stratum and authorized efficiency tier, compute m using the proposal
formula at n=4096. Build a deterministic irregular Tanner graph from the V9A
ensemble using PEG/ACE or an explicitly justified equivalent. Require no
parallel edge, recorded rank, cycle/ACE diagnostics, deterministic tie-breaks,
and independently seeded nonzero GF(1024) edge coefficients.

The matrix must satisfy `rank(H)=m`. A rank failure triggers bounded
deterministic reconstruction before the canary plan or a blocker; it cannot be
accepted with an adjusted effective rate. Each n=4096 input is an ordered
superframe of exactly 4 mutually disjoint 1024-symbol constituents with bound
IDs, roots, seeds, hashes, order, and aggregate mapping. Constituents are not
reused by any other V9 stage.

### 3.2 Decoder

Use error-domain layered log-FFT-SPA, workers=1, a frozen iteration cap in
[100,150], complete-graph syndrome check per iteration, bounded damping only
if frozen before data, and fail-closed allocation/numerics. No fallback decoder
or post-hoc parameter search is allowed.

### 3.3 Canary

After T0-T3 and independent engineering acceptance, prepare a fresh 4+4
synthetic QSC canary at p=.20/.30. Review the plan read-only, execute once, and
strict-replay once.

Advance to V9C only when both strata have >=3/4 verified success, forbidden
states are zero, disclosure equals the actual syndrome plus tag/public
protocol data, median runtime <=2 hours per superframe, and peak process memory
<=3 GiB. Otherwise freeze and stop without tuning or rerun.

## 4. V9C: Long Superframes

### 4.1 n=16384 bridge

Scale the accepted V9B construction without changing its scientific channel
contract. Complete structural/decoder tests and independent plan review, then
run a fresh 4+4 canary exactly once plus one strict replay. Advance only at
>=3/4 verified per stratum, zero forbidden states, median runtime <=8 hours per
superframe, peak memory <=3 GiB, and exact disclosure reconstruction.
Each n=16384 input binds exactly 16 ordered, mutually disjoint 1024-symbol
constituents with complete provenance and cross-stage no-reuse. Its matrix
must satisfy `rank(H)=m` before plan preparation.

### 4.2 n=32768 paper-scale candidate

Each superframe comprises exactly 32 independently identified 1024-symbol
synthetic constituent frames. The manifest records constituent IDs, order,
stratum, roots, seed IDs, hashes, and mapping to the aggregate vector. No
constituent is shared across superframes or earlier stages.
The GF(1024) matrix must satisfy `rank(H)=m` before plan preparation.

Use target f=1.08 only when the corresponding V9A target ensemble passed its
frozen DE target. Otherwise use robust f=1.15 and label all artifacts
`efficiency_target_not_met`.

V9C uses one fixed rate per stratum. The plan freezes
`m=ceil(f*H_q(p)*n)`. Because a GF(1024) syndrome symbol contains 10 bits,
`L_recon=10*m`; the fixed correctness tag is separately 64 bits and
`L_total=10*m+64`. Those exact values are hard caps. V9 has no puncturing,
shortening, interactive stages, information-bearing index/control payload, or
other reconciliation disclosure. Target f=1.08 is used only when its stratum's
target gate passes; otherwise robust f=1.15 is fixed with
`efficiency_target_not_met`. Blind rate adaptation is deferred to V10.

After engineering acceptance, run a fresh 4+4 canary once and strict-replay
once. Gate: >=3/4 verified per stratum, zero forbidden states, peak memory
<=3 GiB, and exact disclosure reconstruction. If PASS, prepare a new disjoint
16+16 development package, review it, execute once, and strict-replay once.
Every n=32768 canary superframe has a hard 24-hour timeout. Canary advance also
requires median runtime <=16 hours; a timeout is a frozen failed row.

Development-ready gate:

- >=15/16 verified success in each stratum;
- zero forbidden states;
- exact strict replay and source/plan/transcript hash binding;
- median runtime <=24 hours per superframe;
- peak memory <=3 GiB.

Stop after this decision. Do not materialize qualification or confirmation.

## 5. Lifecycle and Tamper Model

Every plan binds code/source hashes, git HEAD, graph/edge-label hashes,
parameters, identities, roots, seed IDs, disclosure rules, caps, and gates.
Verification reconstructs raw-byte, semantic-self-hash, manifest-link,
source-identity, transcript, public-payload, leakage, gate, provenance, and
constituent-superframe mappings. Tests use an explicit fake runner and cannot
reach a production decoder by default.

Plans and results use additive no-overwrite paths. Failed evidence remains
immutable. Test roots live under fresh `workspace/<v9-stage>/<uuid>` paths;
scientific packages use separately named fresh workspace roots. No V9 package
is an official `formal_ir_methods` comparison output.

## 6. Resource and Process Controls

- workers=1 for scientific execution;
- measured peak process-tree RSS <=3 GiB;
- no dependency installation, clone, vendor, or external code copy;
- no broad recursive/Glob searches;
- at most two concurrent agents;
- no Git stage, commit, push, reset, or cleanup of unrelated changes;
- record and own every long-running process ID/cell ID;
- report at least every 60 minutes during a long run when the interface allows;
- terminate only processes positively identified as belonging to V9.

## 7. Alternative Routes Deferred

Blind puncturing/shortening, GF(32)xGF(32), spatial coupling, and multiplicative
repetition remain future changes. Blind adaptation is specifically deferred to
V10. They are not fallback branches inside V9. Decoder-list/ADMM tuning is also
out of scope.
