# OpenSpec Design: formal-ir-v56-input-contract-reconstruction

**Lifecycle**: `PLAN_CANDIDATE / VERIFICATION_ONLY / DECODE_FORBIDDEN` — **整合重建，不拆 D5/D6，零 decoder 直至 C 通过后 V57，修复仅 wrapper 不改 src/**
**Cycle**: `V56` (input-contract-reconstruction), predecessor `V56D4` `49a415b` `INCONCLUSIVE_MIXED_SIGNAL`
**Branch**: `formal-ir-mainline` HEAD `49a415b8253c9c73da0013588d0c50c0e9d41dba` data SHA `84d62779603e62de50ded5182ed65b65d3dc6084` (200ps legacy_v1 nearest 1024, 单点)
**Feasibility**: `V56D4` 已在 `pairs.parquet` 上证 `CE 13-16 acc 0.30-0.46` 全面退化 vs `V13 CE0.19-0.91 acc0.74-0.99` 健康，但 `occupancy 256` 正常且 `I32 1.3-2.0` vs `V13 4.1-4.9` 仅辅助、`first_drop=U1U2_consistency` 混合不单点归因；`V13` 已验证 `channel/delay/peak/gate/frame-start/mapping/pairing` 实现可只读复用，无需网格搜索；逐函数复放可在 `debug` 层定位首次分叉，单点 V13 值修复后同批新帧 decoder-free 验收即可闭环，无需 decoder。
**Key judgement**: **`0/90` 非算法证伪，`V56D4` 的 CE/acc 主证据已证输入域系统性失配，但 I32 仅辅助且 occupancy 正常说明非简单丢帧；必须逐函数复放找到第一次产生不同数组的位置，单点修 V13 合同值，再以新帧三源分别 `>60%` 验证可修复性，否则不得进入 decoder。**

## 1. 科学问题与关键判断

> V54 在 `2026-01-21` 域 `43/45`，V55 同方法同点新域 `0/90`；V56D0 猜 `A1/A2/B` 需分流，V56D1 补 raw `peak 窄127ps p2bg 378-708` 部分健康，V56D2 校准 `A==B 27-42% NLL 22-28` 未回落，V56D3 排除五类物理映射 `2060` 候选未恢复，V56D4 以 `32` 态去偏 + `fit→val CE/acc` 主证据证 `CE 13-16 acc 0.30-0.46` 全面退化但 `occupancy 256` 正常、`first_drop` 在 `U1U2` 且 `I32` 仅辅助、`INCONCLUSIVE_MIXED_SIGNAL` 混合不单点归因。**剩余怀疑集中于 `pairing/frame` 链路中某一步的 V13 vs current 合同/代码差异**（delay 符号、应用位置、`frame_start` 空值回退、`floor_div`、`bin`、`legacy_v1`、`U1U2`），需逐函数复放定位首次分叉。

- **不变量**：`dimension 1024 / bin_width 200ps / pairing nearest / legacy_v1 / frame_period 204800ps / BLOCK 4×256 / F03 5+5` 为名义不变量；`V13` 的 `pairing policy/direction/threshold 40000ps/gate 200ps/frame_start/period/delay_used -50/+50/peak_center -50/+50/mapping/wrap_rule occupancy_filter` 为已知健康合同（从 `workspace/v13r3fresh_20260816/sidecars` 实时读）。
- **去偏原理**：`V56D4` 已固化 `CE/acc` 主、`I32`辅（`32×32` 在 `N=1024` 时 `~1/格`，理论偏置 `~0.47 bits` 远小于 `1024×1024` 的 `~500 bits`，但仍需偏置声明）；`first_drop=U1U2_consistency` 说明 `raw coincidence` 与 `occupancy` 未先坍塌，**首次分叉在 `U1U2` 前的某一步**（`pairing/frame/bin/symbol` 链），需逐函数复放。
- **单点修复原理**：不在 `delay/bin_width/mapping/frame anchor` 间搜索择优，仅当逐函数复放找到唯一代码/合同差异时，将该处值**必取 V13 权威合同**（`sidecar used_params` 或 `ttbin_pipeline` 权威实现），`old/current/corrected` 三路字节级对照可证修复必要且充分。
- **校准验收原理**：新校准帧未进 `90` 且未进 `D4 fit/val`，与权威帧零重叠；`timing/routing` 合同完整且 `V13` 与 `corrected` 逐阶段 `array_equal PASS`，`A==B>60%` 且 `validation acc≥60%` 且 `CE ≤ min(0.5*CE_current, CE_V13ref+1.0)` 预注册硬上限（`CE_current 13-16` 相对至少下降 50% 且不高于 `V13 0.19-0.91 +1 bit`，三源分别）方可 `RECOVERED`；`NLL/q_mass` 仅一致性诊断（`V25 prior` 在新域可能失配，不以 `NLL` 单阈硬判）。

## 2. 冻结语义 — V54 方法与 V55 intake 零改

| 项 | 冻结值 | 来源 |
|---|---|---|
| n/d | 1024 | V31/V55 |
| m2 per source | 184 (1M) 190 (1p5M) 192 (2M) | Lane C ordinal-2 |
| GF | GF32 poly37 | GF2mField |
| H1 | V31-H1-QC-16×1024 rank16 80b | V31 |
| 泄漏 | base 1064/1094/1104 +40 +40 | m1=16+64b tag |
| 译码 (冻结禁用) | decode_row_layered_fftqspa 90/1.0 | V43/V52 — 重建期禁用直至 V57 |
| L1-APP | p via H1 BP TRAIN channel_counts.npz | V25 |
| Intake | d1024 bw200 nearest legacy_v1 A1/B5 单点 84d62779 | V55 authoritative |
| V13 合同 | 从 `workspace/v13r3fresh_20260816/sidecars/*/sidecar_meta.json` + `build_manifest.json` 实时读 | V13 |
| Fit/Val | `fit=[7,8,9,10] val=[15,16,17,18]` assert ∩==∅ | V56D4 预注册 |

**禁令**：`SHALL NOT` 任何 `decode_*` / `construct_*` / 调 `m2/leak/decoder/prior/H1/Lane C/H_inc1/2`；**零 decoder 直至 V57**；原 `V55 90-block` 永久禁用；**I32 仅辅助不能单独归因**；`V55` 与 `V13` 处理点 `200ps legacy_v1 nearest 1024` 单点锚点不改；**严禁改 `src/` 基线，修复仅 V56 wrapper/materializer**。

## 3. Phase 0 — 固化 V56D4 独立 pre-RESULT review（阻塞门）

- **独立 pre-RESULT review**（独立线程/reviewer，不可自审）：复核 `HEAD == origin/formal-ir-mainline == implementation SHA`、`ACCEPTED_PLAN_SHA` 重推导一致且 `rg <stale SHA> 0 hits`、`target run_01` 不存在（本变更无 `run_01`）、预算/门禁/`cycle_state` 与冻结 plan 一致、`py_compile` + 关键测试 PASS，逐项勾选落盘于 `cycle docs`（`REVIEW_CHECKLIST.md` 或 `LOW_DIM_DECOMPOSITION_REPORT.md §0`）。
- **SHA 记录**：`implementation SHA = HEAD`、`execution SHA = N/A (decoder-free)`、`ACCEPTED_PLAN_SHA = V56D4 plan HEAD 176bf34f`（重推导 `git log / cycle_state.yaml`，`rg` 无 stale 命中），写入 `v56d4_low_dim_decomposition.json:provenance`。
- **终态固化**：`per_source CE_U1 13.25/14.84/16.68 CE_U2 13.63/14.96/15.15 acc 0.30-0.46` 主证据、`I_U1 2.05/1.74/1.39 I_U2 2.01/1.69/1.36` 辅助（`V13 I 4.17-4.93` 对比，交叉 `0.77-0.80` 一致）、`first_drop=U1U2_consistency`（`occupancy 256` 正常）、`overall=INCONCLUSIVE_MIXED_SIGNAL`（规则 6 混合不强制二选一）；**I32 仅辅助不能单独归因**显式声明；措辞冻结如 proposal。

## 4. Phase A — 逐函数复放 V13 合同（decoder-free，定位首次分叉）

- **输入**：同一批固定 calibration 帧（如 `8 frames [7,8,9,10,15,16,17,18]` 三源各 `2048` pairs，或其中 `4+4` 子集；三源一致，`frame_ids` 预注册，与 `V55 90` 零重叠）。
- **两路 materializer**（同批 `ttbin` 输入，同 `bin_width 200ps`）：
  ```
  V13-authoritative:  read_ttbin_events(ch 1/5) → compute_cross_correlation_histogram(bin100/max819200/n16384, lag=t_B-t_A) → peak_center/sigma/p2bg → pairing(nearest, threshold 40000ps, direction, wrap_rule) → delay 应用(符号±50ps, 前/后于 pairing/bin 位置) → frame_start/period 204800 floor_div → bin index → legacy_v1 symbol(1024) → F03 5+5 U1/U2
  current-intake:     同链路但按 v55_intake_20260828/sidecars 当前单点 (200ps legacy_v1 nearest) 实现；若 intake 为已落盘 pairs.parquet 则以其生成链路为准，缺失字段记 INCOMPLETE
  ```
  `V13` 侧从 `workspace/v13r3fresh_20260816/sidecars/*/sidecar_meta.json: used_params` + `build_manifest.json` 实时读（不硬编码）；`src/qkd_io/ttbin_pipeline` 为冻结基线只读复用，`V13` 权威实现不重发明。
- **逐阶段比对**（阶段截断即停）：
  ```
  1. raw event/channel selection — counts per channel, other<20%, unique⊇{1,5}
  2. pairing index/Δt — pair indices, Δt histogram/median, paired count
  3. delay 符号及应用位置 — delay_used_ps sign, 应用点 (pre-pairing vs post-bin)
  4. frame-start/period/floor-div — frame_start_ps (peak_center vs global min vs null), period 204800, floor_div, before/after pair index
  5. bin index — (t - t0)/200 floor, bin range 0..1023
  6. 1024 symbol — legacy_v1, symbol 0..1023, alice/bob arrays
  7. U1/U2 — sym>>5 / sym&31, U1/U2 arrays
  ```
  每阶段 `np.array_equal` / `mean_equal` / `Δt median` / `occupancy`，**保存首个不一致阶段及行级样例**（前 5 行 `pair_idx, t_A, t_B, Δt, bin_A, bin_B, sym_A, sym_B, U1_A, U2_A, U1_B, U2_B`），目标**找到第一次产生不同数组的位置**。
- **产出**：`per_stage {stage, V13_val, current_val, delta, array_equal, sample_rows}` + `first_divergent_stage`。

## 5. Phase B — 唯一修复（单点，V13 权威值，wrapper 内）

- **条件**：A 找到唯一代码/合同差异（`first_divergent_stage` 非空且 `array_equal==False` 首次出现）。
- **动作**：**只修复该一处**，**不搜索** `delay/bin_width/mapping/frame anchor` 多候选，不做 `threshold/policy/direction` 网格；**修复值必来自 V13 权威合同**（`sidecar used_params` 实时读或 `ttbin_pipeline` 权威实现只读对照），不手填经验值。
- **位置约束（硬）**：修复必须留在 **V56 wrapper/materializer**（`comparison_bench` 内 `v56_*` 物化层 / `replay/verify` 脚本参数层 / `comparison_bench/outputs_comparison/v56_*` 配置层），**严禁改 `src/` 基线**（`src/qkd_io/ttbin_pipeline.py` 等冻结只读复用，`git diff -- src/ ==0` 可验；`ttbin_pipeline` 仅作权威对照，不作写入目标）。
- **对照**：`old = current` 原实现、`current` = 修复前、`corrected` = 单点修后，三路字节/数组级对照（`old→current diff` 非空，`current→corrected` 在首错阶段后显式分叉，阶段后 `array_equal` 翻转，前阶段仍一致）。
- **守卫**：不改 `prior / H1 / Lane C / H_inc1/2 / decoder` 任何参数（`git diff -- comparison_bench/src/comparison_bench/formal_ir/` 0 改动，`rg "CHANNEL_COUNTS|H1|L1-APP"` 改动 0）；`src/qkd_io` 零改动（本变更不产生 `src/` diff，新 SHA 仅记录 wrapper 改动）。

## 6. Phase C — decoder-free 校准验收（新帧，三源分别，硬门槛）

- **新校准帧**：未进 `V55 90-block`（`set(calibration_new) ∩ set(V55 90×4) ==∅`）也未进 `D4 fit=[7,8,9,10]/val=[15,16,17,18]`（`∩ ==∅`），预注册如每源 `8-16` 帧（例 `1M [0,1,2,3,11,12,13,14] 1p5M 同` `2M 同`，`frame_id∈[0,F-1]` 且 `pairs_per_frame 256` 连续，三源一致，`calibration_new_registry.json` 落盘，`gap≥4` 非必须但报告间距）。
- **timing/routing 合同完整（前置守卫）**：
  - `timing_contract_verified` — 真实重算 `TimeTagger` 环境下 `peak_center/σ/p2bg`（记录 `interpreter_path/TimeTagger版本/输入事件数`，`V13` 同环境同版本），`peak` 健康（`σ 50-150ps` 窄）且 `|peak - delay_used|<50ps` 且 `sign` 一致且 `gate 200ps/threshold 40000ps/frame_start/period 204800` 已显式落盘；缺失时只能 `EVIDENCE_INCOMPLETE`，不得判 `RECOVERED`。
  - `routing` — 指定 `channel 1/5` 存在且非零（`count_A>0 && count_B>0 && unique⊇{1,5}`）且无跨 `channel`/丢列/错误合并（`other<20%` 完整性），比例仅报告（`1M/2M 36.4%` 可能来自探测效率非 routing 错误，R1 修正）。
- **contract_equivalent（硬证据，门 1）**：对新帧同批 `ttbin`，`V13-authoritative` 与 `corrected` 在全部七阶段 `raw/channel → pairing/Δt → delay/位置 → frame-start/period/floor-div → bin → 1024 sym → U1/U2` 均 `np.array_equal PASS`（`per_stage_V13_corrected: {array_equal: true}` 附录对照，任一阶段 `False` 即 `contract_equivalent=False`）。
- **distribution_compatible（硬门槛，门 2，三源分别，不用总体平均）**：对每源 `s∈{1M,1p5M,2M}` 分别需同时满足：
  1. `A==B >60%`：`rate_eq = mean(a==b)` 在新校准 `8-16` 帧 `2048-4096` pairs 上 `>60%`；
  2. `validation accuracy ≥60%`：`fit 4→val 4` 同切分下 `acc_U1 ≥60%` 且 `acc_U2 ≥60%`（`fit` 新帧前 4 学 `P_fit(a|b) 1024→32` 列归一，`val` 后 4 测 `CE_U1/U2 = E[-log2 P_fit]`、`acc_U1/U2 = mean(a==argmax P_fit)`）；
  3. `validation CE 预注册明确上限`：`CE_U1 ≤ min(0.5*CE_current_U1, CE_V13ref_U1+1.0)` 且 `CE_U2 ≤ min(0.5*CE_current_U2, CE_V13ref_U2+1.0)`（`CE_current` 为同切分 `V56D4` 基线 `13-16`，`CE_V13ref` 取该源 `V13` 健康值 `0.19-0.91`，未取到则按 `0.91+1.0=1.91` 守卫；预注册于 `verification_manifest.json`，事后不调。相对当前至少下降 50% 且不高于 V13+1 bits，两条件取严）。
- **NLL / q_mass 仅一致性诊断**：基于 `V25 channel_counts.npz` 的 `P(A|B)` 列归一，`NLL = mean(-log2 P(a|b))` 与 `q_mass_on_p_zero = sum_{N_ab=0} P_emp` 仅报告回落方向（`V55 NLL 28-35 q_mass 57-71%` → 新帧向 `V13 ~0.82/3%` 靠近），不作硬门禁。
- **三源分别通过**：`1M` 且 `1p5M` 且 `2M` 均 `timing/routing` 完整 + `contract_equivalent==True` + `distribution_compatible==True` → `C PASS`；任一源不满足则按 §7 优先级分流（`EVIDENCE_INVALID > MIXED_BY_SOURCE > RECOVERED > DOMAIN_SHIFT > UNRESOLVED`）。

## 7. Phase D — 终态 5 选 1（互斥，按优先级，不主观）

- **硬定义**：`contract_equivalent` = V13 与 corrected 七阶段逐元素一致（§6 门 1）；`distribution_compatible` = 三源分别 `A==B>60%` 且 `acc≥60%` 且 `CE≤min(0.5*CE_current, V13ref+1)`（§6 门 2，预注册上限，不用总体平均）。两者为硬证据/硬门槛，非主观“显著恢复”。

```
# 硬定义：contract_equivalent = V13 与 corrected 七阶段逐元素一致（§6 门 1，硬证据）；distribution_compatible = 三源分别 A==B>60% && acc≥60% && CE≤min(0.5*CE_current, V13ref+1.0) 预注册上限
# 先逐源判定 per_source s: shunt_s = UNRESOLVED_s (contract_equivalent_s==False 或 TTBin 不可用) / RECOVERED_s (contract true && distribution true) / DOMAIN_SHIFT_s (contract true && distribution false)
# 再总体 5 选 1（优先级高→低，互斥，不主观）：
if 完整性/守卫/零重叠/rank/nested 失败 或 provenance 不可追溯 或 fit∩val≠∅ 或 set(new)∩set(90)≠∅ / ∩set(D4 fit/val)≠∅ 或 timing 缺失伪造:
    overall = V56_EVIDENCE_INVALID
    # 证据/切分/零重叠失败，最高优先级
elif per_source 判定不全同类 (例 1M RECOVERED_s / 2M DOMAIN_SHIFT_s / 1p5M UNRESOLVED_s 混排，三源 shunt_s 不一致):
    overall = V56_MIXED_BY_SOURCE
    # 不同源分别落两类，逐源分别报告修复/排查清单；含 contract 或 distribution 的源间异构
elif 三源均 contract_equivalent==True 且 三源均 distribution_compatible==True:
    overall = V56_INPUT_CONTRACT_RECOVERED
    # 七阶段一致且 compatible（硬证据+硬门槛三源分别通过），输入合同可修复性得证，允许另起 V57 走 QUALIFICATION_PLAN_READY + EXECUTE_AUTH 的 decoder TEST
elif 三源均 contract_equivalent==True 且 三源均 distribution_compatible==False:
    overall = V56_TRUE_SESSION_DOMAIN_SHIFT
    # 七阶段一致但统计均匀失败（contract 均一致，distribution 三源均未达硬门槛），真域迁移，需重估 H(U1|B), H(U2|U1,B) 与 m_total，prior 仍 TRAIN-only；NLL/q_mass 仍高为一致性佐证
elif 三源均 contract_equivalent==False 或 V13 侧 INCOMPLETE_TTBin_UNAVAILABLE 均匀无法复放:
    overall = V56_INPUT_CONTRACT_UNRESOLVED
    # 无法重现权威路径或仍有分叉且三源均匀未闭合（任一源分叉但总体均匀；异构分叉已由 MIXED 捕获），修复未闭合
```

- `UNRESOLVED` / `DOMAIN_SHIFT` / `MIXED` 时停留在 `PLAN_CANDIDATE / VERIFICATION_ONLY`，不进入 decoder。
- **仅 `RECOVERED` 才允许 `V57` decoder TEST**（需另起 OpenSpec，冻结新 TEST registry 与 `V57` 方法 `plan HEAD` + `data SHA` + `implementation SHA` 三方绑定，独立 `Pre-EXECUTE` / `Pre-RESULT` 双重 review）。
- 修复必须留在 wrapper/materializer，不改 `src/` 基线（`git diff -- src/ ==0`）。

## 8. 边界与 V57 衔接

- **V55 原 90 永久禁用**：`v55_authoritative_registry.json` 的 `90×4 frames` 已揭盲 `0/90`，禁止任何 `corrected pipeline` 在其上重跑（含 `offset-corrected` 重译）；报告显式声明。
- **同 session 剩余帧 freshness**：同一新 session（`20260123_1M_600k_0dB / 20260107_PPLN_1p5M / 20260123_2M_1p2M_0dB`）的剩余帧（未进 `90` 且未进校验帧）可作 **fresh within-session confirmation**（与校验帧零重叠的新块，如每源再选 `B=8-16` 帧），但因已历 `V55` 多轮诊断（`V56D0-D4` 均读同 session `pairs.parquet`），**不宣称完全独立 cross-session qualification**，报告显式边界声明。
- **真正 qualification 放 V57**：需新采集 session（不同 `acquisition date`，`gap` 天级），走独立 `QUALIFICATION_PLAN_READY / EXECUTE_NOT_AUTHORIZED → IMPLEMENTATION_CANDIDATE → EXECUTE_AUTH → run_01` 完整生命周期，双重 review 后方可 `ARCHIVED`。

## 9. 脚本与报告（decoder-free 守卫）

- **脚本 1 `replay_v13_vs_current.py`** (本变更目录下, decoder-free):
  `python replay_v13_vs_current.py [--ttbin-root ...] [--pairs-root ...] [--v13-sidecars ...] [--frames 7,8,9,10,15,16,17,18] [--out verification_manifest.json]` → 同批固定 calibration 帧，两路 materializer 逐阶段 `array_equal` + 首错样例，`rg "decode_" 0 hits` 仅 `numpy/pandas/pyarrow + ttbin_pipeline(TimeTagger optional)`，`py_compile` PASS；输出 `verification_manifest.json:per_stage` + 控制台摘要；`TimeTagger` 不可用时 `raw/pairing` 记 `INCOMPLETE_TTBin_UNAVAILABLE` 不伪造 `peak`。
- **脚本 2 `verify_corrected_calibration.py`** (本变更目录下, decoder-free):
  `python verify_corrected_calibration.py [--ttbin-root ...] [--corrected-pairs ...] [--v13-sidecars ...] [--new-frames ...] [--counts ...] [--out calibration_verification.json]` → 新校准帧 `timing/routing` + `V13/corrected` 一致 + `A==B>60%` + `validation CE/acc` + `NLL/q_mass` 一致性，`rg "decode_" 0 hits`，`py_compile` PASS；输出 `calibration_verification.json` + 控制台摘要；校验 `set(new)∩set(90)==∅` 且 `∩set(D4 fit/val)==∅`。
- **报告 `RECONSTRUCTION_REPORT.md`**：每源 `A==B/CE/acc/NLL/q_mass` + `pipeline first_drop` + `V13 vs current` + `old/current/corrected` 三路对照 + `C` 新帧验收 + 总体 5 选 1 终态，数据与 `json` 一致，结论不扩大为 `FER/阈值/SKR/晋升`，显式 `V55 90 已揭盲不可复用` + `同 session 剩余帧仅 within-session confirmation` + `真正 qualification 放 V57`。
- **守卫**：重建期 **零 decoder**、原 `90` 已揭盲保护、**不创建 `run_01` decoder 执行**、**不做阈值/方向/frame-start 网格**（`rg "grid" 0 hits`，候选数 `2→3` 仅 old/current/corrected）、**`git diff -- src/ ==0`（修复仅 wrapper）**。

## 10. 与 V56D4 衔接

- V56D4 `INCONCLUSIVE_MIXED_SIGNAL` 已固化，不重跑；本重建在其上以**逐函数复放定位首次分叉**补齐 `pairing/frame` 证据，以**单点 V13 值修复**闭合合同差，以**新帧 decoder-free 验收**证可修复性；`V13 已验证 channel/delay/peak/gate/frame-start/mapping/pairing` 仍为对照（`workspace/v13r3fresh_20260816/sidecars`），不重发明。
- `I32` 仅辅助、CE/acc 主、first_drop 在 `U1U2` 的判定顺序冻结 6 条延续至本变更（见 spec），`V56D4` 的 `fit/val` 预注册与措辞冻结保持。

## 11. 自由裁量 D1-D7

- D1 `I32/CE/acc` 仅 `numpy` 直算，不引 `scipy`（ponytail: `numpy` 已装）
- D2 `fit/val` 固定 `[7,8,9,10]/[15,16,17,18]` 不搜索多划分（仅预注册一种）
- D3 `V13` 合同仅两路→三路对照（old/current/corrected），不扩网格（`grid` 禁止）
- D4 交叉 `I(U1A;U2B)` 仅佐证，不作主分流阈
- D5 流水分段取 `raw/channel/pairing/delay/frame/bin/symbol/U1U2` 七段，不做更细 `sync/occupancy` 网格
- D6 不产生新矩阵/码参数，仅分解与判定，最简闭环
- D7 本变更为 `PLAN_CANDIDATE / VERIFICATION_ONLY`，不产生 `TEST run_01`，`V57` 时才 decoder
