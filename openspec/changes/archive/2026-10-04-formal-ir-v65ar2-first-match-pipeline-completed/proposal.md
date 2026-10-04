# OpenSpec Proposal: formal-ir-v65ar2-first-match-pipeline

**Status**: `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED` — 本变更仅产出计划四工件 + decoder-free 脚本框架，零 decoder 调用，不创建 run_01，不运行真实流水线，推送新 implementation SHA 后等待独立复审与显式 PLAN_ACCEPT
**Domain**: Formal IR / V65AR2 first-match stop-on-failure pipeline (V65 `9625afb4` 的后继修订，合并 decoder-free metadata recovery Phase R + Stage0 + Stage1 + Stage2)
**Change ID**: `formal-ir-v65ar2-first-match-pipeline`
**Cycle ID**: `V65AR2` (first-match-pipeline), predecessor `formal-ir-v65-new-session-channel-compatibility` `V65` (`9625afb4` `PLAN_REVISE_REQUIRED`, `84d62779` 单点延续)
**Branch**: `formal-ir-mainline`
**HEAD**: `9625afb4... (V65 revise base)` → 新 implementation SHA (实施前 `git fetch && git rev-parse HEAD == origin/formal-ir-mainline` 40位重核，不一致阻塞；本次推送新 SHA 后停止，不自行进入 EXECUTE)
**Data SHA**: `84d62779` (`d=1024 bw=200ps pairing=nearest rule=legacy_v1` 单点延续；V65AR2 仅新增 Phase R additive sidecar 重建，不换处理点)
**Lifecycle**: `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED` — 合并流水线冻结为确定性定序，先返回 SHA，不跑真实数据

> ponytail lite: 本变更仅 4 OpenSpec 工件 + 1 decoder-free 流水线脚本框架 (`scripts/v65ar2_pipeline.py` 分相 R/0/1/2) + 2 注册表/清单 + 1 报告模板；无 runner、无 decoder、无新矩阵、无新依赖（`numpy/pandas/pyarrow` 已装）。laziest alternative: `numpy` 直算 `C_ab/bincount2d` + 链式 CE，不引 `scipy/sklearn`；候选顺序冻结不做自适应搜索。

> **科学问题（冻结）**：在**完全冻结候选顺序与 provenance tier** 下，以 **decoder-free** 方式重建可信输入并按 **first-match / stop-on-failure** 定序验证：`Phase R` 自候选自身 raw TTBin 与 acquisition routing contract 重建 additive sidecar → `Stage0 4+4` 首个 PASS 即 selected → `Stage1 256/64` 稳定性 → `Stage2 1024/256 + seal TEST32`；任一步 FAIL 立即停止，后续不可达；`Stage1/2` 速率 `ceil(1.3*1024*CE_i/5)` 不 cap 判 `RATE_ADAPTATION_REQUIRED / FULL_DISCLOSURE_LAYER`，不作候选失败混淆；`Stage2 TEST` 仅 identity 不参与估计。

## Goal

以最短 decoder-free 路径将四阶段合并为**确定性 first-match / stop-on-failure 流水线**，满足：

### 1. 候选与 provenance 冻结（不按统计换候选）
- **候选顺序冻结**：`162148 → 2500K → 160254` 严格定序，first-match 语义，禁止按 Stage0/CE/统计结果动态重排、跳序、回退。
- **Provenance tier 冻结**：`A / B / C` 三档 tier 按 acquisition routing contract 显式绑定候选，不按阶段统计提升/降级 tier，不跨 tier 共享 sidecar。
- **判定语义**：`selected = 首个 Stage0 PASS 的候选`；若三候选 Stage0 全 FAIL 则流水线整体 `NO_CANDIDATE_SELECTED`，不以 CE 最优“亚军”递补。

### 2. Phase R — decoder-free metadata recovery（仅 additive sidecar 重建）
- **输入唯一来源**：仅从**候选自身 raw TTBin** 与 **acquisition routing contract** 重建，不复用冲突 sidecar、不改 raw、不搜 channel pair、不运行 decoder。
- **Additive 语义**：重建产物为 **additive sidecar**（`sidecar_additive.json` / `provenance_additive.json`），仅补充缺失 `delay/peak/sigma/gate/threshold/frame_anchor/mapping` provenance，不覆盖已验证 raw 数据，不合并不可信旧 sidecar 字段。
- **禁令**：`SHALL NOT` 复用冲突 sidecar、修改 raw TTBin、搜索/猜测 channel pair、调用任何 `decode_*`。违则 `EVIDENCE_INVALID`。
- **门禁**：Phase R PASS 才允许进入 Stage0；Phase R FAIL 则流水线 `STOP at R`，Stage0/1/2 不可达。

### 3. 确定性流水线（first-match / stop-on-failure）
```
Phase R PASS ──▶ Stage0 4+4 (per candidate 定序) ──▶ 首个 PASS → selected
                                                      │
                                                      ▼
                                              Stage1 256/64 (仅 selected)
                                                      │ PASS
                                                      ▼
                                              Stage2 1024/256 + seal TEST32 (仅 selected)
                                                      │
                                    任一步 FAIL ──▶ 立即 STOP，后续 phase 不可达
```
- **Stage0 4+4**：每候选 `4 + 4` 块（`BLOCK=4×256=1024 symbols`，共 8 blocks = 32 frames = 8192 pairs）的小样本快速门禁；三候选按冻结顺序逐一判定，首个 PASS 即锁定 selected，后续候选不再评估 Stage0。
- **Stage1 256/64 稳定**：仅对 selected 候选执行 `CAL 256 frames (65536 pairs) + VAL 64 frames (16384 pairs)` 的先验稳定性验证，`λ` 与 `CE` 均独立于 Stage0 重算。
- **Stage2 1024/256 + seal TEST32**：仅对 selected 且 Stage1 PASS 的候选执行 `CAL 1024 frames (262144 pairs) + VAL 256 frames (65536 pairs)` 主估计，`TEST32 32 frames (8192 pairs)` 仅 seal identity 不参与任何估计/阈值选择。
- **Stop-on-failure**：任一 phase FAIL 立即停止，该 candidate 的后续 phase 与流水线后续阶段标记 `UNREACHABLE`，不继续、不回退、不换候选重跑（除非 overall 显式 `NO_CANDIDATE_SELECTED` 终态）。

### 4. Stage1/2 速率自适应语义（不 cap，显式分层）
- **Required rate 公式冻结（不 cap 伪装）**：
  ```
  CE1 = -E_VAL log P_λ*(U1|B)   (VAL 上)
  CE2 = -E_VAL log P_λ*(U2|U1,B)
  m1_req = ceil(1.3 * 1024 * CE1 / 5)
  m2_req = ceil(1.3 * 1024 * CE2 / 5)
  # 5 = log2 Q (Q=32 per plane), 1.3 = f_target, 1024 = n
  # 不经 min(16,..) / min(192,..) / min(1024,..) 截断，显式报告 raw
  ```
  - 若 `m1_req ≤16 && m2_req ≤184/190/192`（按 source 三档旧容量）→ `WITHIN_FROZEN_BUDGET`
  - 若 `16 < m*_req <1024` 或 `192 < m2_req <1024` 且至少一层超旧容量但每层 `<1024` → `RATE_ADAPTATION_REQUIRED`（需增量冗余/母码重构，非候选失败）
  - 若任一层 `≥1024` → `FULL_DISCLOSURE_LAYER`（该层信息论上需全披露，当前码族不可行）
  - 以上均**不作候选失败**混淆，仅作速率终态分支；候选失败仅由 G 门禁定义。
- **Stage2 TEST 身份隔离**：`TEST32` 仅报告 `session_id / frame_ids[32] / blocks 8 / pairs 8192` identity，不计算 `H/CE/NLL/MAP/q_mass/m`，不以任何方式参与 `P(a|b)/λ/阈值` 选择，违则 `EVIDENCE_INVALID`。

### 5. 产出四工件与脚本框架（DECODER_FREE，先返回 SHA）
- **四工件**：`proposal.md / design.md / tasks.md / specs/spec.md` 齐全一致，`lifecycle PLAN_CANDIDATE / DECODER_FREE`。
- **脚本框架**：`scripts/v65ar2_pipeline.py`（分 `phase_r / stage0 / stage1 / stage2` 函数，`--candidate-order 162148,2500K,160254 --provenance-tier A,B,C --phase R,0,1,2` CLI），`rg "decode_" 0 hits`，`py_compile PASS`，仅 `numpy/pandas/pyarrow`。
- **先返回 SHA**：推送新 implementation SHA 后**不自行运行**真实流水线（不读真实 raw TTBin、不建 `run_01`），等待独立 `Pre-RESULT` 复审与 `PLAN_ACCEPT` 后才允许受控 dry-run / fresh 估计。

## Non-Goals

- 不运行任何 `decode_row_layered_fftqspa / construct_* / ldpc.*` decoder（`rg "decode_" 0 hits` 在脚本内）；不调 `H1-16 / Lane C m2 / H_inc / decoder 90/1.0 poly37 / full-tag` 任一冻结码参，不新增矩阵/度分布/seed。
- 不复用冲突 sidecar、不改 raw TTBin、不搜 channel pair、不做 `bin_width/dimension/pairing/mapping/frame_anchor` 网格搜索；`λ` 仅 `[1e-2,1e4] log10 连续` 优化，不扩网格。
- 不以 Stage0/Stage1/Stage2 的 CE/H 统计动态重排候选顺序；不以总体平均替代三源分别判定。
- 不读密封 `TEST32` 的任何 `H/CE/NLL/MAP` 统计；`TEST` 仅 identity。
- 不宣称 `FER / 阈值 / SKR / 晋升 / 安全证明`；本变更止于 `PLAN_CANDIDATE / DECODER_FREE`，不直接进入 qualification。
- 不改写/覆盖 `V13 / V48–V65` 已有输出与终态（只读零重叠校验）；不创建正式 `.../v65ar2_*/run_01` decoder 执行。
- 不启动真实流水线执行；推送 SHA 后等待独立审核。

## Scope

1. **冻结候选与 tier 零改**：顺序 `162148→2500K→160254` 与 `A/B/C` tier 完全冻结，first-match 语义，三候选按序逐一 Stage0 判定，首 PASS 锁定，不按统计换序。
2. **Phase R additive sidecar 重建（decoder-free）**：每候选仅自其 `raw TTBin + acquisition routing contract` 重建 additive sidecar，输出 `v65ar2_phase_r.json` + `sidecar_additive.json`，禁复用冲突 sidecar/改 raw/搜 channel pair/调 decoder。
3. **Stage0 4+4 first-match 门禁**：每候选 `4+4 blocks` 小样本门禁，含 `λ 4-fold CV [1e-2,1e4] → CE1/CE2 → m1/m2(CE) + ΔNLL/unseen/VAL NLL + G1-8(含 G7-aux)`，首 PASS 即 selected，其余候选 Stage0 终止。
4. **Stage1 256/64 稳定性**：仅 selected 候选，`CAL 256 + VAL 64` 独立重算 `C_ab/P_global → λ → H_cal描述性 + CE1/CE2/CE_full门禁链式 → m_req + 泛化统计 → G1-8`，PASS 才进 Stage2。
5. **Stage2 1024/256 + seal TEST32**：仅 selected 且 Stage1 PASS，`CAL 1024 + VAL 256` 主估计，同上链路，`TEST32` 仅 seal identity（`v65ar2_test_registry.json`），不参与估计，速率 `ceil(1.3*1024*CE_i/5)` 不 cap 显式 `RATE_ADAPTATION_REQUIRED / FULL_DISCLOSURE_LAYER` 分支。
6. **Stop-on-failure 终态机**：`EVIDENCE_INVALID > PHASE_R_FAIL > STAGE0_NO_CANDIDATE > STAGE1_FAIL > STAGE2_FAIL > RATE_ADAPTATION_REQUIRED / FULL_DISCLOSURE_LAYER / READY` 优先级互斥，任一步 FAIL 后续标记 `UNREACHABLE`。
7. **脚本与报告交付（DECODER_FREE）**：`scripts/v65ar2_pipeline.py` 分相可 CLI 单独 dry-run，`py_compile PASS` `rg "decode_" 0 hits`，输出 `v65ar2_manifest.json + v65ar2_pipeline_report.md + v65ar2_data_registry.json` + 控制台摘要，已推送新 SHA 未建 run_01。

## Impact Scope

- **新增（本变更）**：`openspec/changes/formal-ir-v65ar2-first-match-pipeline/` 下 4 工件 `proposal.md/design.md/tasks.md/specs/spec.md` + 1 decoder-free 流水线脚本框架 `scripts/v65ar2_pipeline.py` (`rg "decode_" 0 hits`, `py_compile PASS`, 仅 `numpy/pandas/pyarrow`) + 注册表 `v65ar2_data_registry.json / v65ar2_test_registry.json` (pre-registered Stage0 4+4 / Stage1 256/64 / Stage2 1024/256+TEST32) + `v65ar2_pipeline_result.json` (per candidate Phase R/Stage0 + selected Stage1/2, CE/m_req, G1-8, overall 五态+) + `V65AR2_PIPELINE_REPORT.md` + `v65ar2_manifest.json` (provenance, HEAD/data SHA, zero_overlap 证明, λ 轨迹, CE 链式, rate_adaptation 分支) + spike 控制台摘要。
- **只读依赖**：`formal-ir-v65-new-session-channel-compatibility` 四工件与 `v65_data_registry.json` 零重叠校验 + `v55_authoritative_registry.json + v64_fresh_registry.json (80c35647...) + V13 sidecars` 含 session provenance + `comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v25_20260818/run_04/channel_counts.npz` (仅 TRAIN 对照) + **候选 raw TTBin** (`162148 / 2500K / 160254` 三候选，各自 raw 目录) + **acquisition routing contract** (`acquisition_routing.yaml` 含 `source→session→channel_pair→delay_sign` 契约)。
- **不修改**：任何既有 `spec/代码/测试/输出`（除本目录 + `scripts/` 外）、`V38–V65` 输出、`outputs_comparison/workspace` 以外；**不改 `src/` 基线，不创建 `run_01` decoder 执行，零码参，不启动 V66**。

## Acceptance Criteria

- [ ] `proposal/design/tasks/specs/spec.md` 齐全一致，`lifecycle PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED`，`HEAD 9625afb4...→新 SHA` + `branch formal-ir-mainline` + `data SHA 84d62779` + `predecessor V65` 已绑定，显式声明 decoder-free、零 decoder、候选顺序 `162148→2500K→160254` 与 `A/B/C tier` 冻结 first-match、不按统计换候选、Phase R additive、Stage0 4+4 首 PASS、Stage1 256/64、Stage2 1024/256+TEST32、stop-on-failure、速率不 cap 分支、TEST 仅 identity。
- [ ] **候选与 tier 冻结可复现**：`candidate_order = [162148, 2500K, 160254]` 显式冻结于 `v65ar2_manifest.json:candidate_order`，`provenance_tier ∈ {A,B,C}` per candidate 冻结，脚本 CLI `--candidate-order` 默认即此序，`rg "sort.*CE|rank.*candidate" 0 hits`（无按统计重排逻辑）。
- [ ] **Phase R additive 重建可复现（decoder-free）**：每候选仅 `raw TTBin + acquisition routing contract` 重建 `sidecar_additive.json`，`rg "decode_" 0 hits` 且 `rg "search.*channel|reuse.*sidecar" 0 hits` 为冲突复用/搜 pair，`raw TTBin` 未改（`git diff -- raw` 无改动且 hash 对照），`provenance_additive` 含 `session_id / channel_pair(A1/B5) / delay_used_ps / peak_center / sigma / gate / threshold / frame_anchor / mapping / contract_hash`，Phase R FAIL 则 Stage0/1/2 标记 `UNREACHABLE` 已验。
- [ ] **流水线定序可复现（first-match / stop-on-failure）**：`Stage0 4+4` 按冻结顺序逐候选判定，`selected = 首个 PASS` 已落盘；`Stage1 256/64` 仅 selected 可达，`Stage2 1024/256+TEST32` 仅 Stage1 PASS 可达；任一步 FAIL 后续标记 `UNREACHABLE` 且 `overall` 按优先级落盘，已验 `selected` 不以 CE 最优递补。
- [ ] **速率公式可复现（不 cap）**：`m_i_req = ceil(1.3*1024*CE_i/5)` 显式未 cap 已验（`grep "min(16" 0 hits` 且 `m_req_raw` 落盘），`m_i_req <1024` 超旧容量 → `RATE_ADAPTATION_REQUIRED`，`m_i_req ≥1024` → `FULL_DISCLOSURE_LAYER`，二者均不作候选失败，仅速率分支；`TEST32` 未参与估计已验 `used_test_in_estimation==False`。
- [ ] **每相报告完整（TEST 隔离）**：每候选 Phase R + Stage0 报告 `pairs/frames, λ/λ_at_boundary, CE1/CE2/CE_full + chain_delta, CV NLL/Val NLL/ΔNLL, MAP/unseen/effective, m1/m2/m_req vs 16/184-192/200-224 + rate_branch`，selected 另 Stage1/2 同模板，`TEST32` 仅附录 `session_id/frames[32]/blocks 8/pairs 8192` identity，不含统计已验。
- [ ] **门禁与终态可复现**：`G1-8(含 G7-aux)` per candidate per stage 已判定，三源分别；`overall` 按 `EVIDENCE_INVALID > PHASE_R_FAIL > STAGE0_NO_CANDIDATE > STAGE1_FAIL > STAGE2_FAIL > RATE_ADAPTATION_REQUIRED / FULL_DISCLOSURE_LAYER / READY` 先到先得互斥已落盘，且 `MODEL_NOT_STABLE` 不扩网格已验。
- [ ] `scripts/v65ar2_pipeline.py` 为 decoder-free 框架（`python scripts/v65ar2_pipeline.py --phase R|0|1|2 --candidate ... [--dry-run]`），`rg "decode_" 0 hits`、`rg "import.*decoder" 0 hits`，仅 `numpy/pandas/pyarrow`，`py_compile` PASS，输出 `v65ar2_pipeline_result.json + V65AR2_PIPELINE_REPORT.md + v65ar2_manifest.json + registries` + 控制台摘要，**未创建 run_01，未运行真实流水线，λ 触界不扩，m_req 不 cap，TEST 未读**。
- [ ] 已推送新 implementation SHA 并停留在 `PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED`，未创建任何 `.../v65ar2_*/run_01` 或 `.../v66_*/run_01` decoder 执行，不碰 `V48-V65` 块，推送后等待独立审核，返回 `Plan SHA / implementation SHA / 流水线框架 spike 摘要 / per-phase G1-8 / overall 终态` 等待 `PLAN_ACCEPT`。

## Tasks

见 `tasks.md`（Phase R additive 重建；Stage0 4+4 first-match；Stage1 256/64；Stage2 1024/256+TEST32 速率分支；流水线 stop-on-failure 终态机；脚本框架与报告交付至 PLAN_CANDIDATE 推送新 SHA；decoder-free 守卫）。

## Lifecycle

`V65 9625afb4 PLAN_REVISE_REQUIRED` → `V65AR2 PLAN_CANDIDATE / DECODER_FREE / EXECUTE_NOT_AUTHORIZED`（仅流水线冻结，不实现 runner，不执行 decoder，不创建 `run_01`，不改主候选/V64/src，三阶段 first-match 定序，TEST 密封仅 identity，`CE` 为 VAL 上分层交叉熵门禁，`m_req` 不 cap）；`READY` 后**另起 successor** 复用已验证 pipeline 再走 `QUALIFICATION_PLAN_READY + Pre-EXECUTE/Pre-RESULT + EXECUTE_AUTH` 的 decoder TEST 完整生命周期，双重 review 后方可 `ARCHIVED`；`V65AR2` 本身不直接进入 qualification；其余终态停留在 `PLAN_CANDIDATE` 修数据或先验/速率分支。
