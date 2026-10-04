# OpenSpec Proposal: formal-ir-v58-secret-key-budget-stoploss

**Status**: `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN` — decoder-free 密钥预算止损，不改 decoder/矩阵/信道估计器，仅做预算诊断
**Domain**: Formal IR / V58 secret-key budget stoploss (V57 唯一后继, V57 PREDECESSOR HEAD `337e3a79` 待 fetch 验证 HEAD==origin)
**Change ID**: `formal-ir-v58-secret-key-budget-stoploss`
**Cycle ID**: `V58P0` (secret-key-budget-stoploss), predecessor `V57` `formal-ir-v57-channel-recharacterization` (HEAD `777338e5` 已固化 `PREDICTIVE_MODEL_NOT_STABLE`)
**Branch**: `formal-ir-mainline`
**HEAD**: `337e3a79` (起点，实施前以 `git fetch && git rev-parse HEAD == origin/formal-ir-mainline` 重核为准；不一致则阻塞)
**Data SHA**: `84d62779` (`84d62779603e62de50ded5182ed65b65d3dc6084`, `d=1024 bw=200ps pairing=nearest rule=legacy_v1` 同 V57，不改)
**Lifecycle**: `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN` — 仅 decoder-free 预算止损诊断，不产生 `run_01` decoder 执行，不改 `H1/Lane C/H_inc/Δ/decoder 90/1.0/poly37 / V57 m`
**Method frozen**: V57 披露完全冻结，仅作输入（重算报告不写入码，禁止改 `m1/m2`）

> ponytail lite: 本变更仅 4 OpenSpec 工件 + 1 只读预算脚本 + 2 报告/JSON + 1 紧凑CSV；无 decoder、无矩阵、无新依赖（`numpy/pandas/pyarrow` 已装），最短科学路径。laziest alternative: 若仓内无权威 H_min/formula 则直接 `SECURITY_INPUTS_INCOMPLETE` 止损，无需自创公式或有限尺寸网格。

> **研究方向保持**：V54 在 `2026-01-21` 域 `43/45` 方法有效性保持；V55 `0/90` 已定位跨 session 域不兼容；V56/V57 已完成诊断与信道重表征（V57 终态 `PREDICTIVE_MODEL_NOT_STABLE` decoder 禁用）；V58 仅将 V57 已接受 `m1/m2 leak` 带入仓内既有有限密钥/PA 公式逐源判断正余量，不改码族架构。

## Goal

以最短 decoder-free 路径完成 **V57 三新 session 密钥预算止损**，将已接受 `m1/m2 leak` 带入仓内权威有限密钥/PA 公式逐源机械判断正余量，满足 **三源独立、标签不重复、单位一致、不跨源平均** 硬门槛，仅全部权威闭合且保守正余量充足才允后续低维模型（仍不自动 decoder）。

### 冻结 V57 披露（每 block 1024 符号，64-bit tag 已含不得重复扣除，仅预算诊断）

| source | m1 | m2 | m_total | leak_total (=5*m_total+64) bits/block | 备注 |
|---|---|---|---|---|---|
| 1M | 981 | 424 | 1405 | 7089 | GF32 5bits/symbol, tag 计入总量 |
| 1p5M | 1024 | 451 | 1475 | 7439 | m1 饱和 FULL_DISCLOSURE_LAYER |
| 2M | 1024 | 516 | 1540 | 7764 | m1 饱和 FULL_DISCLOSURE_LAYER |

- `leak_without_tag = 5*(m1+m2)`，`tag=64` 单次计入；脚本需校验 `leak_total == 5*m_total+64` 且 `m_total == m1+m2`。
- 三源 `block_len 1024 symbols`，`log2 q =5 (GF32)`，`total bits per block =1024*?` 仅作单位校验。

### 工作阶段（decoder-free，全冻）

**A 只读公式调查**：在仓内定位权威 `secret-key length / PA / finite-key` 公式实现（`tools/security_reports/_security_calibrated_common.py` / `build_actual_ir_finite_key_shadow.py` / `round2_build_finite_key_audit_table.py` 等），明确 `H_min^epsilon(A|E)` / `PE penalty` / `finite-key` / `auth` / `EC leakage` 的 **单位（bits/block vs bits/symbol vs bits/pair）** 与公式分解，禁止自创公式；缺决定性输入（无 `H_min` 或 `IAB_est` 未声明为 `H_min` 代理、或有限项系数无权威区间）则终态 `SECURITY_INPUTS_INCOMPLETE` / `DATA_INCOMPLETE` 止损。

**B 单位与重复扣除审计**：建立 `decomposition table` 逐源检查 `tag` 不重复、GF32 `5 bits/symbol`、**不把 `H(A|B)` 当 `H_min`**、不跨 source 平均，单位统一到 `bits/block (n=1024)`。

**C 三源机械重算**：逐源 `ell_final = min_entropy_budget - ir_disclosure - other_disclosure - finite_penalty`，报告 `ell_before_IR / leak_without_tag 5*(m1+m2) / tag64 / other_disclosure / finite_penalty / ell_final / per_pair (ell_final/1024) / margin_ratio (ell_final / min_entropy_budget)`；三源独立，不平均。

**D 敏感性边界**：仅对仓内权威区间参数上下界传播（`eps_sec/eps_cor/franson_visibility/IAB_est` 等若有区间），不得网格调参；报告 `conservative / optimistic` 两端。

**E 终态 first-match**（按优先级互斥）：`EVIDENCE_INVALID` > `SECURITY_INPUTS_INCOMPLETE` > `NO_POSITIVE_KEY_MARGIN`（任一 `conservative ≤0` 止路） > `POSITIVE_BUT_FRAGILE`（>0 但 `margin<0.10` 或 保守乐观跨 0 或 弱代理） > `POSITIVE_KEY_MARGIN`（三源 `conservative>0 && margin≥0.10` 且全部权威闭合才允后继低维模型，仍不自动 decoder）。

仅 `POSITIVE_KEY_MARGIN` 才允另起后继（低维 decomposition）且仍需独立 `OpenSpec + DECODE_FORBIDDEN`；其余一律止损不进 decoder。

## Non-Goals

- 不运行任何 `decode_*` / `construct_*` / 信道估计器（`rg "decode_" 0 hits`, `rg "import.*decoder" 0 hits`）；不改 `H1 16×1024 / Lane C / H_inc1/2 / Δ8+8 / decoder 90/1.0 poly37 / V57 m1/m2` 任一冻结量；不新增矩阵。
- 不改写/覆盖 V57 三新 session 已接受 `m1/m2/leak`（仅只读输入）；不改 `V25` `184/190/192` 历史值。
- 不自创 `H_min / finite-key` 公式；缺权威输入不造安全参数（`eps_sec/eps_cor/visibility` 仅用仓内既有或区间传播，无则 `INCOMPLETE`）。
- 不创建正式 `run_01` decoder 执行；不进入 decoder TEST；不宣称 `FER / SKR / 阈值 / 晋升`。
- 不做 `bin_width/dimension/pairing/mapping/frame anchor` 或 `eps` 网格搜索；敏感性仅区间上下界传播。
- 不以总体平均替代三源分别判定；不把 `H(A|B)` 当 `H_min`；不重复扣除 `tag 64`。
- 不改 `src/ / experiments/ / tools/` 基线代码（`git diff -- src/ ==0` 且 `git diff -- experiments/ ==0` 且 `git diff -- tools/ ==0`）。

## Scope

1. **冻结输入零改**：`n=1024, GF32 log2q=5, tag=64, V57 m1/m2/leak` 三源冻结，`data SHA 84d62779` 同 V57，`pairing nearest legacy_v1` 单点，仅只读。
2. **Phase A 公式调查（只读）**：仓库内 `rg "DeltaFK|chi_E|PIE_secure|IAB_est|_security_calibrated_common"` 定位权威公式文件，记录 `formula_authority = {file, line, expression}`，明确 `H_min^epsilon(A|E)` 来源（若无则标记 `weak_proxy` + `SECURITY_INPUTS_INCOMPLETE` 分支），`PE / finite / auth / EC` 各自单位与是否已含 tag，链式分解 `|H - H1 - H2|` 与 `leak =5*m_total+64` 双校验，缺决定性输入终态 `SECURITY_INPUTS_INCOMPLETE`（`DATA_INCOMPLETE` 子类）。
3. **Phase B 单位审计**：构建 `decomposition_table` 逐源校验 `leak_without_tag =5*(m1+m2)`, `tag64` 单计，`GF32 5bits` 换算 `bits/block = bits/symbol *1024`，**不把 `H(A|B)` 当 `H_min`**（若用 `H(A|B)` 需显式 `weak_proxy` 标签且降级为 `POSITIVE_BUT_FRAGILE` 封顶），不跨 source 平均，`m_total == m1+m2` 且 `leak_total ==5*m_total+64`。
4. **Phase C 机械重算**：逐源 `ell_final = min_entropy_budget - ir_disclosure - other_disclosure - finite_penalty`，其中 `min_entropy_budget = n * h_min_per_symbol`（若 `h_min` 为 per-symbol）或直接 `bits/block`，`ir_disclosure = leak_total`（已含 tag），`other_disclosure = auth + PE + ...`（权威区间），`finite_penalty = DeltaFK + ...`；报告 `ell_before_IR (=min_entropy - other - finite)` 与 `ell_final` 及 `per_pair = ell_final/1024`, `margin_ratio = ell_final / min_entropy_budget`。
5. **Phase D 敏感性边界**：仅对仓内权威区间参数 `[low, high]` 做 `conservative`（`h_min low, leak high, finite high, other high`）与 `optimistic` 两端传播，不得网格；若无区间则 `conservative == optimistic` 并显式 `no_interval`。
6. **Phase E 终态判定**：first-match 五选一（见 Goal E），`EVIDENCE_INVALID` 最高优先（单位/公式自洽失败），次为 `SECURITY_INPUTS_INCOMPLETE`（缺 H_min/缺单位/缺有限项权威），次为 `NO_POSITIVE_KEY_MARGIN`（任一 `conservative_ell ≤0`），次为 `POSITIVE_BUT_FRAGILE`（>0 但 `margin<0.10` 或 保守乐观跨 0 或 `weak_proxy`），末为 `POSITIVE_KEY_MARGIN`（三源均 `conservative_ell>0 && margin≥0.10 && !weak_proxy && !incomplete` 才允后继低维模型，仍 `DECODE_FORBIDDEN` 需另起 OpenSpec）。
7. **脚本与报告交付（DECODE_FORBIDDEN）**：`scripts/v58_secret_key_budget_stoploss.py`（decoder-free, `rg "decode_" 0 hits`, `py_compile PASS`），输出 `docs/research_cycles/V58P0/SECRET_KEY_BUDGET_REPORT.md` + `v58_secret_key_budget.json` + 紧凑CSV（`source,ell_before_IR,leak_without_tag,tag64,other,finite,ell_final,per_pair,margin_ratio,conservative,optimistic,gate`），未创建 `run_01`，已推送新 SHA 并停留 `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN`，等待独立审核。

## Impact Scope

- **新增（本变更最小）**：`openspec/changes/formal-ir-v58-secret-key-budget-stoploss/` 下 4 工件 `proposal.md/design.md/tasks.md/specs/spec.md` + decoder-free 脚本 `scripts/v58_secret_key_budget_stoploss.py` (`rg "decode_" 0 hits`, `py_compile PASS`, 只读预算) + 报告 `docs/research_cycles/V58P0/SECRET_KEY_BUDGET_REPORT.md` + `v58_secret_key_budget.json` (per_source + overall terminal) + 紧凑CSV + `SECRET_KEY_BUDGET_REPORT.md` 内 `decomposition table` 与 `sensitivity` 章节。
- **只读依赖**：`openspec/changes/formal-ir-v57-channel-recharacterization/v57_channel_recharacterization.json`（V57 m1/m2/leak，三源），`tools/security_reports/_security_calibrated_common.py` / `build_actual_ir_finite_key_shadow.py` / `round2_build_actual_ir_finite_key_shadow.py` / `round2_build_finite_key_audit_table.py`（权威 finite-key/PIE 公式，仅参考不改），`comparison_bench/outputs_comparison/v55_intake_20260828`（仅作 n=1024 单位校验，不跑 decoder）。
- **不修改**：任何既有 `spec/代码/测试/输出`（除本目录 + `scripts/` + `docs/research_cycles/V58P0/` 外）、`V38–V57` 输出、`src//experiments//tools/`（`git diff -- src/ ==0` 等），**不改 `V57` m，不创建 `run_01` decoder 执行，零码参**。

## Acceptance Criteria

- [ ] `proposal/design/tasks/specs/spec.md` 齐全一致，`lifecycle DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN`，`HEAD 337e3a79` + `branch formal-ir-mainline` + `data SHA 84d62779` 已绑定，显式声明 decoder-free、零 decoder、三源分别、tag 不重复、仅权威公式、缺输入则 `SECURITY_INPUTS_INCOMPLETE`。
- [ ] **Phase A 公式调查可复现**：仓库内权威 `secret-key length / PA / finite-key` 公式文件与行号已落盘 `formula_authority`（含 `H_min^epsilon(A|E)` / `PE` / `finite` / `auth` / `EC` 各自单位 `bits/block` vs `bits/symbol`），`leak =5*m_total+64` 且 `GF32 5bits` 已校验，禁止自创公式；缺决定性输入则 `SECURITY_INPUTS_INCOMPLETE` 已声明且脚本 `exit` 终态为 `DATA_INCOMPLETE` 子类。
- [ ] **Phase B 单位审计可复现**：`decomposition table` 三源独立已落盘，逐源 `leak_without_tag =5*(m1+m2)` (`1M 7025, 1p5M 7375, 2M 7700`) + `tag64` + `leak_total` (`7089/7439/7764`) 自洽，`H(A|B)` 不当 `H_min`（若借用需 `weak_proxy` 标签且封顶 `FRAGILE`），不跨 source 平均。
- [ ] **Phase C 机械重算可复现**：逐源 `ell_final = min_entropy_budget - ir_disclosure(7089/7439/7764) - other - finite` 已算，落盘 `ell_before_IR / leak_without_tag / tag64 / other / finite / ell_final / per_pair / margin_ratio` 与 `conservative/optimistic` 两端，三源分别，不平均。
- [ ] **Phase D 敏感性可复现**：仅对仓内权威区间参数上下界传播已验，不得网格调参；`margin 0.10` 与 `ell=0` 边界已验；报告含 `conservative vs optimistic` 表。
- [ ] **Phase E 终态互斥可复现**：`overall` 按 `EVIDENCE_INVALID > SECURITY_INPUTS_INCOMPLETE > NO_POSITIVE_KEY_MARGIN (任一 conservative ≤0) > POSITIVE_BUT_FRAGILE (>0但 margin<0.10或跨0或弱代理) > POSITIVE_KEY_MARGIN (三源 conservative>0 && margin≥0.10 && !weak_proxy && !incomplete)` 先匹配已落盘，**仅 `POSITIVE_KEY_MARGIN` 才允后继低维模型且仍不自动 decoder**，其余止损不进 decoder。
- [ ] `scripts/v58_secret_key_budget_stoploss.py` 为 decoder-free 可运行脚本（`python scripts/v58_secret_key_budget_stoploss.py [--v57-json ...] [--out ...]`），`rg "decode_" 0 hits`、`rg "import.*decoder" 0 hits`，仅 `numpy/pandas`（可选 `pyarrow`），`py_compile` PASS，未创建 `run_01`，且 `V57 m` 未改（`git diff -- src/ ==0` 等）。
- [ ] `docs/research_cycles/V58P0/SECRET_KEY_BUDGET_REPORT.md` 已记录权威公式文件、`decomposition table`、三源 `ell` 明细与 `per_pair/margin`、敏感性上下界、总体终态与 `V58` 止损/放行声明，数据与 `json` 一致，结论不扩大为 `FER/阈值/SKR/晋升`，显式 `V57 m` 冻结 + `tag 已含不重复` + `三源分别不平均` + `弱代理封顶`。
- [ ] 已推送新 `SHA` 并停留在 `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN`，未创建任何 `run_01` decoder 执行，不碰 `src//experiments//tools/`，`git diff -- src/ ==0` 且 `rg "decode_" 0 hits`，`py_compile + 关键测试` PASS，推送后等待独立审核。

## Tasks

见 `tasks.md`（Phase A 只读公式调查与 H_min 决策；Phase B 单位与重复扣除审计；Phase C 三源机械重算；Phase D 敏感性边界；Phase E 终态 first-match 与报告；脚本与校验与推送）。

## Lifecycle

`V57` 当前 `PREDICTIVE_MODEL_NOT_STABLE / DECODE_FORBIDDEN`（HEAD `777338e5` 已固化 `m1 981/1024/1024, m2 424/451/516, leak 7089/7439/7764, n1024, tag64`）；`V58` 本止损 `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN`（仅 decoder-free 预算诊断，不实现 runner，不执行 decoder，不创建 `run_01`，不改码参，三源分别）；`C` 中 `ell` 重算若 `NO_POSITIVE_KEY_MARGIN` 止路、`POSITIVE_BUT_FRAGILE` 止路、`POSITIVE_KEY_MARGIN` 才允另起后继低维模型（仍需新 OpenSpec + `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN` + 双重 review，**不自动 decoder**）；`SECURITY_INPUTS_INCOMPLETE` 立即止损。
