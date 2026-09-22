# D7-D schedule discriminator preregistration R1 (frozen before any real artifact or decoder observation)

- Branch `formal-ir-v72p1-addendum-clean`; starting HEAD `1f472c2a` (Phase-A
  D7-C acceptance commit). Provenance only; no remote-equality requirement.
- Packet binding: `D7_C_ACCEPT_D7_D_SCHEDULE_FREEZE_IMPLEMENT_PRE_EXECUTE_R1_TASK_PACKET.md`
  (R1), §4–§10 and §13–§14; this prereg is the Phase-B freeze under §6. R1 binds
  fully.
- Status: `FROZEN_PREREG_R1`. **Observation ordering:** this prereg is committed
  (scoped docs/OpenSpec commit) before any real D7-D artifact or decoder
  observation. No D7-D decoder call, no Model-F binary content read, no output
  root and no UUID exist at freeze time.
- Predecessor facts (immutable): D7-C root
  `workspace/d7_c_bidirectional_oracle_94c0ea15-a786-4cb8-a991-6fec521cccae/`
  (six files: `manifest.json`, `decoder_records.csv`, `paired_summary.csv`,
  `summary.json`, `report.md`, `command_log.txt`); D7-C terminal
  `D7_C_BIDIRECTIONAL_DEPENDENCE`; accepted scope
  `D7_C_RESULT_ACCEPTED_BIDIRECTIONAL_DEPENDENCE_DIAGNOSTIC`; D7-C
  authorization false; D7-B root immutable; R1d/G2 absent; no
  `workspace/d7_d_*` root. All authorization false.
- D7-D does not consume cross-layer returned beliefs and does not depend on the
  deferred interface rework. The layer interface remains
  `DEFERRED_MANDATORY_BEFORE_CROSS_LAYER_APP`.

## 1. Decision question and claim ceiling

Holding every scientific input fixed, does independent flooding FFT-QSPA or the
certified current row-layered FFT-QSPA yield a reproducible exact-recovery
advantage?

May establish: per-`(f,layer,condition)` stratum classification from the frozen
five labels; one run terminal from the frozen ten-entry priority; per-identity
paired exact/syndrome outcomes; work-normalized descriptive differences.

May not establish: FER, leakage, reconciliation efficiency, key rate, protocol
recovery, cross-layer APP viability, interface acceptance, code qualification,
R1d/G1/G2 readiness, promotion, or any general GF32/NB-LDPC conclusion. The
classifications are route discriminators, not success-rate or FER estimates.

## 2. Identical-input contract (schedule is the only variable)

Identical to D7-C for every call pair:

- accepted Model-F estimator and root (`workspace/v72p2d5_model_f_input/20260907_r1`);
- the 16 D7-C paired blocks/seeds `2026091300..2026091315`, sampled once per
  seed and reused across f, conditions and schedules;
- f values `[1.0, 1.2]`; L1/L2 rows and D5 mothers; the four marginal/oracle
  prior conditions;
- syndrome, truth (usage and non-persistence) and labels;
- `max_iter=90`, cold start, finite/exact/syndrome definitions and resource
  limits.

Explicitly forbidden as simultaneous changes: damping (beyond row-layered
`damping_alpha=1.0`), clipping, restart, min-sum, warm start, graph changes, new
priors, more disclosure, cross-layer feedback, cross-layer APP.

## 3. Accepted estimator (H03, re-asserted from D7-C)

The unique accepted post-R2 concentration/backoff estimator is
`v72p2d5_gf32_rate_mother.prepare_model_f_prior_candidate(counts_ab, p_b)`
(L2323–2350) → `build_f_model_concentration` (L274–305) with
`LAMBDA_STAR = 137.3823795883264` (L46). The rejected alternative
`prepare_model_f_prior` (L2292–2320) → `build_f_model` (L246–271), the per-cell
pseudocount `LAMBDA_APPLICATION_CONTRACT_DEFECT`, is never called. No STOP: the
estimator identity is unchanged from D7-C and is not re-adjudicated here.

## 4. Inputs, priors and mothers (unchanged from D7-C)

- Loaded objects: `counts_ab (1024, 1024)` and `p_b (1024,)`; loaded via the D5
  sibling loader (future authorized run only); no CAL/VAL/parquet/raw read.
- `n=64`; `J = p_f.reshape(32, 32, 1024)` with
  `J[u1, u2, b] = P_F(A = 32*u1 + u2 | B = b)`.
- Block generation once per seed:
  `d5.sample_matched_block(p_b, p_f, 64, seed)`, reused byte-identically for
  all 8 decodes of that seed (4 conditions × 2 schedules).
- Four prior constructions (exact formulas, unchanged):
  `L1_MARGINAL = sum_u2 J[:,u2,b_i]`; `L1_ORACLE_U2 = J[:,u2_true,b_i]`
  normalized over u1; `L2_MARGINAL = sum_u1 J[u1,:,b_i]`; `L2_ORACLE_U1 =
  J[u1_true,:,b_i]` normalized over u2; zero-mass oracle slice falls back to
  uniform `1/32`. Boundary: transpose to `(position, q)` only at the decoder
  boundary and one `d5._floor_renorm(prior_qn.T, d5.DECODER_FLOOR)` with
  `DECODER_FLOOR = 1e-15`; no other floor/clip/renormalization. Oracle truth is
  used only to select the prior slice and is never persisted.
- Mothers (in memory only; VOID roots never read):
  `L1: build_dv3_nested_support(64, 64, 49, 2026090501)` +
  `assign_gf32_coefficients(sup, 2026090501, None, 64)`;
  `L2: build_dv3_nested_support(64, 64, 43, 2026090502)` +
  `assign_gf32_coefficients(sup, 2026090502, None, 64)`. Disclosures as row
  prefixes: `f=1.0: L1 49, L2 43`; `f=1.2: L1 59, L2 52`.
- Syndrome: `s = syndrome(H_layer[:rows], x_true_layer)` over GF(32), poly 37,
  via the certified helper; per-call `exact = (x_hat == x_true_layer)`;
  `syndrome_ok = decoder_reported_ok AND syndrome(H_prefix, x_hat) == s`.
  Syndrome never upgrades exact and is never merged into recovery.

## 5. Schedules and frozen decoder call shapes

Schedules in order `[ROW_LAYERED, FLOODING]`. The only per-call delta is the
schedule; `H_prefix`, `prior_pq`, `syndrome`, `max_iter` and cold start are
identical within an identity pair.

Frozen production call shapes (`v35_algorithm_development.py`):

```text
ROW_LAYERED: v35.decode_row_layered_fftqspa(H_prefix, prior_pq, syndrome,
             max_iter=90, damping_alpha=1.0, warm_beliefs=None, field=None)
             # L636-644 signature
FLOODING:    v35.decode_flooding_fftqspa(H_prefix, prior_pq, syndrome,
             max_iter=90, field=None)
             # L529-535 signature; DEFAULT_MAX_ITER=30 never used
```

Flooding declares no `damping_alpha` and no `warm_beliefs`; no damping parameter
is invented. Each decoder retains its own normal internal stopping; no early
stop across identities. The accepted row-layered adapter remains
`d5.bind_historical_decoder()`; the flooding function is the existing module
function reached directly (or through a minimal DI boundary) with this exact
shape.

## 6. Flooding correctness prerequisite (F01–F08)

Before D7-D is declared ready, the existing `decode_flooding_fftqspa` must be
certified in `D7_D_FLOODING_CERTIFICATION_R1.md` against the accepted D7-A
independent oracle on tiny synthetic fixtures:

- F01 direct check update remains the already certified kernel;
- F02 single-check full posterior equals exact enumeration within `1e-10`;
- F03 a two-check tree full posterior/MAP equals exact enumeration within
  `1e-10` after sufficient flooding iterations;
- F04 one flooding iteration matches an independently written flooding
  recurrence, not the production implementation;
- F05 iterations 1/2/3 on a small cycle match independent per-iteration beliefs
  within `1e-10`; do not compare loopy BP with MAP;
- F06 nonzero coefficients and syndromes include negative-direction controls;
- F07 cold start, normalization, stopping and `final_beliefs` current-state
  semantics are explicit, including iteration-0 `PRIOR_ONLY`;
- F08 no real Model-F, production evidence or formal root is read.

If any F item fails: terminal `D7_D_FLOODING_CERTIFICATION_FAIL`, preserve a
minimal counterexample, do not patch flooding in this packet, and do not
continue to D7-D readiness. This gate is separate from the ten run terminals and
precedes them; it never enters the run priority list.

## 7. Call matrix and frozen order

`16 seeds × 2 f × 4 conditions = 128` identities in D7-C original order; two
schedules per identity = exactly 256 calls:

```text
for f in [1.0, 1.2]:
  for seed in 2026091300 .. 2026091315 (ascending):
    for condition in [L1_MARGINAL, L1_ORACLE_U2, L2_MARGINAL, L2_ORACLE_U1]:
      ROW_LAYERED   # call 2k-1
      FLOODING      # call 2k
```

Identities are frozen in memory before the first call: 128 tuples of
`(f, seed, condition, layer, rows, n=64)`. `call_idx = 2*identity_idx - 1` for
`ROW_LAYERED`, `2*identity_idx` for `FLOODING`. Exactly 256 calls on normal
completion; hard cap 256; each call attempted exactly once unless a
higher-priority run stop occurs; no early-success stop; no replacement cell;
each decoder retains its own normal internal stopping.

## 8. Work-normalized metrics

Iteration counts alone are not comparable. Per call persist: `schedule, f, seed,
condition, layer, rows, n, exact, syndrome_ok, iterations, status, finite,
symbol_errors, unsatisfied_checks, wall_s, rss_bytes, check_node_updates,
check_edge_updates, belief_max_prob, belief_mean_true_p, belief_mean_entropy,
beliefs_conditioned, current_belief_label`, where:

- `completed_iterations` is the decoder-returned completed sweep count;
- `check_node_updates = rows * completed_iterations`, iteration-0 explicitly
  zero;
- `check_edge_updates = (sum over disclosed rows r of nnz(H_prefix[r])) *
  completed_iterations`, iteration-0 explicitly zero, using the frozen matrix
  row degrees computed in memory;
- `symbol_errors = count(x_hat != x_true_layer)`; `unsatisfied_checks =
  count(syndrome(H_prefix, x_hat) != s)`;
- current-belief diagnostics from `softmax(final_beliefs)`:
  `belief_max_prob`, `belief_mean_true_p` (at the true layer symbol),
  `belief_mean_entropy` (bits), all scalar;
- provenance labeling: `beliefs_conditioned = (iterations > 0)`;
  `current_belief_label` exactly `PRIOR_ONLY_CURRENT_BELIEF` when
  `iterations == 0`, else `CHECK_UPDATED_CURRENT_BELIEF`; confidence/entropy
  fields are never called "posterior" or "APP" unless independently established,
  which this prereg does not establish.

Per identity (128 rows) paired: `layered_exact`, `flooding_exact`,
`layered_only_exact`, `flooding_only_exact`, `both_exact`, `neither_exact`;
separate syndrome-only analogues `layered_only_syndrome_ok`,
`flooding_only_syndrome_ok`, `both_syndrome_ok`, `neither_syndrome_ok`;
`iteration_diff`, `check_update_diff`, `edge_update_diff` recorded only when
both calls are complete and finite; `wall_ratio = flooding_wall_s /
layered_wall_s` recorded only when both walls are finite and the layered wall is
positive (denominators valid); otherwise the field is empty. No winner is
inferred from iteration count alone.

## 9. Stratum classification and run terminals

Per `(f,layer,condition)` stratum of 16 blocks × 2 schedules = 32 calls; 8
strata (2 f × 4 conditions, each condition fixing its layer). First match in
this frozen order (a stratum satisfying an earlier rule
is not relabeled; thresholds are mechanism-routing rules, not success-rate
estimates):

1. `FLOODING_EXACT_ADVANTAGE`: `flooding_only_exact >= 4` AND
   `layered_only_exact <= 1`.
2. `LAYERED_EXACT_ADVANTAGE`: `layered_only_exact >= 4` AND
   `flooding_only_exact <= 1`.
3. `EXACT_TIE_HIGH`: `both_exact >= 12` AND `flooding_only_exact <= 1` AND
   `layered_only_exact <= 1`.
4. `EXACT_TIE_LOW`: `neither_exact >= 12` AND `flooding_only_exact <= 1` AND
   `layered_only_exact <= 1`.
5. `MIXED_SCHEDULE_EFFECT`: otherwise.

Run terminal, exact priority (first applicable wins):

1. `D7_D_PRE_EXECUTION_BLOCKED`
2. `D7_D_WATCHDOG_TIMEOUT_VOID`
3. `D7_D_NONFINITE_OR_CRASH_BLOCKED`
4. `D7_D_RESOURCE_OVERRUN`
5. `D7_D_INCOMPLETE_CALL_MATRIX`
6. `D7_D_FLOODING_ADVANTAGE` — at least two strata flooding-advantage and no
   layered-advantage stratum
7. `D7_D_LAYERED_ADVANTAGE` — at least two strata layered-advantage and no
   flooding-advantage stratum
8. `D7_D_SCHEDULE_DEPENDENT_MIXED` — both advantage directions appear
9. `D7_D_SCHEDULE_NO_EXACT_DIFFERENCE` — exact flags identical for all 128
   identities
10. `D7_D_SCHEDULE_EFFECT_INCONCLUSIVE`

All eight stratum labels are recorded even when a higher-priority run terminal
applies. A stratum label is assigned only when all 32 of its calls completed; an
incomplete stratum records partial counts and an empty label (never a fabricated
one), with the run terminal carrying the reason.

## 10. Budgets, resource guards, no-retry

- exactly 256 scientific calls on normal completion; hard cap 256;
- per-call watchdog 120 s (exceeded → `D7_D_WATCHDOG_TIMEOUT_VOID`, stop);
- stored scientific wall `<= 1500 s` (exceeded → resource overrun);
- outer GNU `timeout -k 30 1800` (30 s kill grace);
- WSL current-process RSS via stdlib
  `resource.getrusage(resource.RUSAGE_SELF).ru_maxrss` with explicit Linux
  KiB→bytes conversion (`* 1024`); finite and positive; `< 2 GiB`
  (`2 * 1024**3`); absence/nonpositive/nonfinite blocks before the first
  scientific call; no psutil anywhere;
- fail before the first call if RSS is unavailable, Model-F is invalid or the
  target exists (`D7_D_PRE_EXECUTION_BLOCKED`);
- zero retry, rerun, resume, replacement, concurrency or reuse: sequential
  execution only, one invocation, one root.

## 11. Evidence artifacts, schema and verifier contract

Future root `workspace/d7_d_schedule_discriminator_<uuid>/`: fresh, no-overwrite,
no subdirectories, exactly seven files:

- `manifest.json`
- `decoder_records.csv`
- `paired_schedule.csv`
- `stratum_summary.csv`
- `summary.json`
- `report.md`
- `command_log.txt`

Schemas: `decoder_records.csv` 256 rows (frozen field list in §8);
`paired_schedule.csv` 128 rows (frozen paired field list in §8);
`stratum_summary.csv` 8 rows (frozen counts plus median iteration/check/edge/wall
per schedule and `stratum_label`); `manifest.json` (frozen run identities,
model-root file names/sizes, estimator ID, lambda, n, f/rows/seeds, graph seeds,
schedule order, call order, decoder IDs/kwargs, budgets, seven-file list,
terminal priority; run-time uuid/UTC/PID/authorization-consumed);
`summary.json` (terminal, 8 stratum labels, totals, stored wall, peak RSS,
retries/reruns/resumes = 0); `report.md` (compact scalar summary only);
`command_log.txt` (exact command, start/end, scalar checkpoints).

Writer/verifier split: the verifier reads only the seven files and independently
recomputes pairing, paired exact/syndrome counts, all eight stratum labels, work
arithmetic consistency and the run terminal; it never calls a decoder and never
loads Model-F. It detects missing/duplicate/unpaired/tampered records.

Narrow reuse: D7-C identities/priors/mothers/estimator are reused through a
narrow imported helper or an exact contract copy with equality tests; the D7-C
module and previous production modules are read-only and unmodified.

## 12. Nonclaim boundaries

Schedule classifications are route discriminators, not FER estimates. Oracle
conditions remain counterfactual diagnostics only; they are not protocol
recovery, do not count oracle truth as disclosure, and support no FER, leakage,
reconciliation-efficiency, key-rate, CAL/real-data, qualification, promotion,
R1d, G1/G2 or general GF32/NB-LDPC claim. No result of D7-D may be described as
a performance estimate of either schedule.

## 13. Freeze statement

This prereg froze every callable, constant, seed, row, formula, schedule, order,
metric definition, threshold, terminal and label rule above at HEAD
`1f472c2a`, before any real D7-D artifact or decoder observation. Implementation
and readiness may follow only after the scoped commit of this prereg and the
F01–F08 certification. All authorizations are false; no UUID exists; no
`workspace/d7_d_schedule_discriminator_*` root exists; the interface remains
`DEFERRED_MANDATORY_BEFORE_CROSS_LAYER_APP`.
