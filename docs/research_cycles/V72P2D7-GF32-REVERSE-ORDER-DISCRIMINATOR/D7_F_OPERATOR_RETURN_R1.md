# D7-F operator return R1 (one frozen invocation; NOT accepted, NOT solidified)

- UUID: `b6d62184-fd15-483d-947e-01ea66ddc13c`.
- Root: `workspace/d7_f_reverse_order_discriminator_b6d62184-fd15-483d-947e-01ea66ddc13c` (fresh, created by the single authorized run only).
- Authorization: granted once (`a099b257`), consumed by first decoder attempt, revoked immediately after return (`851efb92`) before contents opened. All authorization flags false at return time.
- This document is UNCOMMITTED. No scientific acceptance or generalization is made here. Pre-RESULT review verdict is still required before any solidification.

## Seven-file manifest + no subdirectories

- Files (exactly seven, no subdirectories, `find -mindepth 1 -type d | wc -l` = 0):
  - `manifest.json` (3151 B), `decoder_records.csv` (32429 B, 129 lines), `arm_pairs.csv` (8331 B, 65 lines), `stratum_summary.csv` (396 B, 3 lines), `summary.json` (648 B), `report.md` (266 B), `command_log.txt` (295 B).

## 128-call arithmetic

- `slots_scheduled=128`, `calls_attempted=128`, `calls_completed=128`, `calls_remaining=0`.
- `mandatory_completed=64/64` source marginals; `transfer_invoked=64`, `transfer_blocked=0`; 64 + 64 = 128. No missing/duplicate/retry/resume (`retries=resumes=reruns=0`).
- `slot_idx` sequence exactly 1..128 in frozen order (f outer 1.0→1.2, seeds ascending, per-(f,seed) FWD_SRC/FWD_TGT/REV_SRC/REV_TGT).

## Per-f forward/reverse both-exact 2×2 paired tables (16 seeds each)

- f=1.0: forward_both_exact=0, reverse_both_exact=0 → candidate_only=0, reference_only=0, both=0, neither=16 → `NO_REVERSE_LIFT` (`COVERAGE_OK`, 16/16 eligible both arms).
- f=1.2: forward_both_exact=2 (seeds 2026091302, 2026091304), reverse_both_exact=0 → candidate_only=0, reference_only=2, both=0, neither=14 → `REVERSE_REGRESSION` (`COVERAGE_OK`, 16/16 eligible both arms).

## Stage provenance/eligibility, L1/L2 exact + syndrome separation

- All 128 records `belief_provenance=CHECK_UPDATED`, `finite=True`, `belief_shape_ok=True`; all 64 SOURCE rows `transfer_eligible=True` (TARGET rows carry empty eligibility field by schema); zero blocked second stages.
- Statuses: `converged_exact` ×13 (all exact=True), `converged_no_syndrome` ×115 (all exact=False). Exact rows: 13 (3 FWD_SRC L1, 3 FWD_TGT L2 incl. 2 full forward both-exact arms, 7 REV_TGT L1 with inexact L2 source).
- `exact` vs `syndrome_ok` coincide row-wise in this run (13/13, mismatch 0) but are recorded as separate columns; `both_layers_exact` = AND only (2 arms, both forward at f=1.2).

## Paired labels + first-matching terminal

- Strata: f=1.0 `NO_REVERSE_LIFT`; f=1.2 `REVERSE_REGRESSION`.
- Terminal: `D7_F_REVERSE_ORDER_REGRESSION` (priority 9; no higher-priority terminal triggered). Manifest terminal priority list matches frozen order.

## Crash/nonfinite/watchdog, walls, peak RSS

- `crash_count=0`, `nonfinite_count=0`, `watchdog_timeouts=0`.
- `stored_wall_s=41.2815843069402` (≤1500; equals per-call sum 41.2816); outer wall 44 s (≪1800+30); per-call max 0.4735 s (≪120 s watchdog).
- `peak_rss_bytes=133021696` (~126.9 MiB, strict < 2 GiB).

## Scalar-only forbidden-payload scan

- No `[`/`{` values in any CSV (grep counts 0/0/0); no `array(`/`dtype` in any of the seven files.
- Only `belief_*` hit: column name `beliefs_conditioned` (boolean scalar per row — permitted scalar). Only `prior_*` hit: `prior_candidate` inside the frozen estimator identity string in `manifest.json` (not a persisted prior). No persisted beliefs/priors/symbols/syndromes/vectors/digests.

## Supported/unsupported claim ceiling

- Supported: this single paired order observation on the exact frozen synthetic contract (f=[1.0,1.2], seeds 2026091300..1315, corrected per-Bob-column Model-F, row-layered poly-37 cold max_iter=90 damping=1.0): reverse `L2→L1` recovered both layers exactly on 0 seeds vs forward `L1→L2` on 2 seeds at f=1.2; 0 vs 0 at f=1.0.
- Unsupported: any FER/leakage/reconciliation-efficiency/key-rate estimate, qualification/promotion, real-data performance, general GF32/NB-LDPC claim, alternating-convergence claim, or description of either order as a performance estimate.

## Verifier transcript (STEP 6, filled before review)

- Run exactly once (foreground, direct exit capture from `wait`); never repeated.
- Literal command: `.venv/bin/python scripts/v72p2d7_gf32_reverse_order_discriminator.py --verify workspace/d7_f_reverse_order_discriminator_b6d62184-fd15-483d-947e-01ea66ddc13c` (cwd: repository root).
- Start: local `2026-09-11 22:59:58 +0800` / UTC `2026-09-11 14:59:58 UTC`. End: local `2026-09-11 23:00:00 +0800` / UTC `2026-09-11 15:00:00 UTC`.
- Directly captured exit code: `0`.
- FULL literal stdout: `VERIFY_OK {'ok': True, 'problems': [], 'records': 128, 'terminal': 'D7_F_REVERSE_ORDER_REGRESSION'}`
- FULL literal stderr: (empty).
- Root immutability: all eight names/sizes/mtimes byte-identical before/after verify (dir Size=4096 Modify=2026-09-11 22:57:26.380763500 +0800; manifest.json 3151/22:57:26.369021200; decoder_records.csv 32429/22:57:26.372679900; arm_pairs.csv 8331/22:57:26.374228400; stratum_summary.csv 396/22:57:26.375766500; summary.json 648/22:57:26.378880200; report.md 266/22:57:26.379739300; command_log.txt 295/22:57:26.381764000).
