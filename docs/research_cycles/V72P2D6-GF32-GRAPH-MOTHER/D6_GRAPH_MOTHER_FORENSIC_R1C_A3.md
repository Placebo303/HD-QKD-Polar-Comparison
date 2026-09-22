# D6 Graph Mother Forensic Reconstruction R1c-A3 (read-only, zero decoder)

Status: `FORENSIC_R1C_A3`. Script
`workspace/a3_forensic_66cafb029b6643b888627cba1b3e5c5b/forensic_reconstruct.py`
(task-owned temp, uncommitted) read only the immutable six-file root
`workspace/d6_graph_mother_r1c_dd8c4defe67742a8b2bc1b634c116d6b` plus frozen
builder code (`build_support`, structure-only, no decoder). Evidence root
unedited. Full table: `forensic_table.txt` beside the script.

## 1. Keys

- 184 rows; old key `(arm,seed,point,mode)` → 144 unique, 40 duplicate
  groups (all T1/M1 scaling n128-vs-n256 collisions: 24 T1 groups ×3 modes +
  16 M1 groups ×2 modes, each ×2 widths).
- Corrected key `(n,arm,seed,point,mode)` → 184 unique, zero duplicates.
  `call_idx` 1..184 continuous (independently verified by verifier check 2).

## 2. Counts by `(n,arm,seed,point,mode)`

- `(64,B0/B1/T1)`: 24 rows each = 4 canary seeds × 2 points × 3 modes.
- `(64,T3)/(64,M1)`: 16 rows each = 4 × 2 × 2 modes (L1 + L2-oracle; L2-APP
  skipped placeholder never persisted — consistent with L1 crash → `q=None`).
- `(128,T1)/(256,T1)`: 24 each (3 modes, all decoded).
- `(128,M1)/(256,M1)`: 16 each (L1 + L2-oracle crash pattern).
- Seeds: n64 × canary `2026091000..03` (26 rows each: B0/B1/T1 ×6 + T3/M1 ×4
  … 3×6+2×4=26 ✓); n128/n256 × scaling `2026091100..03` (10 each: T1 ×6 +
  M1 ×4 ✓).

## 3. Attempted / crash / nonfinite / error

- attempted (`call_idx>=0`): 184; skipped placeholders: 0.
- crash=True: 64; finite!=True: 64; identical row sets.
- errors: `''` ×120; `ValueError('Check node requires degree >= 2')` ×64.
- crash by (width,arm): `(64,T3)` 16, `(64,M1)` 16, `(128,M1)` 16,
  `(256,M1)` 16. Zero crashes elsewhere. Zero non-degree errors.

## 4. Stage partitions (seed-domain × width)

- canary (`n64` + canary seeds): 104 rows, arms B0/B1/T1/T3/M1. No scaling
  seed present — non-contamination holds.
- scaling-n128 (scaling seeds): 40 rows, arms T1+M1 = frozen fallbacks
  (`best_T=T1_PEG_DV3`, `best_M=M1_ACCUMULATOR_FOREST_MAX`) ✓.
- scaling-n256: 40 rows, same arms ✓.
- confirmation (seeds `2026091010..25`): 0 rows — stage EMPTY, not safety.
- outside all seed domains: 0.

## 5. Selection / advancement / stop-width recomputation

- Canary per-cell `app=(L1.exact and L2-APP.exact)` recomputed per arm:
  all `f12_exact=0, sq_exact=0` — exactly matches `summary.canary`.
- `select_advancement` recomputed over T/M pool ⇒ `[]` = stored `advancing`.
- Scaling sig per (arm,n): T1 f12/sq 0 at both widths (per-row exacts exist
  but never coincide L1+APP in one cell); M1 all-crash ⇒ 0. Advancing empty
  at n128 → width loop continued to n256; empty again → no confirmation
  dispatch, width stays 64, terminal fell through to stored
  `D6_GRAPH_TOPOLOGY_NO_USEFUL_RECOVERY`.

## 6. Stored vs recomputed terminal (A3 rules)

- 64 attempted degree rows ⇒ crash precedence fires; all 64 carry the degree
  `ValueError` ⇒ structure-invariant class.
- stored: `D6_GRAPH_TOPOLOGY_NO_USEFUL_RECOVERY`; recomputed:
  `D6_GRAPH_STRUCTURE_INVARIANT_BLOCKED`; agree=False.
- Strongest allowed claim: implementation/structure-blocked development
  attempt; topology-no-recovery is unsupported by this evidence.

## 7. Degree-failure source attribution (no decoder calls)

- Raised at `v35_algorithm_development.py:465` (`_check_update_log_batch`,
  `dc<2`): the H slice seen by the decoder contains check rows of degree <2.
- Code-independent integer proof (M1): `zero_rows=0`, `rmax=3` ⇒ with
  `x=#deg-1` rows, `sumsq-k = 3y+8z`; M1-n64-L1-k64 (`sumsq=364,k=64`) forces
  `x=5t-36 ∈ {4,9,…}` ⇒ ≥4 degree-1 rows necessarily. Same residue argument
  holds at every dispatched M1 prefix (all rmax=3, zero_rows=0).
- Direct structure-only rebuild (`build_support`, deterministic; builder code
  identical between generation commit `15f1de79` and HEAD — that commit's
  mother diff is 2-line fsync-only, verified via `git show`): every
  dispatched T3/M1 slice has min row degree 1 (9–83 rows with degree ≤1:
  T3-n64 k59/k64/k52/k64; M1-n64/n128/n256 f1.2+square prefixes).
- Negative controls (same rebuild): all succeeding slices (T1-n64/n128/n256,
  B0-n64) have min degree ≥2. Bidirectional link: degree<2 ⇔ crash.
- Transport/precondition excluded: crashes are arm-perfect (only T3/M1, all
  seeds/points, L1+oracle identically per cell) while the same 18-worker pool
  and decoder binary delivered 120 clean rows for B0/B1/T1;
  `determinism_ok=True` on all prefixes. Random IPC corruption or a decoder
  precondition defect cannot produce this pattern.
- Verdict: **invalid frozen graph structure** for T3_SC_DV3_W4 and
  M1_ACCUMULATOR_FOREST_MAX at all dispatched prefixes (degree-1 check rows
  admitted by audits that gate on `zero_rows`/`eligible` but never on minimum
  check degree). No `NOT_VERIFIABLE` needed; guessing was not used.

## 8. Consequences for A3-03

Verifier must (i) key identity with `n`, (ii) recompute canary/scaling/
confirmation in separated partitions, (iii) apply crash precedence with the
degree→`STRUCTURE_INVARIANT` class, (iv) label confirmation EMPTY, (v) print
stored + recomputed terminals with agreement flag — exactly the frozen A3
contract. No execution, science, or history change is implied.
