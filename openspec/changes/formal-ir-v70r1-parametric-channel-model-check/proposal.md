# Proposal: formal-ir-v70r1-parametric-channel-model-check

**Change ID**: `formal-ir-v70r1-parametric-channel-model-check`
**Cycle ID**: `V70R1` (parametric-channel-model-check)
**Branch**: `formal-ir-mainline`
**HEAD**: `179916f7cfec0ea469683bb78083c3752700193d` (`HEAD == origin/formal-ir-mainline == 179916f7` 已核；推送前 `git fetch && git rev-parse HEAD == origin/formal-ir-mainline` 重核，不一致阻塞，不 force；`accepted_plan_sha` frozen `13b38b79`)
**Data SHA**: `84d62779` (`d=1024 bw=200ps pairing=nearest rule=legacy_v1` 单点，不换处理点)
**Predecessor**: `formal-ir-v70-binary-soft-joint-feasibility` (`9bc34be6` implementation，`V70_OVERALL_PARTIAL_SESSIONS_FEASIBLE`) + `formal-ir-v71-soft-joint-factor-kernel` (`6bc06d4d..487be113` 区间 latest accepted `487be113`，`V71_KERNEL_ADAPTER_FEASIBLE / ADAPTER_REQUIRED` successor `v71_kernel_adapter_design`)
**Lifecycle**: `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED` — `V72_NOT_STARTED`

> ponytail lite: 1 个 decoder-free 脚本 + 4 工件 + 1 小测试；复用 `v70_data_registry.json` 与 V70 的 `hierarchical_P`；仅 `numpy/pandas/pyarrow`（已装）。M1/M2 的 CAL 拟合与 VAL 评估只消费 1024 格的 δ 直方图，不需重扫全量 pairs。

## Why

`V56_TRUE_SESSION_DOMAIN_SHIFT` 已被 R4 接受（`contract_equivalent=true` 三源七阶段逐元素，统计仍不兼容），输入合同不是当前瓶颈，**本变更不重做物化合同**。

真正未验的是**估计器口径**。V67–V70 使用的 hierarchical `1024×1024` 条件表有约 10⁶ 个自由参数，而每 session 的 CAL 只有 262144 对（每个 `b` 行约 256 个样本）。CAL 4-fold CV 选出的 `λ = 221/221/356` 意味着每行约 46% 的概率质量来自先验——这本身就是"数据不足以自由估计百万个条件概率"的直接证据。

`required = ceil(1.3·N·CE_VAL)` 直接由该估计器的 VAL 交叉熵决定，因此估计器的选择会直接改变 V70 的三分流。已有诊断给出可检验的先验：[`diagnosis_v55_domain.json`](../formal-ir-v56-input-domain-diagnosis/diagnosis_v55_domain.json) 的 `δ=(a−b) mod 1024` 质量分布显示三源 `mass_0 = 0.4149/0.3755/0.2749`、`mass_±1 ≈ 0.010–0.013`、`other = 0.560/0.601/0.706`、`direction_asym ≈ 0`——形态是**尖峰 + 近平背景**，而不是宽核。若该形态在 V70 的 Stage2 帧上成立，低维核模型有可能以三个数量级更少的参数达到相近或更低的 VAL CE。

V71 已 `KERNEL_ADAPTER_FEASIBLE / ADAPTER_REQUIRED`（`6bc06d4d..487be113` latest `487be113`），successor 为 `v71_kernel_adapter_design`。**V72 的 mother code 码率将由 `required` 导出**，所以估计器口径必须在 V72 冻结码率之前判定，否则估计误差会被固化进码里。`V72_NOT_STARTED=true`，V70 数值不变。

## Scope

在**完全相同的 CAL/VAL 帧**（`v70_data_registry.json` 的 `stage2_CAL_frame_ids` 1024 帧 / `stage2_VAL_frame_ids` 256 帧）上，对三个预注册模型做同口径对照：

- **M0**（当前权威基线）：`P(a|b) = (C_ab + λ·P_global)/(N_b + λ)`，λ 由 CAL 4-fold CV 在 `[1e-2,1e4]` 30 点网格上选。**与 V70 的 `hierarchical_P` 逐位相同**，必须复现 V70 的 `CE_full_VAL` 到 `<1e-9`。参数量 `1024²+1`。
- **M1** circulant empirical kernel：`P(a|b) = K((a−b) mod 1024)`，`K` 仅在 CAL 上统计并按同族 λ 平滑（CAL 4-fold CV）。参数量 `1024+1`。直接检验平移不变性。
- **M2** wrapped Gaussian/Laplace + uniform background：`P(a|b) = (1−ε)·K_{μ,σ}((a−b) mod 1024) + ε/1024`，只拟合 `μ / σ(或 Laplace scale) / ε`。参数量 `3+1`。**Gaussian 与 Laplace 两族预注册，由 CAL 内 4-fold CV 二选一，VAL 只确认一次。**

## Non-goals

- **不重做输入合同**（V56R4 已接受 `TRUE_SESSION_DOMAIN_SHIFT`），不读 ttbin，不重物化 pairs，不换处理点。
- 不运行 decoder、不构造业务矩阵、不创建 `run_01`、不启动 V72。
- 不改 `src/`、不改 V70/V71 的任何已冻结数值或工件。
- 不用 VAL/TEST 择优 λ、族或任何超参；TEST 不读。
- 不做 `bin_width/dimension/pairing/mapping` 网格；不引第二 estimator 作门禁之外的用途。
- **不声称把 CE 精确分解为 `H_true + KL`。** 只报告 observed VAL CE、模型间 CE 差、以及 MAP/Fano 上界诊断。
- 不同时用 `0/4/10 dB` 同源梯度做模型选择（该轴保留为模型确定后的独立验证）。

## 主判据（每 session 分别报告，不取三源平均）

`CE_table_VAL` / `CE_circulant_VAL` / `CE_parametric_VAL`；MAP accuracy；Fano 上界诊断；`CAL→VAL NLL gap`；`required = ceil(1.3·N·CE_model,VAL)`；`gap = 10240 − required`；`f_max = (10240−64)/(1024·CE)`（信道上限，与规划 f 无关）；模型参数量；CAL 样本需求曲线 `32/64/128/256/512/1024` 帧。

关键量：`ΔCE = CE_table − CE_best_parametric`。

## 终态（first-match 互斥）

1. `V70R1_EVIDENCE_INVALID` — M0 未复现 V70 `CE_full_VAL`（`<1e-9`），或 CE 非有限，或任一 λ 落在网格边界。
2. `V70R1_TRANSLATION_INVARIANCE_REJECTED` — M1 与 M2 的 `CE_VAL` 均比 M0 差超过 `0.05 bit/symbol`。
3. `V70R1_PARAMETRIC_MODEL_CHANGES_CAPACITY_ROUTE` — 最优参数化模型的 `classification`（FEASIBLE/MARGINAL/NO_INFORMATION_MARGIN，沿用 V70 三分流阈）与 M0 不同。
4. `V70R1_PARAMETRIC_MODEL_NO_VALUE` — 以上均不成立（含 `ΔCE < 0.10 bit/symbol` 且无路线变化；`sample_curve` 仅 descriptive-only，不触发终态）。

Overall 按同一 first-match 顺序在三 session 上聚合。

**只有终态 3 才把参数化 estimator 带进未来自动适配器（V77）。** 终态 4 则直接进 `v71_kernel_adapter_design`，不再改估计器。

## Entry gate

本轮止于四工件 + decoder-free 脚本 + 小测试 + 推送，返回 Plan SHA 等待独立复核与 `PLAN_ACCEPT`；执行需另行 `EXECUTE_AUTH`。
