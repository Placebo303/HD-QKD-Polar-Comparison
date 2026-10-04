# V11 Stage M — Non-gated GF(1024) Resource Microbenchmark #2 (V11-30.1', AMEND-2026-08-06-01)

**Status: `resource_blocked`** — predicted formal-matrix wall time ≈ 66.72 h
≫ 24 h hard limit (design.md:92-95). Peak RSS (2.68 GiB) stays under the
3 GiB cap. The matrix is **not** shrunk here; design.md §4 (2×3×5×2) stays
frozen. Formal-plan preparation (V11-30.2' second half) is a main-thread
decision.

Exactly-once re-measurement (#2) authorized by
**AMEND-2026-08-06-01** (`evidence/resource/v11_budget_amendment.json`):
the only change vs #1 is the numba njit hot-kernel integration into
`nonbinary_v11_mcde.py` (WHT butterfly, check convolution, variable/belief
updates, floored normalization). #1 evidence
(`evidence/resource/microbenchmark.json` / `microbenchmark.md`) is
**unchanged**. Engineering-only, non-gating, non-scientific: synthetic
degree distribution, fixed channel `p=0.15`, no threshold search, no winner,
no gate claim.

## Environment (measured, frozen record)

| Item | Value |
|---|---|
| OS | Windows-11-10.0.26200-SP0 |
| CPU | Intel64 Family 6 Model 198 Stepping 2, GenuineIntel |
| Logical CPUs | 20 |
| Total RAM | 33.69 GiB |
| Python | 3.12.12 |
| numpy | 2.4.0 |
| numba | 0.64.0 (new vs #1; njit kernels, `cache=False`, nopython only) |
| Clock | QueryPerformanceCounter(), monotonic, 1e-7 s resolution |

## Measurements (raw, `workspace/nbldpc_v11_microbench2_269b15a4/microbenchmark_raw.json` → `microbenchmark2.json`)

q=1024, L=32, synthetic lambda max degree 40 (bounds frozen S1 max 28 / S3
max 40), p=0.15, seed 2026110000 (engineering; disjoint from all V11 formal
seeds) — the identical #1 configuration. `streak=20 > max_iter` ⇒ full
budget executes; per-iteration time = wall / iterations executed.

| Cell | N | w | W | iters | per-iter (s) | per-sample-per-iter (s) | peak RSS (GiB) |
|---|---|---:|---:|---:|---:|---:|---:|
| G1_500 | 500 | 1 | 8 | 10 | 0.6757 | 0.001351 | 0.346 |
| G2_500 | 500 | 2 | 16 | 10 | 1.0915 | 0.002183 | 0.510 |
| G3_500 | 500 | 2 | 32 | 10 | 2.1203 | 0.004241 | 0.806 |
| G1_2000 | 2000 | 1 | 8 | 5 | 2.2480 | 0.001124 | 0.819 |
| G2_2000 | 2000 | 2 | 16 | 5 | 4.9735 | 0.002487 | 1.458 |
| G3_2000 | 2000 | 2 | 32 | 5 | 9.8899 | 0.004945 | 2.679 |
| CTRL_500 | 500 | 0 | 1 | 10 | 0.0499 | 0.000100 | 0.203 |
| CTRL_2000 | 2000 | 0 | 1 | 5 | 0.2269 | 0.000113 | 0.254 |

Linear-in-N check: per-sample-per-iter rises mildly between N=500 and N=2000
(G1 0.001351→0.001124, G2 0.002183→0.002487, G3 0.004241→0.004945) — the
same ~10-17% rise pattern as #1; the projection uses the direct N=2000
measurements, so it does not rely on a scaling assumption.

## Speedup vs microbenchmark #1 (per-iteration wall, same cells)

| Cell | #1 per-iter (s) | #2 per-iter (s) | speedup |
|---|---:|---:|---:|
| G1_500 | 6.4442 | 0.6757 | 9.54× |
| G2_500 | 12.9954 | 1.0915 | 11.91× |
| G3_500 | 26.0598 | 2.1203 | 12.29× |
| G1_2000 | 28.0216 | 2.2480 | 12.47× |
| G2_2000 | 58.2099 | 4.9735 | 11.70× |
| G3_2000 | 113.2256 | 9.8899 | 11.45× |
| CTRL_500 | 0.5985 | 0.0499 | 12.00× |
| CTRL_2000 | 2.6103 | 0.2269 | 11.50× |
| **Total predicted wall** | **777.33 h** | **66.72 h** | **11.65×** |

The njit kernels give a homogeneous ~11-12× speedup across all cells
(coupled and control). Peak RSS is essentially unchanged vs #1 (2.68 GiB vs
2.64 GiB) — the kernels do not reduce the working-set size; the WHT-spectrum
accumulator and the stacked mixtures still dominate the peak.

## Formal-matrix extrapolation (identical formula to #1; all assumptions explicit, conservative)

Frozen matrix (design.md §4, V11-A07; **not shrunk**): 2 strata × 3
geometries × 5 seeds × 2 arms (coupled + paired uncoupled control) = 60
runs; 10 runs per geometry.

Per run:
- binary search over p ∈ [0.10, 0.40], tol ≤ 0.001
  ⇒ `n_probes = ceil(log2(0.30/0.001)) = 9` probes;
- every probe runs the full `max_iter = 150` iteration budget (conservative
  upper bound of the V9/V10 convention) — no early-convergence savings;
- formal population `n_samples = 2000` (V9A_BUDGETS / V10 refinement bound);
- iterations per run = 9 × 150 = 1350.

Per-iteration wall time at N=2000 taken directly from the measured N=2000
cells for the same (w, W); control = single-position run (w=0, W=1) with the
same per-run budget (design.md §4 control contract); sequential execution,
one process tree (workers=1, V9/V10 convention).

| Geometry | w | W | per-iter N=2000 (s) | 10 runs coupled (h) | 10 runs control (h) | geometry total (h) |
|---|---|---:|---:|---:|---:|---:|
| G1 | 1 | 8 | 2.2480 | 8.43 | 0.85 | 9.28 |
| G2 | 2 | 16 | 4.9735 | 18.65 | 0.85 | 19.50 |
| G3 | 2 | 32 | 9.8899 | 37.09 | 0.85 | 37.94 |
| **Total** | | | | **64.17** | **2.55** | **66.72** |

- **Predicted total wall: 66.72 h (2.8 days)** ≫ 24 h limit.
- **Peak RSS: 2.68 GiB** (G3_2000 single run; sequential runs do not sum)
  < 3 GiB cap (0.32 GiB headroom).

## Verdict

`resource_blocked` — predicted wall time 66.72 h > 24 h (design.md:92-95).
RSS is not the blocker (2.68 GiB < 3 GiB). The numba integration (11.65×
total-wall speedup) brings the projection from 777.33 h down to 66.72 h but
does not reach the 24 h limit; a further main-thread decision is required
(no tuning / no rerun here — the exactly-once authorization is exhausted).

## Notes / scope

- The formal matrix (2×3×5×2, design.md §4) is unchanged; no geometry was
  added, removed, or modified.
- Retest used the identical #1 configuration and the identical extrapolation
  formula (60 runs, 9 probes, max_iter 150, N=2000, control = single-position
  run) per AMEND-2026-08-06-01.
- Correctness of the njit kernels is covered by
  `comparison_bench/tests/test_nonbinary_v11_mcde_numba.py` (known-answer
  butterfly, allclose(rtol=1e-12) vs pure-numpy references, frozen RNG draw
  order, import discipline); the existing 24 V11 MC-DE tests (incl. the w=0
  byte-identity to V9) and the 16 SMP-DE tests still pass.
- Preparing the formal plan is V11-30.2' (main thread); this evidence does
  not draft it.
