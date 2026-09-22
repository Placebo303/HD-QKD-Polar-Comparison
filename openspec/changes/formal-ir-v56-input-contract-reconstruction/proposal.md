# OpenSpec Proposal: formal-ir-v56-input-contract-reconstruction

**Status**: `PLAN_CANDIDATE / VERIFICATION_ONLY / DECODE_FORBIDDEN` — **整合 V56 全链重建：先固化 V56D4 独立 pre-RESULT review，再 A逐函数复放→B单点修复→C decoder-free 校准验收→D终态分流，不拆 D5/D6。零 decoder 直至 C 通过后 V57 才允许 decoder TEST。**
**Domain**: Formal IR / V56 输入合同重建 (V56D4 唯一后继，终结 V56)
**Change ID**: `formal-ir-v56-input-contract-reconstruction`
**Cycle ID**: `V56` (input-contract-reconstruction), predecessor `V56D4` `formal-ir-v56d4-low-dim-decomposition`
**Predecessor**: `formal-ir-v56d4-low-dim-decomposition` (HEAD `176bf34f` / `b332b8a4a51e94fb905023862b8aed3650bac126` `formal-ir-mainline`, data SHA `84d62779603e62de50ded5182ed65b65d3dc6084` `84d62779` `200ps legacy_v1 nearest 1024` 单点；结论已固化为 `INCONCLUSIVE_MIXED_SIGNAL` — CE/acc 主证据 `1M CE13.25 acc0.46 / 1p5M 14.84/0.39 / 2M 16.68/0.30` 远差于 V13 `CE0.19-0.91 acc0.74-0.99`，32态 I `1.39-2.05` vs V13 `4.17-4.93` 低但仅辅助，occupancy 均 `256` 正常，first_drop 在 `U1U2_consistency`，因跨层指标混合未单点归因)
**Branch**: `formal-ir-mainline`
**HEAD**: `49a415b8253c9c73da0013588d0c50c0e9d41dba` (`49a415b`, 实际以 `git rev-parse HEAD` 与 `origin/formal-ir-mainline` 重核为准，proposal 冻结时绑定)
**Data SHA**: `84d62779603e62de50ded5182ed65b65d3dc6084` (`84d62779`, `d=1024 bw=200ps pairing=nearest rule=legacy_v1` 单点不改，校准帧亦同点)
**Lifecycle**: `PLAN_CANDIDATE / VERIFICATION_ONLY / DECODE_FORBIDDEN` — 本变更止于 plan 候选与 decoder-free 验证脚本，不产生 `run_01` decoder 执行，不改 `H1/Lane C/Δ8/decoder 90/1.0/poly37`
**Method frozen**: `V54二阶段 H1-16(80b)+L1-APP via H1 BP(TRAIN channel_counts.npz)+Lane C m2 184/190/192+H_inc1/2 Δ8+8+decoder 90/1.0 poly37+L2-only tag` 完全冻结 (diagnosis/reconstruction 期零改)

> ponytail lite: 本变更仅 4 OpenSpec 工件 + 2 decoder-free 验证脚本 (`replay_v13_vs_current.py` + `verify_corrected_calibration.py`) + 1 报告模板；无 runner、无 decoder、无新矩阵、无新 prior，最短科学路径。laziest alternative: `numpy/pandas/pyarrow` 已装直算 I32/CE/acc，无需新依赖；V13 权威实现 `src/qkd_io/ttbin_pipeline` 只读复用，不重发明。

> **V56R2 amendment (2026-08-29, basis 97602558,起点1e34dafb, VERIFICATION_ONLY/DECODE_FORBIDDEN):** 七阶段权威语义修正为 `raw_channel_timetags → absolute_bin_indices floor_divide(t,200) → physical_frame_match bin//1024 双指针 → pair_sequence (a=binA%1024,b=binB%1024) → logical_frame_grouping 每256对 frame_id=row//256 pair_idx=row%256 → symbol_1024 → U1U2`；明确 `204800ps=1024×200ps` 是配对尺度，V55 `frame_id` 是配对后逻辑帧，校准帧必须在完整 pair sequence 后 `start=frame_id*256 stop=start+256` 切片；raw peak/延迟仅诊断不得擅自注入 -50/+50。两条权威链直接复用 `src.reconciliation.run_nbldpc_demo_point._read_ttbin_timetags/_bin_indices_sorted_for_binwidth/_pairs_from_sorted_bins` 后256分组；V13 通过 sidecar/build manifest 追溯真实入口（同三函数则用 V13 used_params，否则调 export_joint_sequence_sidecar 实际入口，不重写近似版；无法确定返回 AUTHORITY_LINEAGE_INCOMPLETE）。标记保留 `ENGINEERING_INVALID_FRAME_ID_SEMANTICS`，新输出 additive `*_r2.json/_R2.md`，禁覆盖旧证据，禁 decoder/V55 90/src改码参/V57/网格搜索。

## Goal

以**最短可判定科学路径**终结 V56 输入域诊断，**不再拆 D5/D6**，按 `0→A→B→C→D` 冻结顺序一次性完成：

### 0. 先固化 V56D4（阻塞门）

- **独立 pre-RESULT review**（独立线程/reviewer，不可自审）：复核 `HEAD == origin/formal-ir-mainline == implementation SHA`、`ACCEPTED_PLAN_SHA` 重推导一致且 `rg <stale SHA> 0 hits`、`run_01` 未建、`py_compile`+关键测试 PASS，逐项勾选落盘于 cycle docs；FAIL 则阻塞后续 A-D，进入 `revise-required` 新 SHA 重审（`AGENTS.md §3/§10.3`）。
- 记录 **implementation SHA / execution SHA**（decoder-free，无执行 SHA 则记 `N/A`）至 `v56d4_low_dim_decomposition.json:provenance` 与 `LOW_DIM_DECOMPOSITION_REPORT.md` 头。
- 固化 **CE/accuracy 主证据、I32 仅辅助、first_drop=`U1U2_consistency`、终态 `INCONCLUSIVE_MIXED_SIGNAL` 不得强制二选一**，明确 **I32 仅辅助不能单独归因**（`I32` 在 `1024样本/1024格` 下仍有 `~0.47 bits` 理论偏置）；措辞冻结“未发现能由 fit4 学得并在 val4 泛化的1024态经验映射；已排除五类预注册物理映射（2060候选）”。

### A. 逐函数复放 V13 合同（decoder-free，定位首次分叉）

- 对**同一批固定 calibration 帧**（预注册，如 `frames [7,8,9,10,15,16,17,18]` 中选 `N` 帧或全 8 帧，三源一致）**同时运行**两路物化：
  - **权威 V13 materializer**：`workspace/v13r3fresh_20260816` 所记 `V13` 已验证 `read_ttbin_events → compute_cross_correlation_histogram → pairing nearest → delay 应用 → frame_start/period/floor_div → bin(200ps) → legacy_v1 symbol(1024) → F03 5+5 U1/U2` 实现（从 `sidecars/*/sidecar_meta.json: used_params` + `build_manifest.json` 实时读，不硬编码 `delay -50/+50` 等）。
  - **当前 V55 intake materializer**：`comparison_bench/outputs_comparison/v55_intake_20260828` 所记 `current` 单点 `200ps legacy_v1 nearest 1024` 实现（同 `src/qkd_io/ttbin_pipeline`，若 intake 为已落盘 `pairs.parquet` 则以其生成链路为准，缺失字段记 `INCOMPLETE`）。
- **逐阶段比对**（阶段截断即停，保存首个不一致）：
  `raw event/channel selection (channel 1/5 counts, other<20%) → pairing index/Δt 分布 (Δt = t_B - t_A, hist/median) → delay 符号及应用位置 (delay_used_ps sign, 前/后于 pairing/bin) → frame-start/period/floor-div (frame_start_ps, period 204800, floor_div, before/after pair index) → bin index (200ps bin) → 1024 symbol (legacy_v1) → U1/U2 (sym>>5 / sym&31)`。
- 每阶段输出 `array_equal` / `mean_equal` / `Δt median` / `occupancy`，**保存首个不一致阶段及行级样例**（如 `pair_idx, t_A, t_B, Δt, bin_A, bin_B, sym_A, sym_B, U1, U2` 前 5 行），目标**找到第一次产生不同数组的位置**。

### B. 唯一修复（单点，不搜索，wrapper 内）

- 若 A 找到**代码/合同差异**，**只修复该一处**，**不搜索** `delay / bin_width / mapping / frame anchor` 多候选，不做网格择优。
- **修复值必来自 V13 权威合同**（`sidecars` 实时读或 `ttbin_pipeline` 权威实现只读对照），不手填经验值。
- 修复落在 **V56 wrapper/materializer**（`comparison_bench` 内 `v56` 物化层/脚本参数层），**严禁改 `src/` 基线**（`src/qkd_io/ttbin_pipeline.py` 等只读复用，`git diff -- src/` 必须 `0`）。
- 产出 **old / current / corrected 三路字节/数组级对照**（`old=current` 时 `diff old→current` 非空，`diff current→corrected` 在首错阶段后显式分叉，阶段后 `array_equal` 翻转），**不改 prior / H1 / Lane C / 增量矩阵 `H_inc1/2` / decoder 任何参数**。

### C. decoder-free 校准验收（新帧，三源分别，硬门槛）

- 用**未进 V55 90-block 也未进现有 `fit=[7,8,9,10]/val=[15,16,17,18]` 的新校准帧**（预注册，如 `frames [0-6,11-14,19-...]` 中每源选 `8-16` 帧，与 `90-block` 及 `D4 fit/val` 均 `set ∩ == ∅` 可机械校验；`F=2130/5125/5513` 范围内）。
- **contract_equivalent（硬证据，门 1）**：**V13 authority 与 corrected 在七阶段数组逐元素一致** = 对同批新帧 `ttbin` 输入，`V13-authoritative` 与 `corrected` 在全部七阶段 `raw/channel → pairing/Δt → delay/位置 → frame-start/period/floor-div → bin → 1024 sym → U1/U2` 均 `np.array_equal PASS`（逐阶段 `array_equal` + `mean_equal` 附录对照，任一阶段 `False` 即 `contract_equivalent=False`）。为硬证据，不可用总体相似度替代。
- **distribution_compatible（硬门槛，门 2，三源分别判定，不用总体平均）**：对每源 `s∈{1M,1p5M,2M}` 分别判定，需同时满足三项：
  1. `A==B >60%`：`rate_eq = mean(a==b)` 在新校准 `8-16` 帧上 `>60%`（`V55` 原 `27-42%`，`V13` 健康 `~99% U1/74% U2`）；
  2. `validation accuracy ≥60%`：`fit 4→val 4` 同切分下 `acc_U1 ≥60%` 且 `acc_U2 ≥60%`（`fit` 新帧前 4 学 `P_fit(a|b) 1024→32` 列归一，`val` 后 4 测 `acc = mean(a==argmax P_fit)`）；
  3. `validation CE 预注册明确上限`：`CE_U1` 且 `CE_U2` 同时满足 **相对当前合同至少下降 50%**（`CE_corrected ≤ 0.5 × CE_current`，`CE_current` 为同切分 `V56D4` 基线 `13-16`，`CE = E[-log2 P_fit]`）**且不得高于 V13 reference +1 bit**（`CE_corrected ≤ CE_V13ref + 1.0`，`CE_V13ref` 取该源 `V13` 健康值，上限区间 `0.19-0.91`，未取到则按 `0.91+1.0=1.91` 守卫；两者取严，即 `CE_corrected ≤ min(0.5*CE_current, CE_V13ref+1.0)`）。`CE` 阈预注册于 `verification_manifest.json`，事后不调。
- **NLL / q_mass 仅一致性诊断**（基于 `nbldpc_v25_20260818/run_04/channel_counts.npz` 的 `P(A|B)` 列归一，`NLL bits/sym` 与 `q_mass_on_p_zero` 仅报告回落方向，不作硬门禁；因 `V25 prior` 本身在新域可能失配，不以单一 `NLL` 阈定修复成败）。
- **timing/routing 合同完整**为前置：`timing_contract_verified` + `routing` 完整（见 design §6）缺失则不判 `RECOVERED`，先落 `EVIDENCE_INVALID` 或 `UNRESOLVED`。

### D. 终态分流（互斥 5 选 1，按优先级判定，不主观）

- **硬定义**：`contract_equivalent` 如 C 定义（七阶段逐元素一致）；`distribution_compatible` 如 C 定义（三源分别 `A==B>60%` + `acc≥60%` + `CE≤min(0.5*CE_current, V13ref+1)`）。
- **五选一（优先级从高到低，互斥，不主观）**：
```
EVIDENCE_INVALID  # 证据/切分/零重叠失败：fit∩val≠∅ / set(new)∩set(90)≠∅ / set(new)∩set(D4 fit/val)≠∅ / rank/nested/守卫失败 / provenance 不可追溯 / timing 缺失伪造 → EVIDENCE_INVALID (最高优先级)
MIXED_BY_SOURCE   # 不同源分别落两类：逐源 shunt_s 不全同类（例 1M RECOVERED_s / 2M DOMAIN_SHIFT_s / 1p5M UNRESOLVED_s 混排）→ V56_MIXED_BY_SOURCE（含 contract 或 distribution 的源间异构，异构分叉先于均匀判定）
RECOVERED         # 七阶段一致且 compatible：三源均 contract_equivalent==True 且 distribution_compatible==True（三源分别 A==B>60% && acc≥60% && CE≤min(0.5*CE_current, V13ref+1.0) 预注册上限）→ V56_INPUT_CONTRACT_RECOVERED
DOMAIN_SHIFT      # 七阶段一致但统计均匀失败：三源均 contract_equivalent==True 且 三源均 distribution_compatible==False（均匀未达硬门槛，NLL/q_mass 仍高为一致性佐证）→ V56_TRUE_SESSION_DOMAIN_SHIFT
UNRESOLVED        # 无法重现权威路径或仍有分叉且均匀未闭合：V13 侧 INCOMPLETE_TTBin_UNAVAILABLE 均匀无法复放 / 三源均 contract_equivalent==False（异构分叉已由 MIXED 捕获）→ V56_INPUT_CONTRACT_UNRESOLVED
```
> **逐源判定先于总体**：先对每源 s 求 `shunt_s`（`UNRESOLVED_s=contract_s False/不可用`，`RECOVERED_s=contract true && distribution true`，`DOMAIN_SHIFT_s=contract true && distribution false`），再按上表优先级得 `overall`；`MIXED` 为异构，`RECOVERED/DOMAIN_SHIFT/UNRESOLVED` 为三源均匀。
- **仅 `RECOVERED` 才允许后续 decoder TEST**（需另起 `V57` OpenSpec，独立 `QUALIFICATION_PLAN_READY` + `EXECUTE_AUTH` 绑定新 SHA 与新 TEST registry；`V57` 的 qualification 为新 session 内 fresh within-session 还是跨 session 需另案声明，见边界）。
- 修复必须留在 **V56 wrapper/materializer**（`comparison_bench/.../v56_* / replay/verify 脚本内`），**不改 `src/` 基线**（`src/qkd_io/ttbin_pipeline.py` 等冻结只读复用）。

> **硬约束**：`V55` 原 `90-block` (`v55_authoritative_registry.json` 30/source) **永久禁用**，不在其上重跑任何 `corrected pipeline`（已揭盲 `0/90`）；同一新 session 剩余帧可作 **fresh within-session confirmation**（与校验帧零重叠的新块），但因已历 `V55` 多轮诊断**不宣称完全独立 cross-session qualification**；真正 **cross-session qualification 放 V57**（新采集 session）。

## Non-Goals

- 不运行任何 `L1-APP / L2` decoder（`decode_row_layered_fftqspa` 等零调用，`rg "decode_" 0 hits`）；不改 `H1-16 / Lane C m2 184/190/192 / H_inc1/2 Δ8+8 / 泄漏 1064/1094/1104+40+40 / tag L2-only / prior TRAIN-only / decoder 90/1.0 poly37` 任一冻结量；不试新 `Δm/degree/seed`。
- 不在原 `V55 90-block` 上重跑任何 corrected pipeline / offset-corrected 重译；不将 `1500K/600k/1.2M` 任何参数拟合 `V55` 已揭盲块。
- 不做 `bin_width/dimension/pairing/mapping/frame anchor` 网格搜索（`200ps legacy_v1 nearest 1024` 单点锚点）；B 阶段仅单点 V13 合同值，不择优。
- 不宣称 LDPC 证伪 / FER / 阈值 / SKR / 晋升；本变更止于 `PLAN_CANDIDATE / VERIFICATION_ONLY`，不直接进入 qualification。
- 不改写/覆盖 `V38–V56D4` 任何已有输出与终态（只读）；本轮不直接修改 `AGENT_PROJECT_MEMORY.md / docs/decision-log.md`（仅预留 V56 条目占位）。
- 不创建正式 `.../v56_*/run_01` decoder 执行；`V57` decoder TEST 需另起 OpenSpec 与独立 `EXECUTE_AUTH`。

## Scope

1. **冻结方法零改**：`n=1024, m2 184/190/192, GF32 poly37, H1-16 rank16 80b, L1-APP q via H1 BP (TRAIN channel_counts.npz), Lane C ordinal-2, H_inc1/2 Δ8+8, decoder 90/1.0 early-stop, L2-only tag 64b, TRAIN-only prior` 全只读，**零 decoder 直至 C 通过后 V57**。
2. **Phase 0 固化 V56D4**：独立 pre-RESULT review 记录 implementation/execution SHA，固化 `CE/acc 主、I32 辅、first_drop=U1U2_consistency、INCONCLUSIVE_MIXED_SIGNAL`，明确 `I32` 仅辅助不能单独归因；措辞冻结如上。
3. **Phase A 逐函数复放**：同批固定 calibration 帧，两路 materializer（V13 权威 vs current intake），逐阶段 `raw/channel → pairing/Δt → delay符号/位置 → frame-start/period/floor-div → bin → 1024 sym → U1/U2`，保存首个不一致阶段及行级样例，`array_equal` 定位首次分叉。
4. **Phase B 唯一修复（wrapper 内）**：仅一处，值必来自 V13 权威合同，old/current/corrected 三路字节/数组对照，**修复留在 V56 wrapper/materializer，不改 `src/` 基线**，不改 prior/H1/Lane C/增量矩阵/decoder。
5. **Phase C decoder-free 校准验收**：新校准帧（未进 90、未进 D4 fit/val），`contract_equivalent`（V13 与 corrected 七阶段逐元素一致，硬证据）+ `distribution_compatible`（三源分别 `A==B>60%` + `acc≥60%` + `CE≤min(0.5*CE_current, V13ref+1)` 预注册上限，三源分别不用总体平均），`NLL/q_mass` 仅一致性诊断，优先级 `EVIDENCE_INVALID > MIXED_BY_SOURCE > RECOVERED > DOMAIN_SHIFT > UNRESOLVED`（MIXED 异构先于均匀判定）。
6. **Phase D 终态 5 选 1**：`RECOVERED（七阶段一致且 compatible） / TRUE_SESSION_DOMAIN_SHIFT（一致但统计失败） / MIXED_BY_SOURCE（不同源分属两类） / INPUT_CONTRACT_UNRESOLVED（无法重现/仍分叉） / EVIDENCE_INVALID（证据/切分/零重叠失败）` 互斥按优先级判定；仅 `RECOVERED` 允许 `V57` decoder TEST。
7. **边界固化**：`V55 90` 永久禁用；同 session 剩余帧仅 fresh within-session confirmation，不宣称完全独立 cross-session qualification；真正 qualification 放 `V57` 新 session。

## Impact Scope

- **新增/修订（本变更）**：`openspec/changes/formal-ir-v56-input-contract-reconstruction/` 下 4 工件 `proposal.md/design.md/tasks.md/specs/spec.md` + 2 decoder-free 验证脚本 `replay_v13_vs_current.py` / `verify_corrected_calibration.py`（本变更目录下，`rg "decode_" 0 hits`）+ `RECONSTRUCTION_REPORT.md`（待 C/D 落盘后填充，含 per-source `A==B/CE/acc/NLL/q_mass + pipeline first_drop + 三路对照 + 终态`）+ `verification_manifest.json`（含 `HEAD、implementation SHA、data SHA、frame_ids、array_equal、provenance`）。
- **只读依赖**：`src/qkd_io/ttbin_pipeline.{read_ttbin_events,compute_cross_correlation_histogram}`（V13 已验证版，冻结基线，只读复用，`git diff -- src/` 必须 `0`）+ `v55_authoritative_registry.json` + `v55_intake_20260828/{sidecars,pairs}` + `workspace/v13r3fresh_20260816/sidecars + build_manifest.json` + `nbldpc_v25_20260818/run_04/channel_counts.npz` + `v56d4_low_dim_decomposition.json` + `comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_pairs_20260816`。
- **不修改**：任何既有 `spec/代码/测试/输出`（除本目录外）、`V38–V56D4` 输出、`outputs_comparison/workspace` 以外；**尤其不改 `src/` 基线，修复仅 V56 wrapper/materializer 内**；不创建正式 TEST `run_01`；**零 decoder、零码参数直至 V57**。

## Acceptance Criteria

- [ ] `proposal/design/tasks/specs/spec.md` 齐全一致，`lifecycle PLAN_CANDIDATE / VERIFICATION_ONLY / DECODE_FORBIDDEN`，`HEAD 49a415b` + `branch formal-ir-mainline` + `data SHA 84d62779` 已绑定，显式声明 decoder-free、零 decoder、禁重跑原 90、禁调 `H1/Lane C/Δ8/decoder`、I32 仅辅助、措辞冻结、**修复仅 wrapper 不改 `src/`**。
- [ ] **Phase 0 固化**可复现：独立 pre-RESULT review 已完成并落盘（implementation/execution SHA、`ACCEPTED_PLAN_SHA` 重推导 `rg 0 hits`、`py_compile`+关键测试 PASS、`fit∩val==∅`、`I32` 辅助声明、终态 `INCONCLUSIVE_MIXED_SIGNAL` 固化，`LOW_DIM_DECOMPOSITION_REPORT.md` 与 `json` 一致）。
- [ ] **Phase A 逐函数复放**可复现：同批固定 calibration 帧，两路 materializer 逐阶段 `raw/channel → pairing/Δt → delay符号/位置 → frame-start/period/floor-div → bin → 1024 sym → U1/U2` 的 `array_equal/Δt/occupancy` 已逐阶段落盘，**首个不一致阶段及行级样例**已保存，目标为“第一次产生不同数组的位置”。
- [ ] **Phase B 唯一修复**可复现：若找到差异，仅一处已修且**在 V56 wrapper/materializer 内**（`git diff -- src/ ==0`），修复值来自 V13 权威合同，`old/current/corrected` 三路字节/数组级对照已落盘（阶段后 `array_equal` 翻转），未改 prior/H1/Lane C/增量矩阵/decoder（`rg "prior|H1|Lane" 改动 0`）。
- [ ] **Phase C 校准验收**可复现：新校准帧未进 90 且未进 D4 `fit/val`（`set ∩ ==∅` 已验），三源分别 `contract_equivalent`（V13/corrected 七阶段逐元素一致，硬证据）+ `distribution_compatible`（`A==B>60%` 且 `acc≥60%` 且 `CE≤min(0.5*CE_current, V13ref+1)` 预注册上限，三源分别判定不用总体平均）已逐源报告，`NLL/q_mass` 仅一致性诊断；优先级 `EVIDENCE_INVALID > MIXED_BY_SOURCE > RECOVERED > DOMAIN_SHIFT > UNRESOLVED`（MIXED 异构先于均匀）。
- [ ] **Phase D 终态**可复现：`V56_INPUT_CONTRACT_RECOVERED（七阶段一致且 compatible） / V56_TRUE_SESSION_DOMAIN_SHIFT（一致但统计失败） / V56_MIXED_BY_SOURCE（不同源分别落两类） / V56_INPUT_CONTRACT_UNRESOLVED（无法重现/仍分叉） / V56_EVIDENCE_INVALID（证据/切分/零重叠失败）` 5 选 1 已按优先级判定落盘，逐源 `MIXED_BY_SOURCE` 已支持；仅 `RECOVERED` 才允许 `V57` decoder TEST 的声明已冻结。
- [ ] **边界**可复现：`V55 90` 永久禁用已声明；同 session 剩余帧仅 fresh within-session confirmation 不宣称完全独立 cross-session qualification 的边界已写入报告与 spec；真正 qualification 放 `V57` 已声明。
- [ ] `replay_v13_vs_current.py` 与 `verify_corrected_calibration.py` 为 decoder-free 可运行脚本（`rg "decode_" 0 hits`），仅 `numpy/pandas/pyarrow + ttbin_pipeline(TimeTagger optional)`，`py_compile` PASS，输出 `verification_manifest.json` + 控制台摘要；**未创建任何 `.../v56_*/run_01` decoder 执行**，已推送新 SHA 并停在 `PLAN_CANDIDATE / VERIFICATION_ONLY`，不碰 `V55 90` 块。

## Tasks

见 `tasks.md`（Phase 0 固化 V56D4 独立 pre-RESULT review；Phase A 逐函数复放 V13 vs current；Phase B 唯一修复三路对照；Phase C decoder-free 新帧校准验收；Phase D 终态 5 选 1；脚本与报告交付；显式禁止清单与 decoder-free 守卫）。

## Lifecycle

`V56D4` 当前 `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN`（HEAD `49a415b`, `INCONCLUSIVE_MIXED_SIGNAL` — CE/acc 主证据一致退化、I32 辅助低、occupancy 正常、first_drop 在 U1U2）；`V56` 本重建 `PLAN_CANDIDATE / VERIFICATION_ONLY / DECODE_FORBIDDEN`（仅 decoder-free 重放/修复/校准验证，不实现 runner，不执行 decoder，不创建 `run_01`，修复仅 wrapper 不改 `src/`）；C 验收中 `contract_equivalent`（七阶段逐元素一致）为硬证据、`distribution_compatible`（`A==B>60%` + `acc≥60%` + `CE≤min(0.5*CE_current, V13ref+1)` 三源分别）为硬门槛；仅 `RECOVERED` 才允许另起 `V57` 走 `QUALIFICATION_PLAN_READY` 与独立 `EXECUTE_AUTH` 的 decoder TEST，`V57` 的 cross-session qualification 为新采集 session。
