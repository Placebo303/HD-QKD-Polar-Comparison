# Design: V11 Nonbinary Spatially Coupled DE Gate

## 1. Scientific question

Does spatial coupling, rather than extra syndrome disclosure or a changed
uncoupled ensemble, raise the conservative GF(1024) QSC thresholds of the V10
robust S1 and S3 winners to at least .22 and .32?

V11 answers only this ensemble-level question. It does not claim a realizable
finite-length code or decoder.

## 2. Literature-backed reference ladder

### R1 — direct QSC machinery check

Reproduce Ben Yacoub et al. (AEIT 2019), rate-1/2 `(3,6)` ensembles, window
`W=30`:

| q | uncoupled published threshold | coupled published threshold |
|---:|---:|---:|
| 4 | .0890 | .0942 |
| 16 | .1075 | .1288 |

Each value must be reproduced within absolute tolerance .002. The threshold
search tolerance must be at most .001. This is an SMP-DE reference only.

### R2 — structural and oracle checks

- Coupling width zero / a single spatial position must collapse to the V10
  uncoupled update.
- q=4 and q=8 tiny cases must agree with the independent V8 direct oracle
  within the frozen Monte Carlo tolerance.
- Probability vectors must remain finite, nonnegative, and normalized; the
  all-zero and noiseless limits must behave as expected.
- The terminated-rate formula and reconstructed degree-distribution rate must
  agree within `1e-12`.

Failure of R1 or R2 yields `failed_reference`; no GF(1024) scientific plan is
prepared or executed.

## 3. Coupling and rate contract

Let the uncoupled V10 effective rate for stratum `s` be

`R_eff,s = 1 - f_s H_q(p_s)`, with `q=1024` and `f_s=1.15`.

For a terminated chain of length `L` and syndrome-former memory/coupling width
`w`, use the standard rate relation

`R_L = 1 - ((L+w)/L) (1-R_base)`.

Choose the interior/base rate before execution as

`R_base = 1 - (L/(L+w)) (1-R_eff,s)`.

The check distribution is then reconstructed harmonically at `R_base`. The
resulting terminated chain must recover `R_eff,s` within `1e-12`. Therefore
the coupled and uncoupled controls disclose the same total number of q-ary
constraints asymptotically; any threshold gain cannot be attributed to
termination rate loss.

The variable-node edge distribution for each stratum is exactly the frozen
V10 S1 or S3 winner. V11 must not reoptimize it. Coupling uses uniform edge
spreading over positions `0..w`; changing the spreading rule is a new change.

## 4. Frozen geometries

The formal packet contains exactly three coupled geometries:

| ID | w | L | decoding window W | role |
|---|---:|---:|---:|---|
| G1 | 1 | 32 | 8 | low-latency primary |
| G2 | 2 | 32 | 16 | wider-coupling sensitivity |
| G3 | 2 | 32 | 32 | full-chain control |

`W` counts spatial column blocks. No geometry may be added, removed, or
changed after the formal plan is frozen. The uncoupled control uses the same
stratum ensemble, effective rate, threshold grid, population size, iteration
budget, convergence rule, and paired seed.

## 5. Execution ladder

### Stage E — engineering only

Implement SMP reference DE and the full-vector coupled MC-DE as separate
modules. SMP must not be reused as the GF(1024) scientific decoder. Complete
T0/T1 tests and an independent read-only review.

### Stage M — resource microbenchmark

Run a small q=1024 dry microbenchmark with synthetic, non-gating parameters.
Extrapolate the frozen formal plan's runtime and measure peak RSS. If predicted
wall time exceeds 24 hours or measured/projected peak RSS exceeds 3 GiB,
return `resource_blocked`. Do not shrink the formal matrix after seeing the
microbenchmark; a changed matrix requires an amended plan and new review.

### Stage P — prepare and review

Freeze one machine-readable plan containing geometries, strata, rate
reconstruction, seed list, thresholds, stopping rules, budgets, output paths,
and code revision. Review it read-only before execution.

### Stage X — one scientific execute and one replay

Use five fresh independent validation seeds per `(stratum, geometry)` and
paired control. Seeds must be disjoint from V8–V10. Execute the complete
matrix exactly once, then run one strict read-only replay in a fresh workspace.
Interrupted attempts are retained and handled by an explicit main-thread
decision; no result-dependent tuning is allowed.

## 6. Gate

A geometry passes only if all of the following hold in both S1 and S3:

- `conservative_threshold(S1) >= .22`;
- `conservative_threshold(S3) >= .32`;
- paired conservative gain over the uncoupled control is at least .002 in
  each stratum;
- all five seeds in each stratum are valid and converge under the frozen
  estimator; and
- effective-rate equality, resource limits, replay, structured-field
  validation, and semantic recomputation all pass.

If multiple geometries pass, choose the smallest `W`, then the smallest `w`.
No secondary performance score is used. If none passes, the state is
`failed_coupling`. A passing state is only `ready_for_finite_length`; it is not
promotion, qualification, or finite-code evidence.

## 7. Acceptance IDs

- **V11-A01** Literature extract identifies exact QSC reference values and
  distinguishes SMP from full-vector decoding.
- **V11-A02** R1 q=4 and q=16 uncoupled/coupled thresholds reproduce within
  .002.
- **V11-A03** Coupling-collapse tests match V10 uncoupled semantics.
- **V11-A04** q=4/q=8 full-vector updates agree with the V8 oracle.
- **V11-A05** Terminated effective rate matches the control within `1e-12`.
- **V11-A06** V10 S1/S3 lambda distributions are reused without optimization.
- **V11-A07** G1–G3 and no other geometry appear in the formal plan.
- **V11-A08** Fresh paired seeds and complete estimator settings are frozen.
- **V11-A09** T0/T1 tests and independent engineering review pass.
- **V11-A10** Resource microbenchmark clears 24 h and 3 GiB limits.
- **V11-A11** Prepare/review/execute/replay lifecycle is observed.
- **V11-A12** Each scientific cell is executed exactly once with invalid and
  interrupted evidence retained.
- **V11-A13** Absolute and paired-gain gates are recomputed independently.
- **V11-A14** Frozen directories and official production output roots remain
  unchanged.
- **V11-A15** Final state is one of the four declared states, with no silent
  promotion of failures.
- **V11-A16** Finite-length work remains outside V11 and requires a new
  OpenSpec change.

## 8. Simpler alternative retained

The simplest valid successor is to stop after V10 and report that the current
uncoupled ensemble family misses the robust gates. V11 is justified only if
the user wants to test the specific spatial-coupling hypothesis; it is not
required to close V10 honestly.
