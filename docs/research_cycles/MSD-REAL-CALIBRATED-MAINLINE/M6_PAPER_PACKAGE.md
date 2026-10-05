# M6 论文包（G0=(B)，组装件：无新数字、无新执行、无新声称）

> 发表口径（U-3 已裁决）：实测效率曲线（带期望良率的 f）+ 同数据方法对照 +
> 负结果与更正记录；**不写单点 `f_eff ≤ 1.3` 认证句**。
> 本文件只复述已审查证据（每行给出来源指针）；任何数字与源文件不一致以源文件为准。

## 1. 实测效率曲线（带期望良率的 f，point + Wilson upper95）

| 实验 | N（符号/块） | B | f point (upper95) | 来源 |
|---|---|---|---|---|
| MSD M2冻结合成 T2-1M/1.5M/2M | 16384 | 300 | 1.2310/1.2309/1.2285 (1.374/1.369/1.365) | `workspace/m2_synthetic/m2_20261005/m2_summary.csv`，M2批末审查PASS |
| MSD M1′b合成（C_0=2569） | 16384 | 300 | 1.2740/1.2662/1.2620 (1.416/1.403/1.398) | `workspace/m1_synthetic/m1_20261005/m1primeb_summary.csv`，M1批末审查PASS |
| MSD M2合成对照 | 1024 | 300 | 5.9–7.1 | 同上（对照臂，非运营点） |
| NB-marginal合成 R1/R2 | 1024 | 100 | 1.2592–1.3942 (1.66–1.88) | `workspace/m4_synth/m4_20261005/m4_nbmarginal_summary.csv`，M4批末审查PASS（u2-layer口径） |
| NB-marginal真实 R1/R2 | 1024超帧 | 205–383 | 1.5855–1.9364 (1.87–2.39) | `workspace/m5_realframe/m5_20261006/m5_nb_summary.json`，Pre-RESULT三轮后PASS（一致性带内） |
| MSD冻结真实 | 16384块 | 12/17/23 | 12.0–12.5（52/52失败，不一致） | `workspace/m5_realframe/m5_20261006/m5_msd_summary.json`，同上 |

## 2. 同数据方法对照

- 同信道（R1 TRAIN plug-in合成）：`M4_COMPARISON_TABLE_DRAFT.md`（M4审查PASS，ceiling C1–C8）。
- 同批真实帧：`M5_RESULT.md`（Pre-RESULT三轮后PASS）。
- Polar：`polar_recompute.json` 同公式重算（O1b-2均值1.51，O4R-shift 1.36）——外部
  引用（d=32–512曲线数据），不可横比，仅期望校准。

## 3. 负结果与更正记录

- Stage 0 设计错误更正：无条件逐面熵 KILL 实为错误设计；MSD 条件链闭合到 H(A|B)
  （P1 RESULT/P1_TABLE，残差1e-16）。
- GF32 128符号单旋钮探针线：已停止（D-2），SUMMARY 见 `_closed` 归档。
- 本轮新增负结果（均保留证据）：accumulator 族对 p≈0.24 不可用；repetition 精确ML
  结构性脆弱（4.6%组丢失）；v28双层经验路径在R1信道 FER 0.82（对照臂退役）；
  MSD冻结真实52/52不一致（先验稀疏格过置信，修复方向已指明，未在本批解决）。
- HDC/LB void 等历史负结果：见各自归档 SUMMARY（本文件不复述细节，只登记存在）。

## 4. 安全记账

- tag：64 bits/块（全臂统一；实际 tag 协议与验证粒度见 L 账本接受范围，
  `msd_outcome_accounting` 标准构造）。
- 泄漏分解：L_EC（发送行 bits）+ tag + kept加权失败惩罚，三项在每个 summary 行均可
  独立加总；undetected（accepted-wrong）全程隔离、永不计入 success/FER。
- 失败惩罚口径：`kept = N·H_A − E[L]`（P1/M1/M2/M4/M5 全批一致）。

## 5. 可复现性

- 冻结包：M1_PACKET/M1′a/M1′b/M2/M4_PACKET/M5_PREEXECUTE（命令/预算/停规则冻结）。
- 单日志：`EXPLORATION_LOG.md`（尝试+失败+修正+证据+审查全链）。
- 独立复算：`m1_independent_recompute.py`（M1′b 22行/M2 9行/NB 6+1行 PASS）；
  `m5_band_verdicts.py`（9行 f全输入重算 + band verdict + 精确p值）。
- 代码：`msd_m1_synthetic/m1primea_repetition/m1primeb_mixed/msd_peg_code/`
  `msd_m2_incremental/msd_m4_nbldpc/msd_m4_nb_marginal/msd_m5_realframe/`
  `binary_spa_numba` + 8 个聚焦测试文件（15+2+6+3+2+2+2+4 通过）。
