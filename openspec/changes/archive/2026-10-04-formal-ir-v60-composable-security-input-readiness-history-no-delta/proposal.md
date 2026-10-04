# OpenSpec Proposal: formal-ir-v60-composable-security-input-readiness

**Status**: `PLAN_CANDIDATE / DECODE_FORBIDDEN` — composable secret-key 权威输入就绪度判定，不运行 decoder，不产生 `run_01`
**Domain**: Formal IR / V60 composable-security-input-readiness (V59 唯一后继)
**Change ID**: `formal-ir-v60-composable-security-input-readiness`
**Cycle ID**: `V60P0` (composable-security-input-readiness), predecessor `V59` `formal-ir-v59-security-budget-authority-closure`
**Branch**: `formal-ir-mainline`
**HEAD**: `910d921b` (起点，实施前以 `git fetch && git rev-parse HEAD == origin/formal-ir-mainline` 重核为准；不一致则阻塞；本次推送新 SHA)
**Data SHA**: `84d62779` (`84d62779603e62de50ded5182ed65b65d3dc6084`, `d=1024 bw=200ps pairing=nearest rule=legacy_v1` 同 V57/V58/V59，不改)
**Lifecycle**: `PLAN_CANDIDATE / DECODE_FORBIDDEN` — 仅只读数据/记录就绪度审查，不实现 runner，不执行 decoder，不改 `H1/Lane C/H_inc1/2/Δ8+8/decoder 90/1.0/poly37/V57 m`，不产生 `V61`，不把 `IAB/Shannon H/MAP/visibility shadow` 当 `H_min`
**Method frozen**: `V57 m1 981/1024/1024, m2 424/451/516`、`V59 leak 7089/7439/7764 bits/block (n=1024, GF32 log2q=5, tag64 L2-only 已含)` 完全冻结仅作预算输入；`H1 16×1024 / Lane C / H_inc1/2 / Δ8+8 / decoder 90/1.0 poly37 / estimator` 全冻零改

> ponytail lite: 本变更仅 4 OpenSpec 工件 + 1 只读就绪度脚本 + 4 研究产出 (JSON/CSV/报告/清单)；无 decoder、无矩阵、无新依赖（`numpy/pandas/pyarrow` 已装），最短科学路径。laziest alternative: 若仓内无 composable 定理或决定性 PE 数据则直接落盘 `V60_DATA_NOT_READY / V60_PARTIAL / EVIDENCE_INVALID` 并输出最小新增测量清单与 `hmin_break_even` floor，不自创 `H_min` 或有限尺寸网格，不以 shadow 填 null。

> **研究方向保持**：`V59` 已以 `AUTHORITY_INPUTS_ACTIONABLE` 闭合泄漏口径（`leak=5*m_total+64` 双校验、`tag` 不重复、`m_total=m1+m2`），但 `H_min/proxy` 仍为 `shadow/null`；`V60` 仅判定现有数据/记录能否提供 **composable secret-key 权威输入**（逐源 `H_min lower + finite`），若可则在 `READY` 上才算 `ell = 1024*hmin_lower - leak_IR - leak_other - finite`，否则精确列出需新采集参数，禁 proxy 填充。

## Goal

以最短 decoder-free 路径完成 **composable secret-key 权威输入的数据就绪度终态裁决**，在完全冻结 `n=1024, leak 7089/7439/7764 (tag64 已含)` 下：

1. **Phase A 数据就绪逐项寻找验证（10 项只读，不自创，proxy 显式标记）**：逐项定位、逐项验证、逐项落盘 `authority = composable | shadow | proxy | missing` 与 `readiness = ready | partial | missing | invalid`，10 项为：`phase-error / conjugate basis`、`n_PE (PE sample size)`、`visibility 区间与来源`、`eps_sec / eps_cor`、`finite-size authority (DeltaFK / n_eff)`、`EV bound (error-verification)`、`auth leakage`、`post-selection / accepted-frame`、`composable theorem 及假设`、`单位 per-frame/block 换算`。每项记录 `symbol / meaning / unit / source(file:line:expr or data_path:provenance) / authority / readiness / minimal_new_measurement`；禁把 `IAB / Shannon H / MAP_acc / visibility shadow` 当 `H_min`（违规则 `EVIDENCE_INVALID`）。
2. **Phase B 先做 readiness 终态（仅就绪度，不先算密钥）**：按 `first-match` 互斥落盘四终态 `V60_SECURITY_INPUTS_READY` / `V60_PARTIAL` / `V60_DATA_NOT_READY` / `V60_EVIDENCE_INVALID`；**仅 `READY` 才允许计算** `ell = 1024*hmin_lower - leak_IR - leak_other - finite`（单位全 `bits/block`，`hmin_lower` 为 `bits/symbol`），其余三态 `ell` 保持 `null` 不以 floor 冒充 composable 余量；每源 `hmin_break_even` 阈值（`floor / 5% / 10% margin`）必给作门限参考，但 `READY` 外不得升为密钥正余量主张。
3. **阈值逐源机械对比（三源独立，禁平均）**：每源 `hmin_break_even_floor = leak_total/1024`（optimistic `other=0 finite=0`）`1M 6.9238 / 1p5M 7.2637 / 2M 7.5820 bits/symbol` 与 `10% margin 7.6931 / 8.0707 / 8.4245 bits/symbol`（`5% 7.2882/7.6460/7.9811`）为校准锚点；`READY` 时才以真实 `hmin_lower` 比阈值判定 `ell>0`，其余态仅作阈值描述。
4. **停止条件与最小产出**：**缺 composable theorem 或决定性 PE 数据时立即停** `PARTIAL / DATA_NOT_READY`，禁 shadow 补 `null`，禁 `decoder / V61`，输出最小 `authority/readiness JSON + CSV + 报告 + 清单` 四工件并推送新 SHA，停留 `PLAN_CANDIDATE / DECODE_FORBIDDEN` 等待独立审核。

### 冻结 V57/V59 披露（每 block 1024 符号，64-bit tag 已含不得重复扣除，仅输入）

| source | m1 | m2 | m_total | leak_total (=5*m_total+64) bits/block | leak_without_tag | tag |
|---|---|---|---|---|---|---|
| 1M | 981 | 424 | 1405 | 7089 | 7025 | 64 |
| 1p5M | 1024 | 451 | 1475 | 7439 | 7375 | 64 |
| 2M | 1024 | 516 | 1540 | 7764 | 7700 | 64 |

- `n=1024 symbols/block`, `log2 q =5 (GF32)`, `tag=64 L2-only` 仅 `total` 计一次；脚本校验 `leak_total ==5*m_total+64` 且 `m_total==m1+m2`；`bits/symbol *1024 = bits/block`。
- `H1 16×1024 / Lane C / H_inc1/2 / Δ8+8 / decoder 90/1.0 poly37 / estimator` 全冻，不改不跑；`IAB / Shannon H(A|B) / MAP_acc / visibility shadow` 禁当 `H_min` 且禁当 `H_min^epsilon(A|E)` 下界。

### 工作阶段（decoder-free，全冻）

**Phase A 数据就绪逐项验证（只读，禁止自创，proxy 不升级，missing→null）**：仓库内 `rg "phase.error|conjugate|n_PE|visibility|eps_sec|eps_cor|DeltaFK|finite.size|EV |error.verification|auth |authentication|post.selection|accepted.frame|composable|Renner|Niu|Tomamichel" + rag/data 索引` 逐项追踪 10 项权威来源（代码/论文记录/数据仓），明确 `bits/block vs bits/symbol vs bits/pair` 单位，记录 `authority/readiness/minimal_new_measurement`。

**Phase B 就绪度终态先行（first-match 四选一，仅 READY 算 ell）**：按优先级 `EVIDENCE_INVALID > DATA_NOT_READY > PARTIAL > SECURITY_INPUTS_READY` 互斥裁决；仅 `READY`（10 项中 `composable theorem + decisive PE + H_min lower + finite authority + eps/EV/auth/post_sel 单位` 均 `ready` 且 `composable` 声明明确）才计算 `ell =1024*hmin_lower - leak_IR - leak_other - finite` 并逐源比 `floor / 5% / 10%` 阈值，其余态 `ell=null` 仅输出阈值锚点与缺口清单。

**停止与产出**：缺 `composable theorem` 或 `decisive PE (phase-error/n_PE/visibility权威区间)` 任何其一即停 `PARTIAL/DATA_NOT_READY`，禁 shadow 补 `null`，禁 `decoder/V61`，落盘 `v60_composable_security_readiness.json + V60_COMPOSABLE_SECURITY_INPUT_READINESS_REPORT.md + v60_break_even_readiness.csv + v60_minimal_new_measurement_checklist.csv` 四工件，普通推送新 SHA，停留 `PLAN_CANDIDATE / DECODE_FORBIDDEN`。

## Non-Goals

- 不运行任何 `decode_* / construct_* / 信道估计器`（`rg "decode_" 0 hits`, `rg "import.*decoder" 0 hits`）；不改 `H1 16×1024 / Lane C / H_inc1/2 / Δ8+8 / decoder 90/1.0 poly37 / estimator / V57 m1/m2` 任一冻结量；不新增矩阵；不进入 `V61`。
- 不改写/覆盖 V57/V59 三新 session 已接受 `m1/m2/leak`（仅只读输入）；不改 `V25` `184/190/192` 历史值；不改 `src//experiments//tools/` 与 `V54-V59` 既有输出与终态（`git diff -- src/ ==0 && git diff -- experiments/ ==0 && git diff -- tools/ ==0 && git diff -- openspec/changes/formal-ir-v5[4-9]/ ==0`）。
- 不自创 `H_min / finite-key / composable` 公式；缺权威输入不造 `eps_sec/eps_cor/visibility/phase-error` 参数；不把 `IAB / H(A|B) / H_shannon / MAP_acc / visibility shadow` 当 `H_min`（违规则 `EVIDENCE_INVALID`）；不把 `shadow` 升级为 `composable`，`missing/null` 不填 0。
- 不在非 `READY` 上计算或宣称 `ell>0 / SKR / FER / 阈值晋升`；`floor / shadow` 阈值仅作门限描述，不冒充 composable 余量。
- 不创建正式 `run_01` decoder 执行；不宣称 `FER / SKR`；不做 `bin_width/dimension/pairing/frame anchor` 或 `eps` 网格搜索；`hmin / finite` 仅用仓内权威或 `null`，无则 `DATA_NOT_READY`。
- 不以 `optimistic floor` 冒充 `composable` 正余量；不把 `shadow descriptive` 区间升级为 `composable-authority`；不以总体平均替代三源分别判定。
- 不改 `src//experiments//tools/` 基线代码。

## Scope

1. **冻结输入零改**：`n=1024, GF32 log2q=5, tag=64, V57/V59 m1/m2/leak 7089/7439/7764` 三源冻结，`data SHA 84d62779` 同 V57-V59，`pairing nearest legacy_v1` 单点，仅只读；`leak_total ==5*m_total+64` 双校验；`H1/L2/Δ8/decoder/estimator` 全冻。
2. **Phase A 10 项逐项就绪度验证（只读，禁止自创）**：仓库内 `rg` + 数据仓 `inventory / registry / channel_counts` 定位权威，逐项记录 `{item, symbol, meaning, unit, source(file:line:expr or data_path:provenance), authority(composable/shadow/proxy/missing), readiness(ready/partial/missing/invalid), decoder_free?(yes/no/partial), minimal_new_measurement}`，10 项至少覆盖：`phase-error / conjugate`（`e_ph` 率、共轭基统计）、`n_PE`（PE 样本大小）、`visibility 区间与来源`（`[vis_low,vis_high]` 实测链）、`eps_sec / eps_cor`、`finite-size authority`（`DeltaFK / n_eff` 公式与 `eps` 预算）、`EV bound`（`epsilon_EC` 验证界）、`auth leakage`（认证开销）、`post-selection / accepted-frame`（`accepted_frame_fraction`）、`composable theorem 及假设`（Renner/Niu/Tomamichel 等定理声明、假设、适用域）、`单位 per-frame/block 换算`（`bits/block` vs `bits/symbol` vs `bits/pair` vs `bits/pair`×`n`）；明确 `H_min^epsilon(A|E)` 是否被**明确声明为下界**，`IAB/Shannon H/MAP/visibility shadow` 一律标 `proxy` 且禁当 `H_min`，未声明则 `missing`，`proxy 不升级`。
3. **Phase B 就绪度终态裁决（first-match 四互斥，仅 READY 算 ell）**：按优先级 `EVIDENCE_INVALID (单位/tag/m/proxy 自洽 fail) > V60_DATA_NOT_READY (缺 composable theorem 或决定性 PE 数据) > V60_PARTIAL (部分项 ready 但不足 composable) > V60_SECURITY_INPUTS_READY (10 项中关键项均 ready 且 composable 明确)` 互斥落盘；仅 `READY` 允许计算 `ell_s = 1024*hmin_lower_s - leak_IR_s - leak_other_s - finite_s`（`hmin_lower` 单位 `bits/symbol` 下界，三源独立），与阈值比 `floor 6.9238/7.2637/7.5820`、`10% margin 7.6931/8.0707/8.4245`（`5% 7.2882/7.6460/7.9811`）逐源判定 `ell>0`；非 `READY` 时 `ell_* = null` 且 `composable:null` 不填 0，`shadow` 仅描述不升级。
4. **阈值与分解表（三源独立，tag 不重复）**：冻结 `ell =1024*hmin_lower - leak_IR - leak_other - finite` 分解（`leak_IR=leak_total` 已含 `tag`，`leak_other=PE+EV+auth+...`, `finite=DeltaFK+...`），输出 `decomposition table` 三源独立与 `break_even readiness` 表（`source, leak_total, floor, margin_5%, margin_10%, hmin_lower_authority, ell_or_null, gate`），`log2 d=10` 上界校验，不平均。
5. **停止条件与最小清单**：缺 `composable theorem`（无明确 composable 定理声明或假设链断裂）或 `decisive PE`（缺 `phase-error/conjugate` 实测或 `n_PE/visibility` 权威区间）任一即停 `PARTIAL/DATA_NOT_READY`，**禁 shadow 补 null**（`null` 保持 `null`），**禁 decoder/V61**（`rg 0 hits`），输出最小 `authority/readiness JSON + CSV + 报告 + 清单` 四工件，清单按优先级列 `minimal_new_measurement`（采样数、校准链、定理适用域验证）。
6. **脚本与报告交付（DECODE_FORBIDDEN）**：`scripts/v60_composable_security_input_readiness.py`（decoder-free, `rg "decode_" 0 hits`, `py_compile PASS`）输出 `docs/research_cycles/V60P0/v60_composable_security_readiness.json`（`readiness_10items + formula_authority + decomposition + break_even + verdict`）+ `V60_COMPOSABLE_SECURITY_INPUT_READINESS_REPORT.md`（权威裁决、10 项表、分解表、阈值表、最小行动清单、终态声明）+ `v60_break_even_readiness.csv` + `v60_minimal_new_measurement_checklist.csv`，未创建 `run_01`，已推送新 SHA 并停留 `PLAN_CANDIDATE / DECODE_FORBIDDEN`，等待独立审核。

## Impact Scope

- **新增（本变更最小）**：`openspec/changes/formal-ir-v60-composable-security-input-readiness/` 下 4 工件 `proposal.md/design.md/tasks.md/specs/spec.md` + decoder-free 脚本 `scripts/v60_composable_security_input_readiness.py` (`rg "decode_" 0 hits`, `py_compile PASS`, 只读就绪度审查) + 报告 `docs/research_cycles/V60P0/V60_COMPOSABLE_SECURITY_INPUT_READINESS_REPORT.md` + `v60_composable_security_readiness.json` (10项 readiness + authority + decomposition + break_even + verdict) + 紧凑CSV `v60_break_even_readiness.csv` + 清单 `v60_minimal_new_measurement_checklist.csv`。
- **只读依赖**：`openspec/changes/formal-ir-v57-channel-recharacterization/v57_channel_recharacterization.json` / `openspec/changes/formal-ir-v59-security-budget-authority-closure/v59_secret_key_budget_authority.json`（V57 m / V59 leak），`tools/security_reports/_security_calibrated_common.py` / `build_actual_ir_finite_key_shadow.py` / `build_beta_baseline_finite_key_shadow.py` / `round2_build_finite_key_audit_table.py` / `round2_build_actual_ir_finite_key_shadow.py` / `round3_build_proof_gap_matrix.py`（权威公式与缺口，仅参考不改），`comparison_bench/outputs_comparison/v57* + v55_intake_20260828`（数据盘点，仅校验单位/来源，不跑 decoder），`docs/SECURITY_MODEL.md / docs/decision-log.md`（协议模型，仅参考）。
- **不修改**：任何既有 `spec/代码/测试/输出`（除本目录 + `scripts/` + `docs/research_cycles/V60P0/` 外）、`V38–V59` 输出、`src//experiments//tools/`（`git diff -- src/ ==0` 等），**不改 `V57-V59 m/leak`，不创建 `run_01` decoder 执行，不进入 `V61`，零码参**。

## Acceptance Criteria

- [ ] `proposal/design/tasks/specs/spec.md` 齐全一致，`lifecycle PLAN_CANDIDATE / DECODE_FORBIDDEN`，`HEAD 910d921b` + `branch formal-ir-mainline` + `data SHA 84d62779` 已绑定，显式声明 decoder-free、零 decoder、三源分别、tag 不重复、仅权威公式、缺 composable theorem 或决定性 PE 则 `PARTIAL/DATA_NOT_READY` 停止、`shadow` 不补 `null`、`IAB/H/MAP/visibility` 禁当 `H_min`。
- [ ] **Phase A 10项就绪度可复现**：`tools/security_reports` + 数据仓逐项记录已落盘 `readiness_10items[{item,symbol,meaning,unit,source(file:line:expr or data_path),authority(composable/shadow/proxy/missing),readiness(ready/partial/missing/invalid),decoder_free?,minimal_new_measurement}]`，至少覆盖 `phase-error/conjugate、n_PE、visibility区间与来源、eps_sec/cor、finite-size authority、EV bound、auth leakage、post-selection/accepted-frame、composable theorem及假设、单位换算`，明确 `H_min^epsilon(A|E)` 是否被**明确声明为下界**（未声明则 `missing`），`IAB/H/MAP/visibility shadow` 禁当 `H_min` 已验，`H/L2/Δ8/decoder` 零改已验。
- [ ] **Phase B 四终态互斥可复现**：`overall` 按 `EVIDENCE_INVALID > V60_DATA_NOT_READY(缺composable定理或决定性PE) > V60_PARTIAL(部分ready不足composable) > V60_SECURITY_INPUTS_READY(关键项均ready)` first-match 已落盘，`proxy_missing` 保持 `missing/null`，`shadow` 不升级为 `composable`，`missing` 不填 0，禁 `decoder/V61` 已验，**仅 `READY` 计算 `ell =1024*hmin_lower - leak_IR - leak_other - finite`，其余态 `ell=null`**。
- [ ] **阈值与分解可复现**：逐源 `hmin_break_even_floor = leak/1024 = 6.9238/7.2637/7.5820 bits/symbol`（`other=0 finite=0`）已算并与 `leak` 锚点双校验；`5% 7.2882/7.6460/7.9811`、`10% 7.6931/8.0707/8.4245` 已算 `h_m = (leak+other+finite)/(1024*(1-margin))`；`log2 d=10` 上界校验，三源独立不平均；`leak_total ==5*m_total+64` 双校验，`GF32 5bits` 显式，`tag` 不重复。
- [ ] **停止条件与最小清单可复现**：缺 `composable theorem` 或 `decisive PE` 时 `PARTIAL/DATA_NOT_READY` 已正确停止，未以 `shadow` 填 `null`，`decoder/V61` 零触发已验；最小 `authority/readiness JSON + CSV(每源threshold) + 报告 + 清单(按优先级新增测量)` 已落盘且数据一致。
- [ ] `scripts/v60_composable_security_input_readiness.py` 为 decoder-free 可运行脚本（`python scripts/v60_composable_security_input_readiness.py [--v57-json ...] [--v59-json ...] [--out-json ...]`），`rg "decode_" 0 hits`、`rg "import.*decoder" 0 hits`，仅 `numpy/pandas`（可选 `pyarrow`），`py_compile` PASS，未创建 `run_01`，且 `V57-V59 m/leak` 未改（`git diff -- src/ ==0` 且 `git diff -- openspec/changes/formal-ir-v5[4-9]/ ==0`）。
- [ ] `docs/research_cycles/V60P0/V60_COMPOSABLE_SECURITY_INPUT_READINESS_REPORT.md` 已记录 10项权威裁决（`phase-error/conjugate、n_PE、visibility区间/来源、eps、finite、EV、auth、post-sel、composable定理假设、单位`）、`readiness` 表、分源 `decomposition`、`break-even` 阈值与 `ell`（仅 READY）、最小新增测量行动表、`overall` 终态与就绪度声明，数据与 `json` 一致，结论不扩大为 `FER/阈值/SKR/晋升`，显式 `V57-V59 m/leak 冻结` + `tag 已含不重复` + `三源分别不平均` + `proxy 不升级` + `missing→null` + `仅READY算ell`。
- [ ] 已推送新 `SHA` 并停留在 `PLAN_CANDIDATE / DECODE_FORBIDDEN`，未创建任何 `run_01` decoder 执行，不碰 `src//experiments//tools/` 与 `V54-V59` 既有变更，`git diff -- src/ ==0` 且 `rg "decode_" 0 hits`，`py_compile + 关键测试` PASS，推送后等待独立审核；返回 `Plan SHA / implementation SHA / 10项 readiness / 三源阈值 / 最小清单 / 终态`，**不自动进入 `V61`**。

## Tasks

见 `tasks.md`（Phase A 10项逐项权威裁决与 `H_min` 下界追踪；Phase B 四终态就绪度判定与阈值；停止条件与最小清单；脚本与校验与推送）。

## Lifecycle

`V59` 当前 `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN`（`HEAD 910d921b` 前，`m1 981/1024/1024, m2 424/451/516, leak 7089/7439/7764, n1024, tag64` 已固化，`AUTHORITY_INPUTS_ACTIONABLE` 仅闭合泄漏口径，未提供 composable `H_min`）；`V60` 本就绪度审查 `PLAN_CANDIDATE / DECODE_FORBIDDEN`（仅 decoder-free 就绪度判定，不实现 runner，不执行 decoder，不创建 `run_01`，不改码参，三源分别；floor 必给、仅 READY 算 ell、`composable:null` 不自填）；`V60` 仅 `V60_SECURITY_INPUTS_READY` 才允许另起后继密钥计算，否则停 `PARTIAL/DATA_NOT_READY` 精确输出最小新增测量；`V60` 推送后不自动进入 `V61`，需新 `OpenSpec` 与独立授权。
