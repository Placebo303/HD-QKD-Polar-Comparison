# OpenSpec Proposal: formal-ir-v56d4-low-dim-decomposition

**Status**: `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN` — **decoder-free 低维分解诊断，不运行 L1/L2 decoder，不改方法，不重跑原 90 块，不调码参。**
**Domain**: Formal IR / V56D4 decoder-free 低维分解 (V56D3 唯一后继)
**Change ID**: `formal-ir-v56d4-low-dim-decomposition`
**Cycle ID**: `V56D4` (low-dim decomposition), predecessor `V56D3` `formal-ir-v56d3-symbol-decomposition`
**Predecessor**: `formal-ir-v56d3-symbol-decomposition` (HEAD `b332b8a4a51e94fb905023862b8aed3650bac126`, branch `formal-ir-mainline`, data SHA `84d62779603e62de50ded5182ed65b65d3dc6084` `84d62779` `200ps legacy_v1 nearest 1024` 单点；结论已修订 `V56D3R1` 为 `INCONCLUSIVE_PAIRING_FRAME_ANCHOR_OR_DOMAIN_SHIFT` — 1024 态 `val 1024` plug-in MI 严重正偏 `I≈8.4` 且 `MAP val < identity` 无泛化，未发现能由 fit4 学得并在 val4 泛化的1024态经验映射；已排除五类预注册物理映射（2060候选），`V25 prior` 严重失配，但 `pairing/frame anchor` 与真域迁移尚未区分)
**Branch**: `formal-ir-mainline`
**HEAD**: `b332b8a4a51e94fb905023862b8aed3650bac126` (V56D3R1 降级后最新) — **实际代码状态待 `git diff` 重测，`src/qkd_io` 属冻结基线**
**Data SHA**: `84d62779603e62de50ded5182ed65b65d3dc6084` (`84d62779`, `d=1024 bw=200ps pairing=nearest rule=legacy_v1` 单点不改)
**Lifecycle**: `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN` — 仅 decoder-free 低维统计与 `V13` 合同回放，不产生 `run_01` decoder 执行，不改 `H1/Lane C/Δ8/decoder 90/1.0`
**Method frozen**: `V54二阶段 H1-16(80b) + L1-APP via H1 BP + Lane C m2 184/190/192 + H_inc1/2 Δ8+8 + decoder 90/1.0 poly37 + L2-only tag` 完全冻结

> ponytail lite: 本变更仅 6 文件 (`proposal/design/tasks/specs/spec.md` + `v56d4_low_dim_decomposition.py` decoder-free + `LOW_DIM_DECOMPOSITION_REPORT.md`) + `V13` 合同只读回放；无 runner、无 decoder、无新矩阵，最短科学路径。laziest alternative: `numpy` 直算 32 态熵/`pandas` 读 `pairs.parquet` 已覆盖，无需新依赖；`32` 态在 `1024` 样本下 `1024` 格均计更可靠，天然降偏。

## Goal

在 `V56D3R1 INCONCLUSIVE` 之上，以最短科学路径启动 **V56D4 decoder-free 低维分解诊断**，用 **32 态低维统计 + 固定 train/val 交叉熵/准确率 + 逐阶段 `V13` 合同回放** 区分 `PAIRING_OR_FRAME_ANCHOR_ERROR` 与 `TRUE_ACQUISITION_DOMAIN_SHIFT`，彻底摆脱 `1024 plug-in MI` 分流偏差：

### 1. 32 态低维互信息分解（核心去偏）

- 将 `1024` 符号按 `F03 5+5` 分解为 `U1 = sym >> 5` (`0..31`) 与 `U2 = sym & 31` (`0..31`)，分别计算 **32 态** 低维关联：
  - `I(U1A;U1B)` — `32×32` 联合 `1024` 格，`1024` 样本下均值 `~1/格` 远优于 `1024×1024` 的 `1M` 格严重欠采样，plug-in 偏置显著减小
  - `I(U2A;U2B)` — 同理 `32×32`
  - 交叉 `I(U1A;U2B)`、`I(U2A;U1B)` — 用于检验 `U1/U2` 轴交换/串扰是否残留关联（若 `U1A;U2B` 高而 `U1A;U1B` 低则提示轴错，但 `V56D3` 已排除固定轴交换，交叉仅作佐证）
- 每项基于 `pairs.parquet` 的 `32×32` 联合计数的 `numpy log2` 直算（`H(U1A), H(U1B), H(U1A,U1B), I` 同 `V56D3` 公式但维度 `32`），decoder-free，置换仍不敏感（`U1` 维内重标记不改变 `I`）。
- 同时报告 `V13` 参考的同口径 `32` 态 `I`（从 `workspace/v13r3fresh_20260816/pairs.parquet` 同算法算得）与新三源 `val` 对比；`V13` 的 `32` 态 `I` 应健康（接近 `~4-5 bits` 中 `5 bits` 符号熵内），若新 session `32` 态 `I` 亦坍塌则不支持 `pairing` 单点解释。

### 2. 固定 train/val 交叉熵 / 准确率分流（不用 1024 plug-in MI）

- **禁止用 `1024` plug-in `MI` 做三态分流**（已证严重正偏）。改用 **固定 `fit/val` 划分下的 `train/val` 交叉熵或准确率**：
  - 划分：沿用 `V56D3` 预注册 `fit=[7,8,9,10] val=[15,16,17,18]`（`8 frames` 中的前 `4` 学后 `4` 测，`assert fit∩val==∅`，禁同帧），`C_fit(32×32)` 仅 `fit` 上计数，`P_fit(a|b)` 列归一得经验信道，用于 `val` 上 `CE = E_{val}[-log2 P_fit(A|B)]` 与 `acc = mean_{val}(A==argmax P_fit)`。
  - 对 `U1` 与 `U2` 分别算：`CE_U1_val`、`acc_U1_val`、`CE_U2_val`、`acc_U2_val`（`32` 态，`N_fit=N_val=1024`，每 `B` 约 `32` 样本均值，相对可靠），并报告 `U1+U2` 联合 `CE`（`CE_U1 + CE_U2|U1` 近似）与 `all-data` 参考（仅作稳定性佐证，不作分流）。
- 分流阈值（预注册，`32` 态口径）：`32` 态 `I` 健康阈与 `CE` 回落阈基于 `V13` 同口径标定（例 `V13 CE_U1/U2 ~1-2 bits` vs `V25 1024 CE ~0.8` 的 `32` 态分解），报告 `val` 上 `I_32 / CE / acc` 是否回升；**不以 `1024 I>5` 判**

### 3. 逐阶段 `V13` vs 新 session 对比（定位首次坍缩）

- 流水五段（与 `V56D3` 一致但逐源对比 `V13` 与新 session）：
  `raw coincidence (ttbin events + cross-correlation peak) → pairing (policy/direction/threshold, Δt 分布) → per-frame occupancy (pairs per frame 256 期望, 零/缺帧率) → frame anchor (peak_center vs global min, floor_div, period 204800, before/after pair index) → U1/U2 consistency (U1==U1', U2==U2' 分解一致率)`
- 每阶段两侧（`V13` 参考 vs 新三源）报告 **可复现统计**：`raw` 侧 `peak_center/σ/p2bg/total_events/acquisition_duration`、`pairing` 侧 `Δt 直方图/中位/跨帧错配率`、`occupancy` 侧 `mean/median/zero-frame fraction`、`frame anchor` 侧 `before/after pair index` 与 `anchor` 切换时的 `U1/U2` 一致率变化、`U1/U2` 侧 `U1 一致率/U2 一致率/交叉一致率`。
- 报告 **首次下降位置**（`first_drop_stage`）：`V13` 健康而新 session 在某阶段后 `U1/U2 I_32` 或 `CE/acc` 首次显著跌落的阶段；若 `raw/pairing` 阶段已跌则 `pairing` 错，若 `frame anchor` 切换前后跌则 `anchor` 错，若仅 `U1/U2` 后跌但 `I_32` 仍低则倾向域迁移。

### 4. `V13` 已知合同直接回放（仅两路对比，不网格择优）

- **Pairing 合同**（`policy/direction/threshold/frame-start`）**直接复现 `V13` 已知合同**，不做网格搜索择优：
  - 从 `workspace/v13r3fresh_20260816/sidecars/*/sidecar_meta.json` 与 `build_manifest.json` 实时读取 `V13` 的 `pairing_policy (nearest) / pairing_direction / pairing_threshold_ps / gate_width_ps / frame_start_ps / frame_period_ps / delay_used_ps / peak_center_ps / wrap_rule / mapping / occupancy_filter`（不硬编码，仅读 sidecar 时绑定）。
  - 在新 `ttbin` 上 **精确复跑 `V13` 合同**生成 `pairs`（或用已落盘 `v55_intake_20260828/pairs/*.parquet` 的 `current-contract` 对比），与 **当前 intake 合同**（`v55_intake_20260828/sidecars` 所记 `200ps legacy_v1 nearest 1024` 单点）仅做 **两路对比**：`V13-contract` vs `current-contract`，报告各自在 `val` 上的 `I_32(U1/U2)、CE_U1/CE_U2、acc_U1/acc_U2、NLL (via channel_counts.npz 32-态列归一)、q_mass`。
- **判定规则（预注册二选一）**：
  - 若 `V13` 合同在 `val` 上 **恢复低维关联与 `NLL`**（例 `I_32` 回升至 `V13` 的 `>70%` 且 `CE` 从 `~3-4` 回落至 `~1-2 bits` / `acc_U1/U2 >60%` 且 `q_mass` 从 `57-72%` 回落）→ **`PAIRING_OR_FRAME_ANCHOR_ERROR`**（当前 intake 合同错，`pairing/frame` 可修复，需另冻新 `TEST` 再 qualification，原 `90` 永不重跑）
  - 若 `V13` 合同与当前合同在 `val` 上 **一致仍低**（两者 `I_32` 均低、`CE` 均高、`acc` 均 `<50%` 且差值 `<10%`）→ **`TRUE_ACQUISITION_DOMAIN_SHIFT`**（非合同错，真域迁移，届时才规划新 `TRAIN-only prior/泄漏` `m_total=floor((1.3*1024*H-64)/5)`，`prior` 仍 `TRAIN-only` 不读新 `TEST` 做训练）
- **硬约束**：**不做 `pairing threshold/policy/direction/frame-start` 网格**（`V13` 合同 vs 当前合同仅两点，不择优），避免拟合 `val`。

> **硬约束**：原 `V55 90` 永不重跑（已揭盲 `0/90`）；主算法（`H1/Lane C/Δ8/decoder 90/1.0/poly37/L2-only tag`）**不否定**，`V55 0/90` 不记为算法证伪证据；`lifecycle DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN` 保持。

## Non-Goals

- 不运行任何 `L1-APP / L2` decoder；不改 `H1-16 / Lane C / H_inc1/2 Δ8+8 / m2 184/190/192 / leak / tag / prior / decoder 90/1.0 poly37` 任一冻结量；不试新 `Δm/degree/seed`
- 不在原 `V55` authoritative `90-block` 上重跑任何 corrected pipeline / offset-corrected 重译（已揭盲 `0/90`，`base→Δ8→Δ16` 任一变体均禁）；不将低维分解择优值回注为新 pipeline
- 不做任意 `1024` 置换或 `1024!` 搜索（已修正为：未发现能由 fit4 学得并在 val4 泛化的1024态经验映射；已排除五类预注册物理映射（2060候选））、不训练神经网络映射、不做 `bin_width/dimension/pairing` 网格搜索（`200ps legacy_v1 nearest 1024` 单点锚点；`V13` 合同 vs 当前合同仅两路对比，不网格择优）
- 不以 `1024` plug-in `MI`（`val 1024` `I≈8.4` 已证严重正偏）做三态分流；不宣称 `LDPC` 证伪 / `FER` / 阈值 / `SKR` / 晋升；本诊断仅为 `DIAGNOSIS_PLAN_READY` 的低维分解，不直接进入 qualification
- 不创建正式 `.../v56d4_*/run_01` decoder 执行；低维分解修复后**另冻全新 `TEST` blocks**再 qualification，需另起 `OpenSpec` 与独立授权
- 不改写/覆盖 `V38–V56D3R1` 任何已有输出与终态（只读）；不直接修改 `AGENT_PROJECT_MEMORY.md / docs/decision-log.md`

## Scope

1. **冻结方法零改**：`n=1024, m2 184/190/192, GF32 poly37, H1-16 rank16 80b, L1-APP q via H1 BP (TRAIN channel_counts.npz), Lane C ordinal-2, H_inc1/2 Δ8+8, decoder 90/1.0 early-stop, L2-only tag 64b, TRAIN-only prior` 全只读，**零 decoder**
2. **32 态低维互信息分解（Phase A）**：读 `v55_intake_20260828/pairs/*.parquet` + `workspace/v13r3fresh_20260816/.../pairs.parquet` + `channel_counts.npz` 的 `C(u1a,u1b) 32×32` 与 `C(u2a,u2b) 32×32` 及交叉 `C(u1a,u2b)/C(u2a,u1b)`，算每源 `I(U1A;U1B)/I(U2A;U2B)/I(U1A;U2B)/I(U2A;U1B)`（`bits/symbol`，`32` 态熵上限 `5 bits`），与 `V13` 同口径对比；`py` 直算无新依赖
3. **固定 train/val CE/准确率（Phase B）**：预注册 `fit=[7,8,9,10] val=[15,16,17,18]`（与 `V56D3` 一致），`fit` 上学 `P_fit(U1A|U1B)` 与 `P_fit(U2A|U2B)`（`32×32` 列归一），`val` 上测 `CE_U1/CE_U2/acc_U1/acc_U2`（另报 `all-data CE` 仅参考，**不以同帧 CE 判恢复**），**禁同帧评价**
4. **逐阶段流水核对（Phase C）**：`V13` vs 新 session 按 `raw coincidence → pairing Δt → per-frame occupancy → frame anchor (before/after pair index) → U1/U2 consistency` 逐段算 `I_32/CE/acc/occupancy/Δt`，报告 `first_drop_stage` 与每段 `V13 - new` 差值
5. **`V13` 合同回放（Phase D）**：从 `V13 sidecars` 实时读 `pairing policy/direction/threshold/frame-start` 已知合同，在新 `ttbin` 上精确复跑（或对比已落盘两路 `pairs`），仅 **两路对比** `V13-contract` vs `current-intake-contract` 在 `val` 上的 `I_32/CE/acc/NLL/q_mass`，**不网格择优**；按预注册规则二选一分流
6. **分流与落盘（Phase E）**：输出 `v56d4_low_dim_decomposition.json`（`per_source {I_U1/I_U2/I_cross/CE_U1/CE_U2/acc_U1/acc_U2 + pipeline_stage + contract_replay {v13 vs current}} + overall_shunt`）+ `LOW_DIM_DECOMPOSITION_REPORT.md`（三态判定与修复/排查清单），`lifecycle DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN`

## Impact Scope

- **新增/修订（本诊断）**：`openspec/changes/formal-ir-v56d4-low-dim-decomposition/` 下 6 文件：`proposal.md/design.md/tasks.md/specs/spec.md` + `v56d4_low_dim_decomposition.py` (decoder-free) + `LOW_DIM_DECOMPOSITION_REPORT.md`；`specs/spec.md` 为增量（本诊断仍 decoder-free，不改方法 spec 主体）
- **只读依赖**：`src/qkd_io/ttbin_pipeline.read_ttbin_events/compute_cross_correlation_histogram`（冻结基线版，验证用）+ `v55_authoritative_registry.json` + `v55_intake_20260828/pairs/*.parquet + intake_report.json + sidecars` + `workspace/v13r3fresh_20260816/sidecars/*/sidecar_meta.json + build_manifest.json` + `nbldpc_v25_20260818/run_04/channel_counts.npz` + `comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh...`
- **不修改**：任何既有 `spec/代码/测试/输出`（除本目录外）、`V38–V56D3R1` 输出、`outputs_comparison/workspace` 以外；不创建正式 `TEST` `run_01`；**零 decoder、零码参数**；**不碰 `V55 90` 块**

## Acceptance Criteria

- [ ] `proposal/design/tasks/specs/spec.md` 齐全一致，`lifecycle DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN`，`HEAD b332b8a4` + `branch formal-ir-mainline` + `data SHA 84d62779` 已绑定，显式声明 decoder-free、零 decoder、禁重跑原 90、禁调 `H1/Lane C/Δ8/decoder`、原 90 永不重跑、主算法不否定，**显式声明不以 `1024` plug-in `MI` 分流**
- [ ] **32 态分解**可复现：每源 `I(U1A;U1B)/I(U2A;U2B)` 及交叉 `I(U1A;U2B)/I(U2A;U1B)`（`32×32`，`bits/symbol`）已基于 `pairs.parquet` 算得（`32` 态 `1024` 样本下 `~1/格`，偏置远小于 `1024×1024`），与 `V13` 同口径对比已报告
- [ ] **固定 train/val CE/准确率**可复现：`fit=[7,8,9,10] val=[15,16,17,18]` 预注册，`fit` 上学 `P_fit`、`val` 上测 `CE_U1/CE_U2/acc_U1/acc_U2` 已算得，**禁同帧评价**已守卫，**不以 `1024 I>5` 判**
- [ ] **逐阶段流水**可复现：`V13` vs 新 session 按 `raw coincidence → pairing Δt → per-frame occupancy → frame anchor (before/after) → U1/U2` 逐段 `I_32/CE/acc/occupancy` 已核对，`first_drop_stage` 已定位
- [ ] **`V13` 合同回放**可复现：`V13` 已知合同（`pairing policy/direction/threshold/frame-start` 从 `sidecars` 实时读）vs 当前 intake 合同 **仅两路对比**已执行（**无网格择优**），各自在 `val` 上 `I_32/CE/acc/NLL/q_mass` 已报告
- [ ] **二选一分流**可复现：`V13` 合同在 `val` 恢复低维关联与 `NLL` → `PAIRING_OR_FRAME_ANCHOR_ERROR`，合同一致仍低 → `TRUE_ACQUISITION_DOMAIN_SHIFT`，已按 `I_32+CE/acc+NLL` 联合判定落盘，且报告含对应修复/排查清单（新 `prior/泄漏` 仅在 `TRUE_DOMAIN_SHIFT` 时才规划）
- [ ] `v56d4_low_dim_decomposition.py` 为 decoder-free 可运行脚本（`rg "decode_" 0 hits`），仅 `numpy/pandas/pyarrow`，`py_compile` PASS，输出 `v56d4_low_dim_decomposition.json` + 控制台摘要；不创建 `run_01`
- [ ] `LOW_DIM_DECOMPOSITION_REPORT.md` 已记录每源 `32` 态 `I/CE/acc`、流水坍缩点、`V13` 合同回放两路对比与总体分流，数据与 `json` 一致，结论不扩大为 `FER/阈值/SKR/晋升`，明确原 `90` 已揭盲不可复用、主算法不否定
- [ ] 已推送新 `SHA` 并停留在 `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN`，未创建任何 `.../v56d4_*/run_01` decoder 执行，不碰 `V55 90` 块

## Tasks

见 `tasks.md`（Phase A 32 态 `I` 分解；Phase B 固定 `train/val CE/acc`；Phase C 逐阶段 `V13` vs 新 session 流水核对；Phase D `V13` 合同两路回放；Phase E 脚本与报告交付）

## Lifecycle

`V56D3R1` 当前 `INCONCLUSIVE_PAIRING_FRAME_ANCHOR_OR_DOMAIN_SHIFT`（`HEAD b332b8a4`, 未发现能由 fit4 学得并在 val4 泛化的1024态经验映射；已排除五类预注册物理映射（2060候选），`1024` plug-in `MI` 严重正偏）；`V56D4` 本诊断 `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN`（仅 decoder-free 低维分解，不实现 runner，不执行 decoder，不创建 `run_01`）；诊断后若 `PAIRING_OR_FRAME_ANCHOR_ERROR` 则**另起 successor** 修复契约并冻全新 `TEST` blocks 再走 `QUALIFICATION_PLAN_READY`，若 `TRUE_DOMAIN_SHIFT` 则另规划新 `prior/泄漏`，本诊断不直接进入 qualification。

## 判定顺序冻结（V56D4，6条）

1. 交叉验证 CE/accuracy 为主证据
2. 32态 plug-in MI 仅辅助，需注明有限样本偏差（1024样本/1024格偏置）
3. 分别报告 U1→U1、U2→U2 及交叉 U1→U2/U2→U1 四项，不合并
4. V13合同 vs current合同 必须同固定帧 [7-10]fit/[15-18]val、同切分
5. 首次显著退化阶段决定归因：raw/Δt退化→acquisition/pairing；raw正常 frame-anchor后退化→frame合同；U1/U2关联尚可但 V25 CE/NLL崩溃→统计域/prior失配
6. 若指标指向不同层级则终态 INCONCLUSIVE_MIXED_SIGNAL，不强制二选一
