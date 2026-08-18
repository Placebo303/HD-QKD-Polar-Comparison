# Spec Delta: formal-nonbinary-ldpc-v24-structured-single-edge-de-optimization

> This delta is gate-only. It may be merged only after formal closeout and a
> user archive decision. A failed scientific route does not authorize finite
> construction or a successor automatically.

## ADDED Requirements

### Requirement: V24 SHALL remain a single-edge DE-only change

V24 SHALL optimize only aggregate edge-perspective `lambda/rho` distributions
for q=1024 on the frozen V17 structured channel. It SHALL NOT preserve or claim
protograph topology/MET edge-type state and SHALL NOT construct a finite code.

#### Scenario: A finite or MET action is requested inside V24

- **WHEN** work would create a finite matrix/decoder/FER result or true MET
  state
- **THEN** that work SHALL stop
- **AND** a separate OpenSpec change and explicit user authorization SHALL be
  required

### Requirement: M0 SHALL freeze mechanism, channel, and accounting

Before optimization, V24 SHALL read and validate, without execution, the
accepted corrected V8 trace at
`openspec/changes/formal-nonbinary-ldpc-v8-reference-reproduction/evidence/v8_reproduction_trace_corrected.json`.
It SHALL verify q=4/R=0.75; published lambda exponents
`{1:0.107,3:0.245,6:0.192,9:0.034,18:0.207,25:0.161,27:0.049}` and degrees
`{2:0.107,4:0.245,7:0.192,10:0.034,19:0.207,26:0.161,28:0.049}`; corrected rho
`{24:.662342394447661,25:.33765760555233904}`; dc_mean
24.32858932876873; integral_lambda 0.1644156159629844; integral_rho
0.0411039039907461; reconstructed rate 0.75; n_samples 100000; max_iter 150;
seed 2026080418; QSC p bounds 0.01/0.12 and p_tol 0.0025; strict base-q
entropy `<0.01` for streak 20; published threshold 0.069; tolerance 0.012;
accepted proxy 0.06242187500000001, delta 0.006578124999999997, and PASS.
It SHALL verify tolerance arithmetic
`0.0005+0.00125+0.005+0.005=0.01175<=0.012`.
V24 SHALL NOT rerun or replace this exactly-once V8 evidence. V24 SHALL consume
the existing V17 model unchanged, with
`H_V17=0.5499550439219351 bits/symbol`, and SHALL compute
`R=1-(sum rho_d/d)/(sum lambda_d/d)` and
`f_total=10*(1-R)/H_V17`.

#### Scenario: Reference or frozen input check fails

- **WHEN** the reference, schema, channel values, normalization, or accounting
  reconstruction fails
- **THEN** the gate state SHALL be `mechanism_unverified`
- **AND** no development search or holdout SHALL execute

### Requirement: Every evaluated candidate SHALL meet the frozen validity gate

A valid candidate SHALL have finite, non-negative, normalized single-edge
distributions; degrees within the frozen caps; `R>=0.9375`; and
`f_total<=1.3`. The V24 search SHALL additionally restrict rate to
`R<=0.94140625`, variable degree to 64, check degree to 512, and each support
to between one and eight degrees. Profile validity SHALL NOT depend on DE
entropy, convergence, error, or other evaluation output.

#### Scenario: Candidate is invalid

- **WHEN** any validity or bounded-search condition fails
- **THEN** the candidate SHALL be retained in the proposal ledger with reason
- **AND** it SHALL NOT satisfy a DE gate or consume a valid-evaluation slot

### Requirement: Development optimization SHALL be bounded and pre-registered

For each attempt k in 0..8191, V24 SHALL construct exactly one
`rng=default_rng(SeedSequence([24000,k]))`. The frozen arrays SHALL be
`lambda_degree_array=np.arange(2,65,dtype=np.int64)` and
`rho_degree_array=np.arange(2,513,dtype=np.int64)`. With the same rng, V24
SHALL consume calls strictly lambda first and rho second. For each side it
SHALL call, in order, `s=int(rng.integers(1,9))`,
`degrees=np.sort(rng.choice(frozen_degree_array,size=s,replace=False))`,
`probabilities=np.full(s,1.0/s,dtype=np.float64)`, then
`counts=rng.multinomial(64-s,probabilities)+1`. It SHALL NOT substitute
permutation, another sampling API, another order, or an extra RNG call.
The canonical key SHALL be the ascending
`degree:count` strings for both sides; candidate_id SHALL be the first attempt
k producing that key. Rejects and duplicates SHALL NOT affect later attempts.
V24 SHALL retain the first 512 unique valid candidates. V22/V23 baselines SHALL
NOT enter M1 generation or ranking; a predecessor artifact MAY be validated
read-only as a separate T3 control without a DE call. Screening SHALL use seeds 24001/24002,
`n_samples=200`, and `max_iter=50`. The deterministic
`min(8,N_valid)` SHALL be refined with seeds 24003/24004/24005,
`n_samples=1000`, and `max_iter=150`; deterministic
`min(4,N_refined)` finalists SHALL be declared before holdout.

At each stage ranking SHALL be `(converged_count desc, worst_final_entropy asc,
mean_final_entropy asc, candidate_id asc)`. Error/non-finite results SHALL be
non-converged and contribute `+inf`. Refinement count SHALL be
`min(8,N_valid)` and finalist count `min(4,N_refined)`; `N_valid=0` SHALL set
`mechanism_unverified` and forbid holdout.

`N_valid` SHALL mean profile-valid unique candidates admitted among the first
512, determined before DE. A DE error or non-finite entropy SHALL consume its
scheduled valid-evaluation slot, remain in evidence, and rank as
non-converged/`+inf`; it SHALL NOT change profile validity or `N_valid`.

#### Scenario: Frozen budget is exhausted without a development pass

- **WHEN** the complete bounded development budget finds no converged profile
- **THEN** V24 SHALL continue only far enough to produce the frozen holdout set
  if candidates exist
- **AND** SHALL NOT expand the search, seeds, degree caps, or numerical budget

### Requirement: Holdout SHALL be independent and unanimous per candidate

The persisted finalists SHALL be evaluated with seeds 24101–24105,
`n_samples=2000`, and `max_iter=200`. A run converges only if its final
normalized base-q entropy is at most 0.01. A finalist passes only if all five
holdout seeds converge; V24 passes iff at least one finalist passes.

#### Scenario: One holdout seed fails

- **WHEN** a finalist has final base-q entropy above 0.01 or an invalid result
  on any holdout seed
- **THEN** that finalist SHALL fail holdout
- **AND** averaging, majority vote, replacement, tuning, or rerun SHALL NOT
  convert it to PASS

### Requirement: Evidence SHALL be additive and semantically reconstructable

V24 SHALL retain its frozen manifest, exact consumed channel, proposal ledger,
all evaluations, pre-holdout finalist declaration, decision, transcript, and
read-only verifier report in a fresh additive output directory. The verifier
SHALL reconstruct candidate validity, rate, leakage, ranking, seed separation,
convergence, and final gate state.

#### Scenario: Evidence is incomplete or inconsistent

- **WHEN** required records are absent, overwritten, or fail semantic
  reconstruction
- **THEN** the package SHALL NOT support `pass`
- **AND** the concrete engineering/resource blocker SHALL be reported without
  inventing a scientific FAIL

### Requirement: Scientific DE time SHALL stop at the frozen completed-call budget

Within one user-authorized M0–M2 scientific invocation, V24 SHALL accumulate
only `time.perf_counter` durations of completed DE calls. Each completed call
and duration SHALL be appended immediately. It SHALL then first test whether
all frozen required evaluations are complete. If complete, it SHALL compute
normal PASS/FAIL even when accumulated time is at least 24 hours. Only if a
required evaluation remains and accumulated time is at least 24 hours SHALL
it set `resource_blocked` and refuse to start the next call. A call already in
progress MAY finish and SHALL be recorded before this ordered check. M0
read-only checks contribute no DE-call time. No RSS hard gate exists.

#### Scenario: The completed-call ceiling is reached

- **WHEN** accumulated completed-DE-call duration reaches or exceeds 24 hours
- **AND** at least one frozen required evaluation remains
- **THEN** no next DE call SHALL start and state SHALL be `resource_blocked`
- **WHEN** all frozen required evaluations are already complete
- **THEN** normal PASS/FAIL SHALL be computed regardless of accumulated time

### Requirement: Claim and successor states SHALL remain separated

Engineering pass SHALL mean only that the harness passed its tests. V24 DE
pass SHALL mean only an asymptotic single-edge ensemble passed the frozen
holdout. Neither state SHALL imply finite-code success, FER, qualification, or
promotion.

#### Scenario: V24 reaches a terminal scientific state

- **WHEN** V24 passes
- **THEN** it MAY emit only `ready_to_propose_finite_code_change`
- **WHEN** V24 fails after the complete budget
- **THEN** it SHALL emit `single_edge_bounded_optimization_failed`
- **AND** true MET, target relaxation, or finite construction SHALL require a
  separate user-authorized change
