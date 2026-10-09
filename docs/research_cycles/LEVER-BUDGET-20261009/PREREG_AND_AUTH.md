# LEVER-BUDGET-20261009 — 端到端密钥杠杆敏感度（EXPLORE 任务包）

> **Track: EXPLORE**（解析/数值模型；输入只用已落盘、已验收的汇总统计；
> 不读原始数据、不解码、不新采集；无 FER/SKR/发表主张）。
> 粘贴 prompt：`docs/prompts/LEVER_BUDGET_20261009_PROMPT.md`。
> 上位：AGENTS.md §1.2 EXPLORE 合约、R1–R17、`docs/NOW.md`「挑战方向」节。
> 授权边界：本包冻结的全部臂由用户一次授权（见 prompt）；本文件本身不授权。

## 0. 为什么做（反过早收敛）

主线一直在优化"带期望良率的 f"。本包问上一层的问题：**每段 3 s / 10 s 采集
最终能留下多少安全密钥，损失最大的杠杆是哪个？** 如果 f 不是最大杠杆，
主线的优化目标应当改变——那是主线程的 DECIDE 决定，本包只提供证据。

已知事实（本包不重测，只引用）：
- Z-3 曲面的 `SKR_bps = R_pair·max(0,2−f)·H_AB`（`msd_z3_surface.py:192`）
  **不是密钥率模型**，只是边角指标；仓库内没有端到端密钥预算。
- 安全一侧 `chi_from_visibility` 的 Franson 可见度默认 **0.95，为假设值**
  （`tools/security_reports/build_actual_ir_finite_key_shadow.py:137`），仓库内无实测。
- 当前唯一真实全链成功点在**未校准**分帧（p≈0.24，f≈1.14，4dB 一致性）；
  校准点真实全链尚未打通（S-3 全败，S-4d 待授权）。

## 1. 模型（代理模型，所有单位显式）

逐 (源 s, 分帧 bw, 采集时长 T_cap, 状态 θ) 计算一段采集的密钥长度 ℓ（bit）：

- 帧长固定 `T_f = 204.8 ns`（与 Z-3 网格一致，`d·bw = T_f`），`d = T_f / bw`。
- 符合对数 `n = R_pair(s) · T_cap`（`R_pair` 单位 对/s，取自 Z-3 曲面）。
- 参数估计：抽 `r_PE·n` 对公开，密钥对 `n_k = (1−r_PE)·n`。
  相位误差 `e_p = (1−V)/2`（V = Franson 可见度，**假设参数**），
  上界 `e_p^U = e_p + sqrt(ln(1/ε_PE) / (2·r_PE·n))`（Hoeffding）。
- Eve 信息代理（与仓库同式）：`χ_E = h2(e_p^U) + e_p^U·log2(d−1)`。
- Alice 熵代理：`H_A = log2 d`（均匀边际；注明为代理）。
- 协调泄漏：`leak_EC = f · H(A|B)_θ · n_k`，`H(A|B)_θ` 按状态取（§2）。
- 期望良率：`y = 1 − FER`，基线 FER = 0（单列敏感度，不并入 f）。
- **有限长两种口径**（排序须在两种口径下都报）：
  - FK-A（显式常数）：
    `ℓ = y·[ n_k·(H_A − χ_E) − leak_EC ] − log2(2/ε_cor) − 2·log2(1/(2·ε_PA))`
  - FK-B（仓库现有代理，`delta_fk_calibrated` 同式）：
    `ℓ = y·n_k·[ H_A − χ_E(e_p) − f·H(A|B)_θ − Δ_FK(n_k) ]`，
    `Δ_FK = 4·sqrt(log2(2/ε_sec)/n_k) + 2·log2(2/ε_cor)/n_k`。
- ε 预算：`ε_sec = ε_cor = 1e-10`，`ε_PE = ε_PA = ε_sec/2`。
- `ℓ < 0` 记为 0 并单列 `zero_key=True`。
- 每对密钥 `ℓ/n` 与每秒密钥 `ℓ/T_cap` 都要报。

**主张上限**：这是代理模型。χ_E、H_A、FK 都是简化式，
数值**只用于杠杆排序**，不进论文、不作 SKR 主张。

## 2. 基线 B0 与杠杆（每个杠杆单独理想化，其余保持 B0）

**B0 = 今天真实可用的点**：未校准分帧（标称 p）、bw=200 ps、d=1024、硬判决、
f=1.14、FER=0、V=0.95、T_cap=3 s、r_PE=0.10、ε 同 §1。

| 杠杆 | 从 B0 改成 | H(A|B) 或参数来源 |
|---|---|---|
| L-f | f → 1.05；f → 1.00 | — |
| L-cal | 标称 → 校准后 H(e) | B3 表（`B123_RESULT.md` §B3，实测） |
| L-soft | H(A|B_bin) → H(A|B_fine)，同 f | 标称：`H_AB(Z-3) − G(B2)`，同 bw（实测）；校准：A5 混合律 `R_soft`（模型） |
| L-cal+soft | 两者同时 | 同上（这是已知组合，单列，不算独立杠杆） |
| L-bw | bw ∈ {100, 200, 400}，d = T_f/bw，取 ℓ 最大者 | 标称：Z-3 `H_AB`（实测 p）；校准：A5 `R_hard`（模型） |
| L-T | T_cap 3 → 10 s；→ ∞（只作参照，数据里没有） | — |
| L-V | V ∈ {0.90, 0.98, 0.99}（0.90 为下行） | **假设**，报价值信息 |
| L-PE | r_PE 在 {0.01, 0.02, 0.05, 0.1, 0.2, 0.3, 0.5} 中取最优 | — |
| L-ε | ε → 1e-6（只作敏感度） | — |
| L-FER | FER → 0.05、0.10（下行敏感度） | — |

另报**留一法**：所有杠杆都取理想值，再逐个退回 B0，看 ℓ 掉多少（捕捉交互）。

**输入转录**：所有输入值写进模块顶部的 `INPUTS` 字典，每个值带出处注释
（文件 + 表/键）。`workspace/` 被 gitignore，测试在本地 JSON 存在时核对转录、
不存在时跳过。源分两组（事先写死）：
- **主组** T2-1M / T2-1.5M / T2-2M：R_pair、标称 H_AB（Z-3）、校准 H(e)（B3）、
  软增益 G（B2）全部为实测。
- **副组** 0dB / 4dB / 10dB：R_pair、标称 H_AB 取 Z-3；校准 H(e) 由 S-4a 实测
  （marked 率 p、sgn 率 p₋，`S4A_RESULT.md` §1，bw=200）按
  `h2(p) + p·h2(p₋)` 闭式算出，标注「派生」；软增益 G 取 B2 同源行。
- 校准状态下的 bw=100/400 与校准软速率**不按源区分**：统一取 A5
  `law=dg18.5/100.0/0.014, mu=0` 行（Type-II 混合律模型），标注「模型」。
- T0 源不在 Z-3 曲面内 → 排除，日志写明。
- 不能补数、不能插值；缺任一必需值的源整源排除并写明。
- Q1–Q4 判读以主组为准；副组单列，与主组不一致时如实记录。

## 3. 事先写死的判读（只决定挑战方向表怎么更新，不做路线决定）

单元 = (源 × T_cap∈{3,10} × FK∈{A,B} × V∈{0.90,0.95,0.98})。
杠杆按 `Δℓ / max(ℓ_B0, 1)` 排序（L-cal+soft 与 L-T∞ 不参与排序，只单报）。

- **Q1 f 是否主导**：L-f(→1.00) 在 ≥2/3 单元中排第 1 → 「f 主导」；
  在 ≥2/3 单元中排第 3 或更后 → 「f 非主导」；否则 → 「混合」。
- **Q2 排序是否对 V 敏感**：在 ≥1/3 的 (源×T_cap×FK) 组合中，第 1 名杠杆
  随 V 网格改变 → 「V 是高价值未知量」→ 建议在 `C4_PLAN.md` 增加共轭基
  （Franson）可见度测量条目（只写建议，采集由用户决定）。
- **Q3 B0 是否有密钥**：报告 `zero_key=True` 的单元；若 B0 在 3 s 下
  多数单元为零，则写明"在 3 s 采集上，杠杆是必要条件，不是改进项"。
- **Q4 分帧最优点是否随目标改变**：比较 L-bw 下「ℓ 最大的 bw」与
  「f·H(A|B)/H_A 最小的 bw」是否一致；不一致 → 挑战方向 C 存活。

三问的判读结果写回 `docs/NOW.md` 挑战方向表（存活/降级/删除 + 一行证据）。
**路线变更（例如主度量从 f 改为每段密钥）属于 DECIDE，本包不做。**

## 4. 交付与范围

- 新建（加法）：
  - `comparison_bench/src/comparison_bench/formal_ir/msd_lever_budget.py`
    （numpy + math；CLI `--output-root`；无原始数据读取路径）；
  - `comparison_bench/tests/test_lever_budget.py`。
- 机器根：`workspace/lever_budget/lb_20261009/`（执行前必须不存在）。
  输出：`lb_cells.csv`（全部状态）、`lb_levers.csv`（杠杆 Δℓ 与排名）、
  `lb_summary.json`（Q1–Q4 判读 + 排除源 + 墙钟）。
- 单一追加日志：`docs/research_cycles/LEVER-BUDGET-20261009/EXPLORATION_LOG.md`
  （尝试、可用的一次工程修正、最终证据、批末审查都写在这里）。
- 禁止：改 `src/`、`experiments/`、`tools/`；读原始数据；任何解码；
  覆盖 `results/` 或已有 `workspace/` 根；push。
- 预算：墙钟 ≤ 10 min（预期 < 1 min）。

## 5. 测试矩阵（ID 供返回时引用）

| ID | 内容 |
|---|---|
| T-1 | 极限：V=1、n→∞、f=1、r_PE→0、FER=0 时 `ℓ/n → log2 d − H(A|B)`（FK-A、FK-B 都到 1e-6） |
| T-2 | χ_E 与 `tools/security_reports/_security_calibrated_common.py::chi_from_visibility` 在 (d, V) 网格上逐点一致（读源码手算对照值，不 import 冻结目录） |
| T-3 | 单调性：ℓ 随 f、H(A|B)、FER 递减；随 V、n 递增 |
| T-4 | 有限长项随 n→∞ 趋于 0（两种口径） |
| T-5 | `ℓ<0 → 0` 且 `zero_key` 标记正确 |
| T-6 | 转录核对：本地 JSON 存在时，`INPUTS` 与 Z-3 `R_pair_s`/`H_AB`、A5 `R_hard`/`R_soft`、B123 B3 值一致（不存在则 skip，并在日志写明） |
| T-7 | 输出根已存在时 CLI 报错退出、不写任何文件 |

测试：`pytest -p no:cacheprovider comparison_bench/tests/test_lever_budget.py`。

## 6. EXPLORE 流程

1. 实现 + T-1…T-7 → 日志记一行。
2. 确认输出根不存在 → 执行一次 → 日志记命令、墙钟、输出文件。
3. 允许**一次**事先登记的工程修正 + 重跑（仅限转录/代码 bug；科学输入、
   基线、网格、判读阈值不变）；失败尝试保留在日志。
4. 主线程按 §3 写判读 → 更新 `docs/NOW.md` 挑战方向表。
5. 批末一次独立审查（另一线程/审查者）：核对 §1 公式与代码一致、`INPUTS`
   转录、判读按 §3 机械执行、没有越出主张上限 → 写进同一日志。
6. scoped 提交（模块、测试、本目录、`docs/NOW.md`），不 push。

## 7. 升级条件（触发即停，回主线程）

需要读原始数据；需要改 §2 的基线或网格；需要实测 V；
想把任何数值写进论文或对外材料 → 全部转 DECIDE。
