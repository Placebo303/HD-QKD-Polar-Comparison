# V55 数据就绪报告 — decoder-free G1-G7 全 PASS (QUALIFICATION_PLAN_READY)

**Cycle**: `V55P0`
**HEAD**: `efd34ef318014e1d0505605062057b042e2180eb` (branch `formal-ir-mainline`, authoritative 90-block)
**Data SHA**: `84d62779603e62de50ded5182ed65b65d3dc6084` (semantics `d=1024 bw=200 pairing=nearest rule=legacy_v1` 单点)
**Status**: `QUALIFICATION_PLAN_READY / EXECUTE_NOT_AUTHORIZED` — intake 3/3 READY 已固化，authoritative 90-block 已冻，等待独立 plan review；不执行 decoder，不创建正式 `run_01`
**紧凑证据**: `intake_compact_evidence.md` (三源 provenance/结构统计/生成命令/路径/行数/重建方法) + `v55_authoritative_registry.json` (唯一 authoritative 90-block, 30/source, frame_ids frozen, gap≥4, 禁换块)
**Intake 脚本**: `workspace/v55_intake_20260828/v55_decoder_free_intake.py` (decoder-free, `python workspace/v55_intake_20260828/v55_decoder_free_intake.py`), 零 `decode_*` 调用
**日期**: 2026-08-28 (intake 3/3 READY, 1M 2130 / 1p5M 5125 / 2M 5513 frames, 均 200ps legacy_v1)
**关键判断**: **intake 已就绪 (3/3 READY)，G1-G7 全 PASS，authoritative 90-block 已冻，当前为 `QUALIFICATION_PLAN_READY`，等待独立 plan review 后授权执行 180-360 calls。**

## 1. 数据裁决 (已就绪，非 HOLD)

- V13 `split_manifest 60/20/20`：1M `2000` / 1p5M `2767` / 2M `3645` 帧，`HOLD 20%` 为 `400/554/729` 帧（`base 1600/2213/2916`），已污染 (180 块开发使用)，**不复用 HOLD 作 TEST** (已裁定)。
- **Intake 已就绪**：三源 `20260123_1M_600k_0dB F2130 / 20260107_PPLN_1p5M F5125 / 20260123_2M_1p2M_0dB F5513` 均 3/3 READY (均 ≥120, prefer ≥160)，`84d62779` 单点 200ps legacy_v1，**非同分布 2026-01-21** (独立跨 session TEST)，三层绑定实际 acquisition。
- **目标运行域声明（冻结）**：`D_target = {1M_600k_0dB, 1p5M, 2M_1p2M_0dB}` 三源 frozen 标签，非同分布 2026-01-21；超出目标域的新物理条件为 exploratory，不计入门禁 (当前无)。
- **Budget/Gate**：`180-360 硬帽360` (L1 90+base90+stage1≤90+stage2≤90), 门禁 `coverage 70/90 ∧ per-source 20/30 ∧ undetected==0` 主判 `base→Δ16`，仅称 independent cross-session qualification evidence。

## 2. 库存清单 — 已冻结三源及其物理条件 (authoritative)

| session_id | stratum | date | 帧数 F | 行数 (F×256) | provenance (.ttbin + .1.ttbin 同源) | 状态 |
|---|---|---|---|---|---|---|
| `20260123_1M_600k_0dB` | 1M_600k_0dB | 2026-01-23 | 2130 | 545280 | `Type2_1M_600k_3s_0dB_2026-01-23_174534.ttbin (21264, sha ee79c5b8…)` + `..._174534.1.ttbin (19698352, sha d4783222…)` | READY |
| `20260107_PPLN_1p5M` | 1p5M | 2026-01-07 | 5125 | 1312000 | `Type2PPLN_1500K_3s_2026-01-07_174222.ttbin (8640, sha 5e6fcb8f…)` + `..._174222.1.ttbin (32530768, sha 576a299c…)` | READY |
| `20260123_2M_1p2M_0dB` | 2M_1p2M_0dB | 2026-01-23 | 5513 | 1411328 | `Type2_2M_1.2M_3s_0dB_2026-01-23_175008.ttbin (21264, sha e8c6f67b…)` + `..._175008.1.ttbin (37376992, sha e0079630…)` | READY |

- 处理点：`d=1024 bw=200 pairing=nearest rule=legacy_v1 channels A1/B5` (84d62779 单点)
- 生成命令：`python workspace/v55_intake_20260828/v55_decoder_free_intake.py` → `comparison_bench/outputs_comparison/v55_intake_20260828/sidecars|pairs` (parquet 行数已验)，`sidecar_meta.json` 记录 `materialize_params` 与 `checks`，大型文件不进 Git，compact evidence 已记录重建方法
- 非同分布：三源与 `2026-01-21` V13 非同分布，仅称独立跨 session TEST

## 3. 合格 TEST 要求 (authoritative 90-block，已冻结)

| 项 | 冻结值 |
|---|---|
| 处理点 | `d=1024 bw=200 pairing=nearest rule=legacy_v1` 单点 (84d62779), channels A1/B5 |
| 每源帧数 | `2130 / 5125 / 5513` (>120, >160) 已验 |
| 每帧 | 256 pairs, `alice_symbol`/`bob_symbol` ∈0..1023, `frame_id 0..F-1 × pair_idx 0..255` 排序连续无缺失 |
| 每块 | 4 连续帧 =1024 pairs (`BLOCK_LENGTH=1024`), `sampling_mode=deterministic_four_consecutive_frames_independent_test_v55_authoritative` |
| 隔离 | `.ttbin/.1.ttbin` 同源 fully materialize then judge，无 padding/resampling/cross-session stitching，不入 prior |
| 主样本 | `90 blocks` (30/source, 360 frames)，`K=F-3=2127/5122/5510`，`index_j=floor(j*(K-1)/29) j=0..29` 分散，gap≥4，两两非重叠，与 V13 零重叠 per source |
| Identifiers | `v55_authoritative_registry.json` 为唯一合法块集，`frame_ids[4]=[s,s+1,s+2,s+3]` 已 freeze，**禁换块/禁重采样** |
| Budget | `180-360 硬帽360` (L1 90+base90+stage1≤90+stage2≤90, L2 90-270) |

## 4. 数据就绪门 G1-G7 (decoder-free，分层，authoritative 全 PASS)

| 门 | 检查项 | 冻结结果 (intake 3/3 READY, gap≥4) |
|---|---|---|
| G1 | 文件可读 per source | **PASS** — `pairs.parquet` 行数 = frames×256 (545280/1312000/1411328) 已验，列合法，`intake_compact_evidence.md` §3.1 |
| G2 | provenance 完整 per source | **PASS** — `session_id/date + .ttbin/.1.ttbin` 双文件 sha256/size/mtime 完整 (见 §2, sidecar_meta) |
| G3 | 各 stratum 明确 | **PASS** — `D_target` 三源各一 session, 标签 `1M_600k_0dB/1p5M/2M_1p2M_0dB` 冻结，非同分布 2026-01-21 |
| G4 | 256/frame 1024/block per source | **PASS** — 每帧256 每块1024, `0..1023` 范围, `frame_id×pair_idx` 排序无缺失 (assert 已验) |
| G5 | 与 V13 及 V48-V54 完全独立 per source | **PASS** — 三源为 2026-01-23/2026-01-07 新 session，与 V13 全集零重叠 per source |
| G6 | V25 prior 只读 (全局) | **PASS** — `channel_counts.npz` 形态校验，不读 intake TEST 做训练 |
| G7 | 冻结 authoritative registry per source | **PASS** — `K=2127/5122/5510 ≥30`，`index_j` 分散，gap≥4，两两非重叠，与已用零重叠，`v55_authoritative_registry.json` 已 freeze，禁换块 |

**三源全 PASS ⇒ `QUALIFICATION_PLAN_READY` 已达成 (等待独立 plan review)**

### 4.1 脚本实测 (intake decoder-free, 2026-08-28)

```bash
python workspace/v55_intake_20260828/v55_decoder_free_intake.py
# 输出:
# 20260123_1M_600k_0dB: frames=2130 pairs_kept=545280 tail=23 => READY
# 20260107_PPLN_1p5M: frames=5125 pairs_kept=1312000 tail=28 => READY
# 20260123_2M_1p2M_0dB: frames=5513 pairs_kept=1411328 tail=106 => READY
# Overall: 3/3 READY
# Registry authoritative 90 blocks (30/source) frozen, gap≥4
# Outputs: sidecars/pairs under comparison_bench/outputs_comparison/v55_intake_20260828 (additive, not overwriting V13)
# Compact evidence: intake_compact_evidence.md + v55_authoritative_registry.json in openspec/changes/... (large parquet/npy not in Git but reproducible)
```

### 4.2 按源 K/index_j (authoritative)

```
per source authoritative (F frames, need 30):
  K = F-3 (2127 / 5122 / 5510)
  remaining = 0..F-4
  selected = [remaining[floor(j*(K-1)/29)] for j in 0..29]
  gap≥4 verified, frame_ids=[[s,s+1,s+2,s+3] for s in selected]
1M_600k_0dB: K2127 -> selected_starts 0,73,146,219,293,366,439,513,586,659,733,806,879,953,1026,1099,1172,1246,1319,1392,1466,1539,1612,1686,1759,1832,1906,1979,2052,2126 gap≥4 ✓
1p5M: K5122 -> 0,176,353,529,706,882,1059,1236,1412,1589,1765,1942,2119,2295,2472,2648,2825,3001,3178,3355,3531,3708,3884,4061,4238,4414,4591,4767,4944,5121 gap≥4 ✓
2M_1p2M_0dB: K5510 -> 0,189,379,569,759,949,1139,1329,1519,1709,1899,2089,2279,2469,2659,2849,3039,3229,3419,3609,3799,3989,4179,4369,4559,4749,4939,5129,5319,5509 gap≥4 ✓
```

## 5. 预算 (已冻结，180-360 硬帽360)

- `L1 90` + `base L2 90` + `stage1 0–90` + `stage2 0–90` = **`180–360 硬帽360 (L2 90–270)`**
- 每源 `30` 块时每源 `L1 30+base30+stage1≤30+stage2≤30=60-120`，`base` 兼 old 不重复

## 6. 预注册门禁 (已冻结，70/90 + 20/30 + undetected==0，主判 base→Δ16)

```
QUALIFICATION_PLAN_READY 已达成 (G1-G7 全 PASS)
若 完整性/守卫/秩/嵌套/重叠/记账失败 → V55_EVIDENCE_INVALID 优先
else if coverage final_exact_full ≥70/90 (77.8%) ∧ 每源 final_exact_full ≥20/30 (66.7%)
        ∧ undetected==0 全局 ∧ rank/nested/verification/记账通过
     → V55_INDEPENDENT_TEST_PASS (仅称 independent cross-session qualification evidence)
else → V55_INDEPENDENT_TEST_FAIL
```

- **主判**：完整 `base→Δ8→Δ16` (即 `final` base→Δ16)，`base` 仅分层诊断、`stage1` 仅分层报告不取代最终
- `Wilson 95%` / `rescue_rate` / `runtime` / `leakage` 仅报告不作门禁 (按源分层 + coverage)
- PASS 仅独立跨 session 资格确认，非 FER/SKR/阈值/安全/晋升，不宣称同分布复现 (三层绑定实际 acquisition)

## 7. 本报告终态

**当前终态**: **`QUALIFICATION_PLAN_READY / EXECUTE_NOT_AUTHORIZED` (G1-G7 全 PASS, authoritative 90-block 已冻)**

- 已固化：`intake_compact_evidence.md` + `v55_authoritative_registry.json` (30/source 共90, gap≥4, frame_ids/ordinal frozen, 禁换块) 为 compact evidence 进 Git；大型 sidecar/pairs 保留在 `comparison_bench/outputs_comparison/v55_intake_20260828/` (545280/1312000/1411328 行) 不进 Git 但可重建 (命令/路径/行数/重建方法已记)
- 三源标签 `1M_600k_0dB / 1p5M / 2M_1p2M_0dB` 非同分布 2026-01-21，三层绑定实际 acquisition
- 预算 `180-360 硬帽360`，门禁 `70/90 + 20/30 + undetected==0` 且主判 `base→Δ16` 已冻结，等待独立 plan review 后授权执行 90 块三阶段条件 180-360 calls

## 8. 禁止清单 (本轮已遵守)

- 未创建 `comparison_bench/src/comparison_bench/formal_ir/v55_*.py` production module
- 未创建 `scripts/execute_v55_*.py` CLI
- 未创建 `comparison_bench/tests/test_v55_*.py` tests
- 未创建 `comparison_bench/outputs_comparison/formal_ir_methods/v55_*/run_01` 正式 output root
- 未用 HOLD 冒充独立 TEST
- 未模拟 TEST 数据
- 未执行 decoder (intake 零 `decode_*` 调用，P1-P3 仍 PASS)
- 未自授 `EXECUTE_AUTH`，保持 `QUALIFICATION_PLAN_READY / EXECUTE_NOT_AUTHORIZED` 等待独立 review
- 未换块 (authoritative 已冻)

## 9. 结论

**intake 已就绪，G1-G7 全 PASS，authoritative 90-block 已冻，`QUALIFICATION_PLAN_READY` 已达成。** V54 二阶段 rank/nested/leakage/budget 已冻结可构造，intake 侧 3/3 READY (2130/5125/5513 frames, 200ps legacy_v1, 545280/1312000/1411328 rows, 0..1023 范围, 排序无缺失, gap≥4) 已验证。V55 本轮已完成四工件修订至 `QUALIFICATION_PLAN_READY / EXECUTE_NOT_AUTHORIZED` + 紧凑 intake 证据 (authoritative)，推送后停留等待独立 plan review，不实现 runner、不执行 decoder。
