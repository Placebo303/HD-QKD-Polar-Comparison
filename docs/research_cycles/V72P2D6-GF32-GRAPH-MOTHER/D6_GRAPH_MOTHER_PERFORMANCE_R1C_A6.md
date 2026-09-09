# D6 graph/mother performance R1c-A6 (structure-only, zero decoder)

Status: `PERFORMANCE_R1C_A6` (Track B evidence; not an authorization).
Branch `formal-ir-v72p1-addendum-clean`. Prereg
`D6_GRAPH_MOTHER_PREREG_R1C_A6.md` (`FROZEN_PREREG_R1C_A6`); Track A gate
commit `fda539b` landed before any Track B code (same-files serial order).
Machine baseline table: `D6_GRAPH_MOTHER_BASELINE_R1C_A6.json` (this dir).
Decoder calls in A6: exactly zero (builders/benchmarks/tests only; the 16
`decoder_records.csv` files under the bench root are all explicit-fake
unit-test fixtures from the co-located suite run (placeholder rows,
permitted) — the benchmark phases themselves wrote none).

## A6-01 baseline (frozen before code; fresh roots, workers 18 and 1)

Profiler `workspace/d6_r1c_a6_profile_2589503b56624d55b7323ca7896f4d1e/`
faithful instrumented copy (`fidelity_exact` true at n64/n128) + plain
singles + A4-shape per-arm baselines. A4 carried numbers (same machine):
n64 pool 42.2 s (T2 tasks 41.4+31.6), n128 641.3 s (656.8+494.6),
n256 10256.4 s (10255.7+7820.7); scaling before-cold 10897.7 s.

| (n,layer) | candidates total (per-var full) | support-only ref | enum/key/aff splits | aff_max | GC gen0 |
|---|---|---|---|---|---|
| 64 L1 | 4.54M (72,912) | 9.1 s | 0.9/3.3/1.6 s | 0 | 5744 |
| 64 L2 | 3.46M (55,986) | 7.0 s | 0.7/2.5/1.2 s | 0 | 4327 |
| 128 L1 | 75.6M (598,878) | 160.2 s | 15.4/55.0/20.3 s | 0 | 98512 |
| 128 L2 | 57.9M (460,530) | 128.6 s | 12.2/44.0/16.8 s | 0 | 75358 |
| 256 L1 | 1.243B (4,853,940) | ~2424 s model | — | — | — |
| 256 L2 | 957M (3,735,324) | ~1865 s model | — | — | — |

n256 reference support-only is cost-model projected (1.95 us/candidate,
validated +0%/+6.7% at n64/n128); the binding A4 task numbers above are
measured. Affected-update share is 0.0% everywhere measured (greedy holds
four_cycles=0 at every width: committed f1.2 four=0/incid=0 at
n64/n128/n256; instrumented aff_max=0 through full builds) — the reference
pays ~13% of wall rebuilding always-empty affected sets plus ~10% tuple
enumeration churn (tracemalloc peak only 5.3 MB: churn, not footprint).
Per-variable walls are flat (p50 ~= max: no late-variable blowup).
Non-T2 arms re-measured (2 builds): all <= 0.34 s (T1 n256), rest <= 0.02 s;
replay all True. RSS ~85-125 MB.

## A6-02 implementation (allowed techniques only)

`_build_T2_support_fast` (+~140 lines; reference `_build_T2_support`
byte-intact; dispatch via `_T2_FAST_ENABLED`): staged lexicographic
filtering (vector `four` prefix over the full grid, `min`, ties only
onward), vectorized candidate enumeration (int32 pair x C grid),
integer-encoded membership (pair bytearray m^2, triple bytearray m^3,
counts array, no tuples/sets/dicts in the hot loop), incremental
`pair_counts`/`total_four`/`max_pair`/`incid_max`(running max, exact by
per-column monotonicity)/degrees/sumsq, affected rebuild only for
sorted-prefix-competitive candidates with early exit (measured ~1
evaluation/variable; empty sets at every width). Key, field order,
tie-breaks, candidate set, greedy order unchanged; no float arithmetic
(int32 grid/index with stated bounds: pair ids <2^16, triple ids <2^24,
counts/sumsq/four <<2^31 for m<=256); no shortlist; sequential and parallel
paths share the builder; A4 pruning/two-build machinery untouched.

## A6-03 equivalence (all seven gates)

1. Support-array equality 8 arms x 2 layers x {64,128,256}: T2 n64 live
   vs intact reference (both layers); T2 n128/n256 vs committed reference
   fixtures (`comparison_bench/tests/fixtures/d6_r1c_t2_reference/`, 8
   replay-verified npz from the A5-01 slow stage, provenance in the validity
   doc); non-T2 arms dispatch-identical (same functions; pinned by test).
   Mother arrays equal too. PASS.
2. Per-variable chosen-triple trace equality T2 every width (trace hook vs
   support rows; v=0 == (0,1,2) pinned). PASS.
3. Committed R1c-A2 n64 rows: existing `r1c_a4_equivalence_committed_n64`
   (B0/B1/T1/T2 fully byte-identical incl. eligible) + T2-specific
   `r1c_a6_t2_committed_rows_and_selection_n64` (6/6 rows all fields). PASS.
4. Ordering/eligibility/selection: fresh n64 eligible map + selected list
   identical to the I1-gate-commit behavior ({B0,B1,T1}); T-rank
   (T1<T3<T4) recomputed in A5. PASS.
5. Determinism replay all True; seq==par record-identical (T2 n64). PASS.
6. Exactly-two-constructions + A4 pruning: existing `r1c_a4_*` guard tests
   green unmodified (61/61); no touch of that machinery. PASS.
7. Sandbox-T2 gate: VACUOUS — the repair study produced no sandbox T2
   (prereg: T2 key frozen, no admissible rank rule); premise locked by a
   data test (no T2 family in the repair matrix). PASS-by-vacuity, recorded.

Mutation sensitivity: v=0 (0,1,2) tie-break pin at all 6 T2 cells, triple
uniqueness (n distinct), shapes, and full-support equality fail on any
key/tie-break/candidate/greedy change by construction.

## A6-03 performance (fresh roots, cold+warm, A4 protocol)

`workspace/d6_r1c_a6_bench_12496a590500419ebab4fca5c956f366/`
(`bench_after.py` + `after_table.json`); dev-runner task =
2x(support+assign) + prefix audits (post-A4 two-build semantics).

| cell | after cold | after warm | A4 before | factor | target | verdict |
|---|---|---|---|---|---|---|
| T2/layer n64 | 1.2 s | 1.2 s | 41.4/31.6 s | ~30x | <=5 s | PASS |
| T2/layer n128 | 26.6 s | 26.5 s | 656.8/494.6 s | ~24x | <=90 s | PASS |
| T2/layer n256 | 516.1 s | 479.7 s | 10255.7/7820.7 s | ~20x | <=600 s | PASS |
| n64 all-8 | 1.5 s | 1.6 s | 42.2 s | 28x | <=8 s | PASS |

(T2/layer makespan covers both layers in parallel; sequential T2-only:
n64 1.3 s, n128 41.7 s. Replay all True in every cell.) All factors >= 10x.
n64 all-8 <= 8 s. Non-T2 arms: same functions, same outputs, walls unchanged
shape (<=0.34 s; no regression).
Scaling fb-only (T1/M1) vs A4 after-side 2.5/2.7 s: 0.6 s (n128) / 1.3 s
(n256) — faster, within the 2x gate with margin.
Peak RSS ~93 MB << 2 GiB. Zero decoder calls. No retry framework (none
added; diff contains no retry logic).

## A6-04 slow-task inventory (read-only, no implementation)

Measured fresh on this machine except where marked cited (decoder-invoking
or archived items that zero-decoder rules forbid re-running). Nothing in
this section was implemented or changed.

| item | measured wall | hot symbol | suspected cause | expected gain | semantic risk | OpenSpec? |
|---|---|---|---|---|---|---|
| v38 T0 (33 tests) cold+warm | 2.02 s / 1.95 s (fresh) | — | — | none needed | — | no |
| v38 T1 (38 tests) cold+warm | 812.2 s / 810.3 s (fresh; cited 801/802 s post-opt, 1506 s pre) | orchestration loop (below) | repeated lane construction per attempt | ~2x file-level | medium (test semantics) | yes if touched |
| orchestration x2 (fake-runner) | 345.0 s / 343.9 s cold fresh (cited 336/343 s post-opt; 641/634 pre) | `run_v38r1_development` 27-attempt loop | per-attempt full-lane rebuild | share lane builds (~2x) | medium | yes |
| lane-A construction hotspot | 41.0/40.4/40.2 s fresh cold (cited ~20 s residual rank post-opt over ~3.78M tiny `compute_gf32_rank` calls; 47.4 s pre) | `compute_gf32_rank` (exact GF(32) elimination) | per-call Python overhead on 2x2/4x4 | batched rank (~2-5x hotspot) | low-medium (exactness) | yes (perf-v38 follow-up) |
| D5/D6 helpers (fresh micro) | audit_prefix 46 ms, compute_girth 3-25 ms, _build_M_support 6 ms, build_dv3_nested_support 2 ms (n256) | — | — | none (noise) | — | no |
| V30R M1 DE / M3 decoder | cited 74.828 s / 719.876 s (decision-log 2026-08-20) | DE search / V28 decoder | archived failure run | none (frozen) | — | no (prohibited) |
| T2 reference path | cited A4 tasks 10255.7/7820.7 s; model 2424/1865 s support-only | candidate tuple/set churn | superseded by fast path in production | done (this packet, ~20x) | — | no (landed) |
| seven-file suite | 57 s fresh (95 tests) | — | acceptable | none | — | no |

Prioritized menu: P1 orchestration sharing; P2 batched GF(32) rank;
P3-P6 no action (landed / noise / frozen-archived). Any of P1/P2 needs its
own OpenSpec change with fake-only tests before implementation.

## Verdict

`D6_R1C_A6_REVIEW_PASS` recommended: all seven equivalence gates pass,
absolute targets met at every width with >=10x factors, A4 gains intact
(n64 42.2 -> 1.5 s; scaling-release unblocked for T2), zero decoder calls.
No `PERF_TARGET_NOT_MET`. No acceptance marked here (reviewer decides).
