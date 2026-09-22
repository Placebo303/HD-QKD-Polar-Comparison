# OpenSpec Proposal: formal-ir-v61-security-measurement-specification

**Status**: `PLAN_CANDIDATE / DECODE_FORBIDDEN / MEASUREMENT_SPEC_ONLY` — 仅定义“新实验需要记录什么”，不运行 decoder，不产生 `run_01`，不创建数值型 `V62`
**Domain**: Formal IR / V61 security-measurement-specification (V60 唯一后继, 不进入数值计算)
**Change ID**: `formal-ir-v61-security-measurement-specification`
**Cycle ID**: `V61P0` (security-measurement-specification), predecessor `V60` `formal-ir-v60-composable-security-input-readiness` 已固化 `9f1fb02c` + V61 起点 `7b476f62368a410722ab1e0d65ea2709e423d848` (起点以 `git fetch && git rev-parse HEAD == origin/formal-ir-mainline == 7b476f62368a410722ab1e0d65ea2709e423d848` 重核为准；不一致阻塞；本次推送新 Plan SHA)
**Branch**: `formal-ir-mainline`
**HEAD**: `7b476f62368a410722ab1e0d65ea2709e423d848` (V61 当前修订起点，完整 40 位；实施前重核，不一致则阻塞；本次修订普通推送新 Plan SHA 后停止于 `PLAN_CANDIDATE / DECODE_FORBIDDEN`)
**Data SHA**: `84d62779` (`84d62779603e62de50ded5182ed65b65d3dc6084`, `d=1024 bw=200ps pairing=nearest rule=legacy_v1` 同 V57/V58/V59/V60，不改；新采集数据另起新 `data_sha`，本变更仅定义如何记录绑定)
**Lifecycle**: `PLAN_CANDIDATE / DECODE_FORBIDDEN` — 仅产出最小采集规范与验收公式，不实现 runner，不执行 decoder，不改 `H1/Lane C/H_inc1/2/Δ8+8/decoder 90/1.0/poly37/V57 m1/m2/leak`，不重跑 `V55`，不用旧数据伪造缺失 `PE`，在无新安全测量数据时禁止创建数值型 `V62`
**R61 增量**: `R61-01 dependency-aware readiness`（`required_core / required_if_theorem_applicable / not_applicable_with_theorem_reason / missing` 四类，与定理无关的 `visibility/decoy` 允许 `N/A` 不阻塞 `V62_OPEN`）+ `R61-02 verification 口径冻结`（`leak_IR 已含 tag64`，`leak_other = max(0,actual_verification_bits-64)`，`epsilon_EV/EC` 为概率未映射不得入 `leak_other/finite`，新增 `tag64-only / extra-verification / epsilon-not-bits` 三边界测试）

> ponytail lite: 本变更仅 4 OpenSpec 工件 + 1 采集清单 CSV/JSON Schema + 1 报告模板；无 decoder、无矩阵、无新依赖（`numpy/pandas/pyarrow` 已装仅作模板校验，可选）。laziest alternative: 若仓内仍缺 `PE/定理` 权威输入，V60 已裁 `DATA_NOT_READY`，V61 仅把“需新增什么”落成可勾选清单，不自算 `H_min`/`ell`/`SKR`，不以 `IAB/H/MAP/visibility=0.95 shadow` 填充缺口。

> **研究方向保持**：`V60` 已以 decoder-free 判定现有数据仓无 `composable` 密钥计算资格（`composable theorem missing` + `decisive PE missing` → `V60_DATA_NOT_READY`，`ell=null`，`H_min/IAB/shadow` 禁等价）；`V61` 仅将 `V60` 输出的 `minimal_new_measurement` 固化为**可执行的最小采集规范**，使下一轮物理实验返回的数据可被机械判定为 `V61_READY`（可算 `ell =1024*hmin_lower - leak_IR - leak_other - finite`，三源独立 `10% H_min` 门槛），否则仍停 `PENDING` 不进 `V62`。

## Goal

以最短 decoder-free 路径产出 **“新实验需要记录什么”的最小采集规范**，在完全冻结 `n=1024, leak 7089/7439/7764 (tag64 已含, GF32 5bits)` 下，定义下一轮实验的 10 类记录与唯一的 decoder-free 验收公式；其中就绪判定为 **dependency-aware**（`R61-01`）而非 10 类全部 `READY`，`V62_OPEN` 仅要求所有 `required_core` 就绪且所选定理的条件依赖就绪，与该定理无关的 `visibility/decoy` 允许 `not_applicable_with_theorem_reason` 不阻塞；`verification` 按 `R61-02` 冻结口径执行：

1. **协议/安全定理及适用假设**：定理 `theorem_id`（如 `Renner`/`Niu 2016`/`Tomamichel/Lim` 等）+ 假设链 `assumptions[]`（`collective/coherent` 攻击模型、PE 模型、认证/验证假设、post-selection 适用域）+ 定理声明处原文行号/表达式权威绑定；无声明则后续 `ell` 不可算。
2. **conjugate-basis 或 phase-error 观测**：共轭基（如 `X` vs `Z` / Franson 干涉）实测统计 `conjugate_basis_stats` + `phase-error 率 `e_ph`（或等价 `e_p`）估计链 + decoy-state 若适用；禁止以 `SER/Shannon H/visibility` 代理 `e_ph`。
3. **`n_PE` 与抽样规则**：`n_PE` 权威样本数 + 抽样规则 `sampling_rule`（随机抽样、基选择概率 `p_Z/p_X`、无放回/有放回、PE 帧标记与可重放种子/计数链），与 `n_eff` 区分（`n_eff` 仅 `shadow proxy`）。
4. **visibility 逐源区间**：每源（`1M/1p5M/2M`）每 `loss/session` 实测 `visibility` 区间 `[vis_low, vis_high]` + 来源/校准链 `vis_source`（`chi_from_visibility` 输入 `vis` 的实测链，非 `global 0.95 shadow`）。
5. **`eps_sec/eps_cor` 分配**：`eps_sec` / `eps_cor` 总预算及分解 `eps_sec >= eps_PE+eps_PA+eps_EC+...` 和 `eps_cor = eps_EV+...`，每项与 `DeltaFK/EV/auth` 的 `eps` 预算一致性。
6. **verification/authentication 泄漏（R61-02 冻结口径）**：`leak_verification`（`epsilon_EC` 界 + `verification_bits` 转录本）+ `leak_auth`（认证开销 `bits/block`），`leak_IR` 已含 `tag64` 不得重复扣除，`leak_other` 仅计 `max(0, actual_verification_bits - 64)` 超出部分，`epsilon_EV/EC` 保留为概率、未经定理显式 `bits` 映射不得直接加进 `leak_other/finite`。
7. **finite-size correction**：`finite-size` 权威公式与系数（`DeltaFK = 4*sqrt(log2(2/eps_sec)/n_eff)+2*log2(2/eps_cor)/n_eff` 等）+ `n_eff` 有效计数来源，单位 `bits/pair` vs `bits/block` 显式；`epsilon` 仅作概率预算，不经映射不得转 `bits` 入 `finite`。
8. **post-selection 和有效帧计数**：`post_selection` 策略 + `accepted_frame_fraction` + `有效帧/块计数`（`accepted/rejected` 计数、`n_block = N_pairs→frames` 映射、弃帧规则权威声明）。
9. **单位/时间戳/session/source 绑定**：`blocks ×1024 symbols`、`pairs→symbols/blocks` 换算 `unit_map`（`bits/block` vs `bits/symbol` vs `bits/pair` vs 无量纲）+ `timestamp` 绑定（`session_id/source_id/delay_used_ps/block_id/pairing legacy_v1 nearest 200ps` 四元绑定），`tag` 仅 `total` 计一次。
10. **能否达到三源 `10% H_min` 门槛的 decoder-free 验收公式**：冻结 `ell_s =1024*hmin_lower_s - leak_IR_s - leak_other_s - finite_s`（`hmin_lower` 为 `bits/symbol` composable 下界，三源独立）+ 阈值锚点 `floor = leak/1024 = 6.9238/7.2637/7.5820`、`5% 7.2882/7.6460/7.9811`、`10% 7.6931/8.0707/8.4245 bits/symbol`（`other=0 finite=0` 占位），仅当 10 类中关键项 `ready` 且 `hmin_lower` 为 composable 下界时才以真值比阈值判定 `ell>0` / `margin≥10%`，其余 `ell=null`。

### 冻结 V57/V59 披露（每 block 1024 符号，`64-bit tag` 已含不得重复扣除，仅作阈值输入）

| source | m1 | m2 | m_total | leak_total (=5*m_total+64) bits/block | leak_without_tag | tag |
|---|---|---|---|---|---|---|
| 1M | 981 | 424 | 1405 | 7089 | 7025 | 64 |
| 1p5M | 1024 | 451 | 1475 | 7439 | 7375 | 64 |
| 2M | 1024 | 516 | 1540 | 7764 | 7700 | 64 |

- `n=1024 symbols/block`, `log2 q =5 (GF32)`, `tag=64 L2-only` 仅 `total` 计一次；`leak_total ==5*m_total+64` 双校验；`bits/symbol *1024 = bits/block`。
- `H1 16×1024 / Lane C / H_inc1/2 / Δ8+8 / decoder 90/1.0 poly37 / estimator / V57 m` 全冻零改；`IAB / Shannon H(A|B) / MAP_acc / visibility=0.95 shadow` 禁当 `H_min` 且禁当 `H_min^epsilon(A|E)` 下界。

## Non-Goals

- 不运行任何 `decode_* / construct_* / 信道估计器`（`rg "decode_" 0 hits`, `rg "import.*decoder" 0 hits`）；不改 `H1 16×1024 / Lane C / H_inc/Δ/decoder 90/1.0 poly37 / estimator / V57 m1/m2/leak` 任一冻结量；不新增矩阵；不重跑 `V55` 任何 `run_01`。
- 不修改 `LDPC` 码族（`Lane C / H_inc / Δ8+8 / protograph` 全冻）；不做 `bin_width/dimension/pairing/mapping` 重设计。
- 不用旧数据伪造缺失 `PE`（禁止以 `SER/H/IAB/MAP/visibility=0.95` 代理 `e_ph / n_PE / conjugate`，违规则 `EVIDENCE_INVALID`）；不把 `IAB/Shannon H/MAP_acc/visibility shadow` 当 `H_min`（`proxy 不升级`，`missing→null`）。
- 不在无新安全测量数据时继续创建数值型 `V62`（`V62` 仅当本规范 10 类中 `composable theorem + decisive PE (e_ph/conjugate/n_PE/vis_chain)` 均 `ready` 且 `hmin_lower` 为 composable 下界时才允另起 `OpenSpec + 独立授权`，否则 `V62 PENDING`）。
- 不创建正式 `run_01` decoder 执行；不宣称 `FER / SKR / 阈值晋升`；不做 `bin_width/dimension` 或 `eps` 网格搜索；不改 `src//experiments//tools/` 与 `V54-V60` 既有输出与终态（`git diff -- src/ ==0 && git diff -- openspec/changes/formal-ir-v5[5-9]/ ==0 && git diff -- openspec/changes/formal-ir-v60*/ ==0` 除本变更外零改）。
- 不以 `optimistic floor` 冒充 `composable` 正余量；不把 `shadow descriptive` 区间升级为 `composable-authority`；不以总体平均替代三源分别判定；不重复扣除 `tag64`。
- 不自创 `H_min / finite-key / composable` 公式；新 `H_min/finite` 仅用新实验权威输入，缺则 `null`。

## Scope

1. **冻结输入零改**：`n=1024, GF32 log2q=5, tag=64, V57/V59 m1/m2/leak 7089/7439/7764` 三源冻结，`data SHA 84d62779` 同 V57-V60，`pairing nearest legacy_v1` 单点，仅只读；`leak_total ==5*m_total+64` 双校验；`H1/L2/Δ/decoder/estimator` 全冻。
2. **最小采集规范 Schema（10 类，机器可校验，R61-01 dependency-aware）**：定义 `v61_measurement_schema.json`（`JSON Schema`）+ `v61_minimal_measurement_template.csv` 模板，10 类字段至少覆盖：`protocol_theorem`（`theorem_id/assumptions/domain/source(file:line:expr)`）、`conjugate_phase_error`（`e_ph, conjugate_basis_stats, decoy_chain[conditional]`）、`n_PE + sampling_rule`（`n_PE, p_Z/p_X, random_sampling, seed_or_counter`）、`visibility[conditional]`（`[vis_low,vis_high], vis_source, cal_chain` 每源）、`eps_sec/eps_cor`（`eps_sec, eps_cor, eps_PE, eps_PA, eps_EC/E_V 分解`）、`verification/auth leakage`（`leak_verif, leak_auth, actual_verification_bits, tag_included?`）、`finite-size`（`DeltaFK_formula, n_eff, coeff_authority, unit`）、`post_selection`（`accepted_frame_fraction, n_block, post_sel_penalty`）、`unit_timestamp_binding`（`unit_map, session_id, source_id, delay_used_ps, block_id, pairing_rule`）、`acceptance_formula_inputs`（`hmin_lower_authority, leak_other, finite, ell_formula`）。每字段 `authority: composable|shadow|proxy|missing` + `readiness: required_core | required_if_theorem_applicable | not_applicable_with_theorem_reason | missing` 四类 + `minimal_new_measurement` 语义，`proxy 不升级`，`missing→null`；其中 `required_core`（`theorem/e_ph[excl decoy]/n_PE/eps/verification_extra/finite/post_selection/unit/acceptance`）必须 `ready`，`required_if_theorem_applicable`（`visibility` 全项、`decoy_chain`）仅当所选定理显式依赖时要求 `ready`，否则以 `not_applicable_with_theorem_reason` 记录定理依据且不阻塞 `V62_OPEN`。
3. **decoder-free 验收公式冻结（三源独立，tag 不重复，R61-02 口径）**：`ell_s =1024*hmin_lower_s - leak_IR_s - leak_other_s - finite_s`（`leak_IR=leak_total` 已含 `tag=64`，`leak_other_s = max(0, actual_verification_bits - 64) + leak_auth_s + ...` 仅计超出部分，`epsilon_EV/EC` 为概率未映射不得入 `leak_other/finite`，单位全 `bits/block`），`floor = leak/1024 = 6.9238/7.2637/7.5820`、`5% = leak/(1024*0.95)=7.2882/7.6460/7.9811`、`10% = leak/(1024*0.90)=7.6931/8.0707/8.4245` 为必给阈值锚点（`other=0 finite=0` 占位），仅当 `required_core` 全 `ready` 且所选定理的条件依赖 `ready` 且 `hmin_lower` 为 composable 下界时才以真值比阈值判定 `ell>0` / `margin≥10%`，其余 `ell=null`。
4. **停止条件与 V62 门禁（R61-01 dependency-aware）**：缺 `composable theorem`（无明确 composable 定理声明）或 `decisive core PE`（`required_core` 中 `e_ph/n_PE/conjugate` 无权威链）任一 → 本规范产出仍为 `V61_SPEC_READY / DATA_STILL_MISSING`（规范就绪但数据仍缺），`V62` 保持 `PENDING` 禁止数值计算；仅当新实验按本规范 `required_core` 全 `ready` 且所选定理的条件依赖（`visibility/decoy` 若适用）`ready` 且 `hmin_lower` 权威可算时才允另起 `V62` 的 `OpenSpec + 独立授权`，与该定理无关的 `visibility/decoy` 以 `not_applicable_with_theorem_reason` 不得阻塞。
5. **脚本与报告交付（DECODE_FORBIDDEN）**：`scripts/v61_measurement_spec_check.py`（decoder-free, `rg "decode_" 0 hits`, `py_compile PASS`，仅校验模板/阈值/单位）输出 `docs/research_cycles/V61P0/v61_measurement_schema.json` + `v61_minimal_measurement_template.csv` + `v61_minimal_new_measurement_checklist.csv` + `V61_SECURITY_MEASUREMENT_SPEC_REPORT.md` 四工件，未创建 `run_01`，已推送新 SHA 并停留 `PLAN_CANDIDATE / DECODE_FORBIDDEN`，等待独立审核。

## Impact Scope

- **新增（本变更最小）**：`openspec/changes/formal-ir-v61-security-measurement-specification/` 下 4 工件 `proposal.md/design.md/tasks.md/specs/spec.md` + 采集规范 `docs/research_cycles/V61P0/v61_measurement_schema.json`（`JSON Schema` 10 类）+ 模板 `v61_minimal_measurement_template.csv` + 清单 `v61_minimal_new_measurement_checklist.csv` + 报告 `V61_SECURITY_MEASUREMENT_SPEC_REPORT.md` + 可选校验脚本 `scripts/v61_measurement_spec_check.py`（`rg "decode_" 0 hits`, `py_compile PASS`, 只读校验）。
- **只读依赖**：`openspec/changes/formal-ir-v57-channel-recharacterization/v57_channel_recharacterization.json` / `openspec/changes/formal-ir-v60-composable-security-input-readiness/docs/.../v60_composable_security_readiness.json`（V57 m / V60 10项就绪度与缺口，仅参考不改），`tools/security_reports/_security_calibrated_common.py` / `build_actual_ir_finite_key_shadow.py` / `round3_build_proof_gap_matrix.py`（权威公式与缺口，仅参考不改），`comparison_bench/outputs_comparison/v57* + v55_intake_20260828`（数据盘点，仅校验单位/来源，不跑 decoder），`docs/SECURITY_MODEL.md / docs/decision-log.md`（协议模型，仅参考）。
- **不修改**：任何既有 `spec/代码/测试/输出`（除本目录 + `scripts/` + `docs/research_cycles/V61P0/` 外）、`V38–V60` 输出、`src//experiments//tools/`（`git diff -- src/ ==0` 等），**不改 `V57-V60 m/leak`，不创建 `run_01` decoder 执行，不进入 `V62`，零码参**。

## Acceptance Criteria

- [ ] `proposal/design/tasks/specs/spec.md` 齐全一致，`lifecycle PLAN_CANDIDATE / DECODE_FORBIDDEN / MEASUREMENT_SPEC_ONLY`，`HEAD 7b476f62368a410722ab1e0d65ea2709e423d848` + `branch formal-ir-mainline` + `data SHA 84d62779` 已绑定，显式声明 decoder-free、零 decoder、三源分别、tag 不重复、仅定义采集、不自创 `H_min`、`V62 PENDING`，且显式 `R61-01 dependency-aware` 与 `R61-02 verification 口径冻结`。
- [ ] **10 类采集规范可复现（R61-01）**：`v61_measurement_schema.json` 与 `v61_minimal_measurement_template.csv` 精确覆盖 `protocol_theorem、conjugate/phase-error、n_PE+sampling_rule、visibility逐源区间、eps_sec/cor、verification/auth、finite-size、post-selection/effective帧、unit/timestamp/session/source、acceptance_formula_inputs` 10 类，每字段 `symbol/meaning/unit/source/authority/readiness/minimal_new_measurement` 已定义，其中 `readiness` 为 `required_core | required_if_theorem_applicable | not_applicable_with_theorem_reason | missing` 四类，`H/L2/Δ/decoder` 零改已验，禁止 `H/IAB/MAP/vis=0.95` 当 `H_min` 已验，且 `V62_OPEN` 仅要求 `required_core` 全 `ready` 且所选定理的条件依赖 `ready`、无关的 `visibility/decoy` 允许 `not_applicable_with_theorem_reason` 不阻塞已验。
- [ ] **验收公式三源独立可复现（R61-02）**：逐源 `hmin_break_even_floor = leak/1024 = 6.9238/7.2637/7.5820 bits/symbol` 且 `5% 7.2882/7.6460/7.9811`、`10% 7.6931/8.0707/8.4245` 已算并与 `leak` 锚点 `h*1024==leak/(1-margin)` 双校验，`log2 d=10` 上界校验，三源独立不平均，`leak_total ==5*m_total+64` 双校验，`GF32 5bits` 显式，`tag` 不重复，`leak_IR 已含 tag64`、`leak_other = max(0, actual_verification_bits-64)` 且 `epsilon_EV/EC` 未映射不得入 `leak_other/finite` 已验，且显式 `仅 required_core+条件依赖 ready 才以真 hmin_lower 判定 ell>0 / margin≥10%，其余 ell=null`，并通过 `tag64-only / extra-verification / epsilon-not-bits` 三边界测试。
- [ ] **停止条件与 V62 门禁可复现（R61-01）**：缺 `composable theorem` 或 `decisive core PE` 时 `V62 PENDING` 已正确约束，未以旧数据 `shadow` 填 `null`，`decoder/V62数值计算` 零触发已验；与定理无关的 `visibility/decoy` 以 `not_applicable_with_theorem_reason` 不阻塞 `V62_OPEN` 已验；最小 `schema + 模板 + 清单 + 报告` 已落盘且与 `V60 缺口` 一致。
- [ ] `scripts/v61_measurement_spec_check.py` 若提供则为 decoder-free 可运行脚本（`python scripts/v61_measurement_spec_check.py [--schema ...] [--template ...]`），`rg "decode_" 0 hits`、`rg "import.*decoder" 0 hits`，仅 `numpy/pandas`（可选 `pyarrow`），`py_compile` PASS，未创建 `run_01`，且 `V57-V60 m/leak` 未改（`git diff -- src/ ==0` 且 `git diff -- openspec/changes/formal-ir-v5[5-9]/ ==0` 且 `git diff -- openspec/changes/formal-ir-v60*/ ==0`），且内置 `tag64-only / extra-verification / epsilon-not-bits` 三边界断言已验。
- [ ] `docs/research_cycles/V61P0/V61_SECURITY_MEASUREMENT_SPEC_REPORT.md` 已记录 10 类字段定义（含 `required_core / required_if_theorem_applicable / not_applicable_with_theorem_reason` 依赖分类）、单位换算、session/source 绑定、阈值表、`V62` 门禁与最小行动清单，数据与 `json/csv` 一致，结论不扩大为 `FER/SKR/阈值晋升`，显式 `V57-V60 m/leak 冻结` + `tag 已含不重复` + `leak_other = max(0,actual-64)` + `epsilon 不入 bits` + `三源分别不平均` + `proxy 不升级` + `missing→null` + `仅READY算ell` + `V62 PENDING`。
- [ ] 已推送新 `Plan SHA`（基于 `7b476f62368a410722ab1e0d65ea2709e423d848`）并停留在 `PLAN_CANDIDATE / DECODE_FORBIDDEN`，未创建任何 `run_01` decoder 执行，不碰 `src//experiments//tools/` 与 `V54-V60` 既有变更，`git diff -- src/ ==0` 且 `rg "decode_" 0 hits`，`py_compile + 关键测试` PASS，推送后等待独立审核；返回 `Plan SHA / implementation SHA / 10类 schema / 三源阈值 / V62 门禁`，**不自动进入 `V62`，普通推送**。

## Tasks

见 `tasks.md`（10类采集规范 Schema 与模板；验收公式与阈值；V62 门禁与校验与推送）。

## Lifecycle

`V60` 当前 `PLAN_CANDIDATE / DECODE_FORBIDDEN` 已固化 `9f1fb02c`（`m1 981/1024/1024, m2 424/451/516, leak 7089/7439/7764, n1024, tag64` 已冻，`V60_DATA_NOT_READY` 仅闭合就绪度，未提供 composable `H_min`）；`V61` 本采集规范在 `7b476f62368a410722ab1e0d65ea2709e423d848` 起点上修订为 `R61` `PLAN_CANDIDATE / DECODE_FORBIDDEN / MEASUREMENT_SPEC_ONLY`（仅定义新实验需记录什么，不实现 runner，不执行 decoder，不创建 `run_01`，不改码参，三源分别；阈值必给、仅 `required_core + 所选定理条件依赖 READY` 才算 `ell`、`composable:null` 不自填；`R61-02` 冻结 `leak_IR 已含 tag64` / `leak_other = max(0,actual-64)` / `epsilon概率不入bits`）；`V61` 仅当新实验按本规范 `required_core` 全 `ready` 且条件依赖 `ready` 且 `hmin_lower` 权威时才允另起 `V62` 数值后继，否则停 `PENDING` 精确输出本规范与门禁清单；`V61` 推送后不自动进入 `V62`，需新 `OpenSpec` 与独立授权，**本次修订普通推送新 Plan SHA 后停止**。
