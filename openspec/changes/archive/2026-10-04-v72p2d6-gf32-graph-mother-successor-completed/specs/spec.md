# Spec — v72p2d6-gf32-graph-mother-successor (delta)

## R1 Frozen scientific controls

- SHALL keep decomposition `A = 32*U1 + U2`, the accepted E2
  total-concentration/backoff CAL-only prior, GF32 poly-37 arithmetic, the
  historical row-layered FFT-QSPA decoder (cold start, `max_iter=90`,
  `damping=1.0`), L1-then-APP-L2 schedule with oracle-L2 diagnostic only.
- SHALL use row budgets n=64 `(49,43)/(59,52)/(64,64)`, n=128
  `(98,86)/(118,104)/(128,128)`, n=256 `(196,172)/(236,208)/(256,256)`.
- SHALL define exact as full reconstructed Alice equality (`u1` and `u2`
  exact); syndrome SHALL remain separate and never upgrade exact.
- SHALL generate samples once per `(n, block_seed)` and reuse them
  byte-identically across arms.

## R2 Arm family (only axis: graph/mother)

- SHALL implement exactly `B0_D5_DV3_NATIVE`, `B1_D5_DV3_COMMON_LABELS`,
  `T1_PEG_DV3`, `T2_CYCLE_GREEDY_DV3`, `T3_SC_DV3_W4`, `T4_SC_DV3_W8`,
  `M1_ACCUMULATOR_FOREST_MAX`, `M2_ACCUMULATOR_FOREST_HALF`; SHALL NOT add any
  topology, degree distribution, window, or parameter.
- SHALL keep degree-3 coefficient triples identical by `(n, layer, column)`
  across B1/T/M via seeds L1 `202609120100 + n`, L2 `202609120200 + n`;
  degree-2 columns SHALL use the first two entries; SHALL NOT select
  coefficients against decoder outcomes.
- SHALL build every arm deterministically with lexicographic tie-breaks;
  SHALL NOT search graph, block, coefficient, row, estimator, damping,
  schedule, iteration, or decomposition parameters.
- SHALL place M degree-2 supports as a simple forest over the first `k_min`
  checks at every relevant prefix (`N2 = k_min - 1` MAX,
  `floor((k_min - 1) / 2)` HALF), degree-3 variables as 2 base + 1 expansion.

## R3 Structural gates and blind selection

- SHALL record per `(arm, n, layer, prefix)`: rank, zero rows/columns,
  components + largest variable fraction, degree histograms/maxima, duplicate
  and proportional columns, exact 4-cycle count + variable incidence max,
  girth or `NOT_COMPUTED` with reason, M degree-2 cycle rank, replay
  equality, row-degree max/sumsq.
- SHALL admit to decoding only arms passing every hard gate (shape + nonzero
  GF32; rank = rows; zero rows/cols 0; single component incl. all variables;
  duplicate/proportional 0; no parallel edge; M cycle rank 0); SHALL freeze
  B0 + B1 + best two eligible T (by `(four_cycles, incidence_max, -girth,
  row_max, sumsq, arm_id)`) + both eligible M (no substitution, max 6 arms)
  plus two preregistered fallbacks (best T + best M) before any decoder call.

## R4 Bounded execution

- SHALL use seeds canary `2026091000..03`, confirmation `2026091010..25`,
  scaling `2026091100..03` only; SHALL invoke each cell once with no retry.
- SHALL advance (max 2, new T/M arms only) on canary f1.2 APP exact ≥ 1/4 by
  the frozen ordering; SHALL run confirmation 16-seed f1.0/f1.2/square with
  strong ≥ 12/16 and partial 1..11/16 under identical safety conditions
  (monotone f1.0 ≤ f1.2 ≤ square, zero crash/nonfinite, zero APP
  exact/syndrome disagreement, known RSS < 2 GiB).
- SHALL run scaling only after total n=64 no-signal, fallbacks first at
  n=128 then n=256, stopping at the first signaling width with ≤ 2 arms
  confirmed under the same rules (SCALING + width labels).
- SHALL respect 2500 calls / 12 h wall / 120 s per-call watchdog / RSS < 2 GiB
  and stop before exceeding call/wall budgets; SHALL own and record every
  launched process.

## R5 Evidence, reviews, isolation

- SHALL write scalar/metadata-only evidence (`manifest.json`,
  `structure_records.csv`, `selected_arms.json`, `decoder_records.csv`,
  `summary.json`, `command_log.txt` + scalar-ID provenance) under one fresh
  `workspace/d6_graph_mother_r1_<uuid>/`; SHALL independently recompute
  coverage/counts/separation/extrema/advancement/classification from scalars.
- SHALL obtain implementation-review PASS then Pre-EXECUTE PASS before the
  first decoder call (max two cycles, then BLOCKER), and Pre-RESULT PASS
  before result solidification; reviewers SHALL NOT edit files; post-call
  fixes SHALL be limited to evidence/report arithmetic.
- SHALL NOT invoke any CLI `--phase`, formal G1/G2, VAL, real/raw data, or
  parquet (prior only from the explicit Model-F root); SHALL NOT read
  VOID-G1 contents; SHALL NOT create `workspace/v72p2d5_g2*`; SHALL NOT
  modify D5 production wiring/constants/results/authorizations, formal roots,
  or `src/`/`experiments/`/`tools/`; SHALL NOT push or rewrite history.

## R6 Check-degree invariant I1 (R1c-A5, fail-closed, zero decoder)

- SHALL compute per `(arm,n,layer,prefix)` `row_degree_min` /
  `rows_below_degree_2` in D6 `audit_extra` (no D5 edits) and expose them.
- SHALL admit to decoding only arms with frozen R3 gates AND
  `row_degree_min >= 2` at every dispatched prefix of every width/layer.
- SHALL fail closed at build time (violating dispatched prefix =>
  structurally ineligible, never dispatchable) and at dispatch time (no
  decoder cell from a violating matrix; clear error).
- SHALL recompute I1 independently in `--verify` over
  `structure_records.csv` (INFO for the historical root predating the gate;
  PASS/FAIL for post-packet roots) without rewriting the historical root.
- SHALL keep production `build_support` byte-identical in this packet; repair
  candidates live sandbox-only. If no R1-R5 rule exists, SHALL record
  `STRUCTURALLY_INFEASIBLE_AS_FROZEN` + proof + <=3 redefinition menu marked
  `REQUIRES_MAIN_THREAD_RULING` without landing it.
- SHALL force any attempted non-placeholder crash/nonfinite cell to
  `D6_GRAPH_STRUCTURE_INVARIANT_BLOCKED` (degree) or
  `D6_GRAPH_ATTEMPTED_CELL_INVALID` (other), overriding recovery labels;
  `call_idx=-1` placeholders never count.
- SHALL NOT persist a new six-file schema in this packet; schema changes are
  proposed (approval-required) in the R1d readiness package only.

## R7 Exact-equivalent T2 acceleration (R1c-A6, zero decoder)

- SHALL NOT change the T2 choice key, field order, tie-breaks, candidate set,
  or greedy order; SHALL NOT float-approximate the integer key; SHALL NOT use
  an unproven shortlist or decoder-chosen speedup.
- SHALL prove exact equivalence (support equality 8x2x3; per-variable trace;
  committed n64 byte-identical; ordering/eligibility/selected unchanged;
  replay equal; seq==par; two-builds + pruning intact; sandbox-T2 re-run if
  applicable) before any speedup claim.
- SHALL meet T2/layer n64<=5s / n128<=90s / n256<=600s, n64 all-8<=8s, non-T2
  <=10%, scaling fb-only within 2x of A4 after-side, RSS<2GiB, zero decoder;
  else SHALL return `PERF_TARGET_NOT_MET` with profile evidence and keep the
  reference path intact.
