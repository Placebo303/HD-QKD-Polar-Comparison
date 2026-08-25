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
mismatch SHALL be integrity failure I1. Local NPZ files SHALL NOT be inputs
or outputs.

## R5. New development blocks

Block seeds SHALL be exactly: 1M 390101-390105; 1p5M 390201-390205;
2M 390301-390305. Blocks SHALL be sampled with
`sample_empirical_block(source counts, block_seed, 1024)` using
source-specific V25 TRAIN empirical counts and oracle-L1 conditioning via
`factorize_f03` + `get_conditional_posterior_l2(counts, bob, u1_alice)`.
Blocks are development samples; the plan SHALL NOT describe them as real
frames, holdout data, or qualification evidence.

## R6. Posterior-binding preflight

Before any authorized execution, a decoder-free, write-free preflight SHALL:
capture the second argument of `get_conditional_posterior_l2` on probe blocks
390101/390201/390301 and assert it equals complete `bob`; assert the
complete-bob prior differs materially from the `u2_bob` prior and equals the
V36-style complete-Bob call element-for-element; and perform zero production
decoder calls. Failure SHALL block execution.

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
source; the 45-pair C/B discordance table; and per-construction-seed vs
single-baseline same-block joins (9 groups per lane). No aggregation may
treat duplicated baseline values as independent observations.

## R12. Gates

Gate C1 (`C_ROBUST_SIGNAL`) and Gate B1 (`B_ROBUST_SIGNAL`) each require ALL
of: overall exact_l2 >= 36/45; every source >= 12/15; every seed ordinal
>= 12/15; overall median errors_final == 0; every source median
errors_final == 0 (B1 identical thresholds); wrong-codeword count reported
separately.

Gate CB (`C_ADVANTAGE_OVER_B`) requires ALL of: exact_count_C >=
exact_count_B + 5; d_CB > d_BC over the 45 matched pairs; no source where C
trails B by more than one exact; overall median errors_final(C) <= median(B).

Gate BASE(lane): exact_count_lane > exact_count_V31; overall median
errors_final(lane) < median(V31); every source median errors_final(lane) <=
median(V31 of that source). BASE-C PASS gates terminal state 1; BASE-B is
report-only.

McNemar exact p-values and Wilson intervals are descriptive only and SHALL
NOT replace gates.

## R13. Terminal states

With integrity-first precedence, exactly one terminal SHALL be emitted:
`V39_EVIDENCE_INVALID`, `V39_C_ROBUST_AND_ADVANTAGE` (C1+CB+BASE-C PASS),
`V39_C_ROBUST_NO_B_ADVANTAGE` (C1 PASS, CB FAIL, B1 FAIL),
`V39_BOTH_ROUTES_ROBUST` (C1 PASS, CB FAIL, B1 PASS),
`V39_B_ONLY_ROBUST` (C1 FAIL, B1 PASS),
`V39_NO_ROBUST_ROUTE_SIGNAL` (both FAIL, both validly evaluated).
Lane B SHALL be retained even when it fails its gate.

## R14. Evidence outputs

The authorized run SHALL write ONLY, under additive root
`comparison_bench/outputs_comparison/formal_ir_methods/v39_lanec_robustness_laneb_control/run_01/`:
`v39_structural_reconstruction.json/.csv`,
`v39_block_records.json/.csv`, `v39_baseline_records.json/.csv`,
`v39_paired_comparison.json/.csv`, `v39_summary.json`, and, only on
integrity failure, `v39_invalid_notice.json`. No NPZ SHALL be written or
read. Existing V38/V38R1 outputs SHALL remain byte-identical.

## R15. Integrity-first invalidation

Integrity failures I1-I11 (design Section 14) SHALL force terminal
`V39_EVIDENCE_INVALID` with `v39_invalid_notice.json`; performance SHALL NOT
be interpreted on invalid evidence.

## R16. Lifecycle and authorization

Implementation candidates stop at `IMPLEMENTATION_CANDIDATE /
EXECUTE_NOT_AUTHORIZED`. The single development execution requires an
independent plan ACCEPT plus explicit user `EXECUTE_AUTH` bound to the full
target SHA and scope `v39_decoder_only_105_calls_exactly_once`. No rerun,
tuning, post-result threshold edit, post-result seed addition, self-acceptance,
or automatic successor authorization is permitted.

## R17. Claim boundary

Results support only bounded reproducibility statements about prototype
behavior on empirical-count development samples with oracle-L1 conditioning.
FER, asymptotic threshold, SKR, security, formal qualification, promotion,
and real-frame claims remain forbidden regardless of outcome.
