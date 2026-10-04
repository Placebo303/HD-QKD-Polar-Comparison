# V11 Stage M — Parallel Microbenchmark #3 (V11-30.2'', AMEND-2026-08-06-02)

**Status: `resource_blocked`** — predicted parallel wall time ≈ 32.69 h > 24 h
hard limit (design.md:92-95). Peak RSS (2.70 GiB) stays under the 3 GiB cap.
The matrix is **not** shrunk here; design.md §4 (2×3×5×2) stays frozen.

Exactly-once parallel re-measurement (#3) authorized by
**AMEND-2026-08-06-02** (`evidence/resource/v11_budget_amendment2.json`):
identical synthetic non-gating configuration as #1/#2 (q=1024, L=32, p=0.15,
synthetic lambda max-degree 40, seed 2026110000, same 8 cells); run through a
4-worker `multiprocessing` pool. #1/#2 evidence is **unchanged**.

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
| Workers | 4 (DEFAULT_WORKERS, frozen suggestion for 20-logical-core machine) |

## Measurements (parallel batch, 4 workers)

q=1024, L=32, synthetic lambda max degree 40, p=0.15, seed 2026110000 —
identical #1/#2 configuration. `streak=20 > max_iter` ⇒ full budget executes.
Workers warmup-excluded (per-worker numba compilation paid once, before timing).

| Cell | N | w | W | iters | wall (s) | peak RSS (GiB) |
|---|---|---:|---:|---:|---:|---:|
| G1_500 | 500 | 1 | 8 | 10 | 5.71 | 0.336 |
| G2_500 | 500 | 2 | 16 | 10 | 12.97 | 0.481 |
| G3_500 | 500 | 2 | 32 | 10 | 24.90 | 0.807 |
| G1_2000 | 2000 | 1 | 8 | 5 | 13.68 | 0.819 |
| G2_2000 | 2000 | 2 | 16 | 5 | 28.27 | 1.443 |
| G3_2000 | 2000 | 2 | 32 | 5 | 48.80 | 2.697 |
| CTRL_500 | 500 | 0 | 1 | 10 | 0.53 | 0.212 |
| CTRL_2000 | 2000 | 0 | 1 | 5 | 1.36 | 0.258 |
| **Batch total** | | | | | **61.77** | **2.70** (max) |

The 8 cells execute concurrently (4 workers, 8 cells, 2 waves). The batch
wall (61.77 s) is the wall-clock of the parallel run, not the serial sum.

## Parallel speedup vs serial (#2)

| Metric | Value |
|---|---|
| Serial cell sum (#2) | 126.07 s |
| Parallel batch wall (#3) | 61.77 s |
| **Parallel speedup** | **2.04×** |
| Per-worker efficiency | 0.51 (2.04 / 4 workers) |

The 2.04× speedup with 4 workers gives ~51% per-worker efficiency. This is
expected: the 8 cells include 3 small cells (CTRL_500, CTRL_2000, G1_500)
that finish quickly, leaving workers idle for the later waves. The larger
cells (G2_2000, G3_2000) dominate the tail.

## Formal-matrix extrapolation (parallel projection)

Frozen matrix (design.md §4, V11-A07; **not shrunk**): 60 runs.

```
predicted parallel wall = serial_total_hours / parallel_speedup
                        = 66.72 h / 2.04
                        = 32.69 h
```

| Metric | Value | Gate |
|---|---|---|
| Serial total (#2) | 66.72 h | — |
| Parallel speedup | 2.04× | — |
| Predicted parallel wall | 32.69 h | > 24 h → **blocked** |
| Peak RSS (single run) | 2.70 GiB | < 3 GiB → ok |
| Per-worker efficiency | 0.51 | — |

## Comparison vs #1/#2

| Metric | #1 | #2 (numba) | #3 (parallel) |
|---|---|---|---|
| Per-iteration speedup vs #1 | — | ~11.65× | ~11.65× (same kernel) |
| Wall projection (serial) | 777.33 h | 66.72 h | 66.72 h (same serial basis) |
| Wall projection (parallel) | — | — | **32.69 h** (4 workers) |
| Peak RSS | 2.64 GiB | 2.68 GiB | 2.70 GiB (single-run) |
| Verdict | blocked | blocked | **blocked** |

The parallel path halves the serial wall (66.72 h → 32.69 h) but does not
reach the 24 h limit. With 4 workers on 20 logical cores, per-worker
efficiency is 0.51 — the small cells cause load imbalance. Scaling to more
workers would help only if the efficiency holds; the formal plan (Stage P)
must evaluate this.

## Verdict

**`resource_blocked`** — predicted parallel wall 32.69 h > 24 h (design.md:92-95).
Peak RSS (2.70 GiB) stays under 3 GiB cap (0.30 GiB headroom). The
multiprocessing path (AMEND-2026-08-06-02) provides a 2.04× speedup over the
serial #2 baseline but the 8-cell microbenchmark cells do not saturate 4
workers evenly enough to reach the 24 h gate within 4 workers.

## Notes / scope

- The formal matrix (2×3×5×2, design.md §4) is unchanged; no geometry was
  added, removed, or modified.
- Parallel execution uses `multiprocessing` with spawn-safe `if __name__ == "__main__"` guard; each worker runs the untouched single-threaded
  `run_coupled_mcde` — scientific results are bit-identical to serial
  (asserted by `test_nonbinary_v11_parallel.py`).
- #1/#2 evidence is immutable — this module only reads `microbenchmark2.json`.
- Correctness of the parallel determinism is covered by the 6 new tests in
  `test_nonbinary_v11_parallel.py`; the existing 49 V11 MC-DE / SMP-DE
  tests continue to pass.
- No threshold, winner, gate, or scientific claim is made.
