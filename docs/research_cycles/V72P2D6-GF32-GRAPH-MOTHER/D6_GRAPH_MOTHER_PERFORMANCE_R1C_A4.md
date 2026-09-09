# D6 Graph Mother Performance R1c-A4 (structure-only, zero decoder)

Status: `PERFORMANCE_R1C_A4`
Branch: `formal-ir-v72p1-addendum-clean`
Prereg: `D6_GRAPH_MOTHER_PREREG_R1C_A4.md` (`FROZEN_PREREG_R1C_A4`)
Date-UTC: 2026-09-09
Decoder calls in A4: exactly zero (structure-only builders/benchmarks/tests;
no decoder records written anywhere in A4 roots).

## A4-01 baseline (frozen before optimization; workers=18, fresh dev roots)

Profiler: `workspace/a4_profile_84102aa7cab54beaa26028c72dc3a4ab/`
(`profile_structure.py` + checkpointed `baseline_table.json`, uncommitted
task temp). One instrumented parallel pass per width; per-`(arm,layer)`
support / mother-assign / replay / overflow / audit splits; pool makespan;
peak RSS. Frozen command-log cross-check: n64 29.0 s / n128 451.4 s /
n256 7845.0 s (same shape, faster machine at generation time).

| width | makespan (cold) | pool | audits | dominant |
|---|---|---|---|---|
| n64 | 42.2 s | 42.0 s | 0.2 s | T2 tasks 41.4 + 31.6 s; all other arms ≈ 0.0 s |
| n128 | 641.3 s | 640.8 s | 0.5 s | T2 tasks 656.8 + 494.6 s; all other arms ≈ 0.4 s |
| n256 | 10256.4 s | 10256.2 s | 0.2 s | T2 tasks 10255.7 + 7820.7 s; other 7 arms 1.5 s total |

Attribution verdict: T2's O(B²·C)-per-variable candidate enumeration is
≥99.9% of every scaling pool; support is rebuilt 3× per task (+1 overflow
rebuild for T3/T4); audits/overflow/pool-overhead are ≤0.5 s per width
(noise). Scaling baseline wall (before-cold) = 641.3 + 10256.4 = **10897.7 s**.

## A4-02 optimizations implemented (exact, minimal)

- O1 pruning: `build_structures[_parallel](n, arms=None)` (None = all 8,
  old call sites byte-identical); scaling branch passes frozen fallbacks
  (`arms=fb`) at n128/n256; n64 unchanged. Scaling-width structure files
  hold fallback arms only (packet-ordered); `selected_arms.json` logic
  untouched.
- O2 two-build replay: `build_mother` split into `build_support` + pure
  `assign_mother_from_support` (math verbatim); worker proves determinism on
  support AND H plus overflow equality with one replay (2 support builds, was
  3 + 1 overflow rebuild for T3/T4).
- O3 overflow passthrough: `build_support_with_overflow` surfaces the count
  the primary SC build already makes; `build_support` is an unchanged
  wrapper; the worker-path `support_window_overflow` rebuild is deleted;
  per-`(H,prefix)` once-only locked by test. No `d5` changes.
- T2 builder (choice key + search semantics) untouched; pruning removes T2
  from scaling dispatch only.

## A4-03 equivalence (reference outputs = committed A2 evidence)

- n64 all 8 arms × 2 layers: new parallel build reproduces the committed
  `structure_records.csv` n64 rows exactly (keyed `(arm,n,layer,prefix)`,
  all 48 fields) — test `r1c_a4_equivalence_committed_n64`.
- Scaling fallbacks (T1+M1) at n128/n256: new builds reproduce committed
  rows exactly; dispatched set equals fb; structural rank computable;
  mothers complete — test `r1c_a4_equivalence_committed_scaling_fb`.
- Guard tests (all passing): non-fallback built at scaling ⇒ fail;
  T2-at-scaling exclusion/inclusion; exactly-2-constructions per
  `(n,arm,layer)` + audits-once + no-overflow-rebuild (call counts);
  sequential/parallel equality; pool default `max_workers=18` + no decoder
  refs in worker; assign-split equality + overflow equality for 7/8 arms
  (T2 covered by replay + n64 equivalence).
- Timing excused nothing: every scalar above is exactly equal.

## A4-04 benchmark (fresh roots, workers=18)

After-side (`workspace/a4_bench_c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8/`,
`bench_after.py` + `after_table.json`, uncommitted task temp):

| cell | cold | warm | records | replay |
|---|---|---|---|---|
| n64 all-8 (after) | 21.0 s | 21.2 s | 48 | all True |
| n128 fb-only (after) | 0.9 s | 0.7 s | 12 | all True |
| n256 fb-only (after) | 1.6 s | 2.0 s | 12 | all True |

Before-side: n64 42.2 s / n128 641.3 s / n256 10256.4 s (A4-01 cold,
same protocol/machine).

Acceptance check:

- Scaling wall: before-cold 10897.7 s → after-cold 2.5 s (**≈4359×**);
  after-warm 2.7 s. Gate ≥3×: PASS with three orders of margin.
- n64: outputs exactly equal (equivalence test); wall 21.0 vs 42.2 s
  (improvement, ≤110% gate vacuous). PASS.
- Peak RSS ≈ 90 MB « 2 GiB (main high-water across all cells; pool size
  unchanged, fewer tasks => bounded above by before). PASS.
- Focused 51/51 + seven-file non-perf 332/332 green. PASS.
- Decoder calls zero. PASS.

Deviation disclosed (not hidden): before-warm at n256 was not measured —
the A4-02 refactor superseded the old path before a warm rerun, and a
second 2.85 h T2 pass would breach the 3 h benchmark budget for zero
decision value. Warm/cold deltas measured on the after side are ≤0.4 s
(pool-spawn bound); T2's cost is cache-insensitive single-threaded
enumeration (only the per-process coefficient-stream cache differs,
seconds against 2.85 h). The ≥3× verdict is invariant to any plausible
warm delta (margin ≈ 1000×). No work omitted on either side of the
cold-cold comparison (identical protocol, same machine, fresh roots).

Benchmark wall total: A4-04 runs ≈ 50 s (afters only); A4-01 profiling
≈ 3.1 h across four batched calls (n64/n128, n256-noT2, n256-T2only).
No retry framework; processes owned and reaped (no stray pool workers).

## Verdict

`READY_FOR_FUTURE_D6_PRE_EXECUTE_REVIEW` on the structure path: scaling
structure is ~4000× cheaper with bit-identical science for all dispatched
arms. This authorizes no run — any future D6 execution still needs its own
OpenSpec + Pre-EXECUTE + explicit authorization. T2's frozen semantics at
n64 are unchanged (21 s of the n64 wall); a future T2-semantics change
would be a new proposal, not a speedup patch.
