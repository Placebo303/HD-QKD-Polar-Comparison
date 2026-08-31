# OpenSpec Proposal: formal-ir-v65a-alternative-typeii-working-point-scout

**Status**: `PLAN_CANDIDATE / IMPLEMENTATION_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED` — 四工件、decoder-free scout 与 focused tests 已完成；未运行真实 Stage0/Stage1，不实现 decoder，不创建 run_01，不读旧 outcome
**Domain**: Formal IR / V65A alternative Type-II working-point scout (V65 前置，V65 DATA_NOT_READY 保持不变)
**Change ID**: `formal-ir-v65a-alternative-typeii-working-point-scout`
**Cycle ID**: `V65A` (alternative-typeii-working-point-scout), predecessor `formal-ir-v65-new-session-channel-compatibility` (DATA_NOT_READY 保持，不修改其三源 qualification 语义)
**Branch**: `formal-ir-mainline`
**HEAD**: `TBD Plan SHA` (推送前 `git fetch && git rev-parse HEAD == origin/formal-ir-mainline` 重核)
**Data SHA**: `84d62779` (d=1024 bw=200ps pairing=nearest rule=legacy_v1 单点，V65A 复用同一处理点，仅换候选 session，不换处理点)
**Lifecycle**: `PLAN_CANDIDATE → IMPLEMENTATION_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED` — 本轮止于四工件、decoder-free scout 脚本、focused tests 与推送；不运行真实 Stage0/Stage1 或 decoder

> ponytail lite: 本变更仅 4 OpenSpec 工件 + 1 decoder-free scout 脚本 (`v65a_scout.py`) + 1 注册表 + 1 报告 + 控制台摘要；无 decoder、无矩阵、无新依赖（`numpy/pandas/pyarrow` 已装）。laziest alternative: `numpy` 直算 `C_ab` + 链式熵，不引 `scipy/sklearn`。

## Goal

为 **Type-II 工作点**在 V65 三源 qualification 保持 `DATA_NOT_READY` 不动的前提下，提供一条**仅 decoder-free** 的备用工作点勘探路径，按**固定顺序**逐一检查三候选 session（1:`2026-01-13 162148` → 2:`2026-01-07 2500K` → 3:`2026-01-07 160254`），每候选先用 **4+4 帧**做 materialization/provenance 最小物化验证（dimension 1024 / bin200 / nearest / legacy_v1 / 候选自带 channels / 候选自带 delay / peak / sigma / gate / threshold / frame anchor 等逐项显式，`sign(delay)==sign(peak) && |delay-peak|<50ps && sigma∈[50,150] && gate==200 && threshold==40000`），**首个通过即停止**，绝不批量物化三候选。首选通过后再做 **256/64 粗筛**（粗筛只能淘汰不能 READY），通过后才规划 **1024/256 正式重表征**并密封 **32 TEST frames**。全程**不得批量物化、不得运行 decoder、不得读取旧结果文件**，保持 `DECODE_FREE` 至推送。

### Provenance tier（候选均为 provisional）

历史使用不再一律排除：

- **Tier A**：未影响当前 V36–V64 NB-LDPC 的 prior、矩阵、标签、码率、门禁或解释；仅在完成外部使用账本核对后，才可作为未来独立 TEST。
- **Tier B**：早期用于 Polar、Cascade 或无关分析，但没有影响当前 NB-LDPC；可作 development/generalization，不能直接作为独立 TEST。
- **Tier C**：参与 V36–V64 当前 NB-LDPC 决策；只可作回归/机制检查。

只读仓库盘点未发现三候选进入 V36–V64 NB-LDPC 注册表，因此三者暂列 **B-provisional**，不是最终 Tier A 结论。`162148` 的本地 PIESKR 元数据还指向外部 `D:\SPDC源测试`，该 provenance 冲突在 Stage0 未闭合前必须阻断；若后续账本发现任一候选影响 V36–V64，则改列 Tier C。

### 固定顺序与停止规则

```
candidates_ordered = ["2026-01-13 162148", "2026-01-07 2500K", "2026-01-07 160254"]  # 固定，不可重排
for idx, cand in enumerate(candidates_ordered):
    materialize_exactly 4+4 frames (8 frames == 2048 pairs) for cand only
    verify materialization/provenance (G-verify, 见 §3)
    if PASS: selected = cand; break  # 首个通过即停，不再物化后续候选
    else: continue to next cand (不保留失败候选的中间物化产物作后续用)
if none PASS: overall = V65A_NO_CANDIDATE_PASSED_VERIFICATION
```

### 阶段递进

```
Stage 0: 4+4 verification per candidate (sequential, stop-on-first-PASS, 8 frames only)
  → Stage 1: 256/64 coarse screen on selected only (coarse can REJECT, cannot READY)
    → Stage 2: 1024/256 formal re-characterization + seal 32 TEST frames (planned, 本轮仅 freeze 计划，不在本轮密封后读统计)
```

- **V65 不动**：`formal-ir-v65-new-session-channel-compatibility` 的 `proposal/design/tasks/specs/v65_frozen_session_binding.json` 保持 `DATA_NOT_READY`，不修改其三源 qualification 语义（`CAL 4096+VAL512+TEST120 per source` 门禁仍以 V65 原绑定为准）。V65A 为独立 `alternative` 勘探，不覆盖、不复用 V65 的 outcome 作先验/阈值。
- **Batch 禁止**：`8 frames/candidate` 逐候选物化，禁止一次性物化三候选全部帧或预加载三候选 `pairs.parquet` 全量；优先复用候选本地已有 pairs/sidecar，raw TTBin 仅在当前候选合同闭合后按需读取。脚本内 `assert materialized_frames_total <= 8 + (selected? 256+64 :0) + (formal? 1024+256+32 :0)` 可机械校验（本轮 Stage 2 仅规划，实物化上限为 `8 + 320 =328 frames` 若 Stage1 执行）。
- **Decoder-free**：`rg "decode_" 0 hits` 且 `rg "import.*decoder" 0 hits` 在 scout 脚本内；`py_compile PASS`；不创建 `run_01`。
- **旧结果禁读**：不得读取 `comparison_bench/outputs_comparison/**/v6*` `run_01` 的性能、门禁或安全结果作候选排序或阈值调整；候选顺序由本 proposal 冻结，不以历史性能重排。

## Non-Goals

- 不修改原 V65 的 `DATA_NOT_READY` 终态与三源 `CAL 4096+VAL512+TEST120` qualification 语义；不复用、不覆盖、不 reinterpret V65 绑定/注册表。
- 不运行任何 `decode_row_layered_fftqspa / construct_* / sample_uniform_gf32` decoder；`DECODE_FREE` 全程保持。
- 不批量物化三候选（禁止 `3×全量 pairs.parquet` 预加载）；不以 `8` 帧以外批量统计挑候选。
- 不读取旧结果（`V48..V65` 的 `FER/阈值/门禁结果`）作本次排序/阈值依据；V65A 候选顺序固定与历史无关。
- 不以粗筛 `256/64` 宣称 `READY`；粗筛仅具淘汰权，`READY` 必须经 `1024/256` 正式重表征后（本轮仅规划，正式执行需新 `PLAN_ACCEPT`）。
- 不宣称 `FER / 阈值 / SKR / 晋升 / 安全证明`；本变更止于 `PLAN_CANDIDATE / DECODER_FREE`。
- 不改 `src/ experiments/ tools/` 基线；`ttbin_pipeline` 仅只读复用。
- 不做 `bin_width/dimension/pairing/mapping` 网格搜索（`200ps legacy_v1 nearest 1024` 单点）；不新增矩阵/码参。

## Scope

1. **候选冻结**：三候选按固定顺序 `2026-01-13 162148` → `2026-01-07 2500K` → `2026-01-07 160254`，逐一检查，首个通过即停。顺序与数量冻结，不以数据可用性重排。
2. **4+4 最小验证（每候选，sequential）**：每候选仅物化 `4+4 frames = 8 frames = 2048 pairs`，验证 `dimension 1024 / bin200 / pairing nearest double-pointer bin//1024 / rule legacy_v1 / channels(cand-specific) / delay_used_ps vs peak_center sign+50ps / sigma 50-150 / gate 200 / threshold 40000 / frame anchor period 204800 floor_div / mapping legacy_v1 A=32U1+U2 B=32V1+V2 每帧256` 逐项显式落盘，三源改为**单候选单 session**（候选即单源单 session，不跨源），`provenance` 完整且 `frame 256` 校验通过才 `VERIFY_PASS`，否则 `VERIFY_FAIL` 进入下一候选。
3. **256/64 粗筛（selected only，淘汰权）**：对 Stage0 选中的首个 `VERIFY_PASS` 候选，独立物化 `256 frames CAL (65536 pairs) + 64 frames VAL (16384 pairs)`，做 `hierarchical P(a|b)=(C_ab+λ P_global)/(N_b+λ)` 的 `λ` 仅 `Cal 内 2-fold 或 4-fold` 粗筛（域 `[1e-2,1e4]` log10），校验 `λ不触界、ΔNLL、unseen、m(CE)` 等但**阈放宽或仅作淘汰**，粗筛 `FAIL → REJECT` 停止，不进入 Stage2；粗筛 `PASS → 仅允许进入 Stage2 规划`，绝不宣称 `READY`。
4. **1024/256 正式重表征 + 32 TEST 密封（planned，本轮仅规划）**：对粗筛通过的候选，规划 `1024 frames CAL (262144 pairs) + 256 frames VAL (65536 pairs)` 正式重表征（与 V65 同 hierarchical 估计器，`λ` `Cal 内 4-fold` `[1e-2,1e4]` 连续，`CE1/CE2/CE_full` VAL 门禁 `m=ceil(1.3*1024*CE/5)`，链式闭合 `|CE_full-CE1-CE2|<1e-9`），并密封 `32 TEST frames (8192 pairs)` 仅 identity（不读统计），注册表落盘 `v65a_registry.json`。本轮**仅 freeze 计划**，不执行正式重表征全量计算至 `READY`（执行需新 `PLAN_ACCEPT`，可复用同一脚本带 `--stage formal`）。
5. **V65 隔离**：`openspec/changes/formal-ir-v65-new-session-channel-compatibility/**` 零修改；V65A 产物独立目录 `formal-ir-v65a-alternative-typeii-working-point-scout/`；`v65_frozen_session_binding.json` 不动。
6. **脚本与报告（DECODE_FREE）**：`scripts/v65a_scout.py` 单脚本分 `--stage verify|coarse|formal|all`，`rg decode 0 hits`，`py_compile PASS`，输出 `v65a_scout.json + V65A_SCOUT_REPORT.md + v65a_registry.json + v65a_manifest.json` + 控制台摘要；本轮至推送，不创建 `run_01`。

## Impact Scope

- **新增（本变更）**：`openspec/changes/formal-ir-v65a-alternative-typeii-working-point-scout/` 下 4 工件 `proposal.md/design.md/tasks.md/specs/spec.md` + `scripts/v65a_scout.py` (decoder-free, `rg decode 0 hits`) + `v65a_registry.json` (候选顺序、Stage0 8帧验证、Stage1 256/64 粗筛、Stage2 1024/256规划+32 TEST密封) + `v65a_scout.json` + `V65A_SCOUT_REPORT.md` + `v65a_manifest.json` (provenance, HEAD/data SHA, materialization 逐项, λ轨迹, CE链式, 物化帧计数守卫) + 控制台摘要。
- **只读依赖**：`src.reconciliation.run_nbldpc_demo_point._read_ttbin_timetags/_bin_indices_sorted_for_binwidth/_pairs_from_sorted_bins` + `legacy_v1` mapping 的 V56 权威算法只读复用；`PROJECT_DATA_ROOT` 下三候选真实相对路径（`2026.1.13/SHG_Type2PPLN_3s_2_2026-01-13_162148/`、`2026.1.7/Type2PPLN_2500K_3s_2026-01-07_174324.1.ttbin`、`2026.1.7/Type2PPLN_3s_2026-01-07_160254.1.ttbin`，路径由 manifest 记录，不硬编码旧 Windows 路径）；`V13 sidecars` 仅作 `dimension/bin/period` 算法对照，不读 outcome。
- **不修改**：`formal-ir-v65-new-session-channel-compatibility/**` 零改动；任何 `src/ experiments/ tools/ openspec/specs/` 已有 spec；`comparison_bench/outputs_comparison/**` 既有输出；不创建 `run_01` decoder 执行。

## Acceptance Criteria

> Implementation boundary: this candidate contains the decoder-free scout and
> focused fake/fixture tests only. No real candidate Stage0/Stage1 run or
> scout output is claimed or committed in this turn.

- [ ] `proposal/design/tasks/specs/spec.md` 齐全一致，`lifecycle DRAFT→PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED`，`HEAD TBD→新 Plan SHA` + `data SHA 84d62779` + `predecessor V65 DATA_NOT_READY` 已绑定，显式声明 **固定三候选顺序 162148→2500K→160254、首个通过即停、4+4验证、256/64粗筛仅淘汰、1024/256正式+32 TEST密封规划、V65不动、DECODE_FREE、禁批量物化、禁旧 outcome**。
- [ ] **固定顺序首个通过即停可复现**：`candidates_ordered` 三候选按 `["2026-01-13 162148","2026-01-07 2500K","2026-01-07 160254"]` 冻结，脚本按序逐一 `materialize_exactly 8 frames (4+4)`，`materialized_candidates_count <=1 + (selected?1:0)` 且 `materialized_frames_total` 在 Stage0 阶段 `<=8×checked_candidates`（首个 PASS 时 `==8×(index+1)`），`selected` 为首个 `VERIFY_PASS`，后续候选未物化；顺序/首停由 focused tests 覆盖。
- [ ] **4+4 materialization/provenance 逐项可复现**：脚本对每候选 8 帧显式验证 `dimension 1024 / bin_width 200ps / pairing nearest double-pointer bin//1024 / rule legacy_v1 / candidate-specific channels / delay_used_ps / peak_center / sigma / gate / threshold / frame anchor / mapping legacy_v1 / 每帧256 A=32U1+U2 B=32V1+V2`，且 `sign(delay)==sign(peak) && |delay-peak|<50ps && sigma∈[50,150]`；缺失/偏离或 provenance 冲突则 `VERIFY_FAIL`。本轮仅以 fixture 测试覆盖路径，未生成真实三候选明细。
- [ ] **禁批量物化/禁 decoder/禁旧 outcome 已验**：`v65a_manifest.json: guards {batch_materialization==false, decode_rg_0_hits==true, old_outcome_not_read==true, materialized_frames_total, materialized_candidates_count}` 均 `true`，`rg "decode_" 0 hits` 且 `rg "old_outcome|outcome\\.json" 0 hits` 在脚本内，`py_compile PASS`，`git diff -- src/ ==0`。
- [ ] **256/64 粗筛仅淘汰已验**：脚本对 selected 候选的 `256 CAL +64 VAL` 粗筛报告 `λ_at_boundary / ΔNLL / Val NLL / unseen / effective_contexts / CE1/CE2/CE_full chain_delta / m1/m2(CE) ceil`，粗筛 `FAIL → overall=REJECT` 不进入 Stage2，粗筛 `PASS → overall=ELIGIBLE_FOR_FORMAL` 绝不为 `READY`，`coarse_cannot_ready` 由 fixture 测试覆盖；本轮未运行真实 Stage1。
- [ ] **1024/256 正式重表征 + 32 TEST 密封已规划（本轮仅规划）**：`v65a_registry.json` 含 `formal_plan {CAL 1024(262144)/VAL 256(65536)/TEST 32(8192) frames, hierarchical λ [1e-2,1e4] Cal内4-fold, CE门禁 m=ceil(1.3*1024*CE/5), chain |CE_full-CE1-CE2|<1e-9, TEST仅identity}` 与 `sealed TEST identity` 占位，正式执行需新 `PLAN_ACCEPT`，本轮不读 TEST 统计已验 (`used_test_in_estimation==false`)。
- [ ] **V65 不动已验**：`git diff -- openspec/changes/formal-ir-v65-new-session-channel-compatibility/ ==0`，`V65 v65_frozen_session_binding.json` 未改，`V65 overall` 仍 `DATA_NOT_READY`，V65A 结论不 reinterpret V65。
- [ ] `scripts/v65a_scout.py` 为 decoder-free 可运行脚本（`python scripts/v65a_scout.py [--stage verify|coarse|formal|all] [--candidate-root ...] [--out ...]`），`py_compile PASS`，输出 `v65a_scout.json + V65A_SCOUT_REPORT.md + v65a_registry.json + v65a_manifest.json` + 控制台摘要，未创建 `run_01`，未读 TEST 统计，`λ触界不扩`，`m_i CE-based 不 cap`，已推送新 Plan SHA 并停留 `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED`，等待独立审核与显式 `PLAN_ACCEPT` 后才允正式重表征执行。

## Tasks

见 `tasks.md`（Phase A 固定顺序与 4+4 最小验证；Phase B 256/64 粗筛仅淘汰；Phase C 1024/256 正式重表征与 32 TEST 密封规划；Phase D 脚本与报告交付至推送）。

## Lifecycle

`V65` 保持 `DATA_NOT_READY`（三源 `4096+512+120` qualification 不动）；`V65A` 本轮 `PLAN_CANDIDATE→IMPLEMENTATION_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED`（仅 decoder-free 勘探，已实现 scout 与 focused tests，但未运行真实 Stage0/Stage1 或 decoder，不创建 `run_01`，不读旧 outcome，首个通过即停）；`V65A` 正式 `1024/256` 执行需独立 `PLAN_ACCEPT`（`Pre-RESULT` 独立线程复核 `HEAD/ACCEPTED_PLAN_SHA/rg 0 hits/run_01不存在/py_compile+TEST未读/批量物化守卫/固定顺序`），双重 review 后方可进入 `FORMAL_READY`；`V65` 本身不因 V65A 改变终态。
