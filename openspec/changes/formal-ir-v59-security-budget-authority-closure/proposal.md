# OpenSpec Proposal: formal-ir-v59-security-budget-authority-closure

**Status**: `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN` — decoder-free / security-budget authority closure，主动闭合 V58 缺失安全输入
**Domain**: Formal IR / V59 security-budget authority closure (V58 唯一后继)
**Change ID**: `formal-ir-v59-security-budget-authority-closure`
**Cycle ID**: `V59P0` (security-budget-authority-closure), predecessor `V58` `formal-ir-v58-secret-key-budget-stoploss` (起点 `2340257d`，实施前以 `git fetch && git rev-parse HEAD == origin/formal-ir-mainline` 重核为准；不一致则阻塞)
**Branch**: `formal-ir-mainline`
**HEAD**: `2340257d` (起点，实施前重核全 SHA，不一致阻塞；本次推送新 SHA)
**Data SHA**: `84d62779` (`84d62779603e62de50ded5182ed65b65d3dc6084`, `d=1024 bw=200ps pairing=nearest rule=legacy_v1` 同 V57/V58，不改)
**Lifecycle**: `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN` — 仅 decoder-free 安全预算权威闭合，不产生 `run_01` decoder 执行，不改 `H1/Lane C/H_inc/Δ/decoder 90/1.0/poly37 / V57-V58 m`
**Method frozen**: V57/V58 披露完全冻结仅作输入（重算报告不写入码，禁止改 `m1/m2/m_total/leak`）

> ponytail lite: 本变更仅 4 OpenSpec 工件 + 1 只读预算脚本 + 2 报告/JSON + 1 紧凑CSV；无 decoder、无矩阵、无新依赖（`numpy/pandas/pyarrow` 已装），最短科学路径。laziest alternative: 若仓内无权威 H_min/composable 公式则直接 `AUTHORITY_INPUTS_ACTIONABLE` 输出最小清单与 `hmin_break_even` floor，不自创 `H_min` 或有限尺寸网格。

> **研究方向保持**：V58 已以 `SECURITY_INPUTS_INCOMPLETE` 止损但未输出每源 `hmin_break_even` 阈值与最小新增测量清单；V59 仅将 V57 已接受 `m1/m2 leak` 带入仓内既有权威公式逐函数裁决 `PIE_secure` 为 composable vs shadow/proxy，并以统一 `ell = 1024*hmin_lower - leak_IR - leak_other - finite` 给出乐观 floor / shadow 描述 / composable-authority 三档阈值，不改码族架构。

## Goal

以最短 decoder-free 路径完成 **V58 缺失安全输入的主动权威闭合**，在完全冻结 `n=1024, leak 7089/7439/7764 (tag=64 已含)` 下：

1. **逐函数只读裁决** `tools/security_reports` 下 4 权威文件（`_security_calibrated_common.py` / `build_actual_ir_finite_key_shadow.py` / `build_beta_baseline_finite_key_shadow.py` / `round2_build_finite_key_audit_table.py` + 关联 `round2_build_actual_ir_finite_key_shadow.py`）中 `PIE_secure = IAB - leak - chi_E - DeltaFK - post_sel` 是否被**明确授权为 composable** 还是**仅 shadow/proxy**，追踪 `IAB - chi_E` 是否可等价 `H_min^epsilon(A|E)`，不自行认定 authority。
2. **建立统一预算** `ell = 1024 * hmin_lower - leak_IR - leak_other - finite`（单位全 `bits/block`），冻结 `n=1024, leak 7089/7439/7764, tag 已含`，输出 **exact 变量表** `symbol / meaning / unit / source(file:line:expr) / authority(proxy/missing/composable) / decoder-free 可算? / 最小新增测量`，至少覆盖 **smooth min-entropy、phase-error、visibility 区间、PE sample 大小、eps_sec/cor、finite-size 惩罚、EV(error-verification)、post-selection、auth** 共 ≥11 项。
3. **每源输出 `hmin_break_even = (leak_IR + other + finite)/1024` 三档**：**optimistic floor** (`other=0, finite=0` 必给)、**shadow descriptive 区间**（仓内 calibrated shadow 参数的描述性传播，proxy 不升级为 composable）、**composable-authority 区间 `null`**（缺决定性 composable 输入时显式 `null` 而非 0），并给出 **每源 0 / 5% / 10% margin 阈值**，禁把 `H(A|B)/IAB/MAP` 当 `H_min`。
4. **四互斥终态按优先级 first-match 互斥裁决**并落盘验证：`EVIDENCE_INVALID` > `AUTHORITY_CLOSED_NO_POSITIVE_MARGIN`（任一源保守 `ell ≤0` 止路） > `AUTHORITY_CLOSED_POSITIVE_POSSIBLE`（三源 `conservative>0`） > `AUTHORITY_INPUTS_ACTIONABLE`（已输出最小清单与阈值，有效完成） — 其中 **仅缺 `H_min` 不足以判定为 `ACTIONABLE`，必须同时输出最小清单与每源阈值才算有效完成**。

### 冻结 V57/V58 披露（每 block 1024 符号，64-bit tag 已含不得重复扣除，仅预算诊断）

| source | m1 | m2 | m_total | leak_total (=5*m_total+64) bits/block | leak_without_tag | tag |
|---|---|---|---|---|---|---|
| 1M | 981 | 424 | 1405 | 7089 | 7025 | 64 |
| 1p5M | 1024 | 451 | 1475 | 7439 | 7375 | 64 |
| 2M | 1024 | 516 | 1540 | 7764 | 7700 | 64 |

- `n=1024 symbols/block`, `log2 q =5 (GF32)`, `tag=64 L2-only` 仅 `total` 计一次；脚本校验 `leak_total ==5*m_total+64` 且 `m_total == m1+m2`。
- 单位统一到 `bits/block`，`hmin` 若为 `bits/symbol` 则 `*1024`；`bits/pair` 则显式换算并记录。

### 工作阶段（decoder-free，全冻）

**A 只读权威裁决**：逐函数阅读 4 文件（`delta_fk_calibrated` / `chi_from_visibility` / `dary_mutual_info_proxy` / `_build_shadow` / `_build_beta_baseline` / `round2` audit `DeltaFK/leak/post_sel/epsilon_EC`），记录 `formula_authority = {file, function, line, expr, unit, authority}`，裁决 `PIE_secure` 为 `shadow/proxy` 还是 `composable`，追踪 `IAB - chi_E == H_min^epsilon(A|E)` 是否被**明确声明**，未声明则 `proxy_missing`，`H/IAB/MAP` 当 `H_min` 禁止。

**B 统一预算与分解表**：建立 `ell =1024*hmin_lower - leak_IR - leak_other - finite`，分解 `leak_other = PE + EV + auth + ...`, `finite = DeltaFK + ...`，输出 exact 变量表（≥11 项，含 smooth min-entropy、phase-error、visibility、PE sample、eps_sec/cor、finite、EV、post-selection、auth）与 `decomposition table` 三源独立。

**C 三源 break-even 阈值**：逐源 `hmin_break_even_floor = leak_IR/1024`（optimistic `other=0 finite=0`），`hmin_break_even_shadow ∈ [low, high]`（shadow 描述性区间），`hmin_break_even_composable = null`（无 composable 权威时），并派生 `0%/5%/10% margin` 阈值：`h_m(margin) = (leak+other+finite) / (1024*(1-margin))`，`margin 0.05 => /0.95, 0.10 => /0.90`，单位 `bits/symbol`，每源独立不平均。

**D 四互斥终态 first-match**（按序优先级互斥，不可共存）：
`EVIDENCE_INVALID`（单位/tag/m 自洽失败） > `AUTHORITY_CLOSED_NO_POSITIVE_MARGIN`（任一源 `conservative ell ≤0` 止路） > `AUTHORITY_CLOSED_POSITIVE_POSSIBLE`（三源 `>0` 但仅 proxy 描述） > `AUTHORITY_INPUTS_ACTIONABLE`（已输出最小新增测量清单 + 每源阈值，有效完成） —  **仅声明缺 `H_min` 而未输出清单与阈值不得判 `ACTIONABLE`**。

**E 交付与守卫**：`scripts/v59_security_budget_authority_closure.py`（decoder-free, `rg "decode_" 0 hits`, `py_compile PASS`）输出 `docs/research_cycles/V59P0/v59_secret_key_budget_authority.json + SECRET_KEY_BUDGET_AUTHORITY_REPORT.md + v59_break_even.csv`，验证 `tag 不重复、单位换算、break-even 锚点、missing→null、proxy 不升级、终态互斥`，普通推送新 SHA，停留 `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN` 等待独立审核。

## Non-Goals

- 不运行任何 `decode_*` / `construct_*` / 信道估计器（`rg "decode_" 0 hits`, `rg "import.*decoder" 0 hits`）；不改 `H1 16×1024 / Lane C / H_inc1/2 / Δ8+8 / decoder 90/1.0 poly37 / V57-V58 m1/m2` 任一冻结量；不新增矩阵；不进入 `V60`。
- 不改写/覆盖 V57/V58 三新 session 已接受 `m1/m2/leak`（仅只读输入）；不改 `V25` `184/190/192` 历史值；不改 `src/` / `V54-V58` 既有输出与终态（`git diff -- src/ ==0 && git diff -- openspec/changes/formal-ir-v5[4-8]/ ==0`）。
- 不自创 `H_min / finite-key / composable` 公式；缺权威输入不造 `eps_sec/eps_cor/visibility` 参数；不把 `H/IAB/MAP` 当 `H_min`（违规则 `EVIDENCE_INVALID`）。
- 不创建正式 `run_01` decoder 执行；不宣称 `FER / SKR / 阈值晋升`；不做 `bin_width/dimension/pairing` 或 `eps` 网格搜索；`hmin_break_even_composable` 缺权威时显式 `null` 而非自填。
- 不以 `optimistic floor` 冒充 `composable` 正余量；不把 `shadow descriptive` 区间升级为 `composable-authority`；不以总体平均替代三源分别判定。
- 不改 `src/ / experiments/ / tools/` 基线代码（`git diff -- src/ ==0` 且 `git diff -- experiments/ ==0` 且 `git diff -- tools/ ==0`）。

## Scope

1. **冻结输入零改**：`n=1024, GF32 log2q=5, tag=64, V57/V58 m1/m2/leak 7089/7439/7764` 三源冻结，`data SHA 84d62779` 同 V57/V58，`pairing nearest legacy_v1` 单点，仅只读；`leak_total ==5*m_total+64` 双校验。
2. **Phase A 权威逐函数裁决（只读，禁止自创）**：仓库内 `rg "DeltaFK|chi_E|PIE_secure|IAB_est|_security_calibrated_common|dary_mutual_info|chi_from_visibility|post_selection|epsilon.*EC|H_min|min_entropy"` 定位权威，逐函数记录 `{file, function, line_start:line_end, expr, unit, authority: composable|shadow|proxy|missing}`，明确 `bits/block` vs `bits/pair` vs `bits/symbol`，裁决 `PIE_secure = IAB - leak - chi_E - DeltaFK - post_sel` 为 **shadow/proxy**（`not full niu_2016 composable proof` 等显式声明为凭），追踪 `IAB - chi_E ≟ H_min^epsilon(A|E)` 是否被**明确声明**，未声明则 `proxy_missing` 并止于 `shadow`，不自行等价。
3. **Phase B 统一预算与 exact 变量表**：冻结 `ell =1024*hmin_lower - leak_IR - leak_other - finite`，其中 `leak_IR = leak_total (=5*m_total+64)` 已含 `tag`，`leak_other = PE_penalty + EV_tag + auth + ...`, `finite = DeltaFK_calibrated + ...`；输出 `symbol / meaning / unit / source(file:line) / authority(proxy/missing/composable) / decoder_free? / minimal_new_measurement` 表，至少覆盖 **smooth min-entropy `H_min^epsilon`、phase-error `e_ph` / `e_p`、visibility 区间 `[vis_low, vis_high]`、PE sample 大小 `n_PE`、eps_sec、eps_cor、finite-size `DeltaFK`、EV `epsilon_EC`、post-selection `accepted_frame_fraction`、auth bits** 共 ≥11 项；每源 `decomposition table` 三源独立，不平均。
4. **Phase C 三档 break-even 阈值**：逐源 `hmin_break_even_floor = leak_IR/1024 = 6.9238/7.2637/7.5820 bits/symbol`（`other=0 finite=0` optimistic floor 必给），`hmin_break_even_shadow = (leak_IR+other_shadow+finite_shadow)/1024` 描述性区间（用仓内 calibrated shadow 的 `chi/delta/post_sel` 代理，不升级），`hmin_break_even_composable = null`（缺 composable 输入显式 `null`），并派生 `margin 0 / 5% / 10%` 阈值 `h_m = (leak+other+finite)/(1024*(1-margin))`，`0% = floor, 5% => /0.95, 10% => /0.90`，每源独立成表，`log2 d =10` 上界校验。
5. **Phase D 四互斥终态 first-match**：按优先级 `EVIDENCE_INVALID (unit/tag/m 自洽 fail) > AUTHORITY_CLOSED_NO_POSITIVE_MARGIN (任一 conservative ≤0) > AUTHORITY_CLOSED_POSITIVE_POSSIBLE (三源>0 但 composable null，仅 proxy) > AUTHORITY_INPUTS_ACTIONABLE (已输出最小清单≥11项 + 每源三档阈值，有效完成)` 互斥落盘；**仅声明缺 `H_min` 而未输出最小清单与阈值不得判 `ACTIONABLE`**，`null` 保持 `null` 不填 0。
6. **Phase E 脚本与报告交付（DECODE_FORBIDDEN）**：`scripts/v59_security_budget_authority_closure.py`（decoder-free, `rg "decode_" 0 hits`, `py_compile PASS`）+ `docs/research_cycles/V59P0/v59_secret_key_budget_authority.json`（`formula_authority` + `variable_table[≥11]` + `decomposition` + `break_even{optimistic_floor, shadow, composable:null}` + `verdict`）+ `SECRET_KEY_BUDGET_AUTHORITY_REPORT.md`（权威裁决、三源阈值表、最小行动表、终态声明）+ 紧凑CSV（`source, leak, optimistic_floor, shadow_low/high, composable, margin_0/5/10`），未创建 `run_01`，已推送新 SHA 并停留 `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN`，等待独立审核。

## Impact Scope

- **新增（本变更最小）**：`openspec/changes/formal-ir-v59-security-budget-authority-closure/` 下 4 工件 `proposal.md/design.md/tasks.md/specs/spec.md` + decoder-free 脚本 `scripts/v59_security_budget_authority_closure.py` (`rg "decode_" 0 hits`, `py_compile PASS`, 只读预算) + 报告 `docs/research_cycles/V59P0/SECRET_KEY_BUDGET_AUTHORITY_REPORT.md` + `v59_secret_key_budget_authority.json` (per_source + overall + variable_table + break_even) + 紧凑CSV `v59_break_even.csv` + 报告内 `variable_table / decomposition table / break-even 表 / authority verdict / 最小行动表` 章节。
- **只读依赖**：`openspec/changes/formal-ir-v57-channel-recharacterization/v57_channel_recharacterization.json` / `openspec/changes/formal-ir-v58-secret-key-budget-stoploss/v58_secret_key_budget.json`（V57-V58 m1/m2/leak），`tools/security_reports/_security_calibrated_common.py` / `build_actual_ir_finite_key_shadow.py` / `build_beta_baseline_finite_key_shadow.py` / `round2_build_finite_key_audit_table.py` / `round2_build_actual_ir_finite_key_shadow.py` / `round3_build_proof_gap_matrix.py`（权威公式与缺口，仅参考不改），`docs/SECURITY_MODEL.md` / `docs/decision-log.md`（论文/决策，仅参考）。
- **不修改**：任何既有 `spec/代码/测试/输出`（除本目录 + `scripts/` + `docs/research_cycles/V59P0/` 外）、`V38–V58` 输出、`src//experiments//tools/`（`git diff -- src/ ==0` 等），**不改 `V57-V58 m`，不创建 `run_01` decoder 执行，不进入 `V60`，零码参**。

## Acceptance Criteria

- [ ] `proposal/design/tasks/specs/spec.md` 齐全一致，`lifecycle DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN`，`HEAD 2340257d` + `branch formal-ir-mainline` + `data SHA 84d62779` 已绑定，显式声明 decoder-free、零 decoder、三源分别、tag 不重复、仅权威公式、缺 composable 输入则 `composable:null` 不自填。
- [ ] **Phase A 权威裁决可复现**：`tools/security_reports` 下 4 文件逐函数记录已落盘 `formula_authority[{file,function,lines,expr,unit,authority}]`，明确 `PIE_secure = IAB - leak - chi_E - DeltaFK - post_sel` 被裁决为 **仅 shadow/proxy**（以 `not full niu_2016 composable proof` / `calibrated penalty` / `proof_gap_matrix missing` 等原文为凭），且 `IAB - chi_E ≟ H_min^epsilon(A|E)` 被标记为 **未明确授权等价**（`proxy_missing`/`no_declaration`），`H/IAB/MAP` 当 `H_min` 禁止已验。
- [ ] **Phase B exact 变量表可复现**：`variable_table` ≥11 项已落盘（`symbol/meaning/unit/source/authority(proxy/missing/composable)/decoder_free?/minimal_new_measurement`），至少覆盖 **smooth min-entropy、phase-error、visibility 区间、PE sample、eps_sec/cor、finite、EV、post-selection、auth**，单位统一到 `bits/block`，`leak_total ==5*m_total+64` 三源 `7089/7439/7764` 自洽，`GF32 5bits` 显式，`tag` 不重复。
- [ ] **Phase C break-even 可复现**：逐源 `hmin_break_even_floor = leak/1024 = 6.9238/7.2637/7.5820 bits/symbol`（`other=0 finite=0`）已算并与 `leak` 锚点双校验；`shadow` 描述性区间已用仓内 calibrated 值传播（`proxy` 不升级）；`composable` 显式 `null` 不填 0；每源 `0/5%/10% margin` 阈值 `h_m = (leak+other+finite)/(1024*(1-m))` 已算（`0% = floor, 5%=>/0.95, 10%=>/0.90`），`log2 d=10` 上界校验，三源独立不平均。
- [ ] **Phase D 四终态互斥可复现**：`overall` 按 `EVIDENCE_INVALID > AUTHORITY_CLOSED_NO_POSITIVE_MARGIN(任一 conservative≤0止路) > AUTHORITY_CLOSED_POSITIVE_POSSIBLE(三源>0) > AUTHORITY_INPUTS_ACTIONABLE(已输出最小清单≥11项 + 每源阈值，有效完成)` first-match 已落盘，`proxy_missing` 保持 `missing/null`，`shadow` 不升级为 `composable`，`仅缺 H_min 而未输出清单与阈值不得判 ACTIONABLE` 已验。
- [ ] `scripts/v59_security_budget_authority_closure.py` 为 decoder-free 可运行脚本（`python scripts/v59_security_budget_authority_closure.py [--v57-json ...] [--out-json ...]`），`rg "decode_" 0 hits`、`rg "import.*decoder" 0 hits`，仅 `numpy/pandas`（可选 `pyarrow`），`py_compile` PASS，未创建 `run_01`，且 `V57-V58 m` 未改（`git diff -- src/ ==0` 且 `git diff -- openspec/changes/formal-ir-v5[4-8]/ ==0`）。
- [ ] `docs/research_cycles/V59P0/SECRET_KEY_BUDGET_AUTHORITY_REPORT.md` 已记录权威裁决（`PIE_secure` 仅 shadow/proxy，`IAB-chi ≠ H_min` 未授权）、`variable_table ≥11项`、`decomposition table` 三源独立、`break-even` 三档与 `0/5/10%` 阈值表、最小新增测量行动表、`overall` 终态与权威闭合声明，数据与 `json` 一致，结论不扩大为 `FER/阈值/SKR/晋升`，显式 `V57-V58 m 冻结` + `tag 已含不重复` + `三源分别不平均` + `proxy 不升级为 composable` + `missing → null`。
- [ ] 已推送新 `SHA` 并停留在 `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN`，未创建任何 `run_01` decoder 执行，不碰 `src//experiments//tools/` 与 `V54-V58` 既有变更，`git diff -- src/ ==0` 且 `rg "decode_" 0 hits`，`py_compile + 关键测试` PASS，推送后等待独立审核；返回 `Plan SHA / implementation SHA / 权威裁决 / 三源阈值 / 行动表 / 终态`，**不自动进入 `V60`**。

## Tasks

见 `tasks.md`（Phase A 逐函数权威裁决与 IAB-chi 追踪；Phase B 统一 ell 与 exact 变量表≥11项；Phase C 三档 break-even 与 0/5/10% 阈值；Phase D 四互斥终态 first-match；Phase E 脚本与校验与推送）。

## Lifecycle

`V58` 当前 `SECURITY_INPUTS_INCOMPLETE / DECODE_FORBIDDEN`（`HEAD 2340257d`, `m1 981/1024/1024, m2 424/451/516, leak 7089/7439/7764, n1024, tag64` 已固化但缺 `H_min`/composable 输入与阈值）；`V59` 本权威闭合 `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN`（仅 decoder-free 权威闭合，不实现 runner，不执行 decoder，不创建 `run_01`，不改码参，三源分别；乐观 floor 必给、shadow 描述、`composable:null`）；`V59` `AUTHORITY_INPUTS_ACTIONABLE` 为**有效完成**（已输出最小清单与阈值）才算闭合，仅缺 `H_min` 不够；`V59` 推送后不自动进入 `V60`，需新 `OpenSpec` 与独立授权。
