# D6 graph/mother — preregistration R1c-A6 (T2 exact-equivalent acceleration + slow-task inventory)

Status: `FROZEN_PREREG_R1C_A6`. Branch `formal-ir-v72p1-addendum-clean`. Starts after Track A gate commit lands (same files). Zero decoder calls. No `--phase`/G1/G2/VAL/real/raw. No T2 key/candidate/greedy/order/tie-break change, no float approximation of integer key, no unproven shortlist, no decoder-chosen speedup. No six-file schema landing. Reference path kept until gates pass.

Frozen science/knobs per A5 prereg. T2 choice key `(four, max_pair, incid_max, rmax, rsumsq, sorted_triple)` order-independent lexicographic argmin (licence: candidate set fixed by used_pairs/used_triples; last field uniquely identifies candidate).

## A6-01 profile first, freeze baseline

Fresh roots, structure-only, workers 18 and 1. Per `(n,layer)` T2: candidate counts, per-variable wall distribution, affected-update share, allocation/GC share, peak RSS. Per arm n64 + fallback n128/n256: A4-shape baseline for regression. Freeze `A6_BASELINE_TABLE` (machine-readable JSON + human table in performance report) before code. Acceptance A6-A01.

Baseline carried from A4 (same protocol/machine): n64 42.2s cold (T2 41.4+31.6s), n128 641.3s, n256 10256.4s; scaling 10897.7s; after-side fb-only 2.5s. A6 re-measures cold+warm fresh-root per prereg, then compares.

## A6-02/A6-03 implement + prove (allowed only)

Allowed: staged lexicographic filtering (cheap `four` prefix 0.27us first, later fields only for ties on minimal prefix); vectorized candidate enumeration; integer-encoded pair/triple membership; incremental `pair_counts`/`pair_to_cols`/`inc_per_col`/`total_four`/`max_pair`/`incid_max`/degrees; skipping affected rebuild for early-eliminated candidates. Forbidden: key/tie-break/candidate/greedy change; sequential/parallel divergence; A4 pruning/two-builds change.

Equivalence gates (all must pass):
1. support-array equality 8 arms x 2 layers x {64,128,256} vs reference (one n256 T2 reference inside 4h structure-only budget; document).
2. per-variable chosen-triple trace equality T2 every width.
3. committed R1c-A2 n64 `structure_records.csv` byte-identical (existing `r1c_a4_equivalence_committed_n64` + T2-specific test).
4. structural ordering, eligibility, `selected_arms.json` unchanged.
5. determinism replay equal; sequential==parallel.
6. exactly-two-constructions + A4 pruning unchanged.
7. if Track A sandbox repaired T2 exists, re-run 1-3 vs its unoptimized reference.

Tests fail if key/tie-break changes, reference-evaluated candidate skipped, greedy order changes, seq/par differ, T2 differs from committed evidence, A4 guards regress.

Performance acceptance (fresh roots, cold+warm, A4 protocol): T2 per-layer n64<=5s, n128<=90s, n256<=600s (target >=10x, report factor); n64 all-8<=8s; non-T2 regression<=10%; scaling fb-only within 2x of A4 after-side (2.5s/2.7s); peak RSS<2GiB; zero decoder; no retry. Else `PERF_TARGET_NOT_MET` with profile + hot loop, reference intact. Acceptance A6-A02/A6-A03/A6-A05/A6-A06/A6-A07.

## A6-04 slow-task inventory (read-only, no implementation)

Measure+tabulate: v38 T0/T1 cold+warm + residual hot spot (lane-A ~20s ~3.78M tiny `compute_gf32_rank`; perf-v38 1513s->807s); two orchestration tests (~340s each); D5/D6 helpers (`audit_prefix` rank, `compute_girth`, `_build_M_support` pair enum, `build_dv3_nested_support`); V30R DE/decoder (74.8s/719.9s); other measured heavies. Menu: wall, hot symbol, cause, expected gain, semantic risk, OpenSpec needed. Do not implement. Acceptance A6-A04.

Stop: ambiguity => STOP; production test failure => STOP; one rework max; forbidden per mother packet §2.
