# M4 EXPLORE packet — 同口径合成对比 + 设计冻结（2026-10-05）

> Track: **EXPLORE**（合成、已批准 TRAIN 聚合、加法根、有界、无资格/发表声称）。
> 授权：用户持续推进授权（M 系列直推）。U-1 主线裁决在本包证据齐后另提；M5 真帧 Pre-EXECUTE
> 另行报批（U-2），本包不含任何真实帧执行。
> 上位：ROADMAP §2-M4。单日志 EXPLORATION_LOG.md（M4 条目）。结果根：`workspace/m4_synth/m4_20261005/`。

## R1–R9 本包满足方式

- **R1**：目标效应 = 三臂 f 在同信道同口径下的排序（MSD ~1.23 vs NB-LDPC ? vs Polar引用 ~1.35）。
  NB-LDPC 臂 B=100/源：FER~10% 时相对 SE~60%，f 精度 ~±0.1——只定排序档，不断精密差值，如实上报 CI。
- **R2**：一句话——冻结 MSD 配置并给出它相对 NB-LDPC/Polar 的位置，回答 U-1（主线去留），
  否则 M5 真帧烧预算却不知对照。
- **R2 信道**：MSD/NB-LDPC 同用 R1 TRAIN plug-in i.i.d. 符号抽样（NB-LDPC 经 V26 adapter
  由同一 TRAIN 计数构建 posterior——确定性变换，无新拟合无新数据源）；Polar 用其已发表
  final_table（不同数据/信道，只做同公式重算 + 不可比声明，不跑其 decoder）。
- **R3**：统一 `f = (L + tag + (N·H_A − L)·FER) / (N·H(A|B))`，tag=64，H 取 P1 冻结行；
  undetected 单列隔离。NB-LDPC L = 5·m_total + 64 同口径计入。
- **R4**：对比表只给排序，不 KILL 任何路线；U-1 由用户裁决。
- **R5**：三臂数字各自由脚本算出；MSD 沿用已复算 M2 行；NB-LDPC 行由复算脚本覆盖
  （先扩展脚本支持 m_total/5-bit 行再跑全量）；Polar 重算由独立脚本做（不导入主 runner）。
- **R6**：无新 OpenSpec change（MSD 主线 change 内）；复用 v28 empirical 路径零改动。
- **R7**：NB-LDPC 先 smoke B=2（≤240 s，实测 20–75 s/块）；全量 3 源 × B=100，
  投影 ~3×100×45 s ×1.5 ≈ 5.6 h ≤ 21600 s 上限；单块 240 s cap（超限记失败保留）；
  逐块 JSONL 落盘。
- **R8**：scoped 提交，禁 add -A；不删文件；不碰姊妹仓（只读其已入库 CSV）；push 另需确认。
- **R9**：Polar 行标注外部引用+不可比；NB-LDPC 精度如实带 CI。

## 冻结设计

- MSD 冻结配置（M4 采用，即 M2 点）：plane-0 PEG-dv3 m_0=ceil(N·h_0+2000@16384/160@1024)+K400/K100
  单轮定向 rescue；plane-1 PEG m_1（1024 ceil-rule / 16384 固定600）；SPC g=64/256；it200。
  M2 行即冻结证据（种子已 fresh/disjoint），不再重跑。
- NB-LDPC 臂（U-1 对照臂，零新探针）：frozen v28 config 矩阵 + V26 adapter（R1 TRAIN 计数构建）
  + decode_two_layer_sequential_empirical，max_iter 默认，B=100/源，新种子 +9000，
  N=1024 符号原生块（与 MSD-1024 同原生单位；MSD-16384 无 NB 对应臂，单列）。
- Polar 臂：final_table.csv 同公式 f 重算 + 不可比声明（dims≤512 曲线数据 vs d=1024），零执行。
- 真实帧 MDE（M5 输入，纯算术）：key-eligible 200/276/364 超帧 → N=16384 块 12/17/22 →
  真实帧只能做一致性验证（FER 尾部靠合成），共同体量配对独立组数同样受限——MDE 先算再定 M5 设计。

## 冻结命令（qkd_env）

```text
D:\software\Anaconda3\envs\qkd_env\python.exe -m comparison_bench.src.comparison_bench.formal_ir.msd_m4_nbldpc --smoke --output-root workspace/m4_synth/m4_20261005
D:\software\Anaconda3\envs\qkd_env\python.exe -m comparison_bench.src.comparison_bench.formal_ir.msd_m4_nbldpc --full --output-root workspace/m4_synth/m4_20261005
D:\software\Anaconda3\envs\qkd_env\python.exe docs/research_cycles/MSD-REAL-CALIBRATED-MAINLINE/m1_independent_recompute.py --result-root workspace/m4_synth/m4_20261005 --summary m4_nbldpc_summary.json --output workspace/m4_synth/m4_20261005/independent.json
D:\software\Anaconda3\envs\qkd_env\python.exe docs/research_cycles/MSD-REAL-CALIBRATED-MAINLINE/m4_polar_recompute.py --table ../HD-QKD_Polar_Release/low_dim_opt/outputs/final_summary/final_table.csv --output workspace/m4_synth/m4_20261005/polar_recompute.json
```

停规则：smoke 超 240 s → B 降至 60；全量投影超 cap → 先砍源（保 T2-1M），再降 B。
一次工程修正额度（runner 崩溃/落盘类，科学冻结不变）。
