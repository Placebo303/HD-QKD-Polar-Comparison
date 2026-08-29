# OpenSpec Tasks: formal-ir-v56-input-contract-reconstruction — V56 输入合同重建（整合，不拆 D5/D6）

**Lifecycle**: `PLAN_CANDIDATE / VERIFICATION_ONLY / DECODE_FORBIDDEN` — **整合 V56 全链：0固化V56D4 → A逐函数复放 → B单点修复(wrapper 内) → C decoder-free 校准验收(硬门槛) → D终态 5 选 1，零 decoder 直至 C 通过后 V57 才 decoder TEST**
**HEAD**: `49a415b8253c9c73da0013588d0c50c0e9d41dba` (`49a415b`, branch `formal-ir-mainline`, 实际以 `git rev-parse HEAD` 与 `origin/formal-ir-mainline` 重核为准) + data SHA `84d62779603e62de50ded5182ed65b65d3dc6084` (84d62779 200ps legacy_v1 nearest 1024)
**Predecessor**: `formal-ir-v56d4-low-dim-decomposition` `V56D4` `INCONCLUSIVE_MIXED_SIGNAL` (CE 13-16 acc 0.30-0.46 vs V13 CE0.19-0.91 acc0.74-0.99, I32 1.39-2.05 vs 4.17-4.93 仅辅助, occupancy 256 正常, first_drop U1U2_consistency)
**Method frozen**: `V54二阶段 H1-16/Lane C m2 184/190/192/H_inc1/2 Δ8+8/decoder 90/1.0 poly37/L2-only tag/TRAIN prior` 零改直至 V57
**Boundary**: `V55` 原 `90-block` 永久禁用；同 session 剩余帧仅 fresh within-session confirmation 不宣称完全独立 cross-session qualification；真正 qualification 放 `V57` 新 session

## Phase 0 — 固化 V56D4 独立 pre-RESULT review（阻塞门，decoder-free）

- [ ] **0.1 独立 pre-RESULT review**：独立线程/reviewer 复核 `HEAD == origin/formal-ir-mainline == implementation SHA`、`ACCEPTED_PLAN_SHA (=176bf34f V56D4 plan HEAD)` 重推导一致且 `rg <stale SHA> 0 hits`、`target run_01` 不存在（本变更无 `run_01`）、预算/门禁/`cycle_state` 与冻结 plan 一致、`py_compile` + 关键测试 PASS；逐项勾选落盘于 `REVIEW_CHECKLIST.md` 或 `RECONSTRUCTION_REPORT.md §0`，`FAIL` 则阻塞 `A-D` 进入 `revise-required` 新 SHA 重审
- [ ] **0.2 记录 SHA**：`implementation SHA = HEAD`、`execution SHA = N/A (decoder-free)`、`ACCEPTED_PLAN_SHA` 写入 `v56d4_low_dim_decomposition.json:provenance` 与报告头，`git rev-parse HEAD` / `git rev-parse origin/formal-ir-mainline` / `rg <stale SHA>` 可复现
- [ ] **0.3 固化 V56D4 结论**：`CE_U1 13.25/14.84/16.68 CE_U2 13.63/14.96/15.15 acc 0.30-0.46` 主证据、`I_U1 2.05/1.74/1.39 I_U2 2.01/1.69/1.36` 辅助（`V13 I 4.17-4.93` 对比，交叉 `0.77-0.80` 一致）、`first_drop=U1U2_consistency`（`occupancy 256` 正常）、`overall=INCONCLUSIVE_MIXED_SIGNAL` 混合不强制二选一；明确 **I32 仅辅助不能单独归因**（`1024样本/1024格` 理论偏置 `~0.47 bits` 已注）；措辞冻结“未发现能由 fit4 学得并在 val4 泛化的1024态经验映射；已排除五类预注册物理映射（2060候选）”

## Phase A — 逐函数复放 V13 合同（decoder-free，定位首次分叉）

- [ ] **A1 固定同批 calibration 帧**：预注册固定 `frames [7,8,9,10,15,16,17,18]`（或其子集 `N=2048` pairs），三源一致，`frame_ids` 写入 `verification_manifest.json:provenance.frames`，与 `V55 90-block` 零重叠（`set ∩ ==∅` 可验）
- [ ] **A2 双 materializer 定义**：
  - `V13-authoritative`：`workspace/v13r3fresh_20260816/sidecars/*/sidecar_meta.json: used_params` + `build_manifest.json` 实时读（不硬编码 `delay -50/+50` 等），复用 `src/qkd_io/ttbin_pipeline.{read_ttbin_events,compute_cross_correlation_histogram}` 冻结基线实现（`read_ttbin_events(ch 1/5) → compute_cross_correlation_histogram(bin100/max819200/n16384, lag=t_B-t_A) → pairing nearest threshold 40000ps/direction/wrap_rule → delay 应用 → frame_start/period 204800 floor_div → bin 200ps → legacy_v1 symbol 1024 → F03 5+5 U1/U2`）
  - `current-intake`：`comparison_bench/outputs_comparison/v55_intake_20260828/sidecars` 当前单点 `200ps legacy_v1 nearest 1024` 实现（若 intake 为已落盘 `pairs.parquet` 则以其生成链路为准，缺失字段记 `INCOMPLETE`）
- [ ] **A3 逐阶段比对（7 段截断即停）**：
  `raw event/channel selection (channel 1/5 counts, other<20%, unique⊇{1,5}) → pairing index/Δt (pair indices, Δt hist/median, paired count) → delay 符号及应用位置 (delay_used_ps sign, 前/后于 pairing/bin) → frame-start/period/floor-div (frame_start_ps, period 204800, floor_div, before/after pair index) → bin index (200ps) → 1024 symbol (legacy_v1) → U1/U2 (sym>>5/sym&31)`；每阶段 `np.array_equal` / `mean_equal` / `Δt median` / `occupancy`，**保存首个不一致阶段及行级样例**（前 5 行 `pair_idx,t_A,t_B,Δt,bin_A,bin_B,sym_A,sym_B,U1_A,U2_A,U1_B,U2_B`），目标**找到第一次产生不同数组的位置**
- [ ] **A4 落盘**：`per_stage {stage, V13_val, current_val, delta, array_equal, sample_rows}` + `first_divergent_stage` 写入 `verification_manifest.json:per_stage`，控制台摘要打印 `first_divergent_stage` 与样例；`rg "decode_" 0 hits` 可验

## Phase B — 唯一修复（单点，V13 权威值，不搜索，wrapper 内硬约束）

- [ ] **B1 判定差异**：若 `first_divergent_stage` 非空且 `array_equal==False` 首次出现，记录 `divergent_stage` 与 `divergent_field`（如 `delay sign / frame_start null vs peak_center / floor_div / bin / symbol`），`rg "grid" 0 hits`（候选仅 old/current/corrected 3 路，不搜索 `delay/bin_width/mapping/frame anchor`）
- [ ] **B2 单点修复（wrapper 内）**：**只修复该一处**，不搜索多候选；**修复值必来自 V13 权威合同**（`sidecar used_params` 实时读或 `ttbin_pipeline` 权威实现只读对照），不手填经验值；**修复必须留在 V56 wrapper/materializer**（`comparison_bench/.../v56_*` 或脚本参数层），**严禁改 `src/` 基线**（`git diff -- src/ ==0` 可验，`src/qkd_io/ttbin_pipeline.py` 零改动）；若曾误改 `src/` 则回退并在 wrapper 重做，新 SHA 重绑并记录 `ACCEPTED_PLAN_SHA` 重推导
- [ ] **B3 三路对照**：`old = current` 原实现、`current` = 修复前、`corrected` = 单点修后，三路字节/数组级对照（`old→current diff` 非空，`current→corrected` 在首错阶段后显式分叉，阶段后 `array_equal` 翻转，前阶段仍一致），写入 `verification_manifest.json:three_way_comparison`，数据与 `RECONSTRUCTION_REPORT.md` 一致
- [ ] **B4 守卫**：不改 `prior / H1 / Lane C / 增量矩阵 H_inc1/2 / decoder` 任何参数（`git diff -- comparison_bench/src/comparison_bench/formal_ir/` 0 改动，`rg "CHANNEL_COUNTS|H1|L1-APP|H_inc"` 改动 0）；`git diff -- src/ ==0` 已验；`py_compile` PASS

## Phase C — decoder-free 校准验收（新帧，三源分别，硬门槛，DECODE_FORBIDDEN）

- [ ] **C1 新校准帧预注册（含 CE 上限预注册）**：未进 `V55 90-block`（`set(new) ∩ set(V55 90×4) ==∅`）也未进 `D4 fit=[7,8,9,10]/val=[15,16,17,18]`（`set(new) ∩ set(fit∪val) ==∅`），每源 `8-16` 帧（例 `1M [0,1,2,3,11,12,13,14] 1p5M 同 2M 同`，`frame_id∈[0,F-1] F=2130/5125/5513`，`pairs_per_frame 256` 连续，三源一致），`assert` 守卫落盘 `calibration_new_registry.json`（`frame_ids, F, K, gap, pairs_count`），与 `90` 及 `D4 fit/val` 零重叠可机械校验；**同时预注册每源 `CE_V13ref_U1/U2` 与 `CE 上限 = min(0.5*CE_current, CE_V13ref+1.0)`（写入 `verification_manifest.json:pre_registered_thresholds`，事后不调）**
- [ ] **C2 timing/routing 合同完整（前置守卫）**：
  - `timing_contract_verified` — 真实重算 `TimeTagger` 环境下 `peak_center/σ/p2bg`（记录 `interpreter_path/TimeTagger版本/输入事件数`，`V13` 同环境同版本），`peak` 健康（`σ 50-150ps` 窄）且 `|peak - delay_used|<50ps` 且 `sign` 一致且 `gate 200ps/threshold 40000ps/frame_start/period 204800` 已显式落盘；缺失时只能 `EVIDENCE_INCOMPLETE` 不得判 `RECOVERED`
  - `routing` — 指定 `channel 1/5` 存在且非零（`count_A>0 && count_B>0 && unique⊇{1,5}`）且无跨 `channel`/丢列/错误合并（`other<20%` 完整性），比例仅报告（`1M/2M 36.4%` 可能来自探测效率非 routing 错误）；`per_source {timing_status, routing_status}` 落盘
- [ ] **C3 contract_equivalent（硬证据，门 1）**：对新帧同批 `ttbin`，`V13-authoritative` 与 `corrected` 在 `raw/channel → pairing/Δt → delay/位置 → frame-start/period/floor-div → bin → 1024 sym → U1/U2` 七阶段均 `array_equal PASS`（附录对照），`per_stage_V13_corrected: {stage, array_equal, delta}` 落盘；任一阶段 `False` 即 `contract_equivalent=False`
- [ ] **C4 distribution_compatible 门 2a — A==B >60%（三源分别）**：新校准小批量上（`8-16` 帧 `2048-4096` pairs）`rate_eq = mean(a==b)` 三源分别 `>60%`（`V55` 原 `27-41%`，`V13` 健康 `~99% U1 / 74% U2`），`per_source {A_eq, threshold 60%, pass}` 落盘，不用总体平均
- [ ] **C5 distribution_compatible 门 2b/2c — validation accuracy≥60% 且 CE 预注册上限（三源分别）**：`fit 4→val 4` 同切分（`fit` 新帧前 4 学 `P_fit(a|b) 1024→32` 列归一，`val` 后 4 测 `CE_U1/U2 = E[-log2 P_fit]`、`acc_U1/U2 = mean(a==argmax P_fit)`），三源分别 `acc_U1≥60%` 且 `acc_U2≥60%` 且 `CE_U1 ≤ min(0.5*CE_current_U1, CE_V13ref_U1+1.0)` 且 `CE_U2 ≤ min(0.5*CE_current_U2, CE_V13ref_U2+1.0)`（`CE_current` 为 `V56D4` 基线 `13-16`，相对至少下降 50% 且不高于 V13+1 bits，取严）；`per_source {CE_U1/CE_U2/acc_U1/acc_U2, CE_current, CE_V13ref, CE_threshold, delta, pass}` 落盘
- [ ] **C6 NLL / q_mass 仅一致性诊断**：基于 `nbldpc_v25_20260818/run_04/channel_counts.npz` 的 `P(A|B)` 列归一，`NLL = mean(-log2 P(a|b))` 与 `q_mass_on_p_zero = sum_{N_ab=0} P_emp` 仅报告回落方向（`V55 NLL 28-35 q_mass 57-71%` → 新帧向 `V13 ~0.82/3%` 靠近），不作硬门禁，`per_source {NLL, q_mass, note}` 落盘
- [ ] **C7 三源分别判定（硬门槛，不用总体平均）**：每源 `pass_s = timing_complete && routing_complete && contract_equivalent_s && distribution_compatible_s`（`distribution_compatible_s = Aeq>60% && acc≥60% && CE≤threshold`）；`1M` 且 `1p5M` 且 `2M` 均 `pass_s==True` → `C PASS`；否则按 §D 优先级分流（`EVIDENCE_INVALID > MIXED_BY_SOURCE > RECOVERED > DOMAIN_SHIFT > UNRESOLVED`），`C_verdict per_source {contract_equivalent, Aeq, acc, CE, CE_threshold, NLL, q_mass, pass}` 落盘

## Phase D — 终态 5 选 1（互斥，按优先级，不主观，decoder-free）

- [ ] **D1 5 选 1 互斥分流（优先级从高到低，不主观）**：
  ```
  # 硬定义：contract_equivalent = V13 与 corrected 七阶段逐元素一致 (§C3，硬证据)；distribution_compatible = 三源分别 A==B>60% && acc≥60% && CE≤min(0.5*CE_current, V13ref+1.0) 预注册上限 (§C4/C5，不用总体平均)
  # 先逐源判定 shunt_s：UNRESOLVED_s (contract_equivalent_s==False 或 TTBin 不可用)；RECOVERED_s (contract true && distribution true)；DOMAIN_SHIFT_s (contract true && distribution false)
  if 完整性/守卫/零重叠/rank/nested 失败 或 provenance 不可追溯 或 fit∩val≠∅ 或 set(new)∩set(90)≠∅ / ∩set(D4 fit/val)≠∅ 或 timing 缺失伪造:
      overall = V56_EVIDENCE_INVALID          # 证据/切分/零重叠失败，最高优先级
  elif per_source shunt_s 不全同类 (例 1M RECOVERED_s / 2M DOMAIN_SHIFT_s / 1p5M UNRESOLVED_s 混排，三源 shunt_s 不一致):
      overall = V56_MIXED_BY_SOURCE           # 不同源分别落两类（含 contract 或 distribution 的源间异构，异构分叉先于均匀判定）
  elif 三源均 contract_equivalent==True 且 三源均 distribution_compatible==True:
      overall = V56_INPUT_CONTRACT_RECOVERED  # 七阶段一致且 compatible（三源分别硬门槛通过）
  elif 三源均 contract_equivalent==True 且 三源均 distribution_compatible==False:
      overall = V56_TRUE_SESSION_DOMAIN_SHIFT # 七阶段一致但统计均匀失败（contract 均一致，distribution 三源均未达硬门槛），真域迁移
  elif 三源均 contract_equivalent==False 或 V13 侧 INCOMPLETE_TTBin_UNAVAILABLE 均匀无法复放:
      overall = V56_INPUT_CONTRACT_UNRESOLVED # 无法重现权威路径或仍有分叉且三源均匀未闭合（异构已由 MIXED 捕获）
  ```
  `MIXED_BY_SOURCE` 时逐源分别报告修复/排查清单；`UNRESOLVED` 时报告“仍有分叉/无法复现”而非“统计未恢复”；`overall` 与 `shunt_per_source {contract_equivalent, distribution_compatible, pass}` 落盘 `calibration_verification.json:overall`
- [ ] **D2 仅 RECOVERED 才允许后续 decoder TEST**：`RECOVERED` 时报告显式声明“**允许另起 V57 走 QUALIFICATION_PLAN_READY + EXECUTE_AUTH 的 decoder TEST**”，其余 4 态均显式“**不允许 decoder TEST**”；`V57` 的 qualification 为新 session 跨 session 还是 within-session 需另案声明，**本变更不宣称任何 decoder 资格**
- [ ] **D3 边界固化**：报告与 spec 显式声明 `V55 90` 永久禁用（已揭盲 `0/90`）；同 session 剩余帧仅 `fresh within-session confirmation`（与校验帧零重叠的新块）**不宣称完全独立 cross-session qualification**；真正 qualification 放 `V57` 新 session

## Phase E — 脚本与报告交付（PLAN_CANDIDATE / VERIFICATION_ONLY）

- [ ] **E1 编写 `replay_v13_vs_current.py`** (decoder-free, 本变更目录下): `python replay_v13_vs_current.py [--ttbin-root ...] [--pairs-root ...] [--v13-sidecars ...] [--frames 7,8,9,10,15,16,17,18] [--out verification_manifest.json]` → 同批固定 calibration 帧，两路 materializer 逐阶段 `array_equal` + 首错样例，`rg "decode_" 0 hits` 仅 `numpy/pandas/pyarrow + ttbin_pipeline(TimeTagger optional)`，`py_compile` PASS，输出 `verification_manifest.json:per_stage + first_divergent_stage + provenance(HEAD/data SHA/ACCEPTED_PLAN_SHA/frames)` + 控制台摘要；`TimeTagger` 不可用时 `raw/pairing` 记 `INCOMPLETE_TTBin_UNAVAILABLE` 不伪造 `peak`
- [ ] **E2 编写 `verify_corrected_calibration.py`** (decoder-free, 本变更目录下): `python verify_corrected_calibration.py [--ttbin-root ...] [--corrected-pairs ...] [--v13-sidecars ...] [--new-frames ...] [--counts ...] [--out calibration_verification.json]` → 新帧 `timing/routing` + `V13/corrected` 一致 + `A==B>60%` + `validation CE/acc` + `NLL/q_mass` 一致性，`rg "decode_" 0 hits`，`py_compile` PASS，输出 `calibration_verification.json` + 控制台摘要，校验 `set(new)∩set(90)==∅` 且 `∩set(D4 fit/val)==∅`，`TimeTagger` 不可用时 `timing` 记 `EVIDENCE_INCOMPLETE`
- [ ] **E3 撰写 `RECONSTRUCTION_REPORT.md`**：每源 `A==B/CE/acc/NLL/q_mass + pipeline first_drop + V13 vs current + old/current/corrected 三路对照` + `C` 新帧验收 + 总体 5 选 1 终态，数据与 `json` 一致，含 `V55 90 已揭盲不可复用` + `同 session 剩余帧仅 within-session confirmation` + `真正 qualification 放 V57` 边界，结论不扩大为 `FER/阈值/SKR/晋升`，明确 `I32` 仅辅助
- [ ] **E4 自检**：`py_compile` 双脚本 PASS, `rg "decode_" 0 hits`, `git diff -- src/ ==0` 已验, `fit∩val==∅` 已验, `set(new)∩set(90)==∅ && ∩set(D4 fit/val)==∅` 已验, `I32` 辅助 + `CE/acc` 主 + `contract_equivalent`(七阶段逐元素一致) + `distribution_compatible`(`A==B>60%` + `acc≥60%` + `CE≤min(0.5*CE_current,V13ref+1)` 三源分别) + `timing/routing` 完整 已报告, 三路对照已落盘, `first_divergent_stage` 已定位, `I32` 未单独归因已声明, 报告与 json 一致
- [ ] **E5 推送新 SHA 并停留 `PLAN_CANDIDATE / VERIFICATION_ONLY / DECODE_FORBIDDEN`**，未创建任何 `.../v56_*/run_01` decoder 执行，不碰 `V55 90` 块，不运行 decoder，仅改本目录文件与脚本（**不改 `src/`**），`V56D4` 固化已记录，等待 `V57` 另起 qualification

## 本变更显式禁止

decoder 调用 (`decode_*` / `construct_*` / `sample_uniform_gf32` 等)；在原 V55 90-block 上重跑任何 corrected pipeline（含 offset/mapping-corrected 重译)；调 `H1/Lane C/Δ8/decoder 90/1.0/m2/leak/prior/H_inc` 任一冻结参数；**改 `src/` 基线**（`src/qkd_io/ttbin_pipeline.py` 等只读复用，修复仅 V56 wrapper/materializer）；宣称 LDPC 证伪或 FER/阈值/SKR/晋升；创建正式 `.../v56_*/run_01` decoder 执行；任意 `1024` 置换/`1024!` 搜索/神经网络映射；`bin_width/dimension/pairing` 网格（`V13` vs current 仅两路 + corrected 三路，不网格择优）；`I32` 单独归因；将校准择优值回注为新 pipeline；**重发明 V13 已验证 channel/delay/peak/gate/frame-start/mapping/pairing 近似物化**；同帧 `fit/val` 评价；覆盖已有输出；`V55 90` 永久禁用違反；**主观“显著恢复”替代 `CE≤min(0.5*CE_current,V13ref+1)` 硬门槛**。

## 验收

- proposal/design/tasks/specs 一致 HEAD 49a415b 84d62779 lifecycle PLAN_CANDIDATE VERIFICATION_ONLY DECODE_FORBIDDEN 终态 5 选 1 按优先级互斥明确（`EVIDENCE_INVALID > MIXED_BY_SOURCE(异构) > RECOVERED(七阶段一致且compatible) > DOMAIN_SHIFT(一致但统计均匀失败) > UNRESOLVED(均匀未闭合)`），显式 I32 仅辅助、V55 90 永久禁用、同 session 仅 within-session 不独立、真正 qualification 放 V57、**修复仅 wrapper 不改 src/**
- 独立 pre-RESULT review 已完成并落盘 SHA 绑定；逐函数复放同批帧两路 7 段 `array_equal` 已逐阶段落盘且 `first_divergent_stage` 及行级样例已保存；若有单点差异仅一处已修（wrapper 内，`git diff -- src/ ==0`）且值来自 V13 权威且三路对照已落盘
- 新校准帧未进 90 且未进 D4 fit/val 已验，三源分别 `contract_equivalent`(七阶段逐元素一致，硬证据) + `distribution_compatible`(`A==B>60%` + `acc≥60%` + `CE≤min(0.5*CE_current,V13ref+1)` 预注册上限，三源分别不用总体平均) + timing/routing 完整 已逐源报告，NLL/q_mass 仅一致性，优先级 `EVIDENCE_INVALID > MIXED > RECOVERED > DOMAIN_SHIFT > UNRESOLVED`
- 双脚本 `rg 0 hits` `py_compile` PASS 报告与 json 一致 未建 `run_01` 已推新 SHA PLAN_CANDIDATE VERIFICATION_ONLY 仅改本目录（**不改 src/**），原 90 未碰 主算法不否定，V56D4 固化已记录
