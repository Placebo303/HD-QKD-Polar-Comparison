# D7-D schedule discriminator — design (R1)

## Constants (frozen)

- GF(2^5), q=32, poly 37. `n=64`. Block seeds `2026091300..2026091315`
  ascending. f order `[1.0, 1.2]`.
- `LAMBDA_STAR = 137.3823795883264`; `DECODER_FLOOR = 1e-15`;
  `MAX_ITER = 90`; row-layered `DAMPING_ALPHA = 1.0`; graph seeds L1
  `2026090501`, L2 `2026090502`; L1 `k_min=49`, L2 `k_min=43`.
- Rows: L1 `{1.0: 49, 1.2: 59}`; L2 `{1.0: 43, 1.2: 52}`.
- Schedules in order `(ROW_LAYERED, FLOODING)`.
- Conditions (exact strings in call order): `L1_MARGINAL`, `L1_ORACLE_U2`,
  `L2_MARGINAL`, `L2_ORACLE_U1`.
- Budgets: calls `<= 256` (exactly 256 normal), per-call watchdog 120 s, stored
  scientific wall `<= 1500 s`, outer `timeout -k 30 1800`, RSS `< 2 GiB`; zero
  retry/rerun/resume/concurrency.
- 10 run terminals in exact priority order (prereg §9); 5 stratum labels
  (`FLOODING_EXACT_ADVANTAGE`, `LAYERED_EXACT_ADVANTAGE`, `EXACT_TIE_HIGH`,
  `EXACT_TIE_LOW`, `MIXED_SCHEDULE_EFFECT`); prerequisite terminal
  `D7_D_FLOODING_CERTIFICATION_FAIL` (certification gate only, not part of the
  ten-entry run priority).

## Schedule-only boundary

The only per-call delta is the schedule. All of the following are byte-identical
between the two calls of one identity: frozen Model-F root and loaded `counts_ab`
/ `p_b`; estimator `d5.prepare_model_f_prior_candidate` with `LAMBDA_STAR`;
`J = p_f.reshape(32, 32, 1024)`; generated block for the seed; `H_prefix`, row
count, syndrome target, truth and labels; the prior construction and the single
`d5._floor_renorm(..., 1e-15)` boundary; `max_iter=90`; cold start. Forbidden:
damping (other than row-layered `damping_alpha=1.0`), clipping, restart, min-sum,
warm start, graph changes, new priors, more disclosure, cross-layer feedback,
cross-layer APP.

## Decoder call shapes (frozen production signatures)

From `comparison_bench/src/comparison_bench/formal_ir/v35_algorithm_development.py`:

```text
L529: def decode_flooding_fftqspa(
L530:     h_matrix: np.ndarray,
L531:     priors: np.ndarray,
L532:     syndromes: np.ndarray,
L533:     max_iter: int = DEFAULT_MAX_ITER,   # DEFAULT_MAX_ITER = 30 (L60)
L534:     field: Optional[GF2mField] = None,
L535: ) -> DecoderResult

L636: def decode_row_layered_fftqspa(
L637:     h_matrix: np.ndarray,
L638:     priors: np.ndarray,
L639:     syndromes: np.ndarray,
L640:     max_iter: int = DEFAULT_MAX_ITER,
L641:     damping_alpha: float = 1.0,
L642:     warm_beliefs: Optional[np.ndarray] = None,
L643:     field: Optional[GF2mField] = None,
L644: ) -> DecoderResult
```

Frozen D7-D calls:

```text
ROW_LAYERED: v35.decode_row_layered_fftqspa(H_prefix, prior_pq, syndrome,
             max_iter=90, damping_alpha=1.0, warm_beliefs=None, field=None)
FLOODING:    v35.decode_flooding_fftqspa(H_prefix, prior_pq, syndrome,
             max_iter=90, field=None)
```

Flooding declares no `damping_alpha` and no `warm_beliefs`; D7-D must not invent
one, must not pass damping, and must not use `DEFAULT_MAX_ITER=30`. Each decoder
retains its own normal internal stopping (e.g. a cold initial syndrome match
returns `iterations=0`, status `converged_exact`); there is no cross-schedule or
cross-identity early stop.

## Reuse contract

The D7-D module SHALL reuse the D7-C frozen identities/priors/mothers/estimator
through a narrow imported helper from
`comparison_bench/src/comparison_bench/formal_ir/v72p2d7_gf32_bidirectional_oracle.py`
or as an exact contract copy. Tests SHALL confirm equality against the D7-C
module for: seeds `2026091300..2026091315`; f `[1.0,1.2]`; rows 49/59/43/52;
conditions and their layers; `LAMBDA_STAR`; `DECODER_FLOOR`; `MAX_ITER=90`;
graph seeds 2026090501/2026090502; the four prior formulas; and current-belief
labels. D7-C and all previous production modules are read-only and SHALL NOT be
modified. If the D7-C module is imported, it is import-only: no D7-C writer,
decoder, Model-F load or root is reachable from the D7-D path.

## Data flow (frozen order)

1. Parse args; `--help`/`--dry-run`/unauthorized exit with no decoder bind, no
   Model-F read, no root.
2. Preflight: cycle_state `d7d_execution_authorized` true; out-root fresh direct
   child of `workspace/` named `d7_d_schedule_discriminator_<uuid>`; accepted
   `--model-f-root`; RSS measured finite positive.
3. Load accepted Model-F via the D5 sibling loader;
   `(p_b, p_f) = d5.prepare_model_f_prior_candidate(counts_ab, p_b_cal)`.
4. Build `J`; sample 16 blocks once per seed; build both mothers; freeze all 128
   identity tuples `(f, seed, condition, layer, rows, n=64)` in memory.
5. Loop the frozen 256-call order. Per identity: build the prior (same formula
   as D7-C), transpose, one `d5._floor_renorm(..., 1e-15)`, compute the target
   syndrome via the certified GF32 helper, then dispatch `ROW_LAYERED` then
   `FLOODING` with the same `H_prefix`, prior, syndrome and config; recompute
   exact/syndrome; record two scalar rows; watchdog/RSS/nonfinite checks between
   calls.
6. Write the seven files; select the five-label classification for each of the
   eight strata and the run terminal by the frozen rules.

No scientific call may begin before step 4 completes.

## Call matrix and order (frozen)

128 identities in D7-C original order (identity `k`, `k=1..128`):

```text
for f in [1.0, 1.2]:
  for seed in 2026091300 .. 2026091315 (ascending):
    for condition in [L1_MARGINAL, L1_ORACLE_U2, L2_MARGINAL, L2_ORACLE_U1]:
      ROW_LAYERED   # call 2k-1
      FLOODING      # call 2k
```

Exactly 256 calls on normal completion; hard cap 256; every call attempted
exactly once unless a higher-priority run stop occurs; no replacement cell; no
success-based early stop. `call_idx` is `2*identity_idx - 1` for `ROW_LAYERED`
and `2*identity_idx` for `FLOODING`.

## Work-normalized metrics (frozen definitions)

Iteration counts alone are not comparable. Per call, persist:

- `schedule, f, seed, condition, layer, rows, n`;
- `exact` (`x_hat == x_true_layer`), `syndrome_ok` (decoder-reported AND
  independently recomputed `syndrome(H_prefix, x_hat) == target`), `iterations`
  (completed check sweeps as returned), `status`, `finite`;
- `symbol_errors = count(x_hat != x_true_layer)`; `unsatisfied_checks =
  count(syndrome(H_prefix, x_hat) != target)`;
- `wall_s`, `rss_bytes`;
- `check_node_updates = rows * completed_iterations`; iteration-0 is explicitly
  zero; `completed_iterations` is the decoder-returned completed sweep count;
- `check_edge_updates = (sum over disclosed rows r of nnz(H_prefix[r])) *
  completed_iterations`, using the frozen matrix row degrees computed in memory;
  iteration-0 is explicitly zero;
- current-belief confidence/entropy from `softmax(final_beliefs)`:
  `belief_max_prob`, `belief_mean_true_p` (at the true layer symbol),
  `belief_mean_entropy` (bits), `beliefs_conditioned = (iterations > 0)`,
  `current_belief_label` exactly `PRIOR_ONLY_CURRENT_BELIEF` when
  `iterations == 0` else `CHECK_UPDATED_CURRENT_BELIEF`. The label is a
  provenance label; the confidence/entropy fields SHALL NOT be called
  "posterior" or "APP" unless independently established, which this packet does
  not establish.

Per identity (128 rows), paired:

- `layered_exact`, `flooding_exact`;
- `layered_only_exact`, `flooding_only_exact`, `both_exact`, `neither_exact`;
- separate syndrome-only analogues: `layered_only_syndrome_ok`,
  `flooding_only_syndrome_ok`, `both_syndrome_ok`, `neither_syndrome_ok`;
- `iteration_diff = flooding_iterations - layered_iterations`,
  `check_update_diff`, `edge_update_diff`, recorded only when both calls are
  complete and finite, else empty;
- `wall_ratio = flooding_wall_s / layered_wall_s` recorded only when both walls
  are finite and the layered wall is positive (denominators valid), else empty;
- no winner is ever inferred from iteration count alone.

## Stratum classification (frozen, first match in this order)

Per `(f,layer,condition)` stratum of 16 blocks × 2 schedules = 32 calls; 8
strata (2 f × 4 conditions):

1. `FLOODING_EXACT_ADVANTAGE`: `flooding_only_exact >= 4` AND
   `layered_only_exact <= 1`.
2. `LAYERED_EXACT_ADVANTAGE`: `layered_only_exact >= 4` AND
   `flooding_only_exact <= 1`.
3. `EXACT_TIE_HIGH`: `both_exact >= 12` AND `flooding_only_exact <= 1` AND
   `layered_only_exact <= 1`.
4. `EXACT_TIE_LOW`: `neither_exact >= 12` AND `flooding_only_exact <= 1` AND
   `layered_only_exact <= 1`.
5. `MIXED_SCHEDULE_EFFECT`: otherwise.

The listed order is the frozen first-match order; a stratum satisfying an
earlier rule is not relabeled. Thresholds are route discriminators, not
success-rate or FER estimates. A stratum label is assigned only when all 32 of
its calls completed; an incomplete stratum records partial counts and an empty
label (never a fabricated one).

## Run terminals (frozen, exact priority; first applicable wins)

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

All eight stratum labels are reported even under a higher-priority terminal.
The separate certification gate terminal `D7_D_FLOODING_CERTIFICATION_FAIL`
stops readiness before this priority list can ever apply.

## Budgets / resource guards

- exactly 256 scientific calls on normal completion; hard cap 256;
- per-call watchdog 120 s (exceeded → `D7_D_WATCHDOG_TIMEOUT_VOID`, stop);
- stored scientific wall `<= 1500 s` (exceeded → resource overrun);
- GNU outer `timeout -k 30 1800` (30 s kill grace);
- WSL current-process RSS via stdlib
  `resource.getrusage(resource.RUSAGE_SELF).ru_maxrss`, explicit Linux KiB→bytes
  (`* 1024`), finite and positive; `< 2 GiB` (`2 * 1024**3`); no psutil;
- fail before the first call if RSS is unavailable/nonpositive/nonfinite,
  Model-F root is absent/invalid or the target exists;
- zero retry/rerun/resume/concurrency; sequential single process.

## Evidence schema (seven files, scalar-only, frozen field order)

- `decoder_records.csv` (256 rows normal): `call_idx, identity_idx, schedule, f,
  seed, condition, layer, rows, n, exact, syndrome_ok, iterations, status,
  finite, symbol_errors, unsatisfied_checks, wall_s, rss_bytes,
  check_node_updates, check_edge_updates, belief_max_prob, belief_mean_true_p,
  belief_mean_entropy, beliefs_conditioned, current_belief_label`.
- `paired_schedule.csv` (128 rows): `identity_idx, f, seed, condition, layer,
  rows, n, layered_exact, flooding_exact, layered_only_exact,
  flooding_only_exact, both_exact, neither_exact, layered_syndrome_ok,
  flooding_syndrome_ok, layered_only_syndrome_ok, flooding_only_syndrome_ok,
  both_syndrome_ok, neither_syndrome_ok, iteration_diff, check_update_diff,
  edge_update_diff, wall_ratio`.
- `stratum_summary.csv` (8 rows): `stratum_idx, f, layer, condition, blocks,
  layered_exact_count, flooding_exact_count, layered_only_exact_count,
  flooding_only_exact_count, both_exact_count, neither_exact_count,
  layered_syndrome_ok_count, flooding_syndrome_ok_count,
  layered_only_syndrome_ok_count, flooding_only_syndrome_ok_count,
  both_syndrome_ok_count, neither_syndrome_ok_count, nonfinite_count,
  crash_count, layered_median_iterations, flooding_median_iterations,
  layered_median_check_updates, flooding_median_check_updates,
  layered_median_edge_updates, flooding_median_edge_updates,
  layered_median_wall_s, flooding_median_wall_s, stratum_label`.
- `manifest.json`: frozen run identities (cycle, plan revision, model root and
  input file names/sizes, estimator ID, lambda, n, f/rows/seeds, graph seeds,
  schedule order, call order, decoder IDs/kwargs, budgets, seven-file list,
  terminal priority) plus run-time provenance (uuid, start/end UTC, PID,
  authorization consumed).
- `summary.json`: terminal, 8 stratum labels, totals (calls attempted and
  completed, nonfinite, crashes, watchdog timeouts), stored scientific wall,
  peak RSS bytes, retries/reruns/resumes = 0.
- `report.md`: compact scalar summary only.
- `command_log.txt`: exact command, start/end, scalar checkpoint lines.

No raw beliefs, symbols, priors, syndromes, block vectors or digests of them are
persisted. `belief_*` fields are scalar diagnostics only.

## Implementation shape

- New module `formal_ir/v72p2d7_gf32_schedule_discriminator.py`: pure helpers
  (prior math reuse, syndrome construction, pairing, classification), seven-file
  writer, verify mode, lazy local-source package bind, DI for joint tensor,
  blocks, matrices, decoders, clock and RSS; no retry/resume/concurrency
  framework; sequential single process.
- Lazy import: try `comparison_bench.formal_ir.*`; on `ModuleNotFoundError`, load
  the needed sibling modules by file path (D7-C and v35/D5 precedents) so import
  works from the WSL repo and from an external cwd.
- `scripts/v72p2d7_gf32_schedule_discriminator.py`: derive `<repo>` from
  resolved `__file__`, insert `<repo>/comparison_bench/src` into `sys.path` only
  if absent, then load the core; read the D7-D `cycle_state.yaml`; refuse
  unauthorized; consume authorization on the first decoder attempt; no
  install/packaging/vendoring.
- Verifier (`--verify`): reads the seven files only; independently recomputes
  pairing, paired counts/outcomes, all eight stratum labels and the run terminal
  from scalars; never binds a decoder and never loads Model-F. It detects
  missing/duplicate/unpaired/tampered records.
- Fake qualification: DI fakes perform all 256 calls and exercise every terminal
  branch, both classification directions, tie boundaries, prior negatives,
  schema and verifier detection.
- `ponytail:` one sequential loop, stdlib `resource` for RSS, stdlib
  csv/json/pathlib for I/O; no framework.

## Root contract

`workspace/d7_d_schedule_discriminator_<uuid>/`: fresh, refuse overwrite, no
subdirectories, exactly the seven files above. Out-root outside `workspace/`, not
matching the frozen name pattern, or already existing → block before any call
(`D7_D_PRE_EXECUTION_BLOCKED`).

## Pre-EXECUTE / Pre-RESULT gates

- Readiness requires F01–F08 PASS, S01–S22 PASS, independent implementation
  review `D7_D_IMPLEMENTATION_REVIEW_PASS` and independent Pre-EXECUTE review
  `D7_D_PRE_EXECUTE_REVIEW_PASS_AWAITING_EXPLICIT_AUTHORIZATION`; closeout gate
  `D7_D_FROZEN_AWAITING_EXPLICIT_AUTHORIZATION`; all authorization false; no
  UUID; no root.
- A future Pre-RESULT review is mandatory before any `OPERATOR_RETURN.md` /
  `RESULT_SUMMARY.md` / `run_01` solidification: re-check exact 256 matrix and
  order, schedule-only inputs, work-normalized arithmetic, `exact`/syndrome
  isolation, eight strata, terminal replay and seven-file schema against the
  actual files.

## Frozen future command (not run)

```bash
timeout -k 30 1800 python scripts/v72p2d7_gf32_schedule_discriminator.py --model-f-root workspace/v72p2d5_model_f_input/20260907_r1 --out-root workspace/d7_d_schedule_discriminator_<uuid>
```

Cross-layer interface implementation remains
`DEFERRED_MANDATORY_BEFORE_CROSS_LAYER_APP` and D7-D does not depend on it.
