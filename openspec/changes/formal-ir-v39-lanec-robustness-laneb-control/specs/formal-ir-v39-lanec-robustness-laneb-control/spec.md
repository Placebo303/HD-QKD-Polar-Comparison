# Delta Specification: formal-ir-v39-lanec-robustness-laneb-control

**Cycle**: `V39P0`
**Lifecycle of this change**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`

## R1. Predecessor binding

V39P0 SHALL build only on the accepted V38R1 chain: result candidate
`2416486f724f4fb7cbf1058d9dc1bb1fc5ded5ed`, independent acceptance commit
`c8c5cd2e`, accepted implementation
`8f7bc7d8d7366772ff425528cd1080fa67ef7509`. Execution on any other base SHALL
NOT proceed.

## R2. Frozen routes

The experiment SHALL evaluate exactly two routes:

1. Lane C — L=8, w=2 spatially banded prototype (main route);
2. Lane B — eIRA-like lower-bidiagonal prototype (control route).

Lane A SHALL NOT be constructed, evaluated, or reported as a V39 lane. Lane
C and Lane B structures, GF(32) polynomial 37, decoder schedule,
max_iter=30, damping_alpha=1.0, posterior semantics, source dimensions
(m = 184/190/192), and gate thresholds SHALL remain frozen.

## R3. Construction seeds and pairing

All nine pre-registered construction seeds per lane SHALL be used:

- lane_c 1M: 383101/383102/383103; 1p5M: 383201/383202/383203;
  2M: 383301/383302/383303.
- lane_b 1M: 382101/382102/382103; 1p5M: 382201/382202/382203;
  2M: 382301/382302/382303.

`construction_seed_ordinal` (1..3) SHALL equal the seed's position in the
frozen per-(lane, source) list. Lane C and Lane B records SHALL pair by
`(source, ordinal)`; no decoder metric may influence seed selection or
pairing.

## R4. Deterministic structural reconstruction

All 18 matrices SHALL be reconstructed from the accepted constructors and
frozen seeds and strictly compared against the committed V38P0 run_01 file
`v38_architecture_triage/run_01/v38_structural_prototypes.json` (27 records;
lanes b/c subset = 18), including Lane C `position_permutations`. Any
mismatch SHALL be integrity failure I1. Reading the local winner archive
`v38_winning_matrices.npz` SHALL NOT occur and no NPZ SHALL be written;
read-only access to the fixed V25 `channel_counts.npz` through the accepted
`load_v25_channel_counts()` is permitted.

## R5. New development blocks

Block seeds SHALL be exactly: 1M 390101-390105; 1p5M 390201-390205;
2M 390301-390305. Blocks SHALL be sampled with
`sample_empirical_block(source counts, block_seed, 1024)` using
source-specific V25 TRAIN empirical counts and oracle-L1 conditioning via
`factorize_f03` + `get_conditional_posterior_l2(counts, bob, u1_alice)`.
Blocks are development samples; the plan SHALL NOT describe them as real
frames, holdout data, or qualification evidence.

## R6. Posterior-binding preflight

Before any authorized execution, a decoder-free, write-free preflight SHALL,
for each probe block 390101/390201/390301, verify ALL of:
`np.any(bob > 31) == True`; the captured second argument of
`get_conditional_posterior_l2` element-equal to complete `bob`;
`prior_corrected` element-equal to the direct complete-bob call;
`prior_corrected` NOT element-equal to the `u2_bob` prior;
`max(abs(prior_corrected - prior_u2_bob)) > 1e-6`; and at least one position
where the posteriors' `argmax` differs. The preflight SHALL perform zero
production decoder calls. Failure SHALL block execution. A frozen probe
failing a difference sentinel SHALL be replaced only at plan-review stage
(as a pre-registered change), never after production execution.

## R7. Decoder success semantics

A record is an exact recovery iff
`np.array_equal(x_hat, u2_alice)` (`exact_l2`). `syndrome_ok` SHALL be
reported separately; `wrong_codeword = syndrome_ok and not exact_l2` SHALL be
counted separately and SHALL NOT count toward exact recovery in any gate.
Warm start, iteration-cap increase, damping search, failure reruns, and seed
substitution SHALL NOT occur.

## R8. Same-block V31 baseline

The frozen V31 baseline SHALL be recomputed on the same 15 new blocks with
the corresponding source matrix from `load_v31_qc_baseline_matrices()` and
identical posterior/decoder settings, exactly once per
`(source, block_seed)` — 15 calls total. Baseline records SHALL NOT be
duplicated per construction seed; all lane-vs-baseline comparisons SHALL join
to the single same-block baseline record.

## R9. Workload cap

The authorized run SHALL make exactly 105 real decoder calls:
45 (lane_c) + 45 (lane_b) + 15 (baseline). Any other count SHALL trigger
integrity failure I6.

## R10. Records

Each lane record SHALL contain: lane, source, construction_seed,
construction_seed_ordinal, block_seed, matrix_id, errors_initial,
errors_final, exact_l2, syndrome_ok, wrong_codeword, iterations, status,
runtime_s. Baseline records use `lane="v31_baseline"` with null
construction fields.

## R11. Aggregation

Aggregates SHALL be produced at: lane overall; lane/source;
lane/construction-seed ordinal; lane/source/seed; baseline overall and per
source; the complete 45-pair C/B discordance table; per-ordinal
(o = 1..3) lane-vs-single-baseline joins of 15-vs-15 records used by Gate
BASE plus per-(source, ordinal) 5-vs-5 medians; and block-cluster
aggregates per (lane, source, block_seed) across the 3 construction
matrices (seed_exact_count in 0..3, seed_exact_fraction, residual
mean/median). No aggregation may treat replicated baseline values as new or
independent observations.

## R12. Gates

Gate C1 (`C_ROBUST_SIGNAL`) and Gate B1 (`B_ROBUST_SIGNAL`) each require ALL
of: overall exact_l2 >= 36/45; every source >= 12/15; every seed ordinal
>= 12/15; every (source, construction_seed) cell >= 4/5 (nine 5-record
cells per lane); overall median errors_final == 0; every source median
errors_final == 0 (B1 uses identical thresholds); wrong-codeword count
reported separately.

Gate CB (`C_ADVANTAGE_OVER_B`) requires ALL of:
exact_count_C >= exact_count_B + 5;
`d_CB - d_BC >= 3` over the COMPLETE 45 pairs matched by
(source, construction_seed_ordinal, block_seed), where
d_CB = count(C exact and B not exact) and d_BC = count(B exact and C not
exact); no source where C trails B by more than one exact;
mean(errors_final over all 45 C records) <= mean(errors_final over all 45
B records). Under complete pairing `exact_count_C - exact_count_B =
d_CB - d_BC`, so CB-a implies CB-b, and CB-b does NOT imply CB-a; CB-a and
CB-b are retained, computed, and reported separately, and both must hold.

Gate BASE(lane) SHALL be evaluated per construction-seed ordinal against
the single 15-record V31 baseline (a direct 45-vs-15 comparison is
forbidden): for each ordinal o, exact_count_lane_ordinal(o) >
exact_count_V31 over the same 15 blocks;
median(errors_final, ordinal o) < median(errors_final, V31 overall); and
for every (source, o), median(errors_final, source-ordinal, 5 records) <=
median(errors_final, V31 source, 5 records). BASE(lane) PASS iff ALL THREE
ordinals pass. BASE-C PASS gates terminal state 1; BASE-B is report-only.

The 45 lane records per lane are 15 unique sampled blocks x 3 construction
matrices and SHALL NOT be described as 45 independent block draws.
Record-level Wilson intervals are naive descriptive summaries ignoring
clustering; the McNemar exact test on the 45 pairs is descriptive and
uncorrected for construction/block clustering; neither indicates
independent-sample significance nor replaces the frozen gates. Block-cluster
descriptive summaries over the 15 unique blocks SHALL accompany them.

## R13. Terminal states

With integrity-first precedence, the FIRST matching rule SHALL win:

0. any integrity failure -> `V39_EVIDENCE_INVALID` (overrides everything);
1. C1 PASS and CB PASS and BASE-C PASS -> `V39_C_ROBUST_AND_ADVANTAGE`;
2. C1 PASS, rule 1 not satisfied, B1 FAIL ->
   `V39_C_ROBUST_NO_COMPLETE_ADVANTAGE`, recording `terminal_reason` as
   exactly one of `CB_FAIL`, `BASE_C_FAIL`, or `CB_AND_BASE_C_FAIL`;
3. C1 PASS, rule 1 not satisfied, B1 PASS -> `V39_BOTH_ROUTES_ROBUST`;
4. C1 FAIL and B1 PASS -> `V39_B_ONLY_ROBUST`;
5. C1 FAIL and B1 FAIL -> `V39_NO_ROBUST_ROUTE_SIGNAL`.

The mapping SHALL be total and disjoint over all (C1, CB, BASE-C, B1)
combinations, proven by a truth-table test. Lane B SHALL be retained even
when it fails its gate. `V39_B_ONLY_ROBUST` asserts B1 robustness only; it
does NOT assert Lane B superiority over V31 and does not by itself
authorize any successor step. BASE-B ordinal verdicts SHALL be written to
the summary and referenced in result interpretation; successor planning for
Lane B MUST consider BASE-B, not the terminal name alone.

## R14. Evidence outputs

The authorized run SHALL write ONLY, under additive root
`comparison_bench/outputs_comparison/formal_ir_methods/v39_lanec_robustness_laneb_control/run_01/`:
`v39_structural_reconstruction.json/.csv`,
`v39_block_records.json/.csv`, `v39_baseline_records.json/.csv`,
`v39_paired_comparison.json/.csv`, `v39_summary.json`, and, only on
integrity failure, `v39_invalid_notice.json`. Writing any NPZ SHALL NOT
occur and the winner archive `v38_winning_matrices.npz` SHALL NOT be read;
read-only `load_v25_channel_counts()` access to the fixed V25
`channel_counts.npz` is permitted with provenance recorded in the summary.
The summary SHALL additionally contain per-ordinal BASE-C and BASE-B
verdicts (ordinals 1/2/3 plus overall), `terminal_reason` when state 2
occurs, and the block-cluster aggregates. Existing V38/V38R1 outputs SHALL
remain byte-identical.

## R15. Integrity-first invalidation

Integrity failures I1-I11 (design Section 14) SHALL force terminal
`V39_EVIDENCE_INVALID` with `v39_invalid_notice.json`; performance SHALL NOT
be interpreted on invalid evidence. I3 SHALL cover overlap with block seeds
used by V36 AND by V38/V38R1; I8 SHALL include cross-lane/baseline
`errors_initial` equality for each `(source, block_seed)`; I10 SHALL flag
only a forbidden winner-NPZ dependency or any NPZ output. After a mid-run
execution failure, raw partial records MAY be retained byte-for-byte as
evidence but SHALL NOT be aggregated into performance results.

## R16. Lifecycle and authorization

Implementation candidates stop at `IMPLEMENTATION_CANDIDATE /
EXECUTE_NOT_AUTHORIZED`. The single development execution requires an
independent plan ACCEPT plus explicit user `EXECUTE_AUTH` bound to the
repository, branch, full implementation SHA, cycle V39P0, and scope
`v39_decoder_only_105_calls_exactly_once`. Before execution the runner
SHALL verify exact equality of BOTH `git rev-parse HEAD` and
`git rev-parse origin/formal-ir-mainline` with the authorized target SHA;
ancestor or "contains" checks alone are insufficient. No rerun, tuning,
post-result threshold edit, post-result seed addition, self-acceptance,
or automatic successor authorization is permitted.

## R17. Claim boundary

Results support only bounded reproducibility statements about prototype
behavior on empirical-count development samples with oracle-L1 conditioning.
FER, asymptotic threshold, SKR, security, formal qualification, promotion,
and real-frame claims remain forbidden regardless of outcome.
`V39_B_ONLY_ROBUST` SHALL NOT be presented as Lane B superiority over V31;
any successor consideration for Lane B SHALL reference the reported BASE-B
ordinal verdicts.
