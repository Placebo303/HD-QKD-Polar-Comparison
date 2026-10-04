# V11 Stage M — Non-gated GF(1024) Resource Microbenchmark (V11-30.1)

**Status: `resource_blocked`** — predicted formal-matrix wall time ≈ 777.3 h
≫ 24 h hard limit (design.md:92-95). Peak RSS (2.64 GiB) stays under the
3 GiB cap. The matrix is **not** shrunk here; design.md §4 (2×3×5×2) stays
frozen. Formal-plan preparation (V11-30.2 second half) is a main-thread
decision.

Engineering-only, non-gating, non-scientific: synthetic degree distribution,
fixed channel `p=0.15`, no threshold search, no winner, no gate claim.

## Environment (measured, frozen record)

| Item | Value |
|---|---|
| OS | Windows-11-10.0.26200-SP0 |
| CPU | Intel64 Family 6 Model 198 Stepping 2, GenuineIntel |
| Logical CPUs | 20 |
| Total RAM | 33.69 GiB |
| Python | 3.12.12 |
| numpy | 2.4.0 |
| Clock | QueryPerformanceCounter(), monotonic, 1e-7 s resolution |

## Measurements (raw, `microbenchmark_raw.json` → `microbenchmark.json`)

q=1024, L=32, synthetic lambda max degree 40 (bounds frozen S1 max 28 / S3
max 40), p=0.15, seed 2026110000 (engineering; disjoint from all V11 formal
seeds). `streak=20 > max_iter` ⇒ full budget executes; per-iteration time =
wall / iterations executed.

| Cell | N | w | W | iters | per-iter (s) | per-sample-per-iter (s) | peak RSS (GiB) |
|---|---|---|---:|---:|---:|---:|---:|
| G1_500 | 500 | 1 | 8 | 10 | 6.4442 | 0.012888 | 0.257 |
| G2_500 | 500 | 2 | 16 | 10 | 12.9954 | 0.025991 | 0.418 |
| G3_500 | 500 | 2 | 32 | 10 | 26.0598 | 0.052120 | 0.726 |
| G1_2000 | 2000 | 1 | 8 | 5 | 28.0216 | 0.014011 | 0.779 |
| G2_2000 | 2000 | 2 | 16 | 5 | 58.2099 | 0.029105 | 1.419 |
| G3_2000 | 2000 | 2 | 32 | 5 | 113.2256 | 0.056613 | 2.641 |
| CTRL_500 | 500 | 0 | 1 | 10 | 0.5985 | 0.001197 | 0.117 |
| CTRL_2000 | 2000 | 0 | 1 | 5 | 2.6103 | 0.001305 | 0.214 |

Linear-in-N check: per-sample-per-iter is flat between N=500 and N=2000
(G1 0.0129→0.0140, G2 0.0260→0.0291, G3 0.0521→0.0566) — the ~8% rise is
consistent with per-iteration memory-layout effects; the projection uses the
direct N=2000 measurements, so it does not rely on a scaling assumption.

## Formal-matrix extrapolation (all assumptions explicit, conservative)

Frozen matrix (design.md §4, V11-A07; **not shrunk**): 2 strata × 3
geometries × 5 seeds × 2 arms (coupled + paired uncoupled control) = 60
runs; 10 runs per geometry.

Per run:
- binary search over p ∈ [0.10, 0.40], tol ≤ 0.001
  ⇒ `n_probes = ceil(log2(0.30/0.001)) = 9` probes;
- every probe runs the full `max_iter = 150` iteration budget (conservative
  upper bound of the V9/V10 convention: V9A_BUDGETS max_iter=150, V10
  refinement max_iter=100) — no early-convergence savings;
- formal population `n_samples = 2000` (V9A_BUDGETS / V10 refinement bound);
- iterations per run = 9 × 150 = 1350.

Per-iteration wall time at N=2000 taken directly from the measured N=2000
cells for the same (w, W); control = single-position run (w=0, W=1) with the
same per-run budget (design.md §4 control contract); sequential execution,
one process tree (workers=1, V9/V10 convention).

| Geometry | w | W | per-iter N=2000 (s) | 10 runs coupled (h) | 10 runs control (h) | geometry total (h) |
|---|---|---:|---:|---:|---:|---:|
| G1 | 1 | 8 | 28.0216 | 105.08 | 9.79 | 114.87 |
| G2 | 2 | 16 | 58.2099 | 218.29 | 9.79 | 228.08 |
| G3 | 2 | 32 | 113.2256 | 424.60 | 9.79 | 434.38 |
| **Total** | | | | **747.96** | **29.37** | **777.33** |

- **Predicted total wall: 777.33 h (32.4 days)** ≫ 24 h limit.
- **Peak RSS: 2.64 GiB** (G3_2000 single run; sequential runs do not sum)
  < 3 GiB cap.

## Verdict

`resource_blocked` — predicted wall time 777.3 h > 24 h (design.md:92-95).
RSS is not the blocker (2.64 GiB < 3 GiB), but leaves only ~0.36 GiB headroom
for G3, so any population/layout change must re-check RSS.

## Notes / scope

- The formal matrix (2×3×5×2, design.md §4) is unchanged; no geometry was
  added, removed, or modified. A changed matrix would require an amended plan
  and new review (design.md:94-95).
- The microbenchmark uses the pure-numpy V11 kernel (`nonbinary_v11_mcde`).
  A numba/njit hot-kernel path (as V10's budget amendment did) is a possible
  main-thread mitigation; it is **not** authorized here and would itself need
  a frozen amendment before any formal plan.
- Preparing the formal plan is V11-30.2 (main thread); this evidence does not
  draft it.
