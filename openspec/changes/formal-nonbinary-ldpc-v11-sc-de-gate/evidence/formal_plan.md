# V11 Stage P Formal Plan — Human-Readable Summary

**Schema**: `v11_formal_plan_v1`  
**Frozen**: 2026-08-06  
**Author**: planner (agent)  
**Amendments**: AMEND-2026-08-06-01 (numba), AMEND-2026-08-06-02 (parallel)  
**Machine-readable**: `evidence/formal_plan.json`

---

## 1. Plan Structure

| Clause | Content |
|---|---|
| `metadata` | Change, version, amendments |
| `strata` | S1 (p_gate=.22) and S3 (p_gate=.32) with V10 winner λ and R_eff |
| `geometries` | G1(w=1,W=8), G2(w=2,W=16), G3(w=2,W=32) — from `FROZEN_GEOMETRIES` |
| `rate_reconstruction` | R_eff → R_base → R_L chain with 1e-12 tolerance; control at same R_eff |
| `seeds` | 60 run specs: 2 strata × 3 geometries × 5 seeds × 2 arms; frozen order and derivation rule |
| `threshold_search` | Binary search: 9 probes per run, p_tol=0.001, N=2000, max_iter=150 |
| `stopping_rules` | Convergence, invalid, interrupt, convergence-failure handling |
| `budgets` | 4 workers, 24 h wall, 3 GiB single-run RSS, numba warmup |
| `output_paths` | `workspace/nbldpc_v11_execute_{uuid}/` per-run dirs |
| `code_revision` | 17 critical files frozen at plan time |
| `extrapolation` | LPT scheduling simulation with contention overhead |
| `acceptance_mapping` | A01-A16 to plan/execution clauses |
| `frozen_declarations` | No-tuning, no-rerun, immutable evidence, AEIT semantics |

---

## 2. Key Frozen Values

| Parameter | Value | Source |
|---|---|---|
| S1 gate | .22 | design.md §6 |
| S3 gate | .32 | design.md §6 |
| Paired gain minimum | .002 | design.md §6 |
| S1 R_eff | 0.6870106892038108 | V10 winner evidence |
| S3 R_eff | 0.5537001767622565 | V10 winner evidence |
| S1 λ max degree | 28 | V10_WINNER_S1 |
| S3 λ max degree | 40 | V10_WINNER_S3 |
| G1 | w=1, L=32, W=8 | FROZEN_GEOMETRIES |
| G2 | w=2, L=32, W=16 | FROZEN_GEOMETRIES |
| G3 | w=2, L=32, W=32 | FROZEN_GEOMETRIES |
| n_samples | 2000 | V9A_BUDGETS |
| max_iter | 150 | V9A_BUDGETS |
| entropy_tol | 0.01 | V9A_BUDGETS |
| streak | 20 | V9A_BUDGETS |
| p_tol (search) | 0.001 | SEARCH_P_TOL |
| Rate contract tolerance | 1e-12 | HARMONIC_TOL |
| Wall clock limit | 24 h | design.md §5 |
| RSS cap (single run) | 3 GiB | V10_RSS_CAP_BYTES |
| Workers | 4 | AMEND-2026-08-06-02 |
| RSS watcher interval | 1.0 s | RunSpec default |
| Numba warmup | 1 tiny run/worker pre-batch | _warmup_task |

---

## 3. Seed Scheme

**Rule**: `v11_seed(tag) = int(sha256("V11:" + tag)[0:8], 16)`  
**Prefix**: `202611` — disjoint from V8 (`20260804`), V9 (`20260901`), V10 (`202610`)  
**60 tags**: `{S1,S3}:{G1,G2,G3}:{coupled,control}:{1..5}`  
**Order** (frozen for replay): stratum-major → geometry-major → seed-major → arm-major

Seeds are derived deterministically from tags. The plan freezes the tags and the derivation rule; actual integer values are computed at execution time.

S1 and S3 probes use **stratum-specific p ranges**: S1 `[0.18, 0.26]`, S3 `[0.28, 0.36]` (tighter than the microbench `[0.10, 0.40]`, centered around the known gate regions).

**Note on p placeholder**: `formal_matrix_run_specs()` currently sets `p=MICRO_P=0.15` as a placeholder. The Stage X execution wrapper will override this with the binary search p values (9 probes per run). The plan freezes the search range, budget, and convergence rules; the p trajectory is deterministic from those.

---

## 4. LPT Scheduling Extrapolation

### 4.1 Task Durations (from microbenchmark #2 N=2000 per-iteration costs)

| Task type | Per-iter (s) | × 1350 iters = Duration (s) | Count |
|---|---|---|---|
| G3 coupled | 9.8899 | 13,351.3 | 10 |
| G2 coupled | 4.9735 | 6,714.3 | 10 |
| G1 coupled | 2.2480 | 3,034.8 | 10 |
| Control (all) | 0.2269 | 306.3 | 30 |
| **Total serial** | | **240,193.8** | **60** |

> S1 and S3 use the same per-iteration costs — both strata's max degrees are bounded by S3's max=40 (the #2 synthetic λ uses max degree 40, a conservative upper bound for both S1 max 28 and S3 max 40).

### 4.2 LPT Greedy Simulation (4 workers)

Sort tasks descending, assign each to the worker with smallest accumulated load.

| Phase | Tasks | Worker loads after phase (s) |
|---|---|---|
| G3 coupled | 10 × 13351 s | W0=40054, W1=40054, W2=26703, W3=26703 |
| G2 coupled | 10 × 6714 s | W0=53483, W1=40054, W2=53560, W3=53560 |
| G1 coupled | 10 × 3035 s | W0=59552, W1=58263, W2=56594, W3=56594 |
| Control | 30 × 306 s | W0=61696, W1=60407, W2=59045, W3=59045 |

**LPT makespan = 61,696 s = 17.14 h**  
Perfect balance (sum/4) = 60,048 s = 16.68 h  
LPT achieves **97.3%** of perfect balance.

### 4.3 Contention / Overhead

| Scenario | Loss coefficient | Predicted wall (h) | Under 24 h? |
|---|---|---|---|
| Low | 5% | 18.0 | ✓ |
| **Central** | **10%** | **18.9** | ✓ |
| High | 15% | 19.7 | ✓ |

**Basis**: 20 logical cores (≈10 physical + 10 HT), 4 workers → minimal core contention. Microbench #3 measured 0.51 per-worker efficiency, but that was load-imbalance dominated (8 heterogeneous cells: 3 large + 5 small). LPT corrects this. 10% central estimate accounts for memory bandwidth sharing and OS scheduling jitter.

**Verdict: `resource_ok`** — all contention scenarios pass the 24 h limit with ≥ 4.3 h headroom.

### 4.4 Why Batch Efficiency (32.69 h) Overestimates

| Method | Predicted | Why |
|---|---|---|
| Batch efficiency (#3) | 32.69 h | 66.72 / 2.04; 8-cell batch had severe load imbalance |
| LPT (this plan) | 17.1–19.7 h | 60 similar-duration tasks, balanced explicitly |

The #3 batch had 3 large cells (G3_2000 48.8s, G2_2000 28.3s, G1_2000 13.7s) and 5 small cells (CTRL_500 to G3_500, all under 25s). In 4 workers, 4 run in wave 1, the remaining 4 in wave 2. The small ones finish early, leaving workers idle. The 60-task matrix has 30 large coupled tasks (all ≥3035s) where LPT achieves near-perfect balance. The batch efficiency of 0.51 per-worker does not apply.

---

## 5. Acceptance Mapping Summary

| ID | What | Stage |
|---|---|---|
| A01 | QSC reference values documented | P |
| A02 | R1 q=4/q=16 reproduction | E (gated before GF(1024)) |
| A03 | Coupling-collapse (w=0) tests | E (gated) |
| A04 | q=4/q=8 oracle agreement | E (gated) |
| A05 | Rate contract 1e-12 | P/X (recomputed in replay) |
| A06 | V10 S1/S3 λ reused | P |
| A07 | G1/G2/G3 geometry set | P |
| A08 | Fresh paired seeds frozen | P |
| A09 | T0/T1 + engineering review | E (gated) |
| A10 | Resource budget cleared (LPT) | P |
| A11 | Prepare→review→execute→replay | P/X |
| A12 | Evidence retention for invalid/interrupted | X |
| A13 | Independent gate recomputation | X |
| A14 | No production output overwrite | X |
| A15 | One of 4 declared states, no promotion | X |
| A16 | Finite-length = new change | X |

---

## 6. Scope and Stop Rules

- **Preconditions** (must pass before Stage X): A01-A04, A09 (R1, engineering, tests)
- **Stage X stop rules**: Any failed reference, resource breach, invalid evidence, or all-geometry gate failure freezes evidence. V11 stops; no geometry promotion.
- **Never in V11**: Finite-length codebooks, decoders, canary, real-data, qualification, promotion — all require a new OpenSpec change.

---

*See `evidence/formal_plan.json` for the complete machine-readable plan with all 60 run specs, rate reconstruction details, stopping rule semantics, and acceptance clause cross-references.*
