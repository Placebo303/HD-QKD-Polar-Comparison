# V55 intake compact evidence — decoder-free 3/3 READY (authoritative)

**Commit first**: intake 紧凑证据 | **HEAD plan** `efd34ef318014e1d0505605062057b042e2180eb` (branch `formal-ir-mainline`) | **Data SHA** `84d62779603e62de50ded5182ed65b65d3dc6084` (processing semantics 84d62779)
**Lifecycle after this commit**: intake 3/3 READY 已提交，registry authoritative 已冻结，下一步修订四工件至 `QUALIFICATION_PLAN_READY / EXECUTE_NOT_AUTHORIZED` 等待独立 plan review
**Date**: 2026-08-28
**Decoder-free**: P1-P3 仍 PASS，未实现 runner，未运行 decoder，未读译码结果

## 1. 处理点冻结 (single processing point, 单点)

- **dimension**=1024, **bin_width_ps**=200, **pairing**=nearest, **processing_rule**=legacy_v1, **channels** A=1 B=5 (口径来自 `src/reconciliation/run_nbldpc_demo_point.py::_read_ttbin_timetags` / `_bin_indices_sorted_for_binwidth` / `_pairs_from_sorted_bins`)
- 禁止多点搜索：不跑多 bin_width、不重估 prior、不做 padding/resampling/cross-session stitching
- 每帧 256 pairs, 每块 4 连续帧 =1024 pairs (`BLOCK_LENGTH=1024`), `sampling_mode=deterministic_four_consecutive_frames_independent_test_v55_authoritative`, `pairs_count=1024` per block

## 2. 三源 provenance — .ttbin + .1.ttbin 同源 (fully materialize then judge)

| session_id (stratum) | date | label | main .ttbin | .1.ttbin companion | sha256 (main) | sha256 (.1) | size main/.1 |
|---|---|---|---|---|---|---|---|
| `20260123_1M_600k_0dB` (stratum 1M) | 2026-01-23 | 1M 600k 0dB | `D:\Data\Raw Data\2026.1.23\Type2_1M_600k_3s_0dB_2026-01-23_174534.ttbin` | `..._174534.1.ttbin` | `ee79c5b8a26180ebaf4e18361cae4f7c3b44e7adcf8311ef9ed1e30e518aa780` | `d47832223f66234ef5dbd5f9d454e534934f1c424072f789257248eabe8d760a` | 21264 / 19698352 |
| `20260107_PPLN_1p5M` (stratum 1p5M) | 2026-01-07 | PPLN 1p5M | `D:\Data\Raw Data\2026.1.7\Type2PPLN_1500K_3s_2026-01-07_174222.ttbin` | `..._174222.1.ttbin` | `5e6fcb8f041ccc525d31a3ab74ed7c907c9e663c81ef3d3163095f1d54d3b800` | `576a299cf8859d3aa9ce330d8abd17449110a06d074bfef12e05b71e05b71e591` | 8640 / 32530768 |
| `20260123_2M_1p2M_0dB` (stratum 2M) | 2026-01-23 | 2M 1.2M 0dB | `D:\Data\Raw Data\2026.1.23\Type2_2M_1.2M_3s_0dB_2026-01-23_175008.ttbin` | `..._175008.1.ttbin` | `e8c6f67b2e129c6109f45326b3c7cc207a6a7d0a3f3419b6074ca811ef2f669b` | `e00796306c9d2615dfaeb3d6fad0ad4c6c5dd8b335da77af2c84494a63cf54ae` | 21264 / 37376992 |

- 判定规则: `main .ttbin + .1.ttbin = same acquisition`，`FileReader` auto-merge 两文件后 **fully materialize** 再判断 frames，**不补帧、不重采样、不跨 session 拼接**，记录两文件 hash/size/mtime
- 三 session 均与 V13 `2026-01-21` 非同分布 (non-iid)，日期不同，独立采集；不得宣称复现 2026-01-21 同分布

## 3. 结构统计 — decoder-free 验证 (pairs only, no decoder)

### 3.1 行数 = frames×256 (no tail, no gap)

| source | n_pairs_raw | n_pairs_kept | n_frames | n_tail_dropped | kept == frames×256 | tail 丢弃 |
|---|---|---|---|---|---|---|
| 1M_600k_0dB | 545303 | 545280 | 2130 | 23 | 2130×256=545280 ✓ | 23 pairs 丢弃 (不足一帧) |
| 1p5M | 1312028 | 1312000 | 5125 | 28 | 5125×256=1312000 ✓ | 28 pairs 丢弃 |
| 2M_1.2M_0dB | 1411434 | 1411328 | 5513 | 106 | 5513×256=1411328 ✓ | 106 pairs 丢弃 |

- 校验: `assert df.shape[0]==n_pairs_kept`, `assert df.frame_id == repeat(0..F-1 each 256)`, `assert df.pair_idx == tile(0..255)`
- 帧均 256 pairs，块均 1024 pairs，无缺失帧

### 3.2 符号范围 0..1023

- `alice_symbol` ∈ [0,1023], `bob_symbol` ∈ [0,1023] per source (assert min>=0 max<=1023) — 满足 dimension 1024 口径
- 无越界样本，无 NaN

### 3.3 排序无缺失

- `frame_id` 单调 0..F-1 连续无跳号 (2130 / 5125 / 5513)
- 每 frame 内 `pair_idx` 0..255 连续无缺失 (验证 `tile(0..255)` 按帧)
- 无重复 frame_id+pair_idx，无空洞

### 3.4 其他形态

- 不做 prior 重估，不读 decoder，不计 syndrome/residual/exact
- Provenance `no_decoder / no_padding / no_resampling / no_cross_session` 均 true (见 `sidecar_meta.json:checks`)

## 4. 生成命令、路径、行数、重建方法 (large artifacts not in Git)

- **生成命令**: `python workspace/v55_intake_20260828/v55_decoder_free_intake.py` (frozen, decoder-free, SHA 84d62779 semantics)
  - 内部调用: `src/reconciliation/run_nbldpc_demo_point._read_ttbin_timetags(raw_ch0_id=1, raw_ch1_id=5)` → `_bin_indices_sorted_for_binwidth(bin_width_ps=200)` → `_pairs_from_sorted_bins(dimension=1024, pairing=nearest)`
  - 参数 `used_params: {dimension:1024, bin_width_ps:200, pairing_mode:nearest, processing_rule_version:legacy_v1}` 已写 `sidecar_meta.json:materialize_params`
- **输出路径 (additive, not overwriting V13)**:
  - `comparison_bench/outputs_comparison/v55_intake_20260828/sidecars/<session_id>/a_eff.npy` + `b_eff.npy` + `sidecar_meta.json`
  - `comparison_bench/outputs_comparison/v55_intake_20260828/pairs/<session_id>/pairs.parquet` (parquet, 行数 = frames×256)
  - 镜像: `workspace/v55_intake_20260828/sidecars/` + `pairs/` + `intake_report.{md,json}` + `v55_stratified_registry_candidate.json` (additive copy)
- **行数** (pairs.parquet): 1M 545280 行 (2130×256), 1p5M 1312000 行 (5125×256), 2M 1411328 行 (5513×256); sidecar `a_eff.npy`/`b_eff.npy` 各同长度 int64
- **重建方法**: 重新执行上述命令即可重建 sidecars/pairs；输入为双文件 `.ttbin` + `.1.ttbin` (同目录, stem+.1.ttbin)，输出 deterministic，无随机种子，无跨 session
- **Git 策略**: 大型 sidecar/pairs 不提交 Git，仅本报告与 registry 进 Git；报告已记录生成命令、绝对路径、行数与重建方法，满足 compact evidence 要求

## 5. 最终 registry — 唯一 authoritative 90-block (30/source, gap≥4, 禁换块)

- **状态**: 从 `candidate` 提升为 **唯一 authoritative** `v55_authoritative_registry.json` (本目录), `schema=v55_authoritative_registry_v1`, `processing_rule=legacy_v1`, `dimension=1024, bin_width_ps=200, pairing=nearest`
- **规模**: `blocks_per_stratum=30`, `total_blocks=90` (1M 30 + 1p5M 30 + 2M 30)
- **算法**: 每源 `F` 已知，`all_starts=0..F-4` (含端), `K=F-3`, `need=30`, `index_j=floor(j*(K-1)/(need-1)) j=0..29`, `selected_starts=[remaining[index_j]]`, `selected_frame_ids=[[s,s+1,s+2,s+3] for s in selected_starts]`, 两两 `gap≥4` (验证 `abs(a-b)>=4`), 与 V13 及历史 HOLD 零重叠已验证 (新 session 独立采集)
- **Ordinal**: 每源按 ordinal 排序，已 freeze `frame_ids` (见 registry), 保序连续，无跳帧，无换块
- **禁换块**: 自本提交起 **禁换块/禁重采样/禁跨源混用**，任何变块即判 `EVIDENCE_INVALID`；后续四工件修订将引用本 registry 为唯一合法 TEST 块集
- **明细** (selected_starts):

| stratum | F | K | selected_starts (30) |
|---|---|---|---|
| 1M_600k_0dB | 2130 | 2127 | 0,73,146,219,293,366,439,513,586,659,733,806,879,953,1026,1099,1172,1246,1319,1392,1466,1539,1612,1686,1759,1832,1906,1979,2052,2126 |
| 1p5M | 5125 | 5122 | 0,176,353,529,706,882,1059,1236,1412,1589,1765,1942,2119,2295,2472,2648,2825,3001,3178,3355,3531,3708,3884,4061,4238,4414,4591,4767,4944,5121 |
| 2M_1.2M_0dB | 5513 | 5510 | 0,189,379,569,759,949,1139,1329,1519,1709,1899,2089,2279,2469,2659,2849,3039,3229,3419,3609,3799,3989,4179,4369,4559,4749,4939,5129,5319,5509 |

- **frame_ids 示例** (每块 4 帧): 1M 首块 [0,1,2,3], 次块 [73,74,75,76], 末块 [2126,2127,2128,2129]; 余类推，完整见 `v55_authoritative_registry.json: strata.*.selected_frame_ids`

## 6. 三源冻结标签与独立性声明

- 冻结标签: `20260123_1M_600k_0dB` / `20260107_PPLN_1p5M` / `20260123_2M_1p2M_0dB`，三层绑定实际 acquisition (第3章结构统计与第2章 provenance)，**非同分布 2026-01-21** (V13 为 2026-01-21 另一批采集)，不得宣称同分布复现
- 处理点 200ps 唯一，不做多点

## 7. 守卫

- 本 intake 未实现 runner、未运行 decoder、未读译码结果、未写正式 `.../v55_*/run_01`，保持 `EXECUTE_NOT_AUTHORIZED`
- 大型 sidecar/pairs 不进 Git，compact evidence 已进 Git 可复现
