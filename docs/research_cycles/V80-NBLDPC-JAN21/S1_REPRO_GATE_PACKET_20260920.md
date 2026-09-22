# V80 S1 m₂=47 Reproducibility Gate — Frozen Packet (2026-09-20)

- Track: **EXPLORE** (synthetic DE-ensemble diagnostics; bounded, reversible; no FER/SKR/qualification/promotion/publication/route-closure claim).
- Branch: `formal-ir-v72p1-addendum-clean` — do NOT switch/commit/push. Fresh additive root only.
- **This packet authorizes NOTHING.** Execution needs a fresh grant + Pre-EXECUTE (Q0–Q6, explicit user authorization, target-root absence, focused tests). Planning/design only here.

## 1. Question / hypothesis

- PRIMARY's sole ≤1.15 point (m₂=47, layer f=1.1375, 1/9 candidates, single confirm seed, non-monotonic in m) — search luck or reproducible? This gate decides whether m₂=47 may serve as any S2 basis.
- FAIL ⇒ m₂=47 NOT usable as S2 basis; S2 blocked pending new direction. PASS ⇒ clears BER-2 only (BER-1 fix + re-verify still required pre-S2).

## 2. Frozen design (no tuning after start)

- Cells: m₂∈{46,47,48} × confirm seeds BOTH {2026094951,2026094952} × R=5 DE restarts = 30 confirm calls. m₂=47 is the verdict cell; 46/48 are pre-frozen controls (no post-hoc promotion).
- Frozen DE config: pop10×gen14, CONFIRM n_samples/max_iter/tol/streak, DV_SUPPORT, H anchors, gamma binding unchanged. Restart r uses gate-local derivation seed+r×7919 (r=0 recovers exact frozen seeds); `frozen_config()` untouched — hash MUST stay `60ab1e44…0da`, else STOP.
- Pass per cell: `converged ∧ 1.0≤f_row≤1.15` (f<1 = SW violation, never pass). Bar (G-REPRO): m₂=47 converges on BOTH seeds with ≥3/5 restarts each AND f stable within ±0.02 across its converged restarts. Miss ⇒ FAIL.

## 3. Budget / ledger (single 3600 s wall window)

- 30 calls × observed PRIMARY-confirm mean ~18 s (≈540 s) / max 31 s (≈930 s) + overhead ≪ 3600 s. RSS≤4 GiB, cpus=1 (frozen BUDGETS). Single-turn, no checkpoint/resume, no `--resume-from` old partials.
- Fresh additive root `workspace/s1_repro_<uuid>`; old roots (`07723233`, `1b079a49`) never opened for write; retained failures immutable.

## 4. Anti-luck controls

- Pre-frozen m set; no post-hoc m selection/promotion; no threshold tuning (1.15/1.0 fixed); NO_RETRY; multi-seed×multi-restart default per AGENTS §10.3; all 30 rows retained (failures immutable, never deleted).

## 5. Accounting (dual reporting, per batch-end review edge c)

- Report BOTH: (a) layer-unit f_row (gate basis); (b) frozen whole-frame-with-tag superframe-n=1024 f: single-frame leak=5·m_total+64 (m_total=m₂+2), superframe leak=4×5·m_total+64, content=1024·H_full (anchor H_full=0.83256272 → m₂=47 f≈1.22). Numbers raw, no reinterpretation.

## 6. Allowed / forbidden

- ALLOWED: runner + its test (`v80_s1_mcde_runner.py`, `test_v80_s1_readiness.py`) for hash-neutral gate mode only + this packet + result record. FORBIDDEN: `src/ experiments/ tools/ results/ outputs_comparison/`, gamma files, any existing workspace-root write, any `frozen_config()`/seed/budget/cap/threshold change, any commit/push.

## 7. Stop rules + return

- STOP (no execution): hash would rotate; any science-input change; temptation to tune thresholds, add m points, retry failures, reuse/resume old roots, or advance S2/S3.
- Return: G-REPRO PASS/FAIL + per-cell table (m,seed,restart,converged,f_layer,f_superframe) + wall/ledger + deltas only. FAIL blocks S2 entry on m₂=47.
- Acceptance ID: **G-REPRO**.

## 8. dv-support note (SEPARATE later arm, NOT in this gate)

- P7 (DV_SUPPORT (2,3,4,5,8,13,20) vs Mitra VN 2–5; possible search dilution at low m) is NOT tested here. Narrow dv support ONLY as a later arm IF G-REPRO passes AND low-m non-convergence persists — separate packet, separate grant.
