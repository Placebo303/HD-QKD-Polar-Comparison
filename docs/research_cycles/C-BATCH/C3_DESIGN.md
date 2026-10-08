# C-3 合成调参与冻结设计方案（只读设计，不修改文件、不运行、不读原始数据）

> 范围声明：本设计仅为文本方案，不创建/修改任何文件，不运行任何命令，不读取原始数据文件。
> 依据：C批预注册 §2 R16、§6（B≥300 / 最终工作点 B≥1000）、Z-1 教训（逐 p 重选码率）、G-5 经验（RA gap / PEG、Polar 冻结集、B 级 margin、N=16384/32768、B=300）。
> 方法编号 A1–A7 沿用 C 批既有定义；本方案不重定义方法，只定义"每个工作点 × 每种方法 × 每个 N 按同一规则选码率"的冻结函数。
> 注意：§2.2 中 A5/A6/A7 的"界臂/固定码/冻结集对照"角色为本设计草案的提法，
> 与预注册 §3 的方法定义（A5=Zhou式MLC LDPC，A6=NB GF(32)超帧链，A7=MLC Polar只读调用）
> 存在出入；执行前须以预注册为准重新对齐，本草案仅保留记账与冻结函数的框架。

## 1. R16 统一记账公式

### 1.1 符号定义（每格 = 1 工作点 × 1 方法 × 1 N 的记账单元）

| 符号 | 定义 | 单位/备注 |
|---|---|---|
| `C_total` | 该工作点采集段内符合事件总数（采集对数） | 事件数；分母用它，尾部浪费自动受罚 |
| `N` | 块长（每块占用的符合事件数） | 事件数/块；二进制臂先映射到"每符合事件 1 符号/比特"的统一事件计数，信息量差异由 `kept` 体现，不由 N 体现 |
| `M` | 完整块数 `M = floor(C_total / N)` | 块 |
| `C_used = M·N` | 实际进入译码的事件数 | 事件数 |
| `C_tail = C_total − C_used`，`w_tail = C_tail / C_total` | 尾部浪费（绝对数 + 浪费率） | 事件数 / 无量纲；必报 |
| `B` | 实际译码块数。合成要求 `B = M ≥ 300`；最终工作点要求 `B ≥ 1000`（采集不够则该 N 不可选） | 块 |
| `ver_i ∈ {0,1}` | 第 i 块"声称成功且通过 TAG 验证"=1，否则 0 | 含 CRC/hash 验证 |
| `u_i ∈ {0,1}` | 第 i 块 undetected 标记（事后真值对比发现通过验证但实际错误） | 必隔离，永不并入 `ver` / FER |
| `kept_i` | 第 i 块信息保留长度（折算为比特） | 比特；`ver_i=0` 或 `u_i=1` 时主记账取 0 |
| `L_EC,i` | 第 i 块实际公开的纠错泄漏 | 比特；失败块已公开部分仍计入，不清零 |
| `TAG = 64` | 每 `ver_i=1` 块扣除的验证标签开销 | 比特/块；失败块不扣 TAG |
| `T_dec,i` | 第 i 块译码耗时（含验证） | 秒；用于"相同译码时间 f"列 |
| `F = #{i: ver_i=0}` | 失败块数 | 块；`u` 不计入 F |
| `U = #{i: u_i=1}` | undetected 块数 | 块；独立列 |
| `S_main = #{ver_i=1 ∧ u_i=0}` | 主记账成功块数 | 块 |

### 1.2 主记账公式（R16：计尾部浪费、失败惩罚、泄漏、tag）

逐块净贡献：

```
net_i = ver_i·(1−u_i)·(kept_i − L_EC,i − TAG) − (1−ver_i)·L_EC,i
```

段总量与归一化：

```
Net_seg      = Σ_i net_i                     # 每段采集净密钥（比特，主度量之一）
L_total      = Σ_i L_EC,i + S_main·TAG        # 总泄漏+标签（诊断列）
Net_per_coin = Net_seg / C_total              # 每符合事件净 kept（比特/符合，主度量之一，分母含尾部）
Net_per_used = Net_seg / C_used               # 诊断列（分解"尾部 vs 译码"损失）
```

尾部浪费的惩罚机制：分母用 `C_total`，故大 N 的 `w_tail` 自动拉低 `Net_per_coin`；
不得改用 `C_used` 作主分母。

### 1.3 FER 与 Wilson 界（TAG=64，点估计主用）

```
FER_hat       = F / B                         # FER 点估计（主用）
U_rate        = U / B                         # undetected 率，独立列，永不并入 FER_hat
FER_wilson_hi = Wilson95_upper(F, B)          # 敏感性界专用
```

主表 `FER` 列填点估计；Wilson 上界只作敏感性列，不替代主 `Net_seg`，不用于选最优 N。
最优 N 按点估计 `Net_seg` 最大选择；另附"Wilson 下排序是否翻转"稳定性备注。

### 1.4 完整符号 f（与 PAPER_NUMBERS.md 衔接）

```
f_full         = L_total / H_theory_total
H_theory_total = B · N · h_op
```

- `h_op` 为该工作点理论最小值（每符合事件）：二进制臂取 `h2(p_op)`；
  高维臂取 q 元对称容量对应的条件熵折算到比特/事件；`p_op` 取自 Z-2 同一工作点支撑值，全方法共用。
- 分子 `L_total` 含失败块已公开泄漏 + `S_main·TAG`；分母按 `B·N`（used 部分），不含尾部；
  尾部损失体现在 `Net_per_coin` 而不在 `f`。报告时同时列 `w_tail`。
- 诊断列 `f_noTAG = (Σ L_EC,i)/H_theory_total` 可附，但排序与选 N 以 `f_full` 为准。

### 1.5 β 附带列（公式 + 强制警示语）

```
β_side = Net_seg / (C_used · I_op) ， I_op = log2(D_op) − h_op
```

> 警示语（随表强制附注）：β 为附带列，不作为主度量；β 对 p 估计敏感、跨 k/D 不可比，
> 且失败惩罚与 TAG 处理不同即不可比。方法排序以 Net_seg / Net_per_coin 为准，β 仅供一致性检查。

## 2. 冻结调参规则

### 2.1 总则（Z-1 教训冻结）

1. 码率是函数 `R = F_method(p_op, N, B_target)`；同一 `(方法, N)` 函数形式全局冻结，不得按工作点手调。
2. 禁止跨工作点复用固定码：每个 `p_op` 必须重算一次 `R` 并重选/重构造码并记录 hash。沿用旧码即违规格。
3. `p_op` 来源唯一：Z-2 支撑表对应条目的 `p` 点估计；不得用本段数据回估的 `p` 再调码率。
4. 调参自由度冻结为 `(gap, margin)` 两标量 + N 列表；全 C-3 不再逐格搜索。

### 2.2 规则草案（按方法族，数值执行前查冻结表，见顶注对齐要求）

- **二进制臂（A1/A2 及二进制对照）：** `R = 1 − h2(p_op) − gap_bin(N) − margin_B`
  （`gap_bin(N)` 分段冻结如 N=16384→0.03；`margin_B`：B≥300 时 0.01，最终点 B≥1000 时 0.015）。
- **高维臂（A3/A4）：** `R = 1 − H_sym(p_op,k)/log2(q) − gap_nb(N) − margin_B`
 （`gap_nb` 独立冻结；PEG/RA-type 非二进制系综按 R 重选）。
- **对照臂（A5/A6/A7，以预注册定义为准）：** 本草案原将 A5 记为理想界（不译码）、
  A6 记为固定码反例臂、A7 记为冻结集对照——执行前必须按预注册
  （A5=Zhou式MLC LDPC，A6=NB GF(32)超帧链，A7=MLC Polar只读调用）重新对齐角色与公式。
- 取整统一 `K = round(N·R)`（round-half-up）；`K<1` 记 `infeasible`，不参与最优 N 竞选。

### 2.3 B≥300 执行矩阵与格数估计

- 工作点 ≥6（3 组 × 2 损耗），方法 7，N 候选 7 档 `{1024,…,65536}` 经截断后平均有效约 4–5 档；
  格数约 189（上界 294）；每格 B≥300 → 约 5.7 万～8.8 万次块译码；最终工作点最优 N 补到 B≥1000。
- 计时 smoke（R7）：每格先跑 `B_smoke=30`，记录 `median/p95(T_dec)` 并外推；
  超预算格标记 `overtime-risk` 分片续跑，不得擅自减 B 或换 N。
- 逐块落盘字段：`workpoint,method,N,block_id,ver,u,kept,L_EC,TAG,T_dec,code_hash,frozen_hash`；
  任何格 `B<300` 不得进入最优 N 评选。

## 3. 工作点定义（≥3 组，每组 2 损耗；bw/窗/k/p 必须同源自同一 Z-2 条目）

候选表（执行前按 Z-2 编号填实）：W1a/W1b（k=1）、W2a/W2b（k=2）、W3a/W3b（k≥3），
每组低/高损耗两档；`C_total` 取该设置实际采集对数，用于 N 截断。

N 截断（冻结）：`M(N)=floor(C_total/N)≥300` 方可选；最终 WP 获胜 N 须 `≥1000`
（否则在可选 N 中重选满足者，无则标 `B1000-unreachable`）；`N>C_total/2` 删除；
截断先于执行并公布 `N_valid(WP)`。

## 4. 报告表样与"未定"细则

主表每 `(WP, 方法)` 一行：WP、方法、N_valid 列表、最优N*（行内 Net_seg 最大；并列差<1%取较小N注 `tie→smallerN`）、
B@最优N、Net_seg、Net_per_coin、f_full、f_noTAG(诊)、FER_hat、U(隔离)、T_dec中位/块、
相同译码时间f†（总时间对齐到同一预算的外推值，标 `extrap.` 与实测区分）、β_side(附带)、w_tail、net@WilsonHi(敏感)。
另附分 N 明细表备查，列顺序：
`WP | 方法 | N | B | C_total | C_used | C_tail(w_tail) | S_main | F | U | Net_seg | Net_per_coin | Net_per_used | L_total | f_full | f_noTAG | FER_hat | FER_wilson_hi | β_side | median_T_dec | p95_T_dec | code_hash | 备注`。

"未定"细则：任一格 `F≤9`（含0）或 `S_main≤9`，`FER_hat` 填 `未定(F=n)`/`未定(S=n)`，
不参与最优 N 评选；全行未定则填 `无有效最优（全未定）`；f 与 Net_seg 照算但禁用排序；
`net@WilsonHi` 必填；`U≥1` 格主记账作废 U 块 kept 并注 `U=n已隔离`；
解封须补足 B 后重算 `F≥10` 且 `S_main≥10`，不得用 Wilson 上界转正。

## 对照检查点

- [ ] 每个 `(WP,方法,N)` 有 `F_method` 记录 + `code_hash/frozen_hash`
- [ ] 每格 `B≥300`；最终 WP 最优 N 达 `B≥1000`
- [ ] 主排序键为 `Net_seg`（`Net_per_coin` 并列），`f` 与 `β` 不作排序键（R16）
- [ ] TAG=64 已扣，FER 点估计，Wilson 仅敏感性列
