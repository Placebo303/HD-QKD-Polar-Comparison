# OpenSpec Design: formal-ir-v39-lanec-robustness-laneb-control

**Lifecycle**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`
**Cycle**: `V39P0`
**Predecessor**: V38R1, terminal `V38_MULTIPLE_ROUTE_SIGNALS`, accepted result
`2416486f724f4fb7cbf1058d9dc1bb1fc5ded5ed`, independent acceptance commit
`c8c5cd2e`, accepted implementation `8f7bc7d8d7366772ff425528cd1080fa67ef7509`.

## 1. Scientific question and hypotheses

- **Q (single)**: Does the Lane C strong signal from V38R1 reproduce across
  construction seeds and new development blocks, with Lane B as the
  pre-registered structural control?
- H1 (robustness): Lane C exact-L2 success stays high across all nine
  construction seeds and the 15 new blocks (Gate C1).
- H2 (control robustness): Lane B behaves as a genuine comparison route under
  identical criteria (Gate B1); identical thresholds prevent rigging the
  control.
- H3 (advantage): Lane C holds a paired, per-source-safe advantage over Lane B
  (Gate CB), and both routes beat the same-block frozen V31 baseline in
  direction terms (Gate BASE).

## 2. Frozen routes, matrices, seeds

Accepted constructors are reused unchanged from the accepted V38R1 module
`comparison_bench/src/comparison_bench/formal_ir/v38_architecture_triage.py`:
`construct_lane_b_prototype(source, seed, field)` and
`construct_lane_c_prototype(source, seed, field)`. No constructor logic is
modified. Lane A constructors are not invoked anywhere in V39.

Construction-seed registry (identical to the pre-registered V38 registry;
ordinal = position in each ordered list):

| lane | source | ordinal 1 | ordinal 2 | ordinal 3 |
|---|---|---|---|---|
| lane_c | 1M | 383101 | 383102 | 383103 |
| lane_c | 1p5M | 383201 | 383202 | 383203 |
| lane_c | 2M | 383301 | 383302 | 383303 |
| lane_b | 1M | 382101 | 382102 | 382103 |
| lane_b | 1p5M | 382201 | 382202 | 382203 |
| lane_b | 2M | 382301 | 382302 | 382303 |

Pairing rule: Lane C and Lane B are paired by `(source, construction_seed
ordinal)`; blocks are paired by `(source, block_seed)`. All nine seeds per
lane are used. Selecting only the V38 winner seed, or re-selecting seeds by
any decoder metric, is prohibited.

Matrix identity: `matrix_id = f"{lane}_{source}_s{construction_seed}"`.

## 3. Structural reconstruction protocol

All 18 matrices (2 lanes x 3 sources x 3 seeds) are deterministically
reconstructed by the accepted constructors and frozen seeds. The structural
authority is the committed V38P0 run_01 file
`comparison_bench/outputs_comparison/formal_ir_methods/v38_architecture_triage/run_01/v38_structural_prototypes.json`
(exactly 27 records; the lane_b/lane_c subset is exactly 18 records). Every
reconstruction is strictly compared against its committed record on all
committed metric keys, including shape, GF(32) rank, support edge count,
column/row degree statistics, cycle counts, algebraic degeneracy counts, and,
for every Lane C matrix, the frozen `position_permutations`. Any mismatch is
integrity failure I1. The ignored local `v38_winning_matrices.npz` must never
be read or written.

Structural reconstruction is decoder-free and does not count against the
decoder-call budget.

## 4. New development blocks

New fixed block seeds, non-overlapping with all V36/V38 block seeds:

| source | block seeds |
|---|---|
| 1M | 390101, 390102, 390103, 390104, 390105 |
| 1p5M | 390201, 390202, 390203, 390204, 390205 |
| 2M | 390301, 390302, 390303, 390304, 390305 |

Sampling semantics are identical to V36/V38: for each evaluation,
`idx, alice, bob = sample_empirical_block(counts, seed=block_seed, size=1024)`
with source-specific V25 TRAIN empirical counts (`load_v25_channel_counts()`),
then `u1_alice, u2_alice, u1_bob, u2_bob = factorize_f03(alice, bob)`.
Because sampling depends only on `(counts, block_seed)`, the same
`(source, block_seed)` yields identical `(alice, bob)` for Lane C, Lane B, and
the baseline, which is what makes pairing valid. `errors_initial` must be
identical across lanes/baseline for a given `(source, block_seed)`; any
deviation is integrity failure.

These remain development samples drawn from V25 TRAIN empirical counts with
oracle-L1 conditioning. They are NOT newly acquired real frames, NOT holdout
qualification data, and support no real-frame FER/threshold/SKR claim.

## 5. Posterior contract and binding preflight

The posterior call is exactly:

```python
prior = get_conditional_posterior_l2(counts, bob, u1_alice)
```

with complete Bob symbols (values may exceed 31). Passing `u2_bob` is the
exact root cause that invalidated V38P0 and is forbidden.

A mandatory decoder-free posterior-binding preflight SHALL run before any
authorized execution and again inside the guarded runner before the first
decoder call:

- P-BIND-1: wrap or capture the second argument of
  `get_conditional_posterior_l2` on one probe block per source (probe block =
  first new seed of that source: 390101 / 390201 / 390301) and assert the
  forwarded array equals the complete `bob` array element-for-element.
- P-BIND-2: on each probe block, assert that the complete-`bob` prior differs
  materially from the `u2_bob` prior (the V38P0 wrong path), and that the
  corrected call path equals the direct V36-style complete-Bob call
  element-for-element.
- P-BIND-3: assert no production decoder call occurs during preflight and no
  output artifact is written.

Preflight failure blocks authorization and execution; nothing is rerun or
repaired ad hoc.

## 6. Frozen decoder contract

- Field: GF(32), primitive polynomial 37 (`GF2mField.create(32)`).
- Decoder: row-layered FFT-QSPA
  (`decode_row_layered_fftqspa(H, prior, syn_true, max_iter=30,
  damping_alpha=1.0, field=field)`).
- `max_iter = 30`; `damping_alpha = 1.0`; no warm start; no iteration-cap
  increase; no damping search.
- Syndrome input computed from the true `u2_alice` as in V38R1.
- Success metric: `exact_l2 = bool(np.array_equal(x_hat, u2_alice))`.
  This is the ONLY success criterion for gates.
- `syndrome_ok` reported separately; `wrong_codeword =
  syndrome_ok and not exact_l2` counted separately and NEVER counted as
  exact recovery.
- No rerun, no seed change after failure, no post-result threshold edits.

## 7. Same-block V31 baseline

The V38 committed baseline numbers were computed on the OLD block seeds and
must not be reused. On the 15 NEW blocks the frozen V31 baseline is recomputed
exactly once per block:

- matrices: `load_v31_qc_baseline_matrices()` (frozen QC-cyclic-projective L2
  packet), the corresponding source matrix per call;
- posterior/decoder/iteration settings identical to lanes B/C;
- exactly 15 decoder calls total (3 sources x 5 blocks);
- one immutable baseline record per `(source, block_seed)`;
- lane-vs-baseline comparisons join each lane record to the SINGLE baseline
  record of the same block. Replicating a baseline record three times to pair
  with three construction seeds, thereby fabricating 45 independent baseline
  observations, is prohibited and is integrity failure I5.

## 8. Workload accounting (frozen)

| cell | calls |
|---|---:|
| Lane C: 3 sources x 3 construction seeds x 5 blocks | 45 |
| Lane B: 3 sources x 3 construction seeds x 5 blocks | 45 |
| V31 baseline: 3 sources x 5 blocks | 15 |
| Total production decoder calls | 105 |

Exactly one authorized run produces all 105 calls. Structural reconstruction
and preflight perform zero decoder calls.

## 9. Record schemas

Lane record (every Lane C and Lane B decoder call):

```
lane, source, construction_seed, construction_seed_ordinal, block_seed,
matrix_id, errors_initial, errors_final, exact_l2, syndrome_ok,
wrong_codeword, iterations, status, runtime_s
```

Baseline record: same fields with `lane="v31_baseline"`,
`construction_seed=null`, `construction_seed_ordinal=null`,
`matrix_id="v31_baseline_<source>"`.

`wrong_codeword` is derived as `syndrome_ok and not exact_l2` at record level.

## 10. Aggregation levels (all mandatory)

1. lane overall: 45 records per lane;
2. lane/source: 15 records per group (6 groups);
3. lane/construction-seed ordinal: 15 records per group (6 groups);
4. lane/source/construction seed: 5 records per group (18 groups);
5. V31 baseline: overall (15) and per source (5);
6. Lane C vs Lane B paired discordance over the 45 `(source, ordinal,
   block)`-matched pairs;
7. per lane construction seed vs the single V31 baseline on the same blocks:
   9 groups per lane of 5-vs-5 joined records (baseline never duplicated).

Each aggregate reports: n, exact_l2 count/proportion, Wilson 95% interval,
median/mean errors_final, median/mean iterations, runtime totals, and
wrong-codeword counts where applicable.

## 11. Frozen gates

### Gate C1 — Lane C cross-seed robustness (`C_ROBUST_SIGNAL`)

ALL of:
- overall exact_l2 >= 36/45;
- every source exact_l2 >= 12/15;
- every construction-seed ordinal exact_l2 >= 12/15;
- overall median errors_final == 0;
- every source median errors_final == 0;
- wrong_codeword_count reported separately, never counted as exact.

### Gate B1 — Lane B cross-seed robustness (`B_ROBUST_SIGNAL`)

Identical thresholds to Gate C1 (same numbers, lane_b records). The control
route is never held to a lower bar.

### Gate CB — Lane C advantage over Lane B (`C_ADVANTAGE_OVER_B`)

ALL of:
- CB-a: `exact_count_C >= exact_count_B + 5`;
- CB-b: over the 45 pairs matched by `(source, ordinal, block)`:
  `d_CB > d_BC`, where `d_CB = #{C exact and B not exact}` and
  `d_BC = #{B exact and C not exact}`;
- CB-c: no source where `exact_count_C(source) < exact_count_B(source) - 1`
  (C may trail B by at most one exact recovery per source);
- CB-d: overall median errors_final(C) <= overall median errors_final(B).

McNemar exact p-value and Wilson intervals are descriptive statistics only
and never replace these frozen gates.

### Gate BASE — direction signal vs same-block V31 baseline (per lane)

For a given lane, ALL of:
- `exact_count_lane > exact_count_V31(same 15 blocks)`;
- overall median errors_final(lane) < overall median errors_final(V31);
- every source median errors_final(lane) <= median errors_final(V31 of that
  source).

BASE-C PASS is required for terminal state 1; BASE-B is evaluated and
reported but does not drive a terminal state by itself.

## 12. Terminal-state machine

Evaluation order is deterministic; the first matching rule wins:

0. Any integrity failure (Section 14) -> `V39_EVIDENCE_INVALID`
   (overrides everything; write `v39_invalid_notice.json`; no performance
   interpretation).
1. C1 PASS and CB PASS and BASE-C PASS -> `V39_C_ROBUST_AND_ADVANTAGE`.
2. C1 PASS and CB FAIL and B1 FAIL -> `V39_C_ROBUST_NO_B_ADVANTAGE`
   (Lane B is retained regardless; no premature elimination).
3. C1 PASS and CB FAIL and B1 PASS -> `V39_BOTH_ROUTES_ROBUST`
   (both survive; next cycle plans a matched structural mechanism test).
4. C1 FAIL and B1 PASS -> `V39_B_ONLY_ROBUST`.
5. C1 FAIL and B1 FAIL, with both lanes fully validly evaluated ->
   `V39_NO_ROBUST_ROUTE_SIGNAL`.

Edge case: C1 PASS and CB PASS but BASE-C FAIL falls through rules 2/3 by B1
status and is reported explicitly. Rule precedence and this edge case are
flagged for independent plan review (see Section 19).

## 13. Statistics plan (descriptive only)

- Exact counts and proportions at every aggregation level.
- Wilson 95% score intervals (z = 1.959963984540054).
- Paired discordance table (d_CB, d_BC, concordant-exact, concordant-fail)
  over the 45 matched C/B pairs.
- McNemar exact test on the discordant counts, two-sided, descriptive only.
- Residual mean/median per level; iteration mean/median/max; runtime
  totals/means per lane and level; wrong-codeword counts everywhere.
- Source/seed sensitivity narrative grounded only in the recorded aggregates.

Forbidden interpretations: FER, asymptotic threshold, SKR, security,
formal qualification, promotion, "real independent experiment frames", or any
claim derived from syndrome success instead of `exact_l2`.

## 14. Integrity checks (any failure -> `V39_EVIDENCE_INVALID`)

| id | check |
|---|---|
| I1 | any of the 18 reconstructions drifts from committed run_01 metrics |
| I2 | structural authority missing or != 27 records |
| I3 | block-seed registry drift, duplicate, or overlap with V36 seeds |
| I4 | posterior-binding preflight failure |
| I5 | baseline duplication or != 15 baseline records/calls |
| I6 | total calls != 105 or any cell count wrong |
| I7 | record schema violation or missing field |
| I8 | pairing incompleteness (45 C/B pairs; baseline joins) |
| I9 | output root already exists (fail closed, no overwrite) |
| I10 | any NPZ dependency detected |
| I11 | decoder parameters differ from frozen contract (incl. warm start) |

On failure: retain collected evidence unchanged, write
`v39_invalid_notice.json` plus summary with terminal
`V39_EVIDENCE_INVALID`, and stop without performance interpretation.

## 15. Evidence writer and additive output root

Fixed future additive root (created only by the authorized run):

```
comparison_bench/outputs_comparison/formal_ir_methods/v39_lanec_robustness_laneb_control/run_01/
```

Files:

- `v39_structural_reconstruction.json` / `.csv` (18 records + match verdicts)
- `v39_block_records.json` / `.csv` (90 lane records)
- `v39_baseline_records.json` / `.csv` (15 records)
- `v39_paired_comparison.json` / `.csv` (45 C/B pairs + baseline joins +
  gate inputs)
- `v39_summary.json` (accounting, gates, terminal state, statistics, claim
  boundary, provenance SHAs)
- `v39_invalid_notice.json` (only when integrity fails)

No NPZ is written or read. CSV/JSON row parity required. Existing
`results/` and other official outputs are untouched.

## 16. Implementation sketch (future rounds, unauthorized now)

- New module
  `comparison_bench/src/comparison_bench/formal_ir/v39_lanec_robustness_laneb_control.py`:
  reuses `construct_lane_b_prototype`, `construct_lane_c_prototype`,
  `evaluate_single_block`, `sample_empirical_block`, `factorize_f03`,
  `get_conditional_posterior_l2`, `load_v25_channel_counts`,
  `load_v31_qc_baseline_matrices` from the accepted modules. V39 defines its
  own block registry, integrity validator, aggregation, gates, terminal
  machine, and writer (V38 helpers hardcode the old 15-block set and are not
  reused where they would silently bind old seeds).
- New CLI `scripts/execute_v39_development.py` requiring mandatory
  `--development-execution-authorized`, binding `fake_runner=False`,
  failing closed when the output root exists, writing only Section 15 files.
- Focused fake-runner tests only; no production decode in tests.

## 17. Claim boundary

Bounded development evidence about reproducibility of prototype behavior on
empirical-count development samples with oracle-L1 conditioning. Not a
real-frame FER/threshold/SKR/security/formal-qualification/promotion claim.
Success means `exact_l2` only.

## 18. Roadmap pointer (non-binding, not executed in V39)

Post-terminal options follow the task packet Section 15 (V40 small frozen
parameter set only under `V39_C_ROBUST_AND_ADVANTAGE` with a new OpenSpec and
authorization; mechanism test if C robust without B advantage; Lane B-led
replanning if only B robust; close the structured dv~2 route if neither is
robust; real-frame qualification only in an independent later cycle).

## 19. Open items flagged for plan review

- OQ-1: Gate CB-b was transcribed from a partially corrupted task packet; the
  strict-inequality discordance form above is frozen unless plan review
  corrects it before acceptance.
- OQ-2: Gate CB-d uses overall MEDIAN errors_final (mean was unreadable in
  the packet); frozen as median unless corrected at review.
- OQ-3: Terminal states 2 and 3 overlap under a literal reading ("C1 PASS and
  CB FAIL"); Section 12 resolves this by B1 status. Confirm or amend.
- OQ-4: C1+CB PASS with BASE-C FAIL has no literal terminal mapping; Section
  12 defines the fall-through. Confirm or amend.
- OQ-5: BASE-B is report-only. Confirm that BASE-B should not gate any
  terminal state.
