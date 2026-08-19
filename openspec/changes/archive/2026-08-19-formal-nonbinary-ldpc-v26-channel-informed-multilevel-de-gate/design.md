# Design: formal-nonbinary-ldpc-v26-channel-informed-multilevel-de-gate

> Status: RUN_COMPLETE（2026-08-19；终态 pass_target_f13）。冻结输入来自 V25 `channel_counts.npz` / C04 source-delta；
> 复用冻结 `nonbinary_field.py` GF 后端与 `nonbinary_v14_mcde` 更新内核语义。

## 1. Layer-channel adapter（M0 语义）

目标：为每个 layer 构造真正的逐样本 posterior population
`P(U_i = u | B, source, delay, U_<i)`，并作为 MC-DE 的 channel 注入。

对每个 Monte-Carlo sample：
1. 从 `N_ab`（train `P(A,B)`）采样一对 `(A,B)`；
2. 用冻结 natural labeling + F01/F03 MSB→LSB 分解把 `A` 分成 `U_1, U_2`；
3. 第 1 层：
   \[
   P(U_1=u|B,Z) = \sum_{a : L_1(a)=u} P(A=a|B,Z)
   \]
4. 第 2 层（条件在已知第 1 层下）：
   \[
   P(U_2=u|B,Z,U_1) =
   \frac{\sum_{a : L_1(a)=U_1, L_2(a)=u} P(A=a|B,Z)}
        {\sum_{a : L_1(a)=U_1} P(A=a|B,Z)}
   \]
5. 将 posterior 以**真实层符号为零点**重新中心化（center on true layer symbol），
   再送入 MC-DE。

第 2 层在 DE 中使用“前层已渐近正确”的条件是合法的 multistage DE 假设（对应 Mitra et
al. 2024, doi:10.1007/s11128-024-04343-8 的 NB-MLC 条件初始化）；**它不是有限码中的
Alice oracle**。有限码以后必须由 Bob 解码并验证第 1 层。

语义门（M0 不通过 → `implementation_blocked_layer_channel_semantics`，不得继续 DE）：
- 每个 posterior 非负、归一化；
- GF512 / GF32 / GF2 symbol domain 正确；
- 重新计算的平均 posterior entropy 与 V25 `H_i` 一致：`|H_adapter - H_V25| <= 1e-3`
  bit/symbol；
- ±1 正负方向分别保留；1M 与 1p5M/2M 的 posterior population 不能静默合并；
- natural factorization 可逆；第 2 层条件中真正包含已知第 1 层。

### source↔delay 显式元数据（M0/Delay）

- V25 冻结决策：三个 source 的既有 `delay_used_ps = -50 / +50 / +50`
  （1M / 1p5M / 2M），pairs.parquet 行数 512000 / 708352 / 933120。
- `SOURCE_METADATA` 用字典显式记录 source id → `label` / `delay_used_ps` /
  `n_pairs` 映射；`ChannelAdapter` 暴露 `source_label` / `delay_used_ps` /
  `n_pairs`，M0 report 的 per-(arch,source) detail 与每个 run 根目录的
  `RUN_MANIFEST.json` 都落该映射（不再只藏在 source id 字符串里）。
- 不重估亚 bin delay；不改动数据源顺序（`SOURCES_ORDER`）与 V25 holdout。

## 2. MC-DE 内核扩展（M1）

`nonbinary_v14_mcde.run_mcde` 的 `structured` 分支假设平移不变：只接受
`w[delta]` 并构造 `channel[i,j] = w[j XOR delta_i]`。

V26 新增 `posterior` 模式：直接注入**任意 `(n_samples, q)` row-normalized posterior
population**（每行一个 sample 的真实层符号已通过 coefficient permutation 归零）。
其余更新内核（variable 乘积、WHT check convolution、belief）复用 V14/V9 语义。

新增点：
- 任意 posterior population 注入；
- GF(2)/GF(32)/GF(512)（复用冻结 `nonbinary_field.py`）；
- 随机非零 edge coefficient，对消息下标做 GF 乘法 permutation；
- true-symbol centering（真实层符号 → 0 下标）；
- entropy 用 **bits/symbol**（`entropy_base_q * log2(q)`），使不同 q 之间可比。

mechanism 参考测试（M1 gate，任一不过 → `implementation_blocked_layer_channel_semantics`）：
- GF2 BSC/reference 复现；
- GF4 或 GF8 小型 brute-force check-node 对照；
- 随机非零系数 permutation 与 brute-force 一致；
- all-one coefficient 退化结果一致；
- channel adapter 输入熵与 MC-DE iteration-0 entropy 一致；
- 固定 seed 重放一致。

## 3. 固定系综 screen（M2）

只用 `lambda = {2: 1.0}`（variable degree 2）。对每层按目标码率用 harmonic-exact
concentrated check distribution 生成 `rho`。

目标码率由“worst-source 条件熵”（三个 source 中最困难者）确定：

```
A01 F01:
  L1 GF512: worst-source H = 0.41625 bit → f=1.3 目标码率 ≈ 0.93988
  L2 GF2  : worst-source H = 0.41631 bit → f=1.3 目标码率 ≈ 0.45879

A02 F03:
  L1 GF32 : worst-source H = 0.02566 bit → f=1.3 目标码率 ≈ 0.99333
  L2 GF32 : worst-source H = 0.80690 bit → f=1.3 目标码率 ≈ 0.79021
```

效率定义（与代码 `target_rate_layer` 一致，单位 bits/symbol；`width = log2(q)`）：

\[
f_i=\frac{\mathrm{leak}_i}{H_i},\qquad
\mathrm{leak}_i=(1-R_i)\log_2 q_i=\frac{m_i\log_2 q_i}{n}
\]

对给定每层各向同性条件熵 `H_i`（bits/symbol）与效率 `f`，层目标码率为

\[
R_i=1-\frac{f_i H_i}{\log_2 q_i}
\]

注意**不是** `f=R/H`、`R_target=f*H`——那会把 bit/符号与归一化泄漏混淆，导致有限码
阶段算错码率与泄漏。若 `R_target>1` 则取 1 封顶；F03 L1 极高码率可能是构图难点。

测试效率梯度 `f ∈ {1.3, 1.6, 2.0}`：`f=1.3` 是项目目标；`f=1.6/2.0` 只用于测量离目标
多远，后两者通过不能称为项目成功。

screen 参数：
```
n_samples = 400
max_iter   = 100
seeds      = [26001, 26002]
entropy_tol_bits = 0.01
streak     = 20
```

规模：2 architectures × 2 layers × 3 sources × 3 f × 2 seeds = 72 DE calls。

## 4. Confirmation（M3，仅对 screen 中每个架构的最低通过 f）

```
n_samples = 2000
max_iter   = 200
seeds      = [26101, 26102, 26103, 26104, 26105]
```

确认要求：
- 架构的两个层都通过；三个 source 都通过；五个 seed 都通过；
- 无错误或非有限值；final mean entropy ≤ 0.01 bit/symbol 并连续 20 轮；
- 每层单独留证，不只记录总架构状态。

若 screen 没有任何通过点 → 不运行 confirmation。

completed-call 累计资源上限 24h；达到后保存所有已完成调用，不启动新调用
（→ `resource_blocked`）。

**代码实现（V26 closeout）**：`run_screen` / `run_confirmation`（共享
`_run_gated_stage`）对每个 DE 调用计时；`accumulated_seconds` 达到
`RESOURCE_LIMIT_SECONDS = 24*3600` 且仍有剩余调用时立即保存已完成调用并置
`resource_blocked=True`；`decide_terminal` 据此返回 `resource_blocked`。
checkpoint 中已完成的调用视为既往完成，本次调用不重复计时。V26 实测
screen≈44s + confirm≈112s，远低于 24h，门未触发（结果不含该终态）。

## 5. 终态（M4）

- `pass_target_f13`：至少一个架构在 f=1.3 下所有层/source/confirm-seeds 全部收敛
  （允许提出有限码/构造 change；仍无 FER/qualification/promotion）。
- `target_fail_slack_pass`：f=1.3 失败但 f=1.6 或 2.0 通过（架构+adapter 有效，
  当前 degree-2 系综有差距；下一步 bounded degree optimization；非路线失败）。
- `fixed_ensemble_no_convergence`：直到 f=2.0 仍无完整架构通过（仅限当前基线未收敛）。
- `implementation_blocked_layer_channel_semantics`：M0/M1 语义或 reference test 不过。
- `resource_blocked`：24h 门触发。
