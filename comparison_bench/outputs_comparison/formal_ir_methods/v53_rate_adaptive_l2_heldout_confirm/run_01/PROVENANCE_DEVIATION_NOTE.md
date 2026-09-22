# PROVENANCE_DEVIATION_NOTE — v53 run_01

**Scope:** `comparison_bench/outputs_comparison/formal_ir_methods/v53_rate_adaptive_l2_heldout_confirm/run_01/`
**Date:** 2026-08-28
**Affected files (unchanged):** `v53_records.json`, `v53_records.csv`, `v53_summary.json` — not modified by this note.

## Deviation

- **Accepted plan (actual):** `c51b4cd5236a605402fbc58d0d73625dc30e5499`
- **Stale constant in summary:** `v53_summary.json` records `93c12fa5a8524eb5a8a4d071f135c653c746ebaf` as `plan_sha` / provenance reference. This value predates the plan revision and is a stale constant carried into the run.
- **Execution authorization:** correctly bound to implementation `b9b538138ce559f6805c42f2c8bd57a47f1b43e9`. Method, sample, threshold, and run behaviour all correspond to the revised plan.

## Revised-plan alignment (verified)

Run behaviour matches `c51b4cd` / `b9b5381` revisions, not the stale SHA:

- Leakage is **per-source** (not overall-aggregated).
- Rescue counts as `count(!verify)` (not `!=0` semantics).
- `disclosure_per_final` semantics as revised.
- Budget **90–135** iterations (observed: 12 failures, 11 ran full 90 iter).

## Impact assessment

**Classification:** provenance metadata deviation only. No change to performance conclusions.

- Net SKL: **23 → 33 (net +10)**
- Discordance: **10:0**, McNemar **≈ 0.00195**, **+22.2 pp** (45 samples)
- Avg SKL: **1087.33 → 1106.89 (+19.56)**
- Undetected errors: **0**
- Residual: **17 improved / 5 worsened**, avg **−53.1**
- Failure detail: **12 failures, 11 reached 90 iter**

## Action

- No rewrite of the three original run files. This note is the additive correction.
- Downstream consumers should treat `c51b4cd5236a605402fbc58d0d73625dc30e5499` as the authoritative plan and `b9b538138ce559f6805c42f2c8bd57a47f1b43e9` as the authorized implementation for this run.
