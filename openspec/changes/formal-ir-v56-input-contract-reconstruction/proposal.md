# OpenSpec Proposal: formal-ir-v56-input-contract-reconstruction

**Status**: `PLAN_CANDIDATE / VERIFICATION_ONLY / DECODE_FORBIDDEN` — **整合 V56 全链重建：先固化 V56D4 独立 pre-RESULT review，再 A逐函数复放→B单点修复→C decoder-free 校准验收→D终态分流，不拆 D5/D6。零 decoder 直至 C 通过后 V57 才允许 decoder TEST。**
**Domain**: Formal IR / V56 输入合同重建 (V56D4 唯一后继，终结 V56)
**Change ID**: `formal-ir-v56-input-contract-reconstruction`
**Cycle ID**: `V56` (input-contract-reconstruction), predecessor `V56D4` `formal-ir-v56d4-low-dim-decomposition`
**Predecessor**: `formal-ir-v56d4-low-dim-decomposition` (HEAD `176bf34f` / `b332b8a4a51e94fb905023862b8aed3650bac126` `formal-ir-mainline`, data SHA `84d62779603e62de50ded5182ed65b65d3dc6084` `84d62779` `200ps legacy_v1 nearest 1024` 单点；结论已固化为 `INCONCLUSIVE_MIXED_SIGNAL` — CE/acc 主证据 `1M CE13.25 acc0.46 / 1p5M 14.84/0.39 / 2M 16.68/0.30` 远差于 V13 `CE0.19-0.91 acc0.74-0.99`，32态 I `1.39-2.05` vs V13 `4.17-4.93` 低但仅辅助，occupancy 均 `256` 正常，first_drop 在 `U1U2_consistency`，因跨层指标混合未单点归因)
**Branch**: `formal-ir-mainline`
**HEAD**: `176bf34f` (V56D4 落盘后最新，实际以 `git rev-parse HEAD` 与 `origin/formal-ir-mainline` 重核为准，proposal 冻结时绑定)
**Data SHA**: `84d62779603e62de50ded5182ed65b65d3dc6084` (`84d62779`, `d=1024 bw=200ps pairing=nearest rule=legacy_v1` 单点不改，校准帧亦同点)
**Lifecycle**: `PLAN_CANDIDATE / VERIFICATION_ONLY / DECODE_FORBIDDEN` — 本变更止于 plan 候选与 decoder-free 验证脚本，不产生 `run_01` decoder 执行，不改 `H1/Lane C/Δ8/decoder 90/1.0/poly37`
**Method frozen**: `V54二阶段 H1-16(80b)+L1-APP via H1 BP(TRAIN channel_counts.npz)+Lane C m2 184/190/192+H_inc1/2 Δ8+8+decoder 90/1.0 poly37+L2-only tag` 完全冻结 (diagnosis/reconstruction 期零改)

> ponytail lite: 本变更仅 4 OpenSpec 工件 + 2 decoder-free 验证脚本 (`replay_v13_vs_current.py` + `verify_corrected_calibration.py`) + 1 报告模板；无 runner、无 decoder、无新矩阵、无新 prior，最短科学路径。laziest alternative: `numpy/pandas/pyarrow` 已装直算 I32/CE/acc，无需新依赖；V13 权威实现 `src/qkd_io/ttbin_pipeline` 只读复用，不重发明。

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

### B. 唯一修复（单点，不搜索）

- 若 A 找到**代码/合同差异**，**只修复该一处**，**不搜索** `delay / bin_width / mapping / frame anchor` 多候选，不做网格择优。
- **修复值必来自 V13 权威合同**（`sidecars` 实时读或 `ttbin_pipeline` 权威实现），不手填经验值。
- 产出 **old / current / corrected 三路字节/数组级对照**（`old=current` 时 `diff old→current` 非空，`diff current→corrected` 在首错阶段后显式分叉，阶段后 `array_equal` 翻转），**不改 prior / H1 / Lane C / 增量矩阵 `H_inc1/2` / decoder 任何参数**。

### C. decoder-free 校准验收（新帧，三源分别）

- 用**未进 V55 90-block 也未进现有 `fit=[7,8,9,10]/val=[15,16,17,18]` 的新校准帧**（预注册，如 `frames [0-6,11-14,19-...]` 中每源选 `8-16` 帧，与 `90-block` 及 `D4 fit/val` 均 `set ∩ == ∅` 可机械校验；`F=2130/5125/5513` 范围内）。
- **timing/routing 合同完整**且 **V13 与 corrected 逐阶段一致**（`raw/pairing/delay/frame/bin/symbol/U1U2` 附录对照 `array_equal PASS`）。
- **A==B >60%**（主门），**validation CE/accuracy 显著恢复**（`fit 4→val 4` 同切分，`CE_U1/U2` 从 `13-16` 向 V13 的 `0.19-0.91` 回落，`acc_U1/U2` 从 `0.30-0.46` 向 `0.74-0.99` 回升；阈 `CE<5` 且 `acc>60%` 视为显著恢复，门禁仅 `>60%` 一项，其余为一致性描述）。
- **NLL / q_mass 仅一致性诊断**（基于 `nbldpc_v25_20260818/run_04/channel_counts.npz` 的 `P(A|B)` 列归一，`NLL bits/sym` 与 `q_mass_on_p_zero` 仅报告回落方向，不作硬门禁；因 `V25 prior` 本身在新域可能失配，不以单一 `NLL` 阈定修复成败）。
- **三源分别通过**，任一源失败则终态 `V56_INPUT_CONTRACT_UNRESOLVED` 停止，不进入 D 的 `RECOVERED`。

### D. 终态分流（互斥 5 选 1）

```
V56_INPUT_CONTRACT_RECOVERED          # C 三源均过：输入合同可修复性得证
V56_TRUE_SESSION_DOMAIN_SHIFT         # A 未发现单点错或 corrected 亦低，U1U2 后亦低且 NLL/q_mass 仍高 → 真域迁移
V56_MIXED_BY_SOURCE                   # 源间不一致（例 1M recovered 2M domain_shift）
V56_INPUT_CONTRACT_UNRESOLVED         # C 任一源未过，修复未闭合
V56_EVIDENCE_INVALID                  # 完整性/守卫/零重叠/rank/nested 失败或 provenance 不可追溯
```
- **仅 `RECOVERED` 才允许后续 decoder TEST**（需另起 `V57` OpenSpec，独立 `QUALIFICATION_PLAN_READY` + `EXECUTE_AUTH` 绑定新 SHA 与新 TEST registry；`V57` 的 qualification 为新 session 内 fresh within-session 还是跨 session 需另案声明，见边界）。

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
4. **Phase B 唯一修复**：仅一处，值必来自 V13 权威合同，old/current/corrected 三路字节/数组对照，不改 prior/H1/Lane C/增量矩阵/decoder。
5. **Phase C decoder-free 校准验收**：新校准帧（未进 90、未进 D4 fit/val），timing/routing 完整且 V13/corrected 逐阶段一致，三源分别 `A==B>60%` + validation `CE/acc` 显著恢复（`CE 13-16→<5`, `acc 0.30-0.46→>0.60` 方向），`NLL/q_mass` 仅一致性诊断，任一源失败即 `UNRESOLVED`。
6. **Phase D 终态 5 选 1**：`RECOVERED / TRUE_SESSION_DOMAIN_SHIFT / MIXED_BY_SOURCE / INPUT_CONTRACT_UNRESOLVED / EVIDENCE_INVALID` 互斥；仅 `RECOVERED` 允许 `V57` decoder TEST。
7. **边界固化**：`V55 90` 永久禁用；同 session 剩余帧仅 fresh within-session confirmation，不宣称完全独立 cross-session qualification；真正 qualification 放 `V57` 新 session。

## Impact Scope

- **新增/修订（本变更）**：`openspec/changes/formal-ir-v56-input-contract-reconstruction/` 下 4 工件 `proposal.md/design.md/tasks.md/specs/spec.md` + 2 decoder-free 验证脚本 `replay_v13_vs_current.py` / `verify_corrected_calibration.py`（本变更目录下，`rg "decode_" 0 hits`）+ `RECONSTRUCTION_REPORT.md`（待 C/D 落盘后填充，含 per-source `A==B/CE/acc/NLL/q_mass + pipeline first_drop + 三路对照 + 终态`）+ `verification_manifest.json`（含 `HEAD、implementation SHA、data SHA、frame_ids、array_equal、provenance`）。
- **只读依赖**：`src/qkd_io/ttbin_pipeline.{read_ttbin_events,compute_cross_correlation_histogram}`（V13 已验证版，冻结基线，只读复用）+ `v55_authoritative_registry.json` + `v55_intake_20260828/{sidecars,pairs}` + `workspace/v13r3fresh_20260816/sidecars + build_manifest.json` + `nbldpc_v25_20260818/run_04/channel_counts.npz` + `v56d4_low_dim_decomposition.json` + `comparison_bench/outputs_comparison/nonbinary_diagnostics/v13r3fresh_pairs_20260816`。
- **不修改**：任何既有 `spec/代码/测试/输出`（除本目录外）、`V38–V56D4` 输出、`outputs_comparison/workspace` 以外；不创建正式 TEST `run_01`；**零 decoder、零码参数直至 V57**。

## Acceptance Criteria

- [ ] `proposal/design/tasks/specs/spec.md` 齐全一致，`lifecycle PLAN_CANDIDATE / VERIFICATION_ONLY / DECODE_FORBIDDEN`，`HEAD 176bf34f` + `branch formal-ir-mainline` + `data SHA 84d62779` 已绑定，显式声明 decoder-free、零 decoder、禁重跑原 90、禁调 `H1/Lane C/Δ8/decoder`、I32 仅辅助、措辞冻结。
- [ ] **Phase 0 固化**可复现：独立 pre-RESULT review 已完成并落盘（implementation/execution SHA、`ACCEPTED_PLAN_SHA` 重推导 `rg 0 hits`、`py_compile`+关键测试 PASS、`fit∩val==∅`、`I32` 辅助声明、终态 `INCONCLUSIVE_MIXED_SIGNAL` 固化，`LOW_DIM_DECOMPOSITION_REPORT.md` 与 `json` 一致）。
- [ ] **Phase A 逐函数复放**可复现：同批固定 calibration 帧，两路 materializer 逐阶段 `raw/channel → pairing/Δt → delay符号/位置 → frame-start/period/floor-div → bin → 1024 sym → U1/U2` 的 `array_equal/Δt/occupancy` 已逐阶段落盘，**首个不一致阶段及行级样例**已保存，目标为“第一次产生不同数组的位置”。
- [ ] **Phase B 唯一修复**可复现：若找到差异，仅一处已修，修复值来自 V13 权威合同，`old/current/corrected` 三路字节/数组级对照已落盘（阶段后 `array_equal` 翻转），未改 prior/H1/Lane C/增量矩阵/decoder（`rg "prior|H1|Lane" 改动 0`）。
- [ ] **Phase C 校准验收**可复现：新校准帧未进 90 且未进 D4 `fit/val`（`set ∩ ==∅` 已验），三源分别 `timing/routing` 完整且 V13/corrected 逐阶段一致 + `A==B>60%` + `validation CE/acc` 显著恢复（`CE 13-16→<5`, `acc 0.30-0.46→>60%`）已逐源报告，`NLL/q_mass` 仅一致性诊断，任一源失败即 `UNRESOLVED`。
- [ ] **Phase D 终态**可复现：`V56_INPUT_CONTRACT_RECOVERED / V56_TRUE_SESSION_DOMAIN_SHIFT / V56_MIXED_BY_SOURCE / V56_INPUT_CONTRACT_UNRESOLVED / V56_EVIDENCE_INVALID` 5 选 1 已按 `C` 与 `A/B` 联合判定落盘，逐源 `MIXED_BY_SOURCE` 已支持；仅 `RECOVERED` 才允许 `V57` decoder TEST 的声明已冻结。
- [ ] **边界**可复现：`V55 90` 永久禁用已声明；同 session 剩余帧仅 fresh within-session confirmation 不宣称完全独立 cross-session qualification 的边界已写入报告与 spec；真正 qualification 放 `V57` 已声明。
- [ ] `replay_v13_vs_current.py` 与 `verify_corrected_calibration.py` 为 decoder-free 可运行脚本（`rg "decode_" 0 hits`），仅 `numpy/pandas/pyarrow + ttbin_pipeline(TimeTagger optional)`，`py_compile` PASS，输出 `verification_manifest.json` + 控制台摘要；**未创建任何 `.../v56_*/run_01` decoder 执行**，已推送新 SHA 并停在 `PLAN_CANDIDATE / VERIFICATION_ONLY`，不碰 `V55 90` 块。

## Tasks

见 `tasks.md`（Phase 0 固化 V56D4 独立 pre-RESULT review；Phase A 逐函数复放 V13 vs current；Phase B 唯一修复三路对照；Phase C decoder-free 新帧校准验收；Phase D 终态 5 选 1；脚本与报告交付；显式禁止清单与 decoder-free 守卫）。

## Lifecycle

`V56D4` 当前 `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN`（HEAD `176bf34f`, `INCONCLUSIVE_MIXED_SIGNAL` — CE/acc 主证据一致退化、I32 辅助低、occupancy 正常、first_drop 在 U1U2）；`V56` 本重建 `PLAN_CANDIDATE / VERIFICATION_ONLY / DECODE_FORBIDDEN`（仅 decoder-free 重放/修复/校准验证，不实现 runner，不执行 decoder，不创建 `run_01`）；C 验收后 `RECOVERED` 才允许另起 `V57` 走 `QUALIFICATION_PLAN_READY` 与独立 `EXECUTE_AUTH` 的 decoder TEST，`V57` 的 cross-session qualification 为新采集 session。
