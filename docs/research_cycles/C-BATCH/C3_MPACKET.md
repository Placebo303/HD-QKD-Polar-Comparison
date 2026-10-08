# C-3 M 波包（冻结，2026-10-08；用户修订指令 C_BATCH_AMEND）

> Track：EXPLORE（合成校准信道；B≥300/格；块级落盘 + 汇总）。
> 授权：用户 2026-10-08 20:30 修订指令（M1/M2/M4）覆盖本冻结臂序列。
> 本包取代 C-3 原 fresh 矩阵的可比性地位（原波 q 元 kept + 低 cap 格保留为
> pilot 参考，不删除）；M 波是 R16 主排序的唯一依据（M1：否则不得排序）。

## 1. 统一 kept 口径（冻结，全方法）
- `kept_bits = N·H_A_op` /成功块（H_A_op=log2(d)：F1→10，F2→9，F3→11；
  均匀帧假设，与 G-5 T2-1M H_A=9.9977 自洽）。
- L_EC = 实际披露比特（syndrome + B 级 + rescue）；tag=64/成功块。
- `net_of_cell` 原样复用（kept 以参数传入，无需改 C-1 模块）。

## 2. 工作点与网格
- F1（k=1：p*=0.060740，pm*=0.037000，d=1024）、F2（k=1：p*=0.030413，
  pm*=0.018564，d=512）、F3（k=2 exploratory：T2-1M 条件律先验，
  d=2048；M3 理论 I≈9.96>0 已放行）。
- A1/A2：F1/F2 × N{1024,2048,4096,8192,16384,32768}（M1 全 N；F3 二进制
  两级不可行——LSB 面在 p≈0.47 下 R<0，记 `infeasible-by-construction`，
  非 missing）。
- A3/A4：F1/F2 × 同上 6N + F3 × {1024,4096} exploratory。
- A6：F1/F2 × {1024,4096,16384}（代表三点，control 成本理由）。
- B=300/格；种子冻结 20261009（与 C-3 波独立样本，可交叉）。

## 3. 码率规则（沿用 C3 包相对制 + M 锚点；构造按 M1 重做）
- 二进制臂：R = 1−h2(p_op)−gap_bin(N)−margin_B−(M−2.5)×0.01（M∈{2.5,3.0}
  只在 N=16384 锚点二选一，同 bakeoff 冻结映射）。
- 高维臂：R = 1−H_sym/log2(q)−gap_nb(N)−margin_B−(M−2.5)×0.01。
- A1 构造（M1 核心）：高码率区（R 0.65–0.8）二元 LDPC，PEG 或 QC 不规则码；
  T0 须含阈值/小 N 成功门（DE 或 N=1024/B=30 成功率门），过不了门不得开矩阵。
- A1/A2 第二级（M1）：符号位**明文发送**，L_B = #{marked}×1 bit 精确计数
  （合成真值；注明与 C-5 真实（译码标记位）的口径差），按理想值记账。
- A2：冻结集按 p_op 重算 + hash；SC + SCL8 双变体。

## 4. 译码 effort（M2：去掉超时与低 cap 混杂）
- A3 QSPA max_iter=300（冻结单值，在用户区间 200–500 内）；A4 以列表深度为
  effort（SC + SCL8 变体保留）；**不设 per-block 超时**，一律跑到译码 verdict；
  T_dec 逐块记录（p50/p95/max 单独列）；overtime-risk 只用于调度标记，
  格一律跑满 B=300（撞墙则 short，如实）。
- A6 合成桥（M4，最高风险项）：NB-GF32 超帧机制 + 由 (p*,pm*) 拟合的差分
  bundle，喂合成校准三值对；T0/T1 过不了桥即返回 BLOCKED（失败命令+trace+
  已试补救+需主线程的一个决定），主线程裁决 fallback（A6 映射行），
  不得无声降级为 stub。

## 5. 执行与文件范围
- 新建：`formal_ir/msd_c3m_a1a2.py`（OP-M1：高码率构造+明文B+执行循环）、
  `formal_ir/msd_c3m_driver.py`（OP-M2：A3/A4 循环+A6桥+汇总）、
  `tests/test_c3m_a1a2.py`、`tests/test_c3m_driver.py`。
- 只读复用：c1 全模块（不改）、c2 条件律（F3 先验）、bakeoff 码率函数（只读引用）。
- 机器根 `workspace/c3_mtune/mt_20261008/`（fresh-root 纪律）；单一日志
  `C3_MLOG.md`（OP-M2 单写者；OP-M1 经回执由主线程 append，标记来源）。
- 禁区：D:/Data（本包零原始数据）、冻结基线、已有 outputs；A5/A7 不动（缺席维持）。

## 6. 记账报告（R16；与 mini/full 同函数）
- `net_of_cell`（kept=N·H_A_op）、TAG=64、FER 点估计、U 隔离、Wilson 敏感列、
  β 附带+警示语；"未定"（F≤9 或 S≤9 不参选）；N_valid≤16384；
  同时间 min-anchor 内插 + S1 净-时间曲线（`c3_report.py` 已实现，M 行通用）。
- OPT：每 (族,方法[,L]) 行内 Net_seg(fullsym) 最大；A5 缺席、A7 unavailable 照录。

## 7. 验收 ID / 返回（二选一：逐 ID 结果；或阻塞四件套）
- M-A1-01：高码率构造+T0门+A1 矩阵（F1/F2×6N×B300）。
- M-A2-01：冻结集重算+A2 矩阵（SC+SCL8）。
- M-A34-01：cap300 + fullsym kept + A3/A4 矩阵（含 F3 exploratory）。
- M-A6-01：桥 + 3 点矩阵，或 BLOCKED 精确原因。
- M-LOG-01 / M-CLEAN-01：单一日志完整；仅新增文件，冻结目录零 diff。
- 结论上限：只报最优 N/净密钥/同时间分层结果；M1 排序效力、C-0 前缀稳定性
  （M5）、C-5 真实矩阵均不在本包声称。
