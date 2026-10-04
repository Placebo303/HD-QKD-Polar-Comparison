# OpenSpec Tasks: formal-ir-v56d4-low-dim-decomposition — V56D4 decoder-free 低维分解

**Lifecycle**: `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN` — **decoder-free 低维分解，不运行 L1/L2 decoder，不碰 V55 90 块，不调码参**
**HEAD**: `b332b8a4a51e94fb905023862b8aed3650bac126` (branch `formal-ir-mainline`, V56D3R1 降级后) + data SHA `84d62779603e62de50ded5182ed65b65d3dc6084`
**Predecessor**: `formal-ir-v56d3-symbol-decomposition` `V56D3R1` `INCONCLUSIVE_PAIRING_FRAME_ANCHOR_OR_DOMAIN_SHIFT` (未发现能由 fit4 学得并在 val4 泛化的1024态经验映射；已排除五类预注册物理映射（2060候选），1024 plug-in MI 严重正偏，MAP val<identity 无泛化，pairing vs 域迁移未分)
**Revision**: V56D4 — 新增 32 态 I(U1/U2) 分解 + 固定 train/val CE/acc 分流 + 逐阶段 V13 vs 新 session 流水核对 + V13 合同两路回放；方法仍冻结，零 decoder，不以 1024 plug-in MI 分流

## Phase A — 32 态低维互信息分解（去偏核心，decoder-free）

- [ ] **A1 计算 32 态 I(U1/U2) 及其交叉**：读 `comparison_bench/outputs_comparison/v55_intake_20260828/pairs/*.parquet`（三源 `alice_symbol/bob_symbol` 1024） + `workspace/v13r3fresh_20260816/.../pairs.parquet`（V13 参考）+ `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v25_20260818/run_04/channel_counts.npz`（仅对比，不训），按 `sym → U1=sym>>5 (0..31), U2=sym&31 (0..31)` (`F03 5+5`，`binary` 序，`V13` 同口径) 分解，分别算 `32×32` 联合计数 `C_U1(a,b), C_U2(a,b), C_cross1(U1A,U2B), C_cross2(U2A,U1B)` → `P → H/ I` 公式（`log2`，`32` 态熵上限 `5 bits/symbol`），逐源落盘 `per_source.{I_U1_val, I_U2_val, I_U1U2_cross, I_U2U1_cross, H_U1_A, H_U2_A}`，并与 `V13` 同口径 `I_U1/I_U2` 对比
- [ ] **A2 解读**：报告 `I_U1/I_U2` 是否 `32` 态下仍低（`<1.5 bits`）或仍高（`>2-3 bits` 健康，`V13` 参考 `~3-4 bits`）；交叉 `I(U1A;U2B)` 仅佐证轴串扰；若 `I_U1/U2` 均低而 `V13` 高 → 低维亦坍塌倾向域迁移，若至少一维仍健康 → 局部 pairing/frame 错

## Phase B — 固定 train/val 交叉熵/准确率（泛化分流，不用 1024 plug-in MI，decoder-free）

- [ ] **B1 定义 fit/val**：预注册固定 `fit=[7,8,9,10] val=[15,16,17,18]`（`8 frames` 中的前 `4` 学后 `4` 测，与 `V56D3` 一致），从 `pairs.parquet: frame_id` 切片；`C_fit_U1(32×32)` 与 `C_fit_U2(32×32)` 仅 `fit` 上计数，列归一得 `P_fit_U1(a|b)` 与 `P_fit_U2(a|b)`（`b` 无观测时 `P=uniform` 预注册一种）
- [ ] **B2 计算 CE/acc**：每源算 `CE_U1_val = mean_{val}[-log2 P_fit_U1(U1A|U1B)]`、`acc_U1_val = mean_{val}(U1A==argmax_a P_fit_U1(a|U1B))`，同理 `CE_U2/acc_U2`（**val 上测，禁同帧**）；另报 `CE_U1_all / CE_U2_all`（全 `8` 帧）仅作稳定性参考，不作分流依据；同时可选报 `U1+U2` 联合 `CE` 近似（`CE_U1 + CE_U2|U1`）作对照
- [ ] **B3 守卫**：脚本中显式 `assert set(fit) ∩ set(val) == ∅` 且 `fit` 上学 `val` 上测，无同帧 leakage；**显式禁止以 `1024` plug-in `I>5` 做分流**（`rg "I_AB_val.*>5" 0 hits` 或注释声明），`rg "decode_" 0 hits`

## Phase C — 逐阶段流水核对（V13 vs 新 session，找首次坍缩，decoder-free）

- [ ] **C1 定义流水五段**：`raw coincidence (ttbin events + cross-correlation peak_center/σ/p2bg/total_events/duration) → pairing (policy nearest, direction, threshold_ps, Δt 直方图/中位/跨帧率) → per-frame occupancy (pairs per frame 256 期望, mean/median/zero_frame_fraction) → frame anchor (frame_start = peak_center vs global min, wrap floor_div, period 204800, before/after pair index, anchor 切换前后 U1/U2 一致率) → U1/U2 (F03 5+5: U1 一致率/U2 一致率/交叉一致率)`，每阶段两侧 `V13` vs 新 session 对比值
- [ ] **C2 逐段算 I_32/CE/acc/occupancy/Δt**：若 `pairs` 已含 `frame_id/pair_index` 或可从 `ttbin_pipeline` 重算，按阶段截断算 `I_U1/I_U2/CE/acc/occupancy/Δt`，报告 `per_stage {stage, V13_val, new_val, delta, I_U1, I_U2, acc_U1, acc_U2, occupancy, delta_t_median}` 与 `first_drop_stage`（`V13` 健康而新 session 在该阶段后 `I_32/CE/acc` 首次从健康跌至低值的阶段，阈 `I_32 2→1.5 bits` 或 `acc 60%→50%` 或 `CE 2→3 bits`）
- [ ] **C3 定位**：若 Stage 1 `raw` 已低（`p2bg` 差异或 `peak` 弥散）→ `raw` 域迁移；Stage 2 `pairing` 后 `Δt` 宽或 `I_32` 跌 → `pairing` 错；Stage 3 `occupancy` 异常 → `occupancy/filter` 错；Stage 4 `anchor` 切换前后骤变 → `frame anchor` 错；Stage 5 后低但前高且 `V13` 合同可回升 → `pairing/frame` 可修复；落盘至 `json:pipeline_stage`

## Phase D — V13 已知合同两路回放（仅 V13-contract vs current-contract，不网格择优，decoder-free）

- [ ] **D1 读取 V13 已知合同**：从 `workspace/v13r3fresh_20260816/sidecars/*/sidecar_meta.json` + `build_manifest.json` 实时读取 `V13` 的 `pairing_policy/ pairing_direction/ pairing_threshold_ps/ gate_width_ps/ frame_start_ps/ frame_period_ps/ delay_used_ps/ peak_center_ps/ wrap_rule/ mapping/ occupancy_filter`（不硬编码，仅读 sidecar 时绑定），与 `comparison_bench/outputs_comparison/v55_intake_20260828/sidecars/*/sidecar_meta.json` 的当前 intake 合同（`200ps legacy_v1 nearest 1024`）逐字段 `PASS/MISMATCH/INCOMPLETE` 对比矩阵
- [ ] **D2 两路回放**：若已有两路 `pairs.parquet` 则直接读 `V13` 侧 `workspace/.../pairs.parquet` 与 intake 侧 `v55_intake_.../pairs/*.parquet`；否则在新 `ttbin` 上用 `src/qkd_io/ttbin_pipeline` 的 `V13` 已验证实现精确复跑 `V13` 合同（`read_ttbin_events + compute_cross_correlation_histogram + pairing + bin + frame_anchor`），生成 `V13-contract` 的 `pairs` 与 `current-contract` 对比。**仅两路，不做 threshold/policy/direction/frame-start 网格**（`rg "grid" 0 hits`，候选数 `2`）
- [ ] **D3 两路在 val 上报告**：每路在 `val [15,16,17,18]` 上算 `I_U1/I_U2/I_cross/CE_U1/CE_U2/acc_U1/acc_U2/NLL_32/q_mass_32`（`NLL_32` via `channel_counts.npz` 的 `32×32` 列归一 `P(U1A|U1B)` 近似，仅对比用，不重训 prior），以及 `pipeline first_drop` 是否因合同切换消失；**禁止以 val 择优**，仅陈述两路差值（`delta_I_32/ delta_CE/ delta_acc`）

## Phase E — 脚本与报告交付（DIAGNOSIS_PLAN_READY）

- [ ] **E1 编写 `v56d4_low_dim_decomposition.py`** (decoder-free, 本变更目录下): `python v56d4_low_dim_decomposition.py [--pairs-root ...] [--v13-root ...] [--counts ...] [--out v56d4_low_dim_decomposition.json]` → 固定 `fit=[7,8,9,10] val=[15,16,17,18]` 算 `32` 态 `I_U1/I_U2/I_cross + CE_U1/CE_U2/acc_U1/acc_U2 + 流水五段 + V13合同两路对比`，`rg "decode_" 0 hits` 仅 `numpy/pandas/pyarrow`，`py_compile` PASS，输出 `v56d4_low_dim_decomposition.json` + 控制台摘要
- [ ] **E2 编写 `LOW_DIM_DECOMPOSITION_REPORT.md`**: 每源 `I_32/CE/acc/NLL/q_mass/流水坍缩点/两路合同差值` + 总体二选一分流（`PAIRING_OR_FRAME_ANCHOR_ERROR / TRUE_ACQUISITION_DOMAIN_SHIFT` 二选一，逐源可 `MIXED_BY_SOURCE`，否则 `INCONCLUSIVE_NEED_DEEPER_EVIDENCE`），数据与 json 一致，含修复/排查清单（`PAIRING` 时修 `pairing threshold/policy/direction/frame_start/sync/occupancy`，`TRUE_SHIFT` 时才规划新 `TRAIN-only prior/泄漏` `m_total=floor((1.3*1024*H-64)/5)`），结论不扩大为 FER/阈值/SKR/晋升，显式 `原 90 已揭盲不可复用` 与 `主算法不否定`，显式 `不以 1024 plug-in MI 分流`
- [ ] **E3 自检**：`py_compile` PASS, `rg "decode_" 0 hits`, `fit∩val==∅` 已验, `32` 态 `I/CE` 已报告, `V13` 合同两路 `2` 已验 `无网格`, `pipeline_stage first_drop` 已定位, `1024 plug-in MI` 未作分流已声明, 报告与 json 一致
- [ ] **E4 推送新 SHA 并停留 `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN`**，未创建任何 `.../v56d4_*/run_01` decoder 执行，不碰 V55 90 块，不运行 decoder，仅改本目录文件与脚本，`V56D3R1` 降级已固化

## 本诊断显式禁止

decoder 调用 (`decode_*` / `construct_*` / `sample_uniform_gf32` 等)；在原 V55 90-block 上重跑任何 corrected pipeline（含 offset/mapping-corrected 重译）；调 `H1/Lane C/Δ8/decoder 90/1.0/m2/leak/prior` 任一冻结参数；宣称 LDPC 证伪或 FER/阈值/SKR/晋升；创建正式 `.../v56d4_*/run_01` decoder 执行；任意 `1024` 置换/`1024!` 搜索/神经网络映射（措辞冻结为：未发现能由 fit4 学得并在 val4 泛化的1024态经验映射；已排除五类预注册物理映射（2060候选），不得写“已排除任意1024置换”）；`bin_width/dimension/pairing` 网格（`V13` vs 当前仅两路对比，不网格择优）；`1024` plug-in `MI`（`val 1024 I≈8.4` 已证严重正偏）作分流；将低维分解择优值回注为新 pipeline；**重发明 V13 已验证 channel/delay/peak/gate/frame-start/mapping/pairing 近似物化**；同帧 `fit/val` 评价；覆盖已有输出。

## 判定顺序冻结（6条）

1. 交叉验证 CE/accuracy 为主证据
2. 32态 plug-in MI 仅辅助，需注明有限样本偏差（1024样本/1024格偏置）
3. 分别报告 U1→U1、U2→U2 及交叉 U1→U2/U2→U1 四项，不合并
4. V13合同 vs current合同 必须同固定帧 [7-10]fit/[15-18]val、同切分
5. 首次显著退化阶段决定归因：raw/Δt退化→acquisition/pairing；raw正常 frame-anchor后退化→frame合同；U1/U2关联尚可但 V25 CE/NLL崩溃→统计域/prior失配
6. 若指标指向不同层级则终态 INCONCLUSIVE_MIXED_SIGNAL，不强制二选一

## 验收

- proposal/design/tasks/specs 一致 HEAD b332b8a4 84d62779 lifecycle DIAGNOSIS_PLAN_READY DECODE_FORBIDDEN 二选一分流互斥明确，显式不以 1024 plug-in MI 分流
- 每源 `32` 态 `I(U1A;U1B)/I(U2A;U2B)/I_cross`（`32×32`）已算，`CE_U1/CE_U2/acc_U1/acc_U2 (fit 4→val 4, 禁同帧)` 已算，仅 `V13-contract` vs `current-contract` 两路回放已验（无网格），流水 `first_drop_stage` 已定位
- 脚本 `rg 0 hits` `py_compile` PASS 报告与 json 一致 未建 `run_01` 已推新 SHA DIAGNOSIS_PLAN_READY 仅改本目录，原 90 未碰 主算法不否定，V56D3R1 降级已记录
