# V64 Block-Level Dual-Tag Audit — decoder-free — 24-block fresh run_01 (80c35647)

**Cycle**: V64P0 / `formal-ir-v64-full-symbol-verification-correction`
**Run**: `comparison_bench/outputs_comparison/formal_ir_methods/v64_full_symbol_verification/run_01` (commit `80c35647...`)
**Accepted Plan SHA**: `760cb2967c7f5d5548a68f056458ef89398de3f2`
**Head at solidify**: `80c35647374e48d1088323b28b81d738007fd5cc` (HEAD == origin/formal-ir-mainline)
**Registry**: `v64_fresh_registry.json` 24 blocks, 8/source, `deterministic_four_consecutive_frames_heldout_fresh_v64`, gap≥4, zero overlap V48–V63
**Data SHA**: `84d62779` (d=1024 bw=200 nearest legacy_v1)
**Method**: decoder-free read-only audit — no decoder rerun, no `decode_*` invocation, no artifact mutation; `same_decode_single_tag` dual reporting from single 64-bit tag `compute_tag_64(s=32*u1_hat+u2_hat)` canonical, verified via `v64_records.json` + `v64_summary.json` + `v64_records.csv` + `v64_fresh_registry.json`
**Audit date (UTC)**: 2026-08-31 — additive on top of pushed Head 80c35647, additive only

---

## 1. Scope & Invariants

- Single 64-bit tag computed once per block on `s_hat = 32*u1_hat + u2_hat` (10-bit symbol, GF32 poly37 sub-symbols); `tag_ok_l2` = `tag(x2_hat)` vs `tag(x2_true)` is view on same `s_hat` low-half, `tag_ok_full` = `tag(s_hat)` vs `tag(s_true)` canonical. No double calls, no double leak (leak `5*m_total +64` counted once, tiers `base 1064/1094/1104 +40/+80` per `stage_used`).
- Per-block verdict: `accepted_* = syndrome_ok_l2 && tag_ok_*`; `undetected_* = accepted_* && !exact_*`; `intercepted_u1_only = !exact_u1 && exact_l2 && syndrome_ok_l2 && tag_ok_l2 && !tag_ok_full` (requires `exact_u1==False` observed).
- V63 attribution for `v63_dev_1M_0133` remains `INCOMPLETE` (exact_u1/l2, syndrome, tag splits missing in V63 records); this audit does NOT retro-explain that block — fresh run is semantic correction + performance signal only.
- All 24 blocks `exact_u1==True` thus `exact_full == exact_l2` by construction this run; any future `exact_u1==False` would separate L2 vs full deltas.

---

## 2. Per-Block Table (24/24 — exact values from `v64_records.json`)

| # | block_id | source | frame_ids | exact_u1 | exact_l2 | exact_full | tag_ok_l2 | tag_ok_full | syndrome_ok_l1 | syndrome_ok_l2 | stage_used | leak_total | accepted_l2 | accepted_full | undetected_l2 | undetected_full | errors_u1 | errors_u2 |
|---|----------|--------|-----------|----------|----------|------------|-----------|-------------|----------------|----------------|------------|------------|-------------|---------------|---------------|---------------|-----------|-----------|
| 1 | v64_fresh_1M_00 | 1M | [1674,1675,1676,1677] | True | True | True | True | True | True | True | delta8 | 1104 | True | True | False | False | 0 | 0 |
| 2 | v64_fresh_1M_01 | 1M | [1723,1724,1725,1726] | True | True | True | True | True | True | True | delta16 | 1144 | True | True | False | False | 0 | 0 |
| 3 | v64_fresh_1M_02 | 1M | [1764,1765,1766,1767] | True | True | True | True | True | True | True | base | 1064 | True | True | False | False | 0 | 0 |
| 4 | v64_fresh_1M_03 | 1M | [1847,1848,1849,1850] | True | True | True | True | True | True | True | base | 1064 | True | True | False | False | 0 | 0 |
| 5 | v64_fresh_1M_04 | 1M | [1878,1879,1880,1881] | True | True | True | True | True | True | True | base | 1064 | True | True | False | False | 0 | 0 |
| 6 | v64_fresh_1M_05 | 1M | [1907,1908,1909,1910] | True | True | True | True | True | True | True | delta16 | 1144 | True | True | False | False | 0 | 0 |
| 7 | v64_fresh_1M_06 | 1M | [1963,1964,1965,1966] | True | True | True | True | True | True | True | delta16 | 1144 | True | True | False | False | 0 | 0 |
| 8 | v64_fresh_1M_07 | 1M | [1984,1985,1986,1987] | True | True | True | True | True | True | True | delta16 | 1144 | True | True | False | False | 0 | 0 |
| 9 | v64_fresh_1p5M_00 | 1p5M | [2236,2237,2238,2239] | True | True | True | True | True | True | True | delta8 | 1134 | True | True | False | False | 0 | 0 |
| 10 | v64_fresh_1p5M_01 | 1p5M | [2339,2340,2341,2342] | True | True | True | True | True | True | True | base | 1094 | True | True | False | False | 0 | 0 |
| 11 | v64_fresh_1p5M_02 | 1p5M | [2437,2438,2439,2440] | True | True | True | True | True | True | True | delta8 | 1134 | True | True | False | False | 0 | 0 |
| 12 | v64_fresh_1p5M_03 | 1p5M | [2502,2503,2504,2505] | True | True | True | True | True | True | True | base | 1094 | True | True | False | False | 0 | 0 |
| 13 | v64_fresh_1p5M_04 | 1p5M | [2559,2560,2561,2562] | True | False | False | False | False | True | False | delta16 | 1174 | False | False | False | False | 0 | 42 |
| 14 | v64_fresh_1p5M_05 | 1p5M | [2624,2625,2626,2627] | True | True | True | True | True | True | True | base | 1094 | True | True | False | False | 0 | 0 |
| 15 | v64_fresh_1p5M_06 | 1p5M | [2704,2705,2706,2707] | True | True | True | True | True | True | True | delta8 | 1134 | True | True | False | False | 0 | 0 |
| 16 | v64_fresh_1p5M_07 | 1p5M | [2751,2752,2753,2754] | True | False | False | False | False | True | False | delta16 | 1174 | False | False | False | False | 0 | 294 |
| 17 | v64_fresh_2M_00 | 2M | [2928,2929,2930,2931] | True | True | True | True | True | True | True | base | 1104 | True | True | False | False | 0 | 0 |
| 18 | v64_fresh_2M_01 | 2M | [3049,3050,3051,3052] | True | True | True | True | True | True | True | base | 1104 | True | True | False | False | 0 | 0 |
| 19 | v64_fresh_2M_02 | 2M | [3163,3164,3165,3166] | True | True | True | True | True | True | True | delta16 | 1184 | True | True | False | False | 0 | 0 |
| 20 | v64_fresh_2M_03 | 2M | [3256,3257,3258,3259] | True | True | True | True | True | True | True | base | 1104 | True | True | False | False | 0 | 0 |
| 21 | v64_fresh_2M_04 | 2M | [3351,3352,3353,3354] | True | True | True | True | True | True | True | base | 1104 | True | True | False | False | 0 | 0 |
| 22 | v64_fresh_2M_05 | 2M | [3458,3459,3460,3461] | True | True | True | True | True | True | True | base | 1104 | True | True | False | False | 0 | 0 |
| 23 | v64_fresh_2M_06 | 2M | [3557,3558,3559,3560] | True | True | True | True | True | True | True | delta8 | 1144 | True | True | False | False | 0 | 0 |
| 24 | v64_fresh_2M_07 | 2M | [3626,3627,3628,3629] | True | True | True | True | True | True | True | delta8 | 1144 | True | True | False | False | 0 | 0 |

> Verified: `rg` zero drift on `760cb296`/`80c35647` bindings; table values re-read from `v64_records.json` exact.

Invariant per row: `exact_full == (exact_u1 && exact_l2)` PASS 24/24; `accepted_l2 == (syndrome_ok_l2 && tag_ok_l2)` PASS 24/24; `accepted_full == (syndrome_ok_l2 && tag_ok_full)` PASS 24/24; `undetected_* == (accepted_* && !exact_*)` PASS 24/24.

---

## 3. L2 vs Full Delta Table

### 3.1 Overall (denominator 24)

| Metric | L2 | Full | Delta (Full−L2) |
|--------|----|------|-----------------|
| exact | 22/24 | 22/24 | 0 |
| accepted | 22/24 | 22/24 | 0 |
| undetected | 0/24 | 0/24 | 0 |
| tag_ok (exact blocks imply tag_ok) | 22/24 True | 22/24 True | 0 |
| intercepted_u1_only | — | 0/24 | 0 |

Source: `v64_summary.json` `accepted_l2==accepted_full==22`, `undetected_l2==undetected_full==0`, `l2_vs_full.delta_*==0` cross-checked against per-block sums (this audit recomputed).

### 3.2 Per-Source (denominator 8 each)

| Source | exact_l2 | exact_full | Δ exact | accepted_l2 | accepted_full | Δ accepted | undetected_l2 | undetected_full | Δ undetected | intercepted_u1_only |
|--------|----------|------------|---------|-------------|---------------|------------|---------------|-----------------|--------------|---------------------|
| 1M | 8/8 | 8/8 | 0 | 8/8 | 8/8 | 0 | 0/8 | 0/8 | 0 | 0/8 |
| 1p5M | 6/8 | 6/8 | 0 | 6/8 | 6/8 | 0 | 0/8 | 0/8 | 0 | 0/8 |
| 2M | 8/8 | 8/8 | 0 | 8/8 | 8/8 | 0 | 0/8 | 0/8 | 0 | 0/8 |

Recomputed from `v64_records.json` — matches `v64_summary.json` `per_source[*].l2_vs_full` (all zeros) and `per_source[*].intercepted_u1_only==0`.

---

## 4. 24/24 Dual-Caliber Consistency Table

| Check | Definition | Result |
|-------|------------|--------|
| tag_ok consistency | `tag_ok_l2 == tag_ok_full` per block | **24/24 PASS** (22 True/True, 2 False/False) |
| accepted consistency | `accepted_l2 == accepted_full` per block | **24/24 PASS** |
| undetected consistency | `undetected_l2 == undetected_full` per block | **24/24 PASS** (all False) |
| exact decomposition | `exact_full == exact_u1 && exact_l2` | **24/24 PASS** (exact_u1 always True) |
| syndrome coherence | `syndrome_ok_l2 == False` iff `exact_l2==False` in this run | 2/2 fail blocks both `syndrome_ok_l2==False`, 22/22 pass `True` — coherent |
| intercepted_u1_only | `!exact_u1 && exact_l2 && syndrome_ok_l2 && tag_ok_l2 && !tag_ok_full` | **0/24** — none observed |
| same_decode_single_tag | flag in records | **24/24 True** — single tag dual-reported, no extra leak |

**Overall dual-caliber identity**: `accepted_l2 ≡ accepted_full` and `undetected_l2 ≡ undetected_full` on all 24 blocks. Two failures (`1p5M_04`, `1p5M_07`) are L2 syndrome+tag joint rejections, not L2-pass/full-reject splits.

---

## 5. Interpretation — What Δ=0 Means and Does NOT Mean

- **This run Δ=0 does NOT constitute empirical proof of U1-only interception.** `intercepted_u1_only>0` would require observing `exact_u1==False && exact_l2==True && tag_ok_l2==True && tag_ok_full==False`. This run has `exact_u1==True` on **all 24 blocks** (`24/24`), so the interception condition is untestable here — numerator and denominator for that case are zero. Claiming "full tag intercepted a U1-only error" would be unsupported.
- **What Δ=0 does show**: the semantic fix is correctly wired — `tag_ok_full` is computed on `s_hat=32*u1+u2` and reported alongside `tag_ok_l2` from the same single 64-bit tag; no double-counted leak, no hidden double-call budget. The budget code (`base24 + stage1≤24 + stage2≤24 =48–96 hard cap96`, actual 68 calls) and leak decomposition (`base +40/+80`, tag 64 once) are consistent.
- **Relation to V63**: V63 `v63_dev_1M_0133` attribution remains `ATTRIBUTION_INCOMPLETE` (missing `exact_u1/l2`, `syndrome_ok_*`, `tag_ok_l2` per `docs/research_cycles/V64P0/v64_attribution.json`). V64 fresh run does not re-diagnose that historical block; it provides a **V63-case-consistent interpretation**: had a U1-only error occurred, the L2-only scope of V63 would have accepted while V64 full would reject — but this behavior is **by construction/semantics**, not by observed interception in V64-24. No discordance was observed, so no new root-cause claim is warranted.
- **Gate reading**: `exact_full 22/24 (91.7%)` exceeds `19/24 (79.17%)` and per-source `8/8, 6/8, 8/8` meet `≥6/8`; `undetected_full==0` and `all exact tag_ok_full==True` pass. L2 vs full identical, so L2 gate and full gate are equivalent on this run.

---

## 6. Budget, Leak & Provenance Cross-Check (decoder-free)

- **Calls**: `total 68` (`L1 24 + base24 + stage1 13 + stage2 7`), hard cap 96 PASS; per-block `2/3/4` matches `base:11 / delta8:6 / delta16:7`.
- **Leak**: total `26896` bits (`8872/9032/8992` per source), decomposition verified per-block `base/delta8/delta16` consistent with `H` provenance (`1M m2=184→m_total base 200; 1p5M 190→206; 2M 192→208` plus tag64).
- **Registry provenance**: `BLOCK_LENGTH 1024`, `pairs 1024`, `sampling deterministic_four_consecutive_frames_heldout_fresh_v64`, `gap≥4`, `H 400/554/729, base 1600/2213/2916, K2 12/84/254` — matches `v64_fresh_registry.json` entries.
- **Artifacts read, not written**: `v64_records.json:794 lines`, `v64_summary.json:614 lines`, `v64_records.csv:25 lines`, `v64_fresh_registry.json:506 lines` — audited read-only.

---

## 7. Reproduction

```bash
git rev-parse HEAD  # expect 80c35647...
python -c "import json,pathlib; j=json.loads(pathlib.Path('comparison_bench/outputs_comparison/formal_ir_methods/v64_full_symbol_verification/run_01/v64_records.json').read_text()); print(len(j), all(r['tag_ok_l2']==r['tag_ok_full'] for r in j), all(r['accepted_l2']==r['accepted_full'] for r in j))"
# compare to v64_summary.json l2_vs_full
rg -n "tag_ok_l2|tag_ok_full|accepted_l2|accepted_full|l2_vs_full" comparison_bench/outputs_comparison/formal_ir_methods/v64_full_symbol_verification/run_01/
```

---

## 8. Decoder-Free Guarantee & Non-Mutation

- No `decode_row_layered_fftqspa`, no `pairs.parquet` re-decode, no write to `run_01` (verified `git diff -- comparison_bench/outputs_comparison/formal_ir_methods/v64*/run_01` must stay zero; `git diff -- docs/research_cycles/V63*` zero).
- Additive only: this file `docs/research_cycles/V64P0/V64_BLOCK_LEVEL_TAG_AUDIT.md`; `V63`/`V64` records/summaries/registry unchanged.
- If any per-block invariant failed, this audit would report FAIL and block downstream promotion — currently all PASS.

