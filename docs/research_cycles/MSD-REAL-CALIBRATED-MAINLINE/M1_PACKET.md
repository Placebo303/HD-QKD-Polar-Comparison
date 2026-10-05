# M1 EXPLORE packet — 标定合成信道上的 MSD 解码闭环（2026-10-05）

> Track: **EXPLORE**（合成、已批准 TRAIN 聚合输入、加法 workspace 根、有界可逆、无 FER/SKR 资格/发表声称）。
> 授权：用户 2026-10-05「实现并运行 M1（合成、EXPLORE，在用户已授权的 P1→P2/P3→P4 持续推进范围内）」
> ＋「推进直到上面提到的所有步骤都完成，我都提供授权」。真实帧/新 raw/发表/push 不在本包内。
> 上位：AGENTS.md §1.2、REBOOT_HANDOFF R1–R9、ROADMAP_20261005_MSD §2-M1。
> 单日志：`docs/research_cycles/MSD-REAL-CALIBRATED-MAINLINE/EXPLORATION_LOG.md`（M1 条目追加）。
> 结果根（唯一）：`workspace/m1_synthetic/m1_20261005/`（加法，gitignored；逐块 JSONL 落盘）。

## R1–R9 本包满足方式（逐条）

- **R1 先算 MDE**：目标效应 = 相邻 gap 档之间 FER 的量级分离（≥3×）与 operating 档 f_expected 是否 ≤1.25。
  MDE：B=300 时 FER=0.01 的相对 SE≈57%（√(0.99/3)），只能定位档位；B=1000 时 ±30%，可估 operating 点 f 到约 ±0.035
  （按 P-3 系数 0.114/%FER，N=16384）。包冻结 B_1024=300/点（定档位）、B_16384=300/点（估 f，CI 上报）；
  smoke 若显示预算不足，优先保 N=16384 operating 档 B≥200（MDE 放宽到 ±70% 并如实上报），砍 N=1024 边缘档。
  n≤6 逐图计数不用；每点 B≥200。
- **R2 推动真实效率的一句话**：若成功，得到三源实测实用码隙与合成 f_expected，直接决定 M1′ 码设计是否值得做、
  M2 增量披露的目标 FER 档，以及 M4 对照表的 MSD 一臂数值——这是 P1 纸面 1.14–1.15 能否落地的唯一证据。
- **R2 合成信道**：只用已批准 R1 TRAIN 稀疏联合计数（`workspace/r1_histogram_5e2a91c4/` 三源 npz，
  G-R1 接受范围），plug-in 经验分布 i.i.d. 按符号抽样；不读 VAL/HOLD/raw/真帧。iid 指**符号级**
  按联合分布抽样（分布本身就是真实标定的），不是 marginal-shape 玩具。
- **R3 主度量**：`f = (L_EC + tag + (N·H_A − L_EC)·FER_block) / (N·H(A|B))`，
  tag=64，H_A/H(A|B) 取已接受 P1 行（T2-1M 9.9976919099/0.7981344445，
  T2-1.5M /0.8249782282，T2-2M /0.8314077735——H_A 后两源由 runner 从 P1_NUMBERS.json 读取并写入结果，
  不手填）。FER 用 Wilson 95% CI → f 区间。syndrome-pass-but-wrong 单列 `undetected`，
  永不并入 success/FER 主数；块失败 = 非（全过且与 Alice 真值完全一致）。
  零失败 N_req 不作门。p_fail 用同批合成帧估计（EXPLORE 口径；DECIDE 才用样本外）。
- **R4**：任何档位失败只说明该构造/该 gap，不关闭 MSD 路线；f>1.35 则转 M1′（DE/EXIT 度分布），已在判据冻结。
- **R5 数字**：全部由 runner 脚本算出；P1 复现行（natural LSB N=1024/16384 的 L_EC/f）由 runner 自检
  （与 P1_TABLE 六行比对，容差 1e-6）＋独立复算脚本对结论性数字（operating 档 f_expected 三源 × 二 N）复算。
  口径公式显含泄漏项 L_EC、tag、失败惩罚；单位写表头（bits/block）。
- **R6 流程**：本路线无新 OpenSpec change（MSD 主线 change 已有）；新增代码以算法/runner 为主，
  复用现有模块，不复制账本样板。收尾给结论＋下一步＋收益＋成本。
- **R7 计时与落盘**：≤120 s 计时 smoke 先行（冻结命令见下），实测每块成本 × 块数 × 1.5 定预算；
  全量墙钟上限 21600 s，超限按 §停规则 砍档；逐块 JSONL 写盘，撞墙已跑部分可用。
  数值一致移植（M3 numba）是使能工作，与 10-03 用户指示一致；不改数值/选择行为。
- **R8 卫生**：scoped 提交，禁 `git add -A`；不删文件；不 merge polar-mainline；push 另需确认。
  路径用 pathlib；跑完检查仓库根无新增杂项。
- **R9 措辞**：结论只写测到的档位 FER/f＋适用范围（TRAIN 标定合成、plug-in、无平滑）。

## 冻结科学输入

- 信道：三源 TRAIN plug-in 联合分布（`T2-{1M,1.5M,2M}_N_ab_train_sparse.npz`，键 row/col/count/shape/N_train），
  抽样 `rng.choice(nnz, p=count/sum)`，seed：源内 `20261005 + {0,1,2}`，块间顺序抽样（seed 决定全序列，可复现）。
- 编码/顺序：NATURAL，LSB-first（natural LSB-first 为主线；Gray 不在本包）。
- 码：每面 `build_msd_sparse_code(n=N, m=m_k, information_degree=min(3,m_k), tie_offset=stage)`，
  `m_k = min(N-1, max(1, ceil(N·(h_k + gap))))`，h_k = 该源该面 plug-in 条件熵（runner 从 prior 表 deterministically 算，
  写入结果 Parliament；零译码纯算术）。
  gap 档：{0.03, 0.06, 0.10, 0.16} bits/symbol（N=1024 全档；N=16384 先跑 0.06/0.10，smoke 预算允许再加两端）。
- 先验：`build_conditional_prior_model(counts, NATURAL, LSB_FIRST)`；接收端只用 Bob 符号＋已译前缀
  （`receive_syndromes`，truth-free；`condition_exact_variables=False`，`skip_fully_deterministic=False`
  ——保持全译码路径，不走捷径）。
- 后端（主）：`make_bp_decoder`（ldpc 2.4.1 BpDecoder，product_sum/parallel/omp=1/input syndrome），
  `max_iter=100`（smoke 若单块 >2 s 则降至 50 并记录）。
- 后端（参照臂，仅 N=1024 每源一档 gap=0.10）：M1-local LLR 向量 min-sum（与 `binary_spa_numpy` 同消息规则，
  见 runner 内 `decode_error_min_sum_llr`），用途仅为交叉核对 numpy 链路；长块不用 dense（工程不可行，
  16384² dense 不可接受，smoke 实测记录）。
- N：16384 主，1024 对照。B_1024=300/点，B_16384=300/点（smoke 后可调，规则见 R1）。

## MDE/样本表（冻结）

| 目标 | B | FER=0.01 相对SE | f 精度（N=16384, 系数0.114/%） |
|---|---|---|---|
| N=1024 定档 | 300 | ±57% | —（只定档位，不报 f） |
| N=16384 operating | 300 | ±57% | ±0.065（含 Wilson 上界报保守 f） |
| 若预算允许加到 1000 | 1000 | ±30% | ±0.035 |

成功判据：N=16384 合成 operating 档 `f_expected ≤ 1.25`（点估计；上界另报）。
不成功：实用码隙致 f>1.35 → 推荐 M1′（DE/EXIT），不得 KILL 路线。

## 冻结命令（qkd_env；单结果根）

```text
REM 计时 smoke（≤120 s，先跑；输出 smoke.json：每块成本 c1024/c16384、后端版本、m_k 表）
D:\software\Anaconda3\envs\qkd_env\python.exe -m comparison_bench.src.comparison_bench.formal_ir.msd_m1_synthetic --smoke --output-root workspace/m1_synthetic/m1_20261005
REM 全量（仅 smoke 预算通过后；逐块 JSONL 落盘；上限 21600 s）
D:\software\Anaconda3\envs\qkd_env\python.exe -m comparison_bench.src.comparison_bench.formal_ir.msd_m1_synthetic --full --output-root workspace/m1_synthetic/m1_20261005
REM 独立复算（结论性数字：operating 档 f_expected 三源×二N；不导入主 runner）
D:\software\Anaconda3\envs\qkd_env\python.exe docs/research_cycles/MSD-REAL-CALIBRATED-MAINLINE/m1_independent_recompute.py --result-root workspace/m1_synthetic/m1_20261005 --output workspace/m1_synthetic/m1_20261005/independent.json
```

停规则：smoke 超 120 s 未完成 → 降 max_iter 至 50 重 smoke（一次）；仍超 → B_16384 降至 100 且只跑 operating 一档，
并在日志记录 MDE 放宽。全量投影（c×块数×1.5）超 21600 s → 先砍 N=16384 两端档，再砍 N=1024 至单源 T2-1M 定性。
一次工程修正＋rerun 额度：仅限 runner 崩溃/落盘 bug，科学输入/seed/阈值/假设不变，失败保留同日志。

## 产出（M1 有结果 = 以下全部）

每面 FER–m_k（码率）曲线（CSV＋图数据表，不贴图）；实用码隙（operating gap − Shannon h_k，均值/面）；
三源 f_expected（N=16384 与 N=1024，点估计＋Wilson 上界）；每块成本（s/块，按 N、源、后端分列）；
提交哈希；推荐下一步（M2 或 M1′）＋预期收益＋成本。
