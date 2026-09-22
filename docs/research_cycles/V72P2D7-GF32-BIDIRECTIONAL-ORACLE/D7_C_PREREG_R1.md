# D7-C bidirectional cross-layer oracle preregistration R1 (frozen before any real artifact or decoder observation)

- Branch `formal-ir-v72p1-addendum-clean`; starting HEAD `86f6baf6` (Phase-P
  interface-proposal commit, descendant of `212f69ba`). Provenance only; no
  remote-equality requirement.
- Packet binding: `D7_C_BIDIRECTIONAL_ORACLE_FREEZE_IMPLEMENT_PRE_EXECUTE_R1_TASK_PACKET.md`
  (R1) binds fully except where amended by
  `D7_C_BIDIRECTIONAL_ORACLE_FREEZE_IMPLEMENT_PRE_EXECUTE_A1_TASK_PACKET.md`
  (A1); A1 wins on conflict.
- Deferred-start gate satisfied:
  `D7_B_EARLY_EXIT_SOFT_BELIEF_AUDIT_REVIEW_PASS`. Phase-P gate satisfied:
  `D7_B_LAYER_INTERFACE_CORRECTION_PROPOSAL_PASS_D7_C_NONBLOCKING`.
- Status: `FROZEN_PREREG_R1`. **Observation ordering:** this prereg is committed
  (scoped docs/OpenSpec commit by the main thread) before any real D7-C
  artifact or decoder observation. No D7-C decoder call, no Model-F binary
  content read, no output root, and no UUID exist at freeze time.
- Predecessor facts (immutable): D7-B R2 root
  `workspace/d7_b_easy_regime_c605d1e6-8577-4c52-a865-12500fc8c964/` (five
  files); D7-B terminal `D7_B_RESOURCE_OVERRUN`; accepted scope
  `HARD_DECISION_EASY_REGION_OBSERVED_WITH_RESOURCE_AND_SOFT_BELIEF_LIMITATIONS`;
  primary outcome `D7_B_MIXED_METRIC_AND_INTERFACE_DEFECT`; secondary
  `D7_B_RSS_TELEMETRY_DEPENDENCY_GAP`; R1d paused; G2 absent; no
  `workspace/d7_c_bidirectional_oracle_*` root. All authorization false.
- D7-C never consumes decoder-returned beliefs across layers. The layer
  interface correction remains `DEFERRED_MANDATORY_BEFORE_CROSS_LAYER_APP`; this
  module must not import or depend on any interface-rework implementation.

## 1. H03 — accepted Model-F estimator (independently re-verified)

**Confirmed: the accepted post-R2 estimator is unique.** Traced callables and
lines re-opened at HEAD (source):

- Constant: `LAMBDA_STAR = 137.3823795883264`
  (`comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py`
  L46).
- **Accepted (used by D7-C)**: `build_f_model_concentration(counts_ab, lam=LAMBDA_STAR)`
  (same file L274–305). Formula L299–301:
  `n_b = counts.sum(axis=0)`, `p_global = counts.sum(axis=1) / total`,
  `p = (counts + lam * p_global[:, None]) / (n_b[None, :] + lam)` — lambda is a
  **total concentration per Bob column**, not a per-cell pseudocount. Columns
  asserted to sum to 1 within 1e-12 (L303–304); `lam > 0` required (L294–295).
  Public callable: `prepare_model_f_prior_candidate(counts_ab, p_b, lam=LAMBDA_STAR)`
  (L2323–2350; calls `build_f_model_concentration` at L2337; returns
  `(p_b, p_f)` with `p_f` shape `(Alice=1024, Bob=1024)`, every column summing
  to 1).
- Lifecycle acceptance: `G1_INFORMATION_RECOVERY_R2_ACCEPTANCE_R1.md`
  (`docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/`) L13–19 accepted block
  (`ADDITIVE_NONFORMAL_BACKOFF_PRIOR_CANDIDATE`,
  `LAMBDA_APPLICATION_CONTRACT_DEFECT`, no formal/wiring change), L23–25
  decisive formula/provenance, L57–65 lifecycle
  (`g1_information_recovery_r2_candidate_accepted: true`).
- Confirmations: `G1_L1_ESTIMATOR_DISCRIMINATOR_R1.md` L28–29 (E1 formula =
  this backoff); `D5_ROUTE_STOP_REVIEW_R1.md` L28–29 (E1 formula re-derived);
  `D6_GRAPH_MOTHER_PREREG_R1.md` §4 L11–15 (the candidate frozen as the
  accepted prior: `d5.prepare_model_f_prior_candidate(counts_ab, p_b)` with
  `LAMBDA_STAR = 137.3823795883264`).
- Source documents for the above: `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/G1_INFORMATION_RECOVERY_R2_ACCEPTANCE_R1.md`,
  `.../G1_L1_ESTIMATOR_DISCRIMINATOR_R1.md`, `.../D5_ROUTE_STOP_REVIEW_R1.md`,
  `.../G1_NO_SIGNAL_ATTRIBUTION_R1.md`, and
  `docs/research_cycles/V72P2D6-GF32-GRAPH-MOTHER/D6_GRAPH_MOTHER_PREREG_R1.md`.

**Rejected alternative for this task (recorded, never called):**
`prepare_model_f_prior` (L2292–2320) → `build_f_model` (L246–271), which
applies the scalar **cell-wise** (`sm = counts + lam`, L265). This is the
identified `LAMBDA_APPLICATION_CONTRACT_DEFECT`; R1 §3.1 explicitly excludes
per-cell pseudocount. Scale: `1024 * lam ≈ 140,680` added per column against
`n_b ≈ 256` observed counts (acceptance R1 L24 → 99.82% prior). The D5
discriminator E2 estimator (`kap* ≈ 62`, L1-only) was left un-implemented ("no
code justified") and is **not** an accepted joint estimator
(`G1_L1_ESTIMATOR_DISCRIMINATOR_R1.md` L28–33, L102–107).

**No STOP condition:** exactly one accepted estimator exists. D7-C uses
`prepare_model_f_prior_candidate` (equivalently `build_f_model_concentration`)
with the frozen `LAMBDA_STAR`, and never calls `build_f_model` /
`prepare_model_f_prior`.

## 2. Input/model identity

- Accepted Model-F root: `workspace/v72p2d5_model_f_input/20260907_r1`
  (`v72p2d5_gf32_rate_mother.py` L85 `MODEL_F_INPUT_FORMAL_ROOT`).
- Loader path (future authorized run only): the D5 sibling consumer
  `v72p2d5_model_f_input.load_model_f_input`, reached via D5
  `_load_model_f_loader` (L2371–2418) / `_load_model_f_input_or_blocked`
  (L2421–2450). Only this accepted artifact may be loaded; any other
  `--model-f-root` value refuses before any decoder bind, Model-F read, or root
  creation.
- Loaded objects: `counts_ab (1024, 1024)` and `p_b (1024,)`. No
  CAL/VAL/parquet/raw rows are read anywhere in D7-C.
- Dimension: `n = 64` symbols per block.
- Block seeds: `2026091300..2026091315` (16 paired blocks, ascending). Disjoint
  from D5 (`2026090600..`, `2026090801`), D6 (`2026091000..`,
  `2026091010..`, `2026091100..`) and D7-B (`2026091200..`) seed domains.
- The same generated Bob/Alice/U1/U2 block is reused across both f values and
  all four conditions: sampling happens once per seed, before any f/condition
  decode, and never depends on f.

## 3. Prior/estimator derivation and joint tensor

1. `(p_b, p_f) = d5.prepare_model_f_prior_candidate(counts_ab, p_b_cal)`
   (default `lam=LAMBDA_STAR`).
2. Accepted joint table in memory, built once:
   `J = p_f.reshape(32, 32, 1024)` so that
   `J[u1, u2, b] = P_F(A = 32*u1 + u2 | B = b)` (decomposition
   `A = 32*U1 + U2`; `symbols_to_layers` L400–405, `layers_to_symbols`
   L408–416). Each Bob column sums to 1 over `(u1, u2)`; entries are
   nonnegative and may contain zeros from zero-count Alice rows.
3. Block generation, once per seed:
   `block = d5.sample_matched_block(p_b, p_f, 64, seed)` (L872–910) returning
   int arrays `bob, alice, u1, u2` with `alice = 32*u1 + u2`. The same dict is
   reused byte-identically for all 8 decodes of that seed.

## 4. Mother construction and disclosures

Frozen exact call expressions (n = 64, m_max = 64; D5 builder + D5 graph
seeds):

```text
L1: sup = d5.build_dv3_nested_support(64, 64, 49, 2026090501)
    H1  = d5.assign_gf32_coefficients(sup, 2026090501, None, 64)
L2: sup = d5.build_dv3_nested_support(64, 64, 43, 2026090502)
    H2  = d5.assign_gf32_coefficients(sup, 2026090502, None, 64)
```

(Seeds D5 L52–53; builders D5 L422+ / L636; all in
`comparison_bench/src/comparison_bench/formal_ir/v72p2d5_gf32_rate_mother.py`.)

This is exactly `d5.build_dv3_nested_mother(64, 64, 49, 2026090501, None)` /
`(64, 64, 43, 2026090502, None)` (L669–672) and exactly the D6-frozen
`B0_D5_DV3_NATIVE` construction (`v72p2d6_gf32_graph_mother.py` L32–36
`ROW_BUDGETS[64] = {"L1": (49,59,64), "L2": (43,52,64), "k_min": {"L1": 49, "L2": 43}}`;
`D6_GRAPH_MOTHER_PREREG_R1.md` §4 table L26–35 + §5 B0 L50–54; code L612–614
and L644–645). D6's structure validity audit recorded n64 L1 49 / L2 43 as
valid (`docs/research_cycles/V72P2D6-GF32-GRAPH-MOTHER/D6_GRAPH_MOTHER_VALIDITY_R1C_A5.csv`,
B0 rows).

Geometry disambiguation (recorded; no silent choice):

- **Chosen** geometry above (k_min = first disclosure prefix, m_max = 64):
  the frozen D5-native construction with the D6 row budgets and D5 seeds.
- **Not used**: the D5 formal G1 rate-mother geometry
  `build_dv3_nested_mother(64, 59, 59, 2026090501)` /
  `(64, 52, 52, 2026090502)` (`G1_L1_K_MIN = 59`, `G1_L2_K_MIN = 52`,
  L73–74; builds L2204–2207). Its frozen prefixes fail the strict 11-gate
  structure audit (`G1_NO_SIGNAL_ATTRIBUTION_R1.md` D2 L40–45: `H1[:49]` has a
  zero column / 2 components; `H2[:43]` has degree-1 variables; full mothers
  carry base-pair duplicates). It cannot supply the required valid
  disclosure prefixes.
- **Not used**: the discriminator-only L1 family
  `(64, 59, 59, 2026090501)` + square `(64, 64, 64, 2026090801)` from the D5
  route-stop arm (`D5_ROUTE_STOP_REVIEW_R1.md` S01 L35) — a control family,
  not the accepted n=64 L1/L2 mother.

Disclosures (row prefixes of the mothers built above; construction order =
disclosure order):

| f | L1 rows | L2 rows |
|---|---|---|
| 1.0 | 49 | 43 |
| 1.2 | 59 | 52 |

The decoder receives `H1[:49]` / `H1[:59]` / `H2[:43]` / `H2[:52]`. VOID roots
are never read: `workspace/v72p2d5_g1/20260906_r1` (`VOID_RETAINED_IN_PLACE`)
and `workspace/d6_graph_mother_r1_923a25897087495ab4605870e561f3cc`
(`VOID_RETAINED_ZERO_REUSE`). Mothers are built in memory only.

## 5. Decoder identity and single-layer boundary

- Historical certified decoder: `v35.decode_row_layered_fftqspa`
  (`comparison_bench/src/comparison_bench/formal_ir/v35_algorithm_development.py`
  L636–747), cold, `warm_beliefs=None`, `max_iter=90` (`MAX_ITER`, D5 L89),
  `damping_alpha=1.0` (`DAMPING_ALPHA`, D5 L90), `field=None` (GF(2^5),
  poly 37). Accepted D5 adapter for the same call:
  `d5.bind_historical_decoder()` (L2453–2475).
- One single-layer decode per (condition, block, f). No sequential L1→L2 APP,
  no feedback, no flooding, no schedule comparison, no adaptive damping, no
  clipping, no restart, no min-sum, no graph search, no parameter tuning.
- Syndrome: `s = syndrome(H_layer[:rows], x_true_layer)` over GF(32), poly 37,
  using certified arithmetic (`v72p2d7_gf32_decoder_certification.syndrome_reference`
  L81–96 or `d5._gf32_syndrome` L223–240). The decoder receives the frozen
  `(H_prefix, prior_pq, syndrome)`.
- Per-call recomputation (D5 `_decode_block` L1026–1059 semantics):
  `exact = (x_hat == x_true_layer)`; `syndrome_ok = decoder_reported_ok AND
  (syndrome(H_prefix, x_hat) == s)`. Syndrome never upgrades exact; any
  `syndrome_ok != exact` row is isolated as a syndrome-without-exact event and
  is never merged into "exact" or "recovered".

## 6. Four prior constructions (exact formulas)

For each position `i` with Bob symbol `b_i = block.bob[i]`, `u1_true_i`,
`u2_true_i` (arrays indexed `[layer_symbol, position]`):

```text
L1_MARGINAL[:, i]    = sum_u2 J[:, u2, b_i]                     # already sums to 1 over u1
L1_ORACLE_U2[:, i]   = J[:, u2_true_i, b_i] normalized over u1
L2_MARGINAL[:, i]    = sum_u1 J[u1, :, b_i]                     # already sums to 1 over u2
L2_ORACLE_U1[:, i]   = J[u1_true_i, :, b_i] normalized over u2
```

- Oracle slices are normalized by their own slice mass. If a slice mass is
  `<= 0` (possible only when the accepted count table gives `J` an all-zero
  layer slice), the D5-family fallback applies: uniform `1/32` over the layer
  axis for that position (mirroring `marginalize_f_to_p1` L316–319 /
  `conditionalize_f_to_p2` L337–341 zero-mass conventions). Marginals keep
  their possibly-zero entries.
- **Boundary rule (applied exactly once):** transpose to the certified
  `(position, q)` shape only at the decoder boundary, then
  `prior_pq = d5._floor_renorm(prior_qn.T, d5.DECODER_FLOOR)` with
  `DECODER_FLOOR = 1e-15` (L345–350, L48). No other floor, clip, or
  renormalization on the D7-C side; every emitted prior entry is positive and
  every row sums to 1. The decoder's internal 1e-15 floor is decoder
  semantics, not a second D7-C application.
- Oracle truth is used only to select the slice/oracle prior; it is never
  written to any artifact.

## 7. Call matrix and frozen order

`16 blocks × 2 f × 4 conditions = 128` scientific calls. Call order is frozen:

```text
for f in [1.0, 1.2]:
  for seed in 2026091300 .. 2026091315 (ascending):
    L1_MARGINAL
    L1_ORACLE_U2
    L2_MARGINAL
    L2_ORACLE_U1
```

Identities are frozen in memory before the first call: 128 tuples of
`(f, seed, condition, layer, rows, n=64)`. Every call is attempted exactly
once unless a higher-priority run stop occurs; there is no early-success stop
and no replacement cell. The marginal/oracle pair for a given `(f, seed,
layer)` shares `H_prefix`, syndrome target, block and decoder configuration;
only the prior differs.

## 8. Budgets, resource guards, no-retry

- scientific calls `<= 128`, and exactly 128 on normal completion;
- per-call watchdog `120 s` (exceeded → `D7_C_WATCHDOG_TIMEOUT_VOID`, stop);
- stored scientific wall `<= 1500 s` (exceeded → resource overrun);
- outer GNU timeout `1800 s`, kill grace `30 s`;
- WSL current-process RSS: `resource.getrusage(resource.RUSAGE_SELF).ru_maxrss`
  with explicit Linux KiB→bytes conversion (`* 1024`); must be finite and
  positive; **absence/nonpositive/nonfinite measurement blocks before the first
  scientific call**. No psutil anywhere.
- RSS must stay `< 2 GiB` (`2 * 1024**3` bytes); breach stops the run as a
  resource overrun.
- Zero retry, rerun, resume, replacement or reuse: sequential execution only,
  one invocation, one root.

## 9. Recorded scalar evidence

Per call (`decoder_records.csv`), each row a scalar record with exactly:
`call_idx (1..128), f, seed, condition, layer, rows, n, exact, syndrome_ok,
iterations, status, finite, symbol_errors, unsatisfied_checks, wall_s,
rss_bytes, belief_max_prob, belief_mean_true_p, belief_mean_entropy,
beliefs_conditioned, current_belief_label`.

- `exact`, `syndrome_ok` are independently recomputed in-run (Section 5);
  `symbol_errors = count(x_hat != x_true_layer)`; `unsatisfied_checks =
  count(syndrome(H_prefix, x_hat) != s)`.
- `finite` covers `x_hat` and `final_beliefs`; `status` is the decoder-returned
  status string.
- Current-belief diagnostics (explicitly labeled, never posterior/APP):
  `belief_max_prob`, `belief_mean_true_p` (at the true layer symbol),
  `belief_mean_entropy` (bits), all computed from `softmax(final_beliefs)` of
  the single call. `beliefs_conditioned = (iterations > 0)` (A1 ruling 6 +
  audit: at least one completed check sweep). `current_belief_label` is exactly
  `PRIOR_ONLY_CURRENT_BELIEF` when `iterations == 0`, else
  `CHECK_UPDATED_CURRENT_BELIEF`; no other label tokens are permitted and the
  strings "posterior"/"APP" never appear in any label.

Per `(f, layer)` paired summary (`paired_summary.csv`), one row per stratum
(4 rows): `f, layer, marginal_condition, oracle_condition,
marginal_exact_count, oracle_exact_count, oracle_only_count,
marginal_only_count, both_exact_count, neither_exact_count,
paired_syndrome_ok_count, paired_syndrome_disagreement_count, nonfinite_count,
crash_count, marginal_median_iterations, oracle_median_iterations,
marginal_max_iterations, oracle_max_iterations, marginal_median_wall_s,
oracle_median_wall_s, marginal_max_wall_s, oracle_max_wall_s, stratum_label`.

No raw beliefs, symbols, priors, syndromes or block vectors are persisted;
`belief_*` fields are scalars only.

## 10. Frozen stratum classification and run terminals

Per `(f, layer)` stratum (4 strata; 16 marginal + 16 oracle calls each),
classify by first match in this frozen order (a stratum satisfying an earlier
rule is not relabeled; thresholds are mechanism-routing rules, not success-rate
estimates):

1. `STRONG_ORACLE_LIFT`: `oracle_only >= 4/16` AND `marginal_only <= 1/16` AND
   `oracle_exact >= 4/16` AND zero crash/nonfinite in the stratum.
2. `NO_ORACLE_RECOVERY`: `oracle_exact <= 1/16` AND `marginal_exact <= 1/16`.
3. `MARGINAL_ALREADY_RECOVERS`: `marginal_exact >= 12/16`.
4. `AMBIGUOUS_ORACLE_EFFECT`: every other finite completed case.

Run terminal, exact priority (first applicable wins):

1. `D7_C_PRE_EXECUTION_BLOCKED`
2. `D7_C_WATCHDOG_TIMEOUT_VOID`
3. `D7_C_NONFINITE_OR_CRASH_BLOCKED`
4. `D7_C_RESOURCE_OVERRUN`
5. `D7_C_INCOMPLETE_CALL_MATRIX`
6. `D7_C_BIDIRECTIONAL_DEPENDENCE` — at least one f has strong lift for both
   L1 and L2
7. `D7_C_L1_DEPENDS_ON_U2` — strong L1 lift in at least one f, no strong L2
8. `D7_C_L2_DEPENDS_ON_U1` — strong L2 lift in at least one f, no strong L1
9. `D7_C_MARGINAL_REGION_EXISTS` — marginal already recovers in any stratum
10. `D7_C_ORACLE_NO_USEFUL_RECOVERY` — all four strata are no-recovery
11. `D7_C_MIXED_DIAGNOSTIC`

All stratum labels are recorded even when a higher-priority run terminal
applies. A stratum label is assigned only when all 32 of its calls completed;
an incomplete stratum records partial counts and an empty label (never a
fabricated one), with the run terminal carrying the reason.

## 11. Provenance labeling rule (A1 §A1.4 / C14)

- Iteration-0 / current-belief diagnostics are labeled only
  `PRIOR_ONLY_CURRENT_BELIEF`, never posterior/APP. `CHECK_UPDATED_CURRENT_BELIEF`
  is used only when `iterations > 0`; it is still a current belief, not a
  calibrated syndrome-conditioned posterior, and is never a cross-layer input.
- `beliefs_conditioned` is derived from `iterations` plus the reviewed audit
  semantics (E02/E03: a cold iteration-0 return contains no check message and
  `softmax(final_beliefs)` equals the input prior; E08/E09: consumers must not
  sell that prior as `P(U1|B,s1)`).
- D7-C has no `final_beliefs -> other layer` data flow: the four priors are
  direct functions of `J` and block truth (Section 6), and no decoder-returned
  belief is ever used as a prior, APP, or cross-layer evidence.

## 12. Nonclaim boundaries

Oracle conditions are counterfactual diagnostics only. They are not protocol
recovery, do not count oracle truth as disclosure, and support no FER,
leakage, reconciliation-efficiency, key-rate, CAL/real-data, qualification,
promotion, R1d, G1/G2, or general GF32/NB-LDPC claim. The four conditions probe
mechanism location at the frozen operating point; the output is a
diagnostic stratum/terminal record, not a performance estimate.

## 13. Freeze statement

This prereg froze every callable, constant, seed, row, formula, order, budget,
threshold, terminal and label rule above at HEAD `86f6baf6`, before any real
D7-C artifact or decoder observation. Implementation may follow only after the
scoped commit of this prereg. All authorizations are false; no UUID exists; no
`workspace/d7_c_bidirectional_oracle_*` root exists.
