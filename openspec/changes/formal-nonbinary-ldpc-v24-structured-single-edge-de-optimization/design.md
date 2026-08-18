# Design: formal-nonbinary-ldpc-v24-structured-single-edge-de-optimization

## 0. Status and authorization boundary

FROZEN_PENDING_USER_AUTHORIZATION. P06 independent freeze review returned
ACCEPT on 2026-08-17. Before implementation or scientific execution, the user
must explicitly authorize the unchanged frozen packet at P07.

The lifecycle boundaries are distinct:

1. **Engineering pass**: implementation and fake/tiny tests pass. This does
   not authorize or imply a DE result.
2. **DE pass**: the frozen M0/M1/M2 gate passes. This is an asymptotic ensemble
   result only.
3. **Finite success**: not measurable in V24; it requires a later finite-code
   change and Bob-only evidence.
4. **Qualification/promotion**: not measurable or authorized in V24.

No lifecycle state may be silently promoted to the next one.

## 1. Frozen predecessor interpretation

- V21: the tested short-block Bob-only variants hit the stop gate.
- V22: the V22b kernel removed the old degree-cap execution blocker and the
  evaluated target-rate candidates remained non-convergent.
- V23: its base-matrix path aggregates topology to one `lambda/rho` pair and
  calls V22b. It is therefore a single-edge diagnostic, not true
  topology-preserving protograph DE and not MET DE.
- V24 tests only whether a bounded optimization of the remaining single-edge
  space can find a robust DE-convergent candidate. A V24 FAIL does not prove a
  universal coding-theory impossibility.

## 2. M0 — mechanism, channel, and accounting freeze

### 2.1 Accepted V8 mechanism evidence — read-only

Before any q=1024 search, M0 must read and validate the already accepted V8
corrected trace at the exact path:

`openspec/changes/formal-nonbinary-ldpc-v8-reference-reproduction/evidence/v8_reproduction_trace_corrected.json`

M0 must not call the V8 runner, threshold search, or MC-DE. The V8 corrective
run was exactly-once evidence and is neither rerun nor replaced by V24.

The following accepted trace fields are frozen:

- schema `v8_reproduction_trace_corrected_v1`, q=4, rate=0.75;
- published lambda exponents
  `{1:0.107, 3:0.245, 6:0.192, 9:0.034, 18:0.207, 25:0.161,
  27:0.049}` and effective degree distribution
  `{2:0.107, 4:0.245, 7:0.192, 10:0.034, 19:0.207, 26:0.161,
  28:0.049}`;
- corrected harmonic-exact concentrated rho
  `{24:0.662342394447661, 25:0.33765760555233904}`;
- `dc_mean=24.32858932876873`;
- `integral_lambda=0.1644156159629844`,
  `integral_rho=0.0411039039907461`, and reconstructed rate 0.75;
- `n_samples=100000`, `max_iter=150`, seed `2026080418`, QSC p bounds
  `[0.01,0.12]`, binary-search `p_tol=0.0025`;
- strict convergence rule: base-q entropy **`<0.01` for 20 consecutive
  iterations** (`streak=20`);
- published DET 0.069, frozen acceptance tolerance 0.012, accepted
  `threshold_proxy=0.06242187500000001`, delta
  `0.006578124999999997`, verdict PASS.
- frozen tolerance arithmetic:
  `0.0005 + 0.00125 + 0.005 + 0.005 = 0.01175 <= 0.012`.

M0 validates these fields read-only together with the rate identity. Missing
or inconsistent accepted evidence yields `mechanism_unverified`; M1/M2 are
forbidden. V24 does not schedule a new QSC threshold regression. The optional
predecessor T3 control is read-only validation of the existing V22b artifact
and cannot replace or alter accepted V8 evidence.

### 2.2 Frozen q=1024 channel

The only scientific channel input is the existing read-only artifact:

`openspec/changes/formal-nonbinary-ldpc-v17-multibit-structured-de-gate/evidence/v17_multibit_channel_model.json`

Required identity:

- schema: `nbldpc_v17_multibit_channel_model_v1`;
- `q = 1024`, `bit_planes = 10`, mapping `gray`;
- joint form: `product_of_per_plane_marginals`;
- entropy used for accounting:
  `H_V17 = 0.5499550439219351 bits/symbol`;
- the ten persisted MSB-first error probabilities are consumed unchanged.

V24 must copy the exact consumed values into its run manifest. It may not
refit, smooth, reinterpret, or replace the channel after seeing results.

### 2.3 Frozen rate and leakage accounting

For edge-perspective normalized distributions:

`R = 1 - (sum_d rho_d / d) / (sum_d lambda_d / d)`.

For this DE-only change, no finite public verification, blind increment, or
retry payload exists. The frozen accounting proxy is therefore:

`leakage_bits_per_symbol = (1 - R) * log2(1024) = 10 * (1 - R)`

`f_total = leakage_bits_per_symbol / H_V17`.

A scientifically valid candidate must satisfy all of:

- finite, non-negative, normalized `lambda` and `rho` (sum tolerance `1e-12`);
- integer variable/check degrees in `[2, 512]`;
- design `R >= 0.9375`;
- `f_total <= 1.3`.

The V24 search is intentionally narrower: `R <= 0.94140625`, variable degree
`<= 64`, check degree `<= 512`, and no more than eight non-zero degrees on
either side. Candidates outside the search band are recorded as invalid and
cannot consume a DE-evaluation slot.

If a later finite-code change adds public verification, shortening,
puncturing, retries, or blind increments, it must recompute `f_total`; the
V24 proxy cannot be carried forward as finite-code efficiency.

## 3. M1 — bounded development optimization

### 3.1 Search representation

- `lambda` and `rho` are single-edge distributions only; no edge-type or
  protograph-position state is retained.
- Allowed variable degrees: integers `2..64`.
- Allowed check degrees: integers `2..512`.
- Each side has between one and eight non-zero weights.
- Weights are quantized to multiples of `1/64` and sum exactly to one after
  integer-count normalization.
- Duplicate `(lambda, rho)` profiles are evaluated once and logged as
  duplicates thereafter.
- V22/V23 profiles are excluded from M1 generation, ranking, and selection;
  any predecessor control is a separate T3 engineering regression only.

The implementation may use only NumPy and existing repository modules. Freeze
the arrays and exact RNG call order below; no permutation API, alternative
sampling interface, helper reordering, or extra RNG consumption is allowed:

```python
lambda_degree_array = np.arange(2, 65, dtype=np.int64)
rho_degree_array = np.arange(2, 513, dtype=np.int64)
rng = np.random.default_rng(np.random.SeedSequence([24000, k]))

# lambda first
frozen_degree_array = lambda_degree_array
s = int(rng.integers(1, 9))
degrees = np.sort(rng.choice(frozen_degree_array, size=s, replace=False))
probabilities = np.full(s, 1.0 / s, dtype=np.float64)
counts = rng.multinomial(64 - s, probabilities) + 1
degrees_lambda, counts_lambda = degrees, counts

# rho second, using the same rng
frozen_degree_array = rho_degree_array
s = int(rng.integers(1, 9))
degrees = np.sort(rng.choice(frozen_degree_array, size=s, replace=False))
probabilities = np.full(s, 1.0 / s, dtype=np.float64)
counts = rng.multinomial(64 - s, probabilities) + 1
degrees_rho, counts_rho = degrees, counts
```

For every attempt index `k` in `0..8191`:

1. Execute exactly the calls above, in that order.
2. Counts are positive, sum to 64 per side, and define weights `count/64`.
3. Canonical key is
   `L[degree:count,...]|R[degree:count,...]`, with degrees ascending on each
   side. `candidate_id` is the first attempt index `k` that produced that key.

Every attempt has an independent `SeedSequence([24000,k])`; rejection or a
duplicate at one attempt cannot change any later proposal. Invalid and
duplicate attempts are logged. M1 accepts only the first 512 unique valid
keys, or all unique valid keys found when 8192 attempts are exhausted.

### 3.2 Frozen budget and seeds

The complete development budget is:

- at most **512 unique new valid candidates**;
- proposal-generation seed: `24000`;
- screening: all valid candidates, `n_samples=200`, `max_iter=50`, seeds
  `[24001, 24002]`;
- stage-generic deterministic ranking by
  `(converged_count desc, worst_final_entropy asc,
  mean_final_entropy asc, candidate_id asc)`;
- an error or non-finite entropy counts as non-converged and contributes
  `+inf` to worst/mean entropy;
- `N_refine=min(8,N_valid)` top candidates advance to refinement;
- refinement: `n_samples=1000`, `max_iter=150`, seeds
  `[24003, 24004, 24005]`;
- `N_finalist=min(4,N_refined)` top refinement candidates advance to holdout,
  ranked by the same stage-generic tuple over refinement seeds.

The optimizer stops when 512 unique valid proposals have been evaluated or a
frozen proposal-attempt ceiling of 8192 is reached. Reaching the attempt
ceiling with at least one valid evaluated candidate proceeds with the
available candidates; `N_valid=0` yields `mechanism_unverified`
because the generator contract is broken. Neither ceiling may be increased.

`N_valid` is the number of profile-valid, unique candidates admitted among the
first 512. Profile validity is fixed before DE from lambda/rho normalization,
support and degree bounds, rate, and `f_total`; it never depends on a DE result.
Every scheduled DE error or non-finite entropy occurs after admission, consumes
that candidate/seed's valid-evaluation slot, remains in evidence, and ranks as
non-converged with `+inf`. It does not decrement or redefine `N_valid`.

### 3.3 Development convergence and no-tuning rule

A run is converged only when its **final** normalized base-q message entropy is
`<= 0.01` at or before the frozen iteration limit. Early stopping may only
occur after this numerical condition is met. Development results select
finalists; they do not by themselves satisfy V24 PASS.

After M1 begins, the following are frozen: channel values, formulae,
threshold, degree/search bounds, proposal and evaluation budgets, seeds,
ranking, number of finalists, and V22b update semantics. Any change voids the
run and requires an amendment plus new user authorization; it is not a rerun
inside V24.

## 4. M2 — independent holdout validation

Before any holdout computation, the identities and full distributions of all
`N_finalist=min(4,N_refined)` finalists must be persisted. Holdout seeds must
never enter proposal generation, screening, refinement, ranking, or debugging.

Frozen holdout settings:

- seeds `[24101, 24102, 24103, 24104, 24105]`;
- `n_samples=2000` per seed;
- `max_iter=200`;
- normalized base-q final entropy threshold `<= 0.01`;
- same frozen V17 channel, rate/accounting formulae, V22b semantics, and
  degree cap.

A finalist passes holdout only if it is valid and converges on **all five**
holdout seeds. V24 is `pass` iff at least one pre-persisted finalist passes.
One failed seed is a candidate failure; majority vote, average entropy,
confidence intervals, and “near pass” are not substitutes.

Holdout results may not select a replacement finalist, alter a profile, add a
seed, or trigger a rerun. If no finalist passes all seeds after the complete
frozen budget, V24 is `fail` and all results are retained.

## 5. Evidence, verification, and resources

### 5.1 Additive artifacts

Every run writes to a fresh additive directory under:

`comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v24_<run_id>/`

No existing output is overwritten. The evidence package contains at least:

- frozen run manifest and exact consumed channel values;
- M0 accepted-trace read-only validation result;
- proposal ledger, including invalid/duplicate reasons;
- one record for every screening and refinement evaluation;
- pre-holdout finalist declaration;
- one record for every holdout evaluation;
- machine-readable gate decision;
- read-only verifier report and command transcript.

No checksum/integrity framework is added. The independent verifier instead
recomputes normalization, rate, leakage, `f_total`, ranking, finalist
selection, seed separation, per-run convergence, and the final decision from
the persisted records.

### 5.2 Test and execution tiers

- T0: import/compile, tiny normalization/rate/accounting math, deterministic
  proposal reproduction, degree-cap rejection.
- T1: focused tests for invalid profiles, duplicate handling, ranking,
  seed-set disjointness, entropy gate, and no-overwrite behavior.
- T2: complete fake-run lifecycle through decision plus read-only semantic
  verification; the fake runner must be passed explicitly.
- T3: optional read-only predecessor control validation at
  `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v22_20260816/v22b_de_gate_q1024_r09375_dmax512_iter30_n200/de_gate.json`.
  It is excluded from M1 generation/ranking and runs no V8 or V22b DE call.

Tests use a fresh additive `workspace/nbldpc_v24_<uuid>/` root and never invoke
the production runner implicitly.

### 5.3 Resource stop

The 24-hour ceiling is defined only as the accumulated `time.perf_counter`
duration of **completed DE calls** within one user-authorized M0–M2 scientific
invocation. Each completed call is appended to the evidence record immediately
with its elapsed duration, and the accumulated duration is recomputed.

After each call finishes, the runner must use this priority order:

1. append the completed call record and elapsed duration;
2. test whether **all frozen required evaluations are complete**;
3. if complete, compute the normal PASS/FAIL decision even when accumulated
   completed-call time is at least 24 hours;
4. only if required evaluations remain and accumulated time is at least 24
   hours, set `resource_blocked` and do not start the next call;
5. otherwise start the next frozen call.

A call already in progress may finish before this ordered check. M0's
read-only checks add no DE-call time. There is no RSS hard gate. Resource stop
retains all partial evidence and does not authorize a smaller budget, fewer
seeds, or rerun; a new invocation requires a reviewed amendment and explicit
user authorization.

## 6. M3 — closeout and successor rule

- `pass`: record only `ready_to_propose_finite_code_change`. Finite
  construction still requires a new OpenSpec change and user authorization.
- `fail`: record `single_edge_bounded_optimization_failed`. Do not claim MET,
  protograph topology, or all q=1024 codes failed.
- `mechanism_unverified` or `resource_blocked`: record the concrete blocker;
  do not reinterpret it as scientific FAIL.

After FAIL, true MET/multi-edge DE may be proposed only as a separate change
with edge-type state preserved and only after a new user decision. Changing
q, channel decomposition, or `f_total` target is likewise a separate route.
