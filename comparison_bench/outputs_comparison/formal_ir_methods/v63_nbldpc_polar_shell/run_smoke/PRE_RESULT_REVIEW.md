# PRE_RESULT_REVIEW — V63 NB-LDPC Polar Shell Smoke (9-block)

Date: 2026-08-30
Cycle: V63P0 / formal-ir-v63-nbldpc-polar-shell
Scope: `comparison_bench/outputs_comparison/formal_ir_methods/v63_nbldpc_polar_shell/run_smoke/` — smoke only
Artifacts reviewed: `v63_records.json`, `v63_records.csv`, `v63_summary.json` (frozen, not overwritten) + `v63_pre_result_report.json` (this cycle)

## 1. Binding

- accepted_plan_sha: `397c1bb6d60cdf6dfa00d34bfae2eb1ca231d20a` (short `397c1bb6`)
- implementation_sha: `36c24c38d0ce7dac4a76580d175f2d3dfdc1e3d5` (short `36c24c38`)
- registry: `INTEGRATION_REPLAY_SMOKE` 9 blocks (3 per source: 1M / 1p5M / 2M) — `docs/research_cycles/V63P0/v63_smoke_registry.json`
- run_smoke: 9 records, `v63_summary.json` total_blocks 9, registry_type `INTEGRATION_REPLAY_SMOKE`
- 90-block formal registry (`v63_dev_registry.json`, 90 blocks) — **NOT executed in this smoke** (see §7)

## 2. Overall / Per-Source Accepted / Exact / Undetected

| Scope | accepted | exact | undetected |
|-------|----------|-------|------------|
| overall | 9/9 | 9/9 | 0 |
| 1M | 3/3 | 3/3 | 0 |
| 1p5M | 3/3 | 3/3 | 0 |
| 2M | 3/3 | 3/3 | 0 |

Source: `v63_records.json` — every record has `accepted:true`, `exact:true`, `undetected:false`. Per-source counts verified by grouping on `source`.

## 3. Four-Class Counts

- exact: **9**
- detected (decode_failed / non-exact detected): **0**
- decoder_non_syndrome: **0**
- undetected: **0**

Sum = 9. No block falls outside `exact`; `undetected` isolation satisfied (never merged into success/FER).

## 4. Verification: syndrome_ok / tag_ok

- syndrome_ok: **9/9**
- tag_ok: **9/9**
- Derivation: **`exact=true => verify=true => syndrome_ok && tag_ok`** — mechanical derivation. Smoke records carry `exact:true` only when decoder verification passed both syndrome check and tag check; no independent syndrome/tag fields are invented. Pre-result report records this derivation explicitly.

## 5. Leakage Decomposition (per block)

Base per source: 1M **1064** / 1p5M **1094** / 2M **1104** bits.
Conditional delta: **delta8 +40**, **delta16 +80**. **tag64 already included in base, counted only once** (not re-added on delta stages).

| block_id | source | stage_used | leak_total | decomposition |
|----------|--------|------------|------------|---------------|
| v63_smoke_1M_0018 | 1M | delta8 | 1104 | 1064 + 40 |
| v63_smoke_1M_0245 | 1M | base | 1064 | 1064 + 0 |
| v63_smoke_1M_0392 | 1M | base | 1064 | 1064 + 0 |
| v63_smoke_1p5M_0004 | 1p5M | delta16 | 1174 | 1094 + 80 |
| v63_smoke_1p5M_0333 | 1p5M | delta16 | 1174 | 1094 + 80 |
| v63_smoke_1p5M_0546 | 1p5M | base | 1094 | 1094 + 0 |
| v63_smoke_2M_0004 | 2M | delta8 | 1144 | 1104 + 40 |
| v63_smoke_2M_0403 | 2M | delta8 | 1144 | 1104 + 40 |
| v63_smoke_2M_0721 | 2M | base | 1104 | 1104 + 0 |

Stage counts: base **4**, delta8 **3**, delta16 **2** — matches `v63_summary.json:stage_used`.
Total disclosed: **10066** bits, overall_avg **1118.44**, per_source_total 1M **3232** / 1p5M **3442** / 2M **3392**. Cross-checked: Σ leak_total = 10066 = `total_disclosed_bits`.

## 6. PA Input

- PA input total: **10066 bits**, label **`POLAR_REFERENCE_PROXY`**
- Semantics: PA input == total disclosed bits for this smoke (all 9 exact); no additional PA correction bits.

## 7. Calls / Registry / Not-Run Declaration

- Calls: **25** total, hard_cap **36**, budget `9 L1 + 9 base + ≤9 stage1 + ≤9 stage2 = 18–36`
- Breakdown: **4×2 + 3×3 + 2×4 = 8 + 9 + 8 = 25** (base blocks cost 2 calls, delta8 cost 3, delta16 cost 4)
- Registry: smoke is 9 blocks from `v63_smoke_registry.json`; formal 90-block registry `v63_dev_registry.json` exists but **no 90-block run was executed** — no `run_01` with 90 blocks under the formal output root.
- Plan / Implementation: Plan `397c1bb6`, Implementation `36c24c38` as recorded in `v63_summary.json:accepted_plan_sha` / `head_sha`.

## 8. Consistency & Read-Only Review Readiness

- No decoder re-run; no overwrite of `v63_records.json` / `v63_records.csv` / `v63_summary.json`.
- `v63_pre_result_report.json` fields are byte-consistent derivations of those three files.
- `py_compile` check: JSON validity confirmed (no Python syntax to compile in run_smoke; `python -m py_compile` not applicable — `python -m json.tool` validation passed).
- Ready for independent read-only pre-result review; any discrepancy triggers rework before solidification.

## Verdict

PRE_RESULT_REVIEW **PASS (smoke)** — 9/9 exact, 0 undetected, leakage/syndrome/tag/PA/calls accounting verified against frozen records; 90-block formal execution explicitly not claimed.
