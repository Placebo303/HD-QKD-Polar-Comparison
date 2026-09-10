## ADDED Requirements

### Requirement: Schedule-only pair and decision boundary
The D7-D harness SHALL decode exactly two schedules per frozen identity — `ROW_LAYERED` and `FLOODING` — and SHALL change nothing else. All non-schedule scientific inputs SHALL be identical between the two calls of an identity. The harness SHALL NOT add damping (beyond row-layered `damping_alpha=1.0`), clipping, restart, min-sum, warm start, graph changes, new priors, more disclosure, cross-layer feedback or cross-layer APP; the layer interface SHALL remain `DEFERRED_MANDATORY_BEFORE_CROSS_LAYER_APP`.

#### Scenario: One variable only
- **WHEN** the two calls of an identity are compared
- **THEN** the schedule token is the only difference
- **AND** joint tensor, block, mother prefix, rows, prior, syndrome target, truth, labels and `max_iter` are identical.

#### Scenario: Forbidden schedules and parameters
- **WHEN** source or a run trace is inspected
- **THEN** no third schedule, damping/clipping/restart/min-sum/warm-start/graph/prior/disclosure/feedback change appears.

### Requirement: Frozen input identity and reuse contract
The harness SHALL use only the accepted Model-F root `workspace/v72p2d5_model_f_input/20260907_r1`, `n=64`, block seeds `2026091300..2026091315` sampled once per seed, one block reused across both f values, all four conditions and both schedules. The prior estimator SHALL remain the D7-C accepted `v72p2d5_gf32_rate_mother.prepare_model_f_prior_candidate` (`build_f_model_concentration`, `LAMBDA_STAR = 137.3823795883264`); `prepare_model_f_prior`/`build_f_model` SHALL never be called. The D7-C identities/priors/mothers SHALL be reused through a narrow imported helper or an exact contract copy with equality tests; the D7-C module and all previous production modules SHALL NOT be modified.

#### Scenario: Model-F root is fixed
- **WHEN** the runner receives any `--model-f-root` other than the accepted root
- **THEN** it refuses before any decoder bind, Model-F read or root creation.

#### Scenario: Contract equality with D7-C
- **WHEN** the reuse tests run
- **THEN** seeds, f values, rows, conditions, layer mapping, `LAMBDA_STAR`, `DECODER_FLOOR`, `MAX_ITER=90`, graph seeds and the four prior formulas equal the D7-C contract.

### Requirement: Frozen decoder call shapes and schedules
The row-layered schedule SHALL be `v35.decode_row_layered_fftqspa(H_prefix, prior_pq, syndrome, max_iter=90, damping_alpha=1.0, warm_beliefs=None, field=None)`. The flooding schedule SHALL be `v35.decode_flooding_fftqspa(H_prefix, prior_pq, syndrome, max_iter=90, field=None)`; flooding declares no damping or warm-start parameter and none SHALL be invented or passed. Both decoders SHALL start cold, SHALL retain their own normal internal stopping, and SHALL receive the same `H_prefix`, prior and syndrome per identity.

#### Scenario: No invented flooding parameter
- **WHEN** the flooding dispatch is inspected
- **THEN** exactly the frozen production call shape is used
- **AND** no `damping_alpha`, `warm_beliefs` or other non-signature keyword is passed.

#### Scenario: Internal stopping is retained
- **WHEN** either decoder returns early by its own stopping logic (e.g. cold initial syndrome match, `iterations=0`)
- **THEN** the call is recorded as returned
- **AND** no cross-schedule or cross-identity early stop is applied.

### Requirement: Frozen call matrix and order
Normal completion SHALL perform exactly 256 scientific calls: 128 identities × 2 schedules, each attempted exactly once unless a higher-priority run stop occurs, with no early-success stop and no replacement cell. The frozen order SHALL be `for f in [1.0,1.2]: for seed in 2026091300..2026091315: for condition in [L1_MARGINAL,L1_ORACLE_U2,L2_MARGINAL,L2_ORACLE_U1]: ROW_LAYERED; FLOODING`, so `call_idx = 2*identity_idx - 1` for `ROW_LAYERED` and `call_idx = 2*identity_idx` for `FLOODING`. The hard cap SHALL be 256.

#### Scenario: Identity freeze precedes the first call
- **WHEN** the runner starts decoding
- **THEN** the accepted Model-F has loaded and all 128 identities are frozen in memory
- **AND** each identity is `(f, seed, condition, layer, rows, n=64)` in the D7-C original order.

#### Scenario: No substitution
- **WHEN** a call fails or returns an unexpected outcome
- **THEN** no replacement call, rerun, resume or retry is performed.

### Requirement: Work-normalized metrics
Per call the writer SHALL persist `schedule, f, seed, condition, layer, rows, n, exact, syndrome_ok, iterations, status, finite, symbol_errors, unsatisfied_checks, wall_s, rss_bytes, check_node_updates, check_edge_updates, belief_max_prob, belief_mean_true_p, belief_mean_entropy, beliefs_conditioned, current_belief_label`, where `check_node_updates = rows * completed_iterations` with iteration-0 explicitly zero and `check_edge_updates = sum(frozen matrix row degrees) * completed_iterations`, also zero at iteration 0. Current-belief confidence/entropy SHALL carry the provenance labels `PRIOR_ONLY_CURRENT_BELIEF` (`iterations == 0`) or `CHECK_UPDATED_CURRENT_BELIEF` (`iterations > 0`) and SHALL NOT be called "posterior" or "APP" unless independently established. Per identity the paired record SHALL keep exact outcomes (`layered_only_exact`, `flooding_only_exact`, `both_exact`, `neither_exact`) and separate syndrome-only analogues; iteration, check-update, edge-update and wall-ratio differences SHALL be recorded only when denominators are valid; no winner SHALL be inferred from iteration count alone.

#### Scenario: Iteration-0 work arithmetic
- **WHEN** a call returns `iterations == 0`
- **THEN** `check_node_updates` and `check_edge_updates` are exactly zero
- **AND** the current-belief fields carry `PRIOR_ONLY_CURRENT_BELIEF`.

#### Scenario: Syndrome never upgrades exact
- **WHEN** a call returns `syndrome_ok` without exact recovery
- **THEN** the record keeps `exact=false` and the event is never counted as recovery or merged into an exact rate.

### Requirement: Frozen stratum classification
Each `(f,layer,condition)` stratum of 16 blocks SHALL be classified by first match in this frozen order: `FLOODING_EXACT_ADVANTAGE` (`flooding_only_exact >= 4` and `layered_only_exact <= 1`); `LAYERED_EXACT_ADVANTAGE` (converse); `EXACT_TIE_HIGH` (`both_exact >= 12`, exclusives `<= 1`); `EXACT_TIE_LOW` (`neither_exact >= 12`, exclusives `<= 1`); `MIXED_SCHEDULE_EFFECT` (otherwise). All eight `(f,condition)` strata SHALL be reported even under a higher-priority run terminal. An incomplete stratum SHALL record partial counts with an empty label, never a fabricated one.

#### Scenario: Label boundaries
- **WHEN** a stratum has `flooding_only_exact = 4` and `layered_only_exact = 1`
- **THEN** it is `FLOODING_EXACT_ADVANTAGE`
- **AND** a stratum with `flooding_only_exact = 4` and `layered_only_exact = 2` is not.

#### Scenario: Tie thresholds
- **WHEN** both schedules are exact on at least 12 blocks and each exclusive win is at most 1
- **THEN** the stratum is `EXACT_TIE_HIGH`.

### Requirement: Frozen run terminals and certification gate
The run SHALL select exactly one terminal from the ten-entry priority list `D7_D_PRE_EXECUTION_BLOCKED`, `D7_D_WATCHDOG_TIMEOUT_VOID`, `D7_D_NONFINITE_OR_CRASH_BLOCKED`, `D7_D_RESOURCE_OVERRUN`, `D7_D_INCOMPLETE_CALL_MATRIX`, `D7_D_FLOODING_ADVANTAGE`, `D7_D_LAYERED_ADVANTAGE`, `D7_D_SCHEDULE_DEPENDENT_MIXED`, `D7_D_SCHEDULE_NO_EXACT_DIFFERENCE`, `D7_D_SCHEDULE_EFFECT_INCONCLUSIVE`, where `D7_D_FLOODING_ADVANTAGE` requires at least two flooding-advantage strata and no layered-advantage stratum, `D7_D_LAYERED_ADVANTAGE` is the converse, `D7_D_SCHEDULE_DEPENDENT_MIXED` requires both advantage directions, and `D7_D_SCHEDULE_NO_EXACT_DIFFERENCE` requires identical exact flags on all 128 identities. Flooding certification F01–F08 SHALL PASS before readiness; failure SHALL stop as `D7_D_FLOODING_CERTIFICATION_FAIL` with a minimal counterexample preserved and no flooding patch.

#### Scenario: Terminal priority is exact
- **WHEN** several terminal conditions are simultaneously true
- **THEN** the first applicable terminal in the frozen order is selected.

#### Scenario: Certify before readiness
- **WHEN** any F01–F08 item fails
- **THEN** the certification gate stops D7-D readiness
- **AND** no D7-D scientific command may be prepared as ready.

### Requirement: Budgets and resource guards
The run SHALL enforce exactly 256 scientific calls on normal completion with a hard cap of 256, a 120 s per-call watchdog, stored scientific wall `<= 1500 s`, an outer `timeout -k 30 1800`, and current-process RSS `< 2 GiB` measured via stdlib `resource.getrusage(RUSAGE_SELF).ru_maxrss` with explicit Linux KiB→bytes conversion. RSS unavailable, nonpositive or nonfinite SHALL block before the first scientific call, as SHALL an invalid Model-F root or an existing target. `psutil` SHALL NOT be used. Zero retry/rerun/resume/concurrency.

#### Scenario: RSS preflight
- **WHEN** the RSS probe is unavailable, nonpositive or nonfinite
- **THEN** the run stops as `D7_D_PRE_EXECUTION_BLOCKED` with zero scientific calls.

#### Scenario: Watchdog fires
- **WHEN** a single call exceeds 120 s
- **THEN** the run stops as `D7_D_WATCHDOG_TIMEOUT_VOID` and no further call is attempted.

### Requirement: Seven-file scalar evidence root
The writer SHALL create exactly seven compact scalar files in a fresh
`workspace/d7_d_schedule_discriminator_<uuid>/` root with no subdirectories:
`manifest.json`, `decoder_records.csv`, `paired_schedule.csv`,
`stratum_summary.csv`, `summary.json`, `report.md`, `command_log.txt`. Per-call,
per-identity and per-stratum records SHALL contain the frozen scalar fields of
the design; no raw beliefs, symbols, priors, syndromes, block vectors or digests
SHALL be persisted. The writer SHALL refuse overwrite and create no root when
the target exists, is outside `workspace/` or does not match the frozen name
pattern.

#### Scenario: Root is fresh and closed
- **WHEN** the target exists, is outside `workspace/`, does not match the frozen name pattern or contains a subdirectory
- **THEN** the writer refuses before any call or overwrite.

#### Scenario: Exact evidence set
- **WHEN** a normal run completes
- **THEN** the root contains exactly the seven files and no others.

### Requirement: Verify mode independence
Verify mode SHALL read only the seven files and independently recompute pairing,
paired exact/syndrome counts, all eight stratum labels, work-normalized
arithmetic consistency and the run terminal; it SHALL never call a decoder and
never load Model-F.

#### Scenario: Tampered records are detected
- **WHEN** a record is missing, duplicated, unpaired or its scalar values are altered
- **THEN** verify fails with the affected identity or field.

#### Scenario: Verifier isolation
- **WHEN** verify mode runs
- **THEN** no decoder binding and no Model-F read occur.

### Requirement: Implementation isolation and authorization gating
Import, `--help`, `--dry-run` and unauthorized runs SHALL bind no decoder, read no Model-F and create no root. The implementation SHALL use lazy local-source package import (works from the WSL repo and an external cwd), dependency injection for joint tensor, blocks, matrices, dual decoders, clock and RSS, and a single sequential loop with no retry/resume/concurrency framework. The runner SHALL read the D7-D `cycle_state.yaml` and refuse while `d7d_execution_authorized` is false; authorization SHALL be consumed on the first decoder attempt. The implementation SHALL NOT import or depend on the future layer-interface rework.

#### Scenario: Unauthorized refusal
- **WHEN** the key is false
- **THEN** the runner refuses before any Model-F read, decoder bind or root creation.

#### Scenario: External-cwd bind
- **WHEN** the module/runner is imported from outside the repository with fake decoder sentinels
- **THEN** the local-source package bind reaches both exact decoder functions with zero real Model-F read and zero root creation.
