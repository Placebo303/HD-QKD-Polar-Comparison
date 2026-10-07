# Final handoff (2026-10-08) — HD-QKD IR mainline closeout

## 项目现状（一句话）
两级二元协调（RA-LDPC / Polar 持平，合成 f=1.140，真实 70/70 一致）
是真实 HD-QKD 数据上的最优已知路线；NB GF(32) 真实 1.376 作对照；
MSD 作负结果（先验路径缺陷已定位）。

## 复现命令（关键）
- 合成定稿：`msd_g5_bakeoff --full --ns 16384,32768`（24 配置 × B=300）。
- 真实一致：`msd_g5_bakeoff --real`（G-6，RA 最优 35 块）；
  `msd_g2_twolevel --real`（G-3，PEG 35 块）。
- 重分帧统计：`msd_z2_reframe --full`（30 格零解码）。
- 数字冻结：`PAPER_NUMBERS.md`（独立复算；D1/D2 措辞发现已处理）。

## 未做事项（诚实清单）
- Polar 只测单码率单列表档（SCL-8，disclosure 0.88）；未调优。
- p<0.12 与宽窗支撑（bw50/100）的码未实现（RA 阈值崩 + B 级密检查墙）。
- 文献对照数字待 sciverse 查证（[TODO-LIT] 占位）。
- 有限密钥安全分析不在范围内；真实 FER 尾部依赖合成。
- H-4 重分帧 Pre-EXECUTE 草案待批（读原始事件）。

## 停放线最终状态
- COMMON_VOLUME → 被两级方案取代（训练只需 ~10k 对，不再需要大战训练集）。
- DIMBW → 被 Z-3 f(d,bw) 曲面取代（30 格 + 内插规则）。
- M6 包 → 被本文（PAPER_DRAFT.md）取代。
- msd-real-calibrated-mainline OpenSpec → 已归档 completed（delta 规格已合并）。

## 证据入口
- `docs/research_cycles/MSD-REAL-CALIBRATED-MAINLINE/`：EXPLORATION_LOG.md
 （S→Z 全记录）、PAPER_NUMBERS.md、PAPER_DRAFT.md。
- 产物根：`workspace/{s1_proxy,s5_nbfull,d4_oos,f1_oos,g5_bakeoff,g6_real,z1_fpcuve,z2_reframe,z3_surface}/`。
