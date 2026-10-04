# OpenSpec Design: formal-ir-v58-secret-key-budget-stoploss

**Lifecycle**: `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN` — decoder-free 密钥预算止损，不改 decoder/矩阵/信道估计器，三源独立止损门
**Cycle**: `V58P0` (secret-key-budget-stoploss), predecessor `V57` `777338e5` `PREDICTIVE_MODEL_NOT_STABLE`
**Branch**: `formal-ir-mainline` HEAD `337e3a79` (需 `git fetch && git rev-parse HEAD == origin/formal-ir-mainline` 重核) data SHA `84d62779` (200ps legacy_v1 nearest 1024)
**Feasibility**: V57 已披露 `m1 981/1024/1024, m2 424/451/516, leak 7089/7439/7764 bits/block (n=1024, GF32 5bits, tag64 已含)`；仓内既有 `tools/security_reports/_security_calibrated_common.py` 的 `DeltaFK` 与 `build_actual_ir_finite_key_shadow.py` 的 `PIE_secure = IAB - leak - chi_E - DeltaFK - post_sel` 为候选权威；但 `H_min^epsilon(A|E)` 是否显式且单位闭合需只读调查验证，缺则止损。
**Key judgement**: **V58 不是 decoder 优化，而是预算止损**：在完全冻结 V57 泄漏口径（`leak=5*m_total+64`，tag 不重复）与仓内有限密钥公式下，逐源机械判断 `ell` 正余量；任何 `conservative ≤0` 立即止路，仅三源保守充足且权威闭合才考虑低维分解后继，且仍不自动 decoder。

## 1. 科学问题与关键判断

> 在**完全冻结 V57 方法与泄漏**（`m1/m2/m_total/leak 7089/7439/7764, n1024, GF32 5bits, tag64 L2-only 仅 total 计一次`）与**仓内既有有限密钥公式**下：**V57 当前 `m` 的 `ir_disclosure` 是否已超出 `min_entropy_budget - other - finite` 的正余量？** 若任一源保守 `ell ≤0` 则止损；仅三源均 `ell>0 && margin≥0.10` 且 `H_min` 等权威输入闭合才考虑低维模型，且仍 `DECODE_FORBIDDEN`。

- **不变量**：`dimension 1024 / block_len 1024 symbols / bin_width 200ps / pairing nearest / legacy_v1 / GF32 poly37 / tag 64` 为名义不变量；V58 不改任一码参，仅做预算诊断。
- **止损性质**：纯 **decoder-free**，`rg "decode_" 0 hits`，`py_compile PASS`，`git diff -- src/ ==0` 等；缺决定性输入终态 `SECURITY_INPUTS_INCOMPLETE`（含 `DATA_INCOMPLETE`）而非自创公式强行算 `ell`。

## 2. 冻结语义 — V57 与仓内公式零改

| 项 | 冻结值 | 来源 |
|---|---|---|
| n | 1024 symbols/block | V31/V57 |
| log2 q | 5 (GF32) | GF2mField poly37 |
| tag | 64 bits/block, L2-only, 仅 total 计一次 | V28/V54/V57 |
| V57 m1 per source | 981 (1M) 1024 (1p5M) 1024 (2M) | V57 `v57_channel_recharacterization.json` |
| V57 m2 per source | 424 / 451 / 516 | 同上 |
| V57 m_total / leak_total | 1405/1475/1540, 7089/7439/7764 (=5*m_total+64) | 同上, per-layer ceil `m_i=min(1024,ceil(1.3*n*H_i/5))` |
| 候选权威公式 | `DeltaFK=4*sqrt(log2(2/eps_sec)/n_eff)+2*log2(2/eps_cor)/n_eff` ( `_security_calibrated_common.delta_fk_calibrated`)；`PIE_secure = IAB - leak - chi_E - DeltaFK - post_sel` (`round2_build_actual_ir_finite_key_shadow`)；`chi_E = h2((1-vis)/2)+...` | `tools/security_reports/` 只读 |
| 禁止 | 任何 `decode_*` / `construct_*` / 信道估计器改造；改 `m1/m2/leak`；自创 `H_min` | 本变更 |

## 3. 密钥预算模型（decoder-free，仓内权威为准，缺则 INCOMPLETE）

### 3.1 输入与单位

- 每源 `block =1024 symbols`，`GF32 log2q=5`，故 `raw block bits =1024*10?` 不直接用，仅校验 `leak_total =5*m_total+64` 的 `5` 来自 `log2 q`。
- 单位统一到 **`bits/block`**：`min_entropy_budget` 若为 `per-symbol` 则 `*1024` 转 `per-block`；`leak_EC` 已是 `per-block`；`DeltaFK * n_eff` 需确认是 `per-pair` 还是 `per-block`——调查阶段必须显式记录权威单位，若权威为 `bits per pair` 则 `* n` 转块。
- `GF32 5bits` 校验：`leak_without_tag =5*(m1+m2)` (`1M 7025, 1p5M 7375, 2M 7700`)，`tag=64` 单加。
- `H(A|B)` vs `H_min^epsilon(A|E)`：**禁止等同**；若仓内仅有 `H(A|B)` / `IAB_est` 而无 `H_min`，则标记 `weak_proxy=true` 且终态封顶 `POSITIVE_BUT_FRAGILE`，或若 `IAB_est` 未声明为 `H_min` 代理则直接 `SECURITY_INPUTS_INCOMPLETE`。

### 3.2 权威公式调查（Phase A，只读，禁止自创）

```python
# 候选权威 1: _security_calibrated_common.delta_fk_calibrated
# n_eff_pairs 需权威定义；若无明确 n_eff 对 V58 块的映射则记 incomplete
delta_fk = 4* sqrt(log2(2/eps_sec)/n_eff) + 2*log2(2/eps_cor)/n_eff  # bits per pair? 需查文件注释

# 候选权威 2: round2_build_actual_ir_finite_key_shadow._build_shadow / round2_build_finite_key_audit_table
# PIE_secure_actual_ir = IAB_est - leak_EC_actual_bits - chi_E_calibrated - DeltaFK_calibrated - post_selection_correction
# 其中 leak_EC_actual_bits = total_leak_ec_bits / n_pairs_actual  (per pair) vs 本 V58 的 per block 需单位换算
# chi_E 来自 franson_visibility, post_sel 来自 accepted_frame_fraction
# 若权威链要求 IAB_est 来自 dary_mutual_info_proxy (dimension, ser) 则需记录 ser 来源与 eps 预算
```

- 调查产出 `formula_authority = {delta_fk: {file, lines, expr, unit}, pie_secure: {file, lines, expr, unit}, h_min: {file, lines or "MISSING", proxy_flag}}`。
- `eps_sec/eps_cor/franson_visibility/IAB_est` 等若有仓内默认值（`1e-10` 等）或区间，记录区间 `[low, high]`；无则 `MISSING`。
- **决策**：若 `h_min` 无权威文件或无 `H_min` 到 `bits/block` 的闭合换算（`n_eff`, `epsilon` 预算缺失），则 `SECURITY_INPUTS_INCOMPLETE` 止损，不自创 `h_min = log2 d - leakage` 等近似。

### 3.3 预算重算（Phase C，逐源机械，tag 不重复）

```
# 对每源 s ∈ {1M,1p5M,2M}:
m1_s, m2_s, m_total_s = V57 冻值
leak_without_tag_s = 5*(m1_s+m2_s)  # 7025 / 7375 / 7700
tag_s = 64
leak_total_s = leak_without_tag_s + tag_s  # 校验 == V57 7089/7439/7764
ir_disclosure_s = leak_total_s  # bits/block, 已含 tag, 不重复扣除

# min_entropy_budget: 需 Phase A 权威 h_min_per_symbol 或 IAB_est per pair
# 若 h_min_per_symbol 权威： min_entropy_budget = 1024 * h_min_per_symbol
# 若 IAB_est per pair 权威且声明为 H_min 代理： min_entropy_budget = 1024 * IAB_est (需 weak_proxy 标签)
# 若 n_eff !=1024 则需按权威 n_eff 换算，缺则 INCOMPLETE

# other_disclosure: auth bits + PE penalty + ...  (权威区间，若无则 0 并显式 "no_authority_other=0")
# finite_penalty: DeltaFK * n? 或 DeltaFK_calibrated (需单位统一)；若权威为 per pair 则 finite_per_block = n_eff * delta_fk 或直接 delta_fk*n?

ell_before_IR_s = min_entropy_budget_s - other_disclosure_s - finite_penalty_s
ell_final_s    = ell_before_IR_s - ir_disclosure_s
per_pair_s     = ell_final_s / 1024  # bits/symbol 诊断
margin_ratio_s = ell_final_s / min_entropy_budget_s  if min_entropy_budget_s>0 else nan
```

- `leak_total ==5*m_total+64` 双校验，失败则 `EVIDENCE_INVALID`。
- `other/finite` 若权威区间缺失则 `other=0 / finite=0` 仅作 `no_interval` 占位但报告 `incomplete_flag` 并可能触发 `SECURITY_INPUTS_INCOMPLETE` 分支（见 §5）。
- 三源分别，不平均。

### 3.4 敏感性边界（Phase D，仅区间传播）

- 对仓内权威区间参数 `eps_sec ∈ [low, high]`, `eps_cor`, `vis`, `IAB_est±delta` 仅传播 `conservative`（`h_min low, leak high, other high, finite high`）与 `optimistic` 两端；**禁止网格调参**。
- 若无区间则 `conservative == optimistic` 且 `interval_tag = "no_interval"`。
- 报告 `ell_conservative / ell_optimistic / margin_conservative / margin_optimistic / cross_zero_flag = (conservative<=0 < optimistic)`.

## 4. 分解表与校准/验证注册表（预注册，零重叠可机械校验）

### 4.1 分解表（decomposition table）

| source | min_entropy_budget (bits/block) | ell_before_IR | leak_without_tag (5*m) | tag64 | other | finite | ell_final | per_pair | margin_ratio | weak_proxy | interval |
|---|---|---|---|---|---|---|---|

- `weak_proxy` 列显式 `true/false`（`H(A|B)` 当 `H_min` 则 `true` 且终态封顶 `FRAGILE`）。
- `interval` 列显式 `conservative/optimistic/no_interval`。

### 4.2 公式溯源注册

- `v58_secret_key_budget.json: formula_authority {file, line, expr, unit}`，`inputs: {n=1024, log2q=5, tag=64, m1/m2/leak 三源冻值, h_min_source, eps_sec, eps_cor, vis, iab}`，`decomposition: [per_source rows]`，`sensitivity: {conservative, optimistic}`，`verdict`。
- `manifest` 含 `HEAD 337e3a79, data_sha 84d62779, script_sha, formula_authority_sha, zero_decode_verified`.

## 5. 三源总体判定与后继门（first-match 五选一，按优先级互斥）

```
if not unit_ok or not formula_self_consistent or leak !=5*m+64:
    overall = EVIDENCE_INVALID  # 硬完整性：单位不一致、tag 重复、m 不自洽
elif h_min_missing or unit_missing or finite_coeff_missing or security_inputs_incomplete:
    overall = SECURITY_INPUTS_INCOMPLETE  # 缺决定性输入，含 DATA_INCOMPLETE 子类，不进预算，止损
elif any(ell_conservative_s <= 0 for s in sources):
    overall = NO_POSITIVE_KEY_MARGIN  # 任一源保守 ≤0 立即止路，需后继低维或重估计
elif any(weak_proxy_s) or any(margin_conservative_s < 0.10 for s in sources) or any(cross_zero_s):
    overall = POSITIVE_BUT_FRAGILE  # >0但余量薄 (<10%) 或保守乐观跨0 或弱代理，止损观望，不自动低维
else: # 三源均 conservative>0 && margin≥0.10 && !weak_proxy && !incomplete && unit_ok
    overall = POSITIVE_KEY_MARGIN  # 全部权威闭合且余量充足，才允后继低维模型（仍不自动 decoder，需新 OpenSpec + DECODE_FORBIDDEN）
```

- **仅 `POSITIVE_KEY_MARGIN` 才允后继**：后继为**低维分解（U1/U2 separate）或 1D 假设下的保守预算**，需另起 `OpenSpec`，独立 `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN` + 双重 review，**不自动 decoder**。
- `POSITIVE_BUT_FRAGILE` / `NO_POSITIVE_KEY_MARGIN` / `SECURITY_INPUTS_INCOMPLETE` / `EVIDENCE_INVALID` 均显式“**不允许 decoder / 不进入后继低维 decoder**”，需扩样本、换 `H_min` 权威、或低维重预算但仍止损观望。
- V57 前版 `H vs NLL` 分裂已归档为 `ESTIMATOR_UNDERSAMPLED`；V58 预算不改该结论，仅在新 `m` 上判断余量。

## 6. 脚本与报告（decoder-free 守卫）

- **脚本 `scripts/v58_secret_key_budget_stoploss.py`** (decoder-free):
  ```
  python scripts/v58_secret_key_budget_stoploss.py \
    [--v57-json openspec/changes/formal-ir-v57-channel-recharacterization/v57_channel_recharacterization.json] \
    [--out-json docs/research_cycles/V58P0/v58_secret_key_budget.json] \
    [--report docs/research_cycles/V58P0/SECRET_KEY_BUDGET_REPORT.md] \
    [--csv docs/research_cycles/V58P0/v58_secret_key_budget.csv]
  → fetch/HEAD 自检 (若 HEAD != origin 则 warning) → A 权威公式 rg 定位 + H_min 决策 → B 分解表单位/tag/GF32/H_min 校验 → C 三源 ell 重算 → D 区间传播 → E first-match 终态 → 输出 json/report/csv + 控制台摘要
  rg "decode_" 0 hits, 仅 numpy/pandas/pyarrow，py_compile PASS，不创建 run_01
  ```

- **报告 `SECRET_KEY_BUDGET_REPORT.md`**：`formula_authority` 段、`decomposition table` 三源独立、`ell` 明细与 `per_pair/margin`、`sensitivity` 上下界、`overall` 终态与止损/放行声明，数据与 `json` 一致，结论不扩大为 `FER/阈值/SKR/晋升`，显式 `V57 m 冻结` + `tag 已含不重复` + `三源分别不平均` + `弱代理封顶`。

- **守卫**：`git diff -- src/ ==0 && git diff -- experiments/ ==0 && git diff -- tools/ ==0`，`rg "decode_" 0 hits`，`rg "import.*decoder" 0 hits`，`py_compile` PASS，`pytest -p no:cacheprovider` 关键测试 PASS，`HEAD==origin` 已验，`run_01` 不存在。

## 7. 与 V57/V59 衔接

- `V57` `PREDICTIVE_MODEL_NOT_STABLE / DECODE_FORBIDDEN` 已固化 `m` 与泄漏；V58 以 **decoder-free 预算止损**补齐密钥余量证据，**未否定 V57 终态**，仅在既有 `m` 上判断是否已无正余量。
- 仅 `POSITIVE_KEY_MARGIN` 允许后继低维模型（`1D / U1U2` 分解下的保守 `H_min` 重算），后继需新 `TEST`（与 V57 `Cal/Val` 零重叠）与独立 `EXECUTE_AUTH`，双重 review 后方可 `ARCHIVED`；其余 `FAIL` 类终态停留 `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN` 修预算或扩 `H_min` 权威，不进 decoder。

## 8. 自由裁量 D1-D7

- D1 `leak_without_tag=5*m_total`, `tag=64` 仅整型算术，不引新库
- D2 `H_min` 代理判定：若仓内仅有 `IAB_est` 则 `weak_proxy=true` 且封顶 `FRAGILE`，不自创 `H_min`
- D3 `finite_penalty` 单位以权威文件为准，缺则 `SECURITY_INPUTS_INCOMPLETE`，不假设 `per-block`
- D4 `other_disclosure` 无权威则 `0` 并 `no_authority_other` 标签，仅预算诊断
- D5 三源分别，不平均，`margin 0.10` 固定阈
- D6 不产生新矩阵/码参，仅预算与判定，最简闭环
- D7 本变更为 `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN`，不产生 `run_01`，后继 `V59` 时才考虑低维
