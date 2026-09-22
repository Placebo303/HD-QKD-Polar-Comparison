# D5 decomposition successor R1 — CAL-only/development discriminator report

- status: `DEVELOPMENT_ONLY / NO_FORMAL_EXECUTION_AUTHORIZATION`
- repo: `D:\Code\HD-QKD_Polar_Comparison`, branch `formal-ir-v72p1-addendum-clean`
- packet: `D5_ROUTE_STOP_AND_DECOMPOSITION_SUCCESSOR_R1_TASK_PACKET.md` (FROZEN_TASK_PACKET)
- prereg: `D5_DECOMPOSITION_SUCCESSOR_PREREG_R1.md` (commit `e4d3af7`, before all scores/calls)
- evidence root: `workspace/d5_decomposition_successor_r1_c765e3010674/` (fresh UUID, development-only)
- premise: `D5_CURRENT_TWO_LAYER_RATE_MOTHER_BP_PATH_STOPPED` (accepted)

## 1. 252-score invariants and top table

CAL-only scoring (S1, 40.8 s, `val_touched=false`, 262144 CAL rows, TRAIN 196608 / TEST 65536 per fold):

- 252/252 reversible ordered partitions enumerated exactly once; all-1024 round trip PASS for every partition.
- Chain identity `|CE_joint − (CE_L1 + CE_L2)|` max `8.88e-16` (< 1e-9) over all partitions/folds.
- `CE_joint` bit-identical (`7.162347`) for all 252 partitions (row-permutation invariant, as required).
- Control `S1=(5,6,7,8,9)` reproduces the accepted discriminator value: `CE_L1 = 3.814742` (c1 E1 mean `3.8147422680`).
- Row range over family: `m1 ∈ {59,60,61}`, `m2 ∈ {50,51,52}`; all 252 eligible (both rows < 64).
- Ranking is decoder-blind (frozen before any call) under lexicographic `(max(CE_L1,CE_L2), CE_joint, CE_L1, S1)`.

Top 10 (all `CE_joint = 7.162347`, all `m = (59,52)`):

| rank | S1 | CE_L1 | CE_L2 | max |
|---|---|---|---|---|
| 1 | 5-6-7-8-9 (current mapping) | 3.814742 | 3.347605 | 3.814742 |
| 2 | 4-5-7-8-9 | 3.815857 | 3.346491 | 3.815857 |
| 3 | 4-6-7-8-9 | 3.816418 | 3.345930 | 3.816418 |
| 4 | 4-5-6-7-9 | 3.817624 | 3.344723 | 3.817624 |
| 5 | 4-5-6-8-9 | 3.818114 | 3.344234 | 3.818114 |
| 6 | 4-5-6-7-8 | 3.819367 | 3.342980 | 3.819367 |
| 7 | 3-4-5-8-9 | 3.823287 | 3.339060 | 3.823287 |
| 8 | 3-4-5-7-9 | 3.823321 | 3.339027 | 3.823321 |
| 9 | 3-5-7-8-9 | 3.823340 | 3.339008 | 3.823340 |
| 10 | 3-4-7-8-9 | 3.823811 | 3.338536 | 3.823811 |

Swapped control `S1=(0,1,2,3,4)`: rank 242, `CE = (3.910601, 3.251747)`, `m = (61,50)`.

## 2. Frozen selection, rows, mothers

Frozen manifest `selected_partitions.json` (S2, before any decoder call; dedup applied — rank-1 coincides with the current-mapping control):

- top-3: `(5,6,7,8,9)` rank 1, `(4,5,7,8,9)` rank 2, `(4,6,7,8,9)` rank 3 — all `m = (59,52)`, eligible.
- controls: `(5,6,7,8,9)` (same entry), `(0,1,2,3,4)` rank 242, `m = (61,50)`, eligible.
- 4 unique frozen candidates; seeds `2026090600..2026090607` paired across all.
- Mothers (deterministic, recorded pre-call): L1 `build_dv3_nested_mother(64,61,61,2026090501)` (M1 = 61 from max eligible m1), L2 `build_dv3_nested_mother(64,59,59,2026090502)`, square `build_dv3_nested_mother(64,64,64,2026090801)` rank-64 asserted.
- Decoder: explicit injection `bind_historical_decoder`, cold start, `max_iter=90`, `damping=1.0`.

## 3. Call accounting and budgets

192 decoder calls used of 600 (4 candidates × 8 seeds × 2 geometries × 3 modes: L1, APP-L2, oracle-L2-diagnostic). Cell visit-once, no retries. Total decoder wall 100.8 s of 6 h; max per-call wall 0.623 s (watchdog 120 s PASS all); peak RSS 124219392 B (< 2 GiB, known all calls); crashes 0; nonfinite 0; exact/syndrome flag disagreement 0/192.

Four-file regression suite: `259 passed, 1 warning in 58.27s` (benign `Unknown config option: cache_dir`); task-owned basetemp removed after resolve+verify; evidence root preserved.

## 4. Paired exact/syndrome/oracle summary (exact counts /8)

| candidate | nonsquare APP e2e | nonsquare oracle-L2 | square APP e2e | square oracle-L2 |
|---|---|---|---|---|
| 5-6-7-8-9 (rank 1, m 59/52) | 0/8 (L1 0/8, APP-L2 0/8) | 6/8 | 0/8 | 8/8 |
| 4-5-7-8-9 (rank 2, m 59/52) | 0/8 | 0/8 | 0/8 | 0/8 |
| 4-6-7-8-9 (rank 3, m 59/52) | 0/8 | 0/8 | 0/8 | 1/8 |
| 0-1-2-3-4 (control, m 61/50) | 0/8 | 0/8 | 0/8 | 0/8 |

Syndrome end-to-end APP: 0/8 everywhere (never counted as success; exact/syndrome stored separately). All 128 APP failures (L1 + APP-L2) saturate at 90 iterations; the 15 oracle hits converge in 3–31 iterations. Median L1 prior truth-mass on failed blocks 0.0591 vs 0.2608 on oracle-hit blocks (scalars only, no belief persistence).

## 5. Terminal classification (§4.5)

Rank-1 `(5,6,7,8,9)`: both rows < 64, end-to-end APP exact 0/8 non-square, zero nonfinite/crash, zero syndrome/exact disagreement → **`DECOMPOSITION_NO_N64_RECOVERY`**.

## 6. Conditional implementation

Not strong → **no production code, no OpenSpec implementation change** (§4.6). Formal mapping, production wiring, roots, constants, CLI phases, accepted artifacts unchanged.

## 7. Strongest supported statement and explicit non-claims

Strongest supported: the CAL-only-optimal reversible 5+5 partition is the current mapping itself, and no tested partition yields nonzero-rate APP recovery at n=64 under the frozen development matrix (development-only routing observation, not a formal result).

Non-claims: no FER/leakage/key-rate claim; no qualification/promotion; no real-data performance claim; no G2 readiness; no universal BP threshold; oracle-L2 counts are diagnostic only and are never recovery.

## 8. Next route

**`D5_GRAPH_MOTHER_SUCCESSOR_PROPOSAL`** (no-recovery terminal: the decomposition family is exhausted without APP signal; graph/mother redesign is the next fallback route, by main-thread proposal — not authorized here).
