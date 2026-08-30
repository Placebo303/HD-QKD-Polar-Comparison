# OpenSpec Proposal: formal-ir-v65-new-session-channel-compatibility

**Status**: `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED` — 仅产出计划四工件 + decoder-free 就绪/估计 spike，不实现/不执行 decoder，不创建 run_01，不读 TEST 统计，等待独立复审与显式 PLAN_ACCEPT
**Domain**: Formal IR / V65 new-session channel compatibility (V64 唯一后继，V66 decoder TEST 前置门)
**Change ID**: `formal-ir-v65-new-session-channel-compatibility`
**Cycle ID**: `V65` (new-session-channel-compatibility), predecessor `formal-ir-v64-full-symbol-verification-correction` (branch `formal-ir-mainline`, 终态以 `git log` 重核为准)
**Branch**: `formal-ir-mainline`
**HEAD**: `TBD` (实施前以 `git fetch && git rev-parse HEAD == origin/formal-ir-mainline` 40位重核，不一致阻塞；本次推送新 Plan SHA 后停止)
**Data SHA**: `84d62779` (`84d62779603e62de50ded5182ed65b65d3dc6084`, `d=1024 bw=200ps pairing=nearest rule=legacy_v1` 同 V54/V64 单点；V65 引入 **new-session CAL/VAL/TEST** 新鲜域，不复用历史域样本，但处理点单点不变)
**Lifecycle**: `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED` — 本轮止于 plan 四工件 + decoder-free readiness/estimation spike，不改冻结主候选，不调 `H1/Lane C/m2/H_inc/Δ/decoder`，不启动 V66

> ponytail lite: 本变更仅 4 OpenSpec 工件 + 2 decoder-free 脚本 (`v65_data_readiness.py` + `v65_channel_compatibility.py`) + 2 注册表 + 1 报告 + spike 控制台摘要；无 runner、无 decoder、无新矩阵、无新依赖（`numpy/pandas/pyarrow` 已装），最短科学路径。laziest alternative: `numpy` 直算 `C_ab/bincount2d` + 链式熵，不引 `scipy/sklearn`；`λ` 搜索为确定性标量优化，无需 LDPC 依赖。

> **科学问题（冻结）**：冻结主候选 `H1-16 + L1APP + Lane C m2 184/190/192 + Δ8+Δ8 + full-tag (compute_tag_64 canonical 32*U1+U2, 单64-bit)` 在 **新独立 session** 上是否同时满足 1) 输入/materialization 合同与 V64 相同 2) 新 prior 在独立 validation 上稳定泛化 3) `m1≤16 && m2≤200/206/208` 且 TEST 未参与先验/阈值选择 — 全部通过才允许 V66 decoder TEST。

## Goal

以最短 decoder-free 路径完成 **新 session 通道兼容性预冻结**，为 V66 decoder TEST 提供可验证的输入合同、独立先验泛化、与冻结容量一致的速率预算，且满足 **三源独立、G1-8 全过才放行** 的硬门槛：

### 1. 新 session 数据角色冻结（per source 三源分别，不跨 session 拼接，零重叠）

- **每源必备**：`CAL_SESSION` 4096 frames (=1,048,576 pairs≈1M) + `CAL-validation` 512 frames (=131,072 pairs) + `TEST_SESSION` 120 frames (=30,720 pairs)，四帧一块 (`BLOCK=4×256=1024 symbols`)，`CAL || VAL || TEST` 零重叠，可机械校验。
- **零重叠硬约束**（可机械校验，`assert`）：
  ```
  set(CAL_s) ∩ set(VAL_s) == ∅  per source
  set(CAL_s ∪ VAL_s) ∩ set(TEST_s) == ∅  per source
  set(CAL_s ∪ VAL_s ∪ TEST_s) ∩ set(V13 ∪ V48..V64 已用 frame_ids) == ∅  per source
  frame_id ∈ [0, F_s-1], F_s 取决于新 session 原始导出，pairs_per_frame 256 连续
  不允许跨 session 拼接凑数（single session 内连续 Furnace 导出，session provenance 单一）
  ```
  未通过则按终态优先级落 `EVIDENCE_INVALID` 或 `DATA_NOT_READY`，不进入估计。
- **不足两 session 则 DATA_NOT_READY**：若可用的新独立 session 数 `<2`（即无法同时满足 `CAL_SESSION + VAL` 来自 session A 且 `TEST_SESSION` 来自独立 session B，三源各自均需两 session 支撑），则直接 `V65_DATA_NOT_READY` 停止，不伪造，不以旧 `V55/V64 held-out` 代理冒充。单 session 伪 two-session 拼接显式 `EVIDENCE_INVALID`。
- **预注册帧**：每源 `CAL 4096 + VAL 512 + TEST 120` 的 `frame_ids` 确定性冻结，落盘 `v65_data_registry.json` (`per_source {CAL_session_id, VAL_session_id, TEST_session_id, CAL_frames[4096], VAL_frames[512], TEST_frames[120], blocks, pairs, provenance, zero_overlap_verified}`)，禁止事后换帧。

### 2. 输入/materialization 合同与 V64 相同（严格复用 V56 权威链，decoder-free 校验）

- **权威链复用**：严格复用 V56 已验证权威链 `dimension 1024 / bin_width 200ps / pairing nearest / legacy_v1 / channels A1/B5 / delay + peak/sigma/gate/threshold / frame anchor / mapping` 每帧 256 `A=32U1+U2 B=32V1+V2` 的完整物化定义，逐项显式落盘，不手填经验值。
- **三源分别 provenance**：`1M / 1p5M / 2M` 分别记录 `session_id / channel_pair / delay_used_ps / peak_center / sigma / gate / threshold / frame_anchor / mapping / bin_width`，不共享 sidecar，变更需 per-source 显式。
- **偏则 EVIDENCE_INVALID**：任一 `channel/delay/peak/sigma/gate/threshold/frame anchor/mapping` 与 V56 权威值不一致，或 `frame 内 256 对` 非 `A=32U1+U2` / `B=32V1+V2` 物化，或 `provenance` 缺失/伪造，直接 `EVIDENCE_INVALID`，不进入 G2-8。

### 3. 单一预注册 hierarchical 估计器（仅 CAL 训练，λ 仅 Cal 内 4-fold 择优，禁第二 estimator）

- **估计器冻结**：
  ```
  P(a|b) = (C_ab + λ * P_global(a)) / (N_b + λ)    # a,b ∈ [0,1023], Q=1024
  C_ab = bincount2d(a_cal, b_cal)  1024×1024, N_b = Σ_a C_ab
  P_global(a) = Σ_b C_ab / N_cal  (仅 CAL)
  λ ∈ [1e-2, 1e4]  log10 连续搜索，目标 minimize Cal-CV NLL (4-fold Cal 内)
  ```
  `C_ab` 与 `P_global` 仅来自 `CAL (4096 frames)`，`λ` 仅在 `Cal` 内 `4-fold` (按 CAL 4096 frames 切 4 份 1024 frames/份，逐 fold 训练测) 选择，使 `Cal-CV NLL = mean_{folds} NLL_fold` 最小；落在边界 `[1e-2, 1e4]` 则模型不稳定，不扩搜索，直接 `MODEL_NOT_STABLE`。
- **同时生成**：`P(U1|B)` (`32×1024`) 与 `P(U2|U1,B)` (`32×(32*1024)` 或等价 `32×1024×32`) 表，链式 `H(A|B)=H(U1|B)+H(U2|U1,B)` 闭合校验 `|H-H1-H2|<1e-9`，否则 `EVIDENCE_INVALID`。
- **禁第二 estimator**：禁止同时报告 `MLE/Laplace/0.5` 等第二先验作门禁对照；仅 hierarchical 一路为门禁口径，其余仅作 `V57 negative control` 背景不入判定。

### 4. 每源报告（Cal/Val pairs/frames、λ、熵、NLL、MAP、零质量、有效上下文、m1/m2/m_total 相对冻结容量差额，TEST identity 不读统计）

- 每源 `s∈{1M,1p5M,2M}` 报告：
  ```
  样本: Cal pairs/frames (1048576/4096), Val pairs/frames (131072/512), TEST frames 120 (identity only)
  先验: chosen λ, λ_at_boundary(bool), λ_search_trace (log10 λ vs CV NLL)
  熵: H(U1|B), H(U2|U1B), H(A|B)  bits/symbol, 链式闭合差
  泛化: Cal-CV NLL (4-fold mean), Val NLL, ΔNLL = Val - CV, MAP_acc = mean[a==argmax P(a|b)], q_mass_unseen (Val 中 b 未在 Cal 出现比例), effective_contexts = #{b: N_b>0}
  预算: m1_raw = ceil(1.3*1024*H(U1|B)/5), m1_required = min(16, m1_raw) ??? 见下; m2_raw, m2_required, m_total, Δ vs frozen (16/200/206/208, leak diff)
  ```
  **公式冻结** `m_i = ceil(1.3 * 1024 * H_i /5)` **不 cap 伪装**：先算 `m1_raw = ceil(1.3*1024*H(U1|B)/5)`, `m2_raw = ceil(1.3*1024*H(U2|U1B)/5)`，再与冻结容量比较 `m1_required ≤16`, `m2_required ≤200/206/208`；**禁止** `min(1024, ceil(...))` 截断后宣称通过，`m_i_raw` 必须显式报告，截断视为 `RATE_INCOMPATIBLE`。
- **TEST identity 不读统计**：`TEST_SESSION` 仅报告 `session_id / frame_ids[120] / blocks 30 / pairs 30720` identity，不计算 `H/NLL/MAP/q_mass/m` 任何统计，不以任何方式参与 `P(a|b)/λ/阈值` 选择。

### 5. 门禁每源独立 G1-8（全过才整体通过）

| 门 | 检查项 | 阈值 (per source) |
|---|---|---|
| G1 | authority 一致 | `channel/delay/peak/sigma/gate/threshold/anchor/mapping` 与 V56 逐项一致，三源分别 |
| G2 | λ 不触界 | `chosen λ ∈ (1e-2, 1e4)` 开区间，且 `λ` 非边界最优（`argmin` 不在两端 `±ε`） |
| G3 | ΔNLL 受控 | `ΔNLL = Val NLL - Cal-CV NLL ≤ 0.50` bits/symbol |
| G4 | Val NLL 有界 | `Val NLL ≤ H_cal(A|B) + 1.0` bits/symbol 且 `isfinite` |
| G5 | unseen 不超 | `q_mass_unseen = P_val(b ∉ Cal_support) ≤ 1%` (context 未见率) |
| G6 | m1 容量 | `m1_raw ≤16` (与冻结 H1-16 等长) |
| G7 | m2 容量 | `m2_raw ≤ m2_total_frozen` 即 `200 (1M) /206 (1p5M) /208 (2M)` (`H_total_rows = m2+16? V65 用 m_total 200/206/208 直接比较，若 G6 已过则等价`) |
| G8 | provenance 零重叠 | `CAL∩VAL==∅ && CAL∪VAL∩TEST==∅ && CAL∪VAL∪TEST ∩ (V13∪V48..V64)==∅` 且非跨 session 拼接 |

- **三源分别**：每源 `PASS_s = G1..G8 全 True`，任一门 FAIL 则 `PASS_s=False`，不用总体平均。

### 6. 终态按序五选一（优先级高→低，互斥，不主观）

```
if provenance/materialization 失败 或 frame 256 A/B 映射错误 或 跨 session 拼接:
    overall = V65_EVIDENCE_INVALID  # 最高优先级
elif 可用新独立 session 数 <2 或 per source 数据不足 (CAL 4096 / VAL 512 / TEST 120 任一为空):
    overall = V65_DATA_NOT_READY
elif G2 触界 或 ΔNLL>0.5 或 Val NLL 逸出 (G3/G4 失败):
    overall = V65_MODEL_NOT_STABLE  # 先验未稳定，不扩 λ 网格
elif G6/G7 失败 (m1_raw>16 或 m2_raw>200/206/208):
    overall = V65_RATE_INCOMPATIBLE_WITH_FROZEN_CANDIDATE
else:  # G1-8 全过
    overall = V65_CHANNEL_COMPATIBILITY_READY_FOR_V66
```

- **仅第 5 态允许 V66**：`V65_CHANNEL_COMPATIBILITY_READY_FOR_V66` 时，报告显式声明“允许另起 V66 走 `QUALIFICATION_PLAN_READY + Pre-EXECUTE/Pre-RESULT + EXECUTE_AUTH` 的 decoder TEST”；其余 4 态均显式“不允许 decoder TEST”，且 `MODEL_NOT_STABLE` 不得扩 `λ` 网格、`RATE_INCOMPATIBLE` 不得改 `Δ8/Δ16` 矩阵。

### 7. V66 预冻结（本轮仅声明，不执行，不创建输出）

- **V66 已预冻结**：`90 blocks 30/source (4×256 frames/block => 1024 symbols), total leak 1144/1174/1184? 等价 m_total 200/206/208 + tag64 三档 + V64 full-tag`，等待 V65 `READY` 后走独立 `EXECUTE_AUTH`。
- **门禁等比**：`70/90 overall exact_full ≥77.78% 且每源 ≥20/30 (66.67%)`，`undetected_full_tag ==0` 全局，`syndrome_ok && tag_ok_full` 双验证通过，否则非 PASS。
- 本轮不启动 V66，不创建 `.../v66_*/run_01`，不读 TEST 统计。

## Non-Goals

- 不运行任何 `decode_row_layered_fftqspa / construct_*` decoder（`rg "decode_" 0 hits` 在脚本内）；不改 `H1-16 / Lane C m2 184/190/192 / H_inc1/2 Δ8+Δ8 / decoder 90/1.0 poly37 / full-tag canonical / TRAIN prior / 泄漏 1064→1144/1174 1184` 任一冻结量；不试新 `Δm/degree/seed`，不新增矩阵。
- 不读密封 `TEST_SESSION` 的任何 `H/NLL/MAP/熵/分布` 统计；`TEST` 仅 identity 注册，不参与 `P(a|b)/λ/阈值` 选择，违则 `EVIDENCE_INVALID`。
- 不做 `bin_width/dimension/pairing/mapping/frame anchor` 网格搜索（`200ps legacy_v1 nearest 1024` 单点）；`λ` 仅在 `[1e-2,1e4] log10 连续` 优化，不扩网格，触界即 `MODEL_NOT_STABLE`。
- 不宣称 `FER / 阈值 / SKR / 晋升 / 安全证明`；本变更止于 `PLAN_CANDIDATE / DECODER_FREE`，不直接进入 qualification。
- 不改写/覆盖 `V13 / V48–V64` 任何已有输出与终态（只读）；不复用其 `frame_ids`，零重叠已验。
- 不以总体平均替代三源分别判定；不以 `V25 184/190/192` 历史值作新域预算（V65 `H` 另算，仅容量比较）。
- 不用第二 estimator（`MLE/Laplace` 等）作门禁，违则 `EVIDENCE_INVALID`。
- 不创建正式 `.../v65_*/run_01` 或 `.../v66_*/run_01` decoder 执行；`V66` decoder TEST 需另起 `OpenSpec` 与独立 `EXECUTE_AUTH`。

## Scope

1. **冻结主候选零改**：`n=1024, m2 184/190/192, GF32 poly37, H1 16×1024 rank16 80b, L1-APP q via H1 BP (TRAIN channel_counts.npz 仅对照), Lane C ordinal-2, H_inc1/2 Δ8+8 (V54 二阶段), decoder 90/1.0 early-stop, full-symbol tag 64b canonical (V64), TRAIN-only prior (V65 仅重估 H 供 V66预算)` 全只读，**零 decoder 直至 V66**。
2. **预注册数据角色（零重叠，可机械校验，decoder-free）**：每源 `CAL 4096 (1M pairs) + VAL 512 (131k) + TEST 120 (30k)`，`BLOCK 4×256`, `FRAME 256 pairs`，`F_s 取决于新 session 原始导出`，三源 `CAL||VAL||TEST` 零重叠且与 `V13/V48..V64` 均零重叠，不跨 session 拼接，少两 session 则 `DATA_NOT_READY`，禁止事后换帧（`v65_data_registry.json` authoritative）。
3. **输入合同复用（strict V56）**：`dimension 1024 / bin200 / pairing nearest legacy_v1 / channels A1/B5 / delay/peak/sigma/gate/threshold/frame anchor/mapping 每帧256 A=32U1+U2 B=32V1+V2` 三源分别 provenance，`V56 ttbin_pipeline` 权威实现只读对照，不重发明，偏则 `EVIDENCE_INVALID`。
4. **单一 hierarchical 估计（decoder-free，预注册）**：每源 `CAL` 上 `C_ab/P_global → P(a|b)=(C_ab+λ P_global)/(N_b+λ) → H(U1|B), H(U2|U1B), H(A|B) (F03 5+5, U1>>5 &31, 链式 |H-H1-H2|<1e-9) → m1_raw=ceil(1.3*1024*H1/5), m2_raw=ceil(...,H2) (不 cap 伪装，显式 raw vs required)`，`λ` 仅 `Cal 内 4-fold` `log10[-2,4]` 连续搜索最小 `Cal-CV NLL`，触界则 `MODEL_NOT_STABLE`，同时生成 `P(U1|B)/P(U2|U1B)` 表，禁第二 estimator。
5. **门禁 G1-8（per source 独立，预注册阈）**：`G1 authority一致, G2 λ不触界, G3 ΔNLL≤0.5, G4 Val NLL≤H_cal+1.0, G5 unseen≤1%, G6 m1≤16, G7 m2≤200/206/208, G8 provenance零重叠`，三源分别，不用总体平均。
6. **终态五选一（优先级互斥）**：`EVIDENCE_INVALID > DATA_NOT_READY > MODEL_NOT_STABLE > RATE_INCOMPATIBLE_WITH_FROZEN_CANDIDATE > CHANNEL_COMPATIBILITY_READY_FOR_V66`，仅第5态允许 V66（`90 blocks 30/src 180-360, 70/90(77.78%) per 20/30(66.67%) undetected_full 0` 预冻结）。
7. **脚本与报告交付（DECODER_FREE，PLAN_CANDIDATE）**：`v65_data_readiness.py` (G8/零重叠/session 数/不足两 session → DATA_NOT_READY) + `v65_channel_compatibility.py` (hierarchical + G1-7 + 五态) `rg "decode_" 0 hits`, `py_compile PASS`, 输出 `v65_channel_compatibility.json` + `V65_CHANNEL_COMPATIBILITY_REPORT.md` + `v65_data_registry.json` + `v65_manifest.json` + spike 控制台摘要，**未创建 run_01，已推送新 Plan SHA 并停留 PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED，等待独立审核后才允 V66**。

## Impact Scope

- **新增（本变更）**：`openspec/changes/formal-ir-v65-new-session-channel-compatibility/` 下 4 工件 `proposal.md/design.md/tasks.md/specs/spec.md` + 2 decoder-free 脚本 `scripts/v65_data_readiness.py` + `scripts/v65_channel_compatibility.py` (`rg "decode_" 0 hits`, `py_compile PASS`, 严格复用 V56 materialization，仅 `numpy/pandas/pyarrow`) + 2 注册表 `v65_cal_registry.json / v65_data_registry.json` (pre-registered 4096+512+120 frames) + `v65_channel_compatibility.json` (per source H/λ/NLL/MAP/m + overall 五态) + `V65_CHANNEL_COMPATIBILITY_REPORT.md` + `v65_manifest.json` (provenance, HEAD/data SHA, zero_overlap 证明, λ 轨迹) + spike 摘要。
- **只读依赖**：`v55_authoritative_registry.json + v64_fresh_registry.json + V13 sidecars` (V56 权威链对照) + `comparison_bench/outputs_comparison/v55_intake_20260828/pairs` 旧域仅作零重叠校验 + **新 session raw/pairs** (待接入，路径由 `PROJECT_DATA_ROOT` 预留，不硬编码) + `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v25_20260818/run_04/channel_counts.npz` (仅作 TRAIN 对照，不训) + `nonbinary_v25_gate.py` (`P(A|B)/熵定义` 仅参考) + `v38_architecture_triage.py` (Lane C 常量仅背景)。
- **不修改**：任何既有 `spec/代码/测试/输出`（除本目录 + `scripts/` 外）、`V38–V64` 输出、`outputs_comparison/workspace` 以外；**不改 `src/` 基线，不创建 `run_01` decoder 执行，零码参，不启动 V66**。

## Acceptance Criteria

- [ ] `proposal/design/tasks/specs/spec.md` 齐全一致，`lifecycle PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED`，`HEAD TBD→新 Plan SHA` + `branch formal-ir-mainline` + `data SHA 84d62779` 已绑定，显式声明 decoder-free、零 decoder、三源分别、λ 预注册 hierarchical 唯一、前瞻 `V66 90 blocks 30/src 70/90 & 20/30 undetected 0` 已冻结，全部通过才放行 V66。
- [ ] **预注册零重叠可复现（新 session，不跨 session 拼接）**：每源 `CAL 4096 (1048576 pairs) + VAL 512 (131072) + TEST 120 (30720)`，`BLOCK 4×256`, `frame 256`，已 `assert` 三重零重叠（`CAL∩VAL==∅`, `CAL∪VAL∩TEST==∅`, `CAL∪VAL∪TEST ∩ (V13∪V48..V64)==∅`），且 `CAL/VAL` 同一 `CAL_SESSION`、`TEST` 独立 `TEST_SESSION`，不跨 session 拼接已验，少两 session 则 `DATA_NOT_READY` 已验，少两 session 伪拼接则 `EVIDENCE_INVALID`，注册表已落盘，`TEST 仅 identity` 未读统计。
- [ ] **输入合同严格复用 V56 可复现**：每源 `dimension 1024 / bin200 / pairing nearest / legacy_v1 / channels/delay/peak/sigma/gate/threshold/frame anchor/mapping 每帧256 A=32U1+U2 B=32V1+V2` 三源分别 provenance 已显式落盘，与 V56 权威值逐项一致已验，偏则 `EVIDENCE_INVALID` 已验，`git diff -- src/ ==0` 且 `ttbin_pipeline` 只读复用。
- [ ] **单一 hierarchical 估计可复现（预注册 λ 搜索，不扩网格）**：每源 `CAL` 上 `C_ab 1024×1024 → P_global → P(a|b)=(C_ab+λ P_global)/(N_b+λ) → H(U1|B), H(U2|U1B) 校验链式 |H-H1-H2|<1e-9 → m1_raw/m2_raw = ceil(1.3*1024*H_i/5) 不 cap 伪装` 已算，`λ` 仅 `Cal 内 4-fold` `log10[-2,4] 连续` 搜索最小 `CV NLL` 已落盘，`λ_at_boundary` 已标记，触界则 `MODEL_NOT_STABLE` 不扩搜索，同时生成 `P(U1|B)/P(U2|U1B)` 表已验，禁第二 estimator 已验。
- [ ] **每源报告完整（不读 TEST 统计）**：每源 `Cal/Val pairs/frames, chosen λ 是否触界, H(U1|B)/H(U2|U1B)/H(A|B), Cal-CV NLL/Val NLL/ΔNLL, MAP_acc, q_mass_unseen, effective_contexts, m1_raw/m1_required/m2_raw/m2_required/m_total 相对冻结容量 16/200/206/208 差额` 已报告，`TEST 仅 identity 不含统计` 已验，`m_i` 公式 `ceil(1.3*1024*H_i/5)` 未 cap 伪装已验。
- [ ] **门禁 G1-8 逐源判定可复现**：`G1 authority一致, G2 λ不触界, G3 ΔNLL≤0.5, G4 Val NLL≤H_cal+1.0, G5 unseen≤1%, G6 m1≤16, G7 m2≤200/206/208, G8 provenance零重叠` 已逐源判定，三源分别，不用总体平均，`per_source PASS_s` 已落盘。
- [ ] **五态总体判定可复现（优先级正确）**：`overall = EVIDENCE_INVALID > DATA_NOT_READY > MODEL_NOT_STABLE > RATE_INCOMPATIBLE_WITH_FROZEN_CANDIDATE > CHANNEL_COMPATIBILITY_READY_FOR_V66` 先到先得互斥已落盘，且 `G2-4 失败 → MODEL_NOT_STABLE 不扩网格` 已验，`G6-7 失败 → RATE_INCOMPATIBLE 不得改矩阵` 已验，仅第5态允许 V66 已声明，`V66 90 blocks 30/src 70/90 & 20/30 undetected 0` 预冻结已显式。
- [ ] `scripts/v65_data_readiness.py` 与 `scripts/v65_channel_compatibility.py` 为 decoder-free 可运行脚本（`python scripts/v65_*.py [--pairs-root ...] [--out ...]`），`rg "decode_" 0 hits`、`rg "import.*decoder" 0 hits`，仅 `numpy/pandas/pyarrow`，`py_compile` PASS，输出 `v65_channel_compatibility.json + V65_CHANNEL_COMPATIBILITY_REPORT.md + v65_manifest.json + registries` + 控制台摘要，**未创建 run_01，未读 TEST 统计，λ 触界不扩搜索，m_i 不 cap 伪装**。
- [ ] 已推送新 `Plan SHA` 并停留在 `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED`，未创建任何 `.../v65_*/run_01` 或 `.../v66_*/run_01` decoder 执行，不碰 `V48-V64` 块，未启动 V66，**推送后等待独立审核**（`Pre-RESULT` 独立线程复核 `HEAD/ACCEPTED_PLAN_SHA/rg 0 hits/run_01不存在/py_compile+关键测试 PASS/TEST 未读统计/λ 预注册不调/m_i raw 显式`），返回 `Plan SHA / implementation SHA / readiness|estimation spike 结果 / per-source G1-8 / 五态终态` 等待 `PLAN_ACCEPT`。

## Tasks

见 `tasks.md`（Phase A 数据就绪预注册与零重叠；Phase B 合同复用 strict V56；Phase C hierarchical 唯一估计与 λ 搜索；Phase D 熵/m 报告与 TEST identity 隔离；Phase E G1-8 门禁；Phase F 五态判定与 V66 预冻结；Phase G 脚本与报告交付至 PLAN_CANDIDATE 推送新 SHA；显示禁止清单与 decoder-free 守卫）。

## Lifecycle

`V64` 当前 `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`（`V64 full-symbol verification correction 24-block` 已收缩，仅 plan）；`V65` 本验证 `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED`（仅 decoder-free 新 session 兼容性预冻结，不实现 runner，不执行 decoder，不创建 `run_01`，不改主候选/V64/src，三源分别；`TEST` 密封仅 identity）；`V65_CHANNEL_COMPATIBILITY_READY_FOR_V66` 后**另起 successor `V66`** 冻全新 `TEST 90 blocks (30/source, 30×4=120 frames/source)`（与 `CAL 4096+VAL512` 及 `TEST_SESSION 120` 预留及 `V48-V64` 均零重叠，未揭盲）再走 `QUALIFICATION_PLAN_READY + Pre-EXECUTE/Pre-RESULT 双重 review + EXECUTE_AUTH` 的 `decoder TEST 90 blocks (70/90 overall & 20/30 per source & undetected_full 0)` 完整生命周期，双重 review 后方可 `ARCHIVED`；`V65` 本身不直接进入 qualification；`V65_DATA_NOT_READY / EVIDENCE_INVALID / MODEL_NOT_STABLE / RATE_INCOMPATIBLE` 则停留修数据或检查先验/速率，不进入 `V66`。
