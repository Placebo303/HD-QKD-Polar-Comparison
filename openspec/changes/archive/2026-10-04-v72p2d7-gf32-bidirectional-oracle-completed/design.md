# D7-C bidirectional cross-layer oracle — design (R1 + A1)

## Constants (frozen)

- GF(2^5), q=32, poly 37. `n=64`. Block seeds `2026091300..2026091315`
  ascending. f order `[1.0, 1.2]`.
- `LAMBDA_STAR = 137.3823795883264`; `DECODER_FLOOR = 1e-15`;
  `MAX_ITER = 90`; `DAMPING_ALPHA = 1.0`; graph seeds L1 `2026090501`,
  L2 `2026090502`.
- Rows: L1 `{1.0: 49, 1.2: 59}`; L2 `{1.0: 43, 1.2: 52}`.
- Budgets: calls `<= 128` (exactly 128 normal), per-call watchdog 120 s,
  stored scientific wall `<= 1500 s`, outer `timeout -k 30 1800`, RSS
  `< 2 GiB`; zero retry/rerun/resume.
- Conditions (exact strings): `L1_MARGINAL`, `L1_ORACLE_U2`, `L2_MARGINAL`,
  `L2_ORACLE_U1`; call order per f/seed exactly that order.
- 11 run terminals in exact priority order (prereg §10); 4 stratum labels
  (`STRONG_ORACLE_LIFT`, `NO_ORACLE_RECOVERY`, `MARGINAL_ALREADY_RECOVERS`,
  `AMBIGUOUS_ORACLE_EFFECT`).

## Estimator trace (H03, recorded)

Accepted: `d5.prepare_model_f_prior_candidate(counts_ab, p_b)` →
`build_f_model_concentration` (D5 L274–305; L2323–2350), total-concentration
per Bob column. Rejected: `build_f_model` per-cell pseudocount (L246–271,
L265), the `LAMBDA_APPLICATION_CONTRACT_DEFECT`, R1 §3.1 exclusion. Lifecycle:
`G1_INFORMATION_RECOVERY_R2_ACCEPTANCE_R1.md` L13–19/L57–65; D6 prereg §4
L11–15. No STOP.

## Mother construction (frozen)

```text
L1: sup = d5.build_dv3_nested_support(64, 64, 49, 2026090501)
    H1  = d5.assign_gf32_coefficients(sup, 2026090501, None, 64)
L2: sup = d5.build_dv3_nested_support(64, 64, 43, 2026090502)
    H2  = d5.assign_gf32_coefficients(sup, 2026090502, None, 64)
```

Equals `d5.build_dv3_nested_mother(64, 64, k_min, seed, None)` (L669–672) and
the D6-frozen `B0_D5_DV3_NATIVE` construction (D6 `ROW_BUDGETS[64]` L32–36,
prereg L26–35/L50–54, code L612–614/L644–645). Built in memory; VOID roots
(`workspace/v72p2d5_g1/20260906_r1`,
`workspace/d6_graph_mother_r1_923a25897087495ab4605870e561f3cc`) are never
read. Disclosure = row prefix `H[:rows]`.

## Data flow (frozen order)

1. Parse args; `--help`/`--dry-run`/unauthorized exit with no decoder bind, no
   Model-F read, no root.
2. Preflight: cycle state authorized; out-root fresh direct child of
   `workspace/` named `d7_c_bidirectional_oracle_*`; RSS measured finite
   positive.
3. Load accepted Model-F (`--model-f-root` must equal
   `workspace/v72p2d5_model_f_input/20260907_r1`) via the D5 sibling loader;
   `(p_b, p_f) = d5.prepare_model_f_prior_candidate(counts_ab, p_b_cal)`.
4. Build `J = p_f.reshape(32, 32, 1024)`; sample 16 blocks once
   (`d5.sample_matched_block(p_b, p_f, 64, seed)`); build both mothers; freeze
   all 128 identity tuples in memory.
5. Loop the frozen call order; each call: build prior (four formulas, zero-mass
   uniform fallback), transpose, one `d5._floor_renorm(., 1e-15)`, syndrome via
   certified GF32 helper, write the target syndrome nowhere, one cold decode,
   recompute exact/syndrome, record scalar row; watchdog/RSS/nonfinite checks
   between calls.
6. Write six files; select stratum labels and run terminal by frozen rules.

No scientific call may begin before step 4 completes.

## Prior math (frozen)

`J[u1,u2,b] = P_F(32*u1+u2 | b)`, nonnegative, columns sum to 1.
Per position `i` with `b_i`, `u1_true_i`, `u2_true_i`:

- `L1_MARGINAL[:,i] = J[:,:,b_i].sum(axis=1)`
- `L1_ORACLE_U2[:,i] = J[:,u2_true_i,b_i] / J[:,u2_true_i,b_i].sum()` (if mass
  <= 0: uniform `1/32`)
- `L2_MARGINAL[:,i] = J[:,:,b_i].sum(axis=0)`
- `L2_ORACLE_U1[:,i] = J[u1_true_i,:,b_i] / J[u1_true_i,:,b_i].sum()` (if mass
  <= 0: uniform `1/32`)

Boundary: transpose only here; one `d5._floor_renorm(prior_qn.T, 1e-15)`.
Unit tests recompute every formula from a literal small joint tensor and
negative-control swapped U1/U2/B axes.

## Decoder boundary

`v35.decode_row_layered_fftqspa(H_prefix, prior_pq, syndrome, max_iter=90,
damping_alpha=1.0, warm_beliefs=None)`; accepted equivalent adapter
`d5.bind_historical_decoder()`. `exact = x_hat == x_true_layer`;
`syndrome_ok = decoder_reported AND syndrome(H_prefix, x_hat) == target`; never
conflated. `symbol_errors`, `unsatisfied_checks` independently recomputed.

## Evidence schema (six files, scalar-only, frozen field order)

- `decoder_records.csv` (128 rows normal): `call_idx, f, seed, condition,
  layer, rows, n, exact, syndrome_ok, iterations, status, finite,
  symbol_errors, unsatisfied_checks, wall_s, rss_bytes, belief_max_prob,
  belief_mean_true_p, belief_mean_entropy, beliefs_conditioned,
  current_belief_label`.
- `paired_summary.csv` (4 rows): `f, layer, marginal_condition,
  oracle_condition, marginal_exact_count, oracle_exact_count,
  oracle_only_count, marginal_only_count, both_exact_count,
  neither_exact_count, paired_syndrome_ok_count,
  paired_syndrome_disagreement_count, nonfinite_count, crash_count,
  marginal_median_iterations, oracle_median_iterations,
  marginal_max_iterations, oracle_max_iterations, marginal_median_wall_s,
  oracle_median_wall_s, marginal_max_wall_s, oracle_max_wall_s,
  stratum_label`.
- `manifest.json`: frozen run identities (cycle, plan revision, model root and
  input file names/sizes, estimator ID, lambda, n, f/rows/seeds, graph seeds,
  mother expressions, decoder ID/kwargs, call order, budgets, six-file list,
  terminal priority) plus run-time provenance (uuid, start/end UTC, PID,
  authorization consumed).
- `summary.json`: terminal, 4 stratum labels, totals (calls attempted and
  completed, nonfinite, crashes, watchdog timeouts), stored scientific wall,
  peak RSS bytes, retries/reruns/resumes = 0.
- `report.md`: compact scalar summary only.
- `command_log.txt`: exact command, start/end, scalar checkpoint lines.

No raw beliefs, symbols, priors, syndromes, block vectors or digests of them
are persisted. `belief_*` are scalar diagnostics; `current_belief_label` is
`PRIOR_ONLY_CURRENT_BELIEF` when `iterations == 0`, else
`CHECK_UPDATED_CURRENT_BELIEF`; "posterior"/"APP" never appear as labels and no
belief flows to another layer.

## Stratum / terminal rules

Exactly as prereg §10: first-match stratum classification in the listed order;
run terminal T1–T11 first-applicable; labels recorded even under a
higher-priority terminal; incomplete strata carry partial counts and an empty
label.

## Implementation shape

- New module `formal_ir/v72p2d7_gf32_bidirectional_oracle.py`: pure helpers
  (prior math, syndrome construction, answers/classification), six-file writer,
  verify mode, lazy local-source package bind, DI for joint tensor, blocks,
  matrices, decoder, clock and RSS; no retry/resume/concurrency framework;
  sequential single process.
- Lazy import: try `comparison_bench.formal_ir.*`; on `ModuleNotFoundError`,
  load the needed sibling modules by file path (D5/D6/D7-A/v35 precedents) so
  import works from the WSL repo and from an external cwd.
- `scripts/v72p2d7_gf32_bidirectional_oracle.py`: derive `<repo>` from resolved
  `__file__`, insert `<repo>/comparison_bench/src` into `sys.path` only if
  absent, then load the core; read the D7-C `cycle_state.yaml`; refuse
  unauthorized; consume authorization on first decoder attempt; no
  install/packaging/vendoring.
- Verifier (`--verify`): reads the six files only; recomputes schema, identity
  uniqueness (128), pair matching (marginal/oracle share rows/H/syndrome
  target/block/config), counts/outcomes, stratum labels and terminal; never
  binds the decoder, never loads Model-F.
- Fake qualification: DI fakes perform all 128 calls and exercise every
  terminal branch (T1–T11), all boundaries, prior formula negatives, schema and
  verifier detection of duplicate/missing/unpaired/tampered records.
- `ponytail:` one sequential loop, stdlib `resource` for RSS, stdlib
  csv/json/pathlib for I/O; no framework.

## Root contract

`workspace/d7_c_bidirectional_oracle_<uuid>/`: fresh, refuse overwrite, no
subdirectories, exactly the six files above. Out-root outside `workspace/`, or
not matching the frozen name pattern, or already existing → block before any
call.

## Frozen future command (not run)

```bash
timeout -k 30 1800 python scripts/v72p2d7_gf32_bidirectional_oracle.py --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d7_c_bidirectional_oracle_<uuid>
```

Pre-RESULT review mandatory before any result commit. Interface rework remains
out of scope and must not be imported; closeout records
`D7_C_FROZEN_AWAITING_EXPLICIT_AUTHORIZATION` and
`LAYER_INTERFACE_IMPLEMENTATION_DEFERRED_BEFORE_CROSS_LAYER_APP`.
