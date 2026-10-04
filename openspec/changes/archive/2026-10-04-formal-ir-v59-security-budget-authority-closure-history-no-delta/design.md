# OpenSpec Design: formal-ir-v59-security-budget-authority-closure

**Lifecycle**: `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN` — decoder-free 安全预算权威闭合，主动闭合 V58 缺失输入并给出每源 `hmin_break_even`
**Cycle**: `V59P0` (security-budget-authority-closure), predecessor `V58` `2340257d` `SECURITY_INPUTS_INCOMPLETE`
**Branch**: `formal-ir-mainline` HEAD `2340257d` (需 `git fetch && git rev-parse HEAD == origin/formal-ir-mainline` 重核) data SHA `84d62779` (200ps legacy_v1 nearest 1024)
**Feasibility**: V57/V58 已披露 `m1 981/1024/1024, m2 424/451/516, leak 7089/7439/7764 bits/block (n=1024, GF32 5bits, tag64 已含)`；仓内既有 `tools/security_reports/_security_calibrated_common.py` 的 `DeltaFK/chi/IAB` 与 `round2` 审计的 `PIE_secure` 为候选权威；但 `PIE_secure` 是否为 composable、 `IAB-chi ≟ H_min` 是否等价需逐函数裁决，缺则 `composable:null` 不自填。
**Key judgement**: **V59 不是 decoder 优化，而是权威闭合**：在完全冻结 V57/V58 泄漏口径（`leak=5*m_total+64`，tag 不重复）与仓内有限密钥公式下，逐函数裁决 `PIE_secure` 为 shadow/proxy，追踪 `H_min` 缺口，统一 `ell =1024*hmin - leak_IR - leak_other - finite` 并给出可验证的 `hmin_break_even` 三档与最小新增测量清单；任何 `conservative ≤0` 立即止路，仅输出清单与阈值才算 `ACTIONABLE` 有效完成。

## 1. 科学问题与关键判断

> 在**完全冻结 V57/V58 方法与泄漏**（`m1/m2/m_total/leak 7089/7439/7764, n1024, GF32 5bits, tag64 L2-only 仅 total 计一次`）与**仓内既有有限密钥公式**下：**`V57 当前 m` 的 `ir_disclosure` 对应的 `hmin_break_even` 是多少？`PIE_secure = IAB - leak - chi_E - DeltaFK - post_sel` 是否被明确授权为 composable？若否，缺哪些最小测量才能使 `ell>0` 有 composable 意义？**

- **不变量**：`dimension 1024 / block_len 1024 symbols / bin_width 200ps / pairing nearest / legacy_v1 / GF32 poly37 / tag 64` 为名义不变量；V59 不改任一码参，仅做预算权威闭合。
- **止损性质**：纯 **decoder-free**，`rg "decode_" 0 hits`，`py_compile PASS`，`git diff -- src/ ==0` 且 `git diff -- openspec/changes/formal-ir-v5[4-8]/ ==0`；缺 composable 输入则 `composable:null`，`optimistic floor` 必给但不冒充 composable。
- **禁把 H/IAB/MAP 当 H_min**：`H(A|B)` (`V25/V57` 经验熵) 与 `IAB_est = dary_mutual_info_proxy(d, SER)` 与 `MAP_acc` 均为**代理**，未被声明为 `H_min^epsilon(A|E)`；借用即 `weak_proxy=true` 且封顶 `POSITIVE_POSSIBLE`，最高不升 `ACTIONABLE` 的 composable 区间。

## 2. 冻结语义 — V57/V58 与仓内公式零改

| 项 | 冻结值 | 来源 |
|---|---|---|
| n | 1024 symbols/block | V31/V57/V58 |
| log2 q | 5 (GF32) | GF2mField poly37 |
| tag | 64 bits/block, L2-only, 仅 total 计一次 | V28/V54/V57/V58 |
| V57/V58 m1 per source | 981 (1M) 1024 (1p5M) 1024 (2M) | `v57_channel_recharacterization.json` / `v58_secret_key_budget.json` |
| V57/V58 m2 per source | 424 / 451 / 516 | 同上 |
| V57/V58 m_total / leak_total | 1405/1475/1540, 7089/7439/7764 (=5*m_total+64) | 同上, per-layer ceil `m_i=min(1024,ceil(1.3*n*H_i/5))` |
| 候选权威公式 | `chi_from_visibility(d, vis) = h2((1-vis)/2)+e*log2(d-1)`；`DeltaFK=4*sqrt(log2(2/eps_sec)/n_eff)+2*log2(2/eps_cor)/n_eff`；`dary_mutual_info(d,ser)=log2 d+(1-e)log(1-e)+e log(e/(d-1))`；`PIE_secure = IAB - leak - chi_E - DeltaFK - post_sel` | `tools/security_reports/` 只读 |
| 禁止 | 任何 `decode_*` / `construct_*` / 信道估计器改造；改 `m1/m2/leak`；自创 `H_min` 或把 `H/IAB/MAP` 当 `H_min` | 本变更 |

## 3. 权威裁决模型 — 逐函数只读追踪（Phase A）

### 3.1 输入与单位先验

- 每源 `block =1024 symbols`，`GF32 log2q=5`，故 `raw block bits =1024*10=10240` 仅作 `hmin` 上界校验（`hmin ≤10 bits/symbol`）。
- 单位统一到 **`bits/block`**：`hmin_per_symbol *1024 = bits/block`；`leak_EC` 已是 `bits/block`；`DeltaFK` 在 `_security_calibrated_common.delta_fk_calibrated` 为 **`bits/pair (= bits/symbol)`**，需 `*n_eff` 或 `*1024` 转块时显式记录；`chi_E` 为 `bits/pair`；`post_sel` 为 `bits/pair` 或无量纲分数取决于文件；调查阶段必须显式记录权威单位。
- `GF32 5bits` 校验：`leak_without_tag =5*(m1+m2)` (`1M 7025, 1p5M 7375, 2M 7700`)，`tag=64` 单加；`leak_total 7089/7439/7764` 双校验。

### 3.2 权威文件逐函数定位（只读，禁止自创）

```python
# 候选权威 A: tools/security_reports/_security_calibrated_common.py
# - def chi_from_visibility(dimension, franson_visibility) -> float   #  L92-99: chi_E = h2(e_p)+e_p*log2(d-1), unit bits/pair, global vis=0.95
# - def dary_mutual_info_proxy(dimension, ser) -> float                # L102-117: IAB_est = log2 d + (1-e)log(1-e)+e log(e/(d-1)), proxy NOT H_min
# - def calibrated_effective_sample_count(row) -> (n_eff, meta)       # L246-284: n_eff = n_pairs * layer_fraction * clean_fraction
# - def delta_fk_calibrated(n_eff_pairs, eps_sec, eps_cor) -> float   # L288-297: 4*sqrt(log2(2/eps_sec)/n_eff)+2*log2(2/eps_cor)/n_eff, bits/pair
# => 结论预研：均为 calibrated shadow，无 H_min/composable 声明

# 候选权威 B: tools/security_reports/build_actual_ir_finite_key_shadow.py
# - def _build_shadow(frame, franson_visibility, eps_sec, eps_cor)    # L27-88: leak = IAB - best_hard_PIE (surrogate), PIE_secure = max(0, IAB - leak - chi_E - DeltaFK), tag surrogate_from_best_hard_pie_gap
# - model_tag = "strict_zhong_like_calibrated_actual_ir"  # L24:显式 zhong_like calibrated, summary L116: "not full niu_2016 composable proof"
# => 结论预研：仅 zhong_like calibrated shadow，leak 为 surrogate，非 composable

# 候选权威 C: tools/security_reports/round2_build_finite_key_audit_table.py
# - 主循环 per row: leak_bits = total_leak_ec_bits / n_pairs_actual if actual else leak_ec_bits_or_proxy (surrogate), L75-81
# - DeltaFK = 4*sqrt(.../n_eff)+2*log2(...)/n_eff, n_eff = n_pairs * layer_frac * accepted_frame_frac * block_success_rate, L114-122
# - post_sel = accepted_frame_fraction, chi_E = chi_from_visibility, L124-125
# => 结论预研：audit 表显式区分 actual vs surrogate，仍为 calibrated，无 H_min

# 候选权威 D: tools/security_reports/round2_build_actual_ir_finite_key_shadow.py
# - PIE_secure_actual_ir = max(0, IAB_est - leak_EC_actual_bits - chi_E_calibrated - DeltaFK_calibrated - post_selection_correction).fillna(0))  # L31-38
# - model_tag = "strict_zhong_like_actual_ir_finite_key_calibrated"  # L48
# => 结论预研：同 B，仅 strict_zhong_like calibrated，含 post_sel 惩罚，仍非 niu_2016 composable

# 关联权威 E: tools/security_reports/round3_build_proof_gap_matrix.py (缺口矩阵)
# - ROWS 显式列出: per_point_franson_pe_chain: missing, frame_level_post_selection: partial, decoy_state_PE: missing, conjugate_basis_stats: missing, protocol_specific_composable_constants: missing  # L12-23
# => 结论预研：composable 所需观测缺失，需新测量

# 关联权威 F: tools/security_reports/build_beta_baseline_finite_key_shadow.py
# - 仅 literature beta baseline 对比，BETA_BASELINE_ROLE = comparison_only, NIU_2016_STATUS = not_supported_by_current_observables  # build_security_calibrated_summary L101
```

- 调查产出 `formula_authority[] = {file, function, lines, expr, unit, authority: shadow/proxy/missing/composable}`；`h_min_source = MISSING`（仓内 `rg H_min|min_entropy` 无权威定义，`IAB_est` 未声明为 `H_min` 代理）。
- **决策**：`PIE_secure` 在全部文件中均被标记为 `strict_zhong_like_calibrated` / `calibrated penalty, not full niu_2016 composable proof` / `proof_gap_matrix missing`，故裁决为 **仅 shadow/proxy，不可升为 composable**；`IAB - chi_E` 未在任何文件中被**明确声明等价于 `H_min^epsilon(A|E)`**，故标记 `proxy_missing`，`H/IAB/MAP` 当 `H_min` 显式禁止。

### 3.3 预算重算（Phase B+C，逐源机械，tag 不重复）

```
# 对每源 s ∈ {1M,1p5M,2M}:
m1_s, m2_s, m_total_s = V57/V58 冻值
leak_without_tag_s = 5*(m1_s+m2_s)  # 7025 / 7375 / 7700
tag_s = 64
leak_total_s = leak_without_tag_s + tag_s  # 校验 == 7089/7439/7764
leak_IR_s = leak_total_s  # bits/block, 已含 tag, 不重复扣除

# 统一预算（decoder-free，仓内权威为准，缺 composable 则 null）
ell_s(hmin_lower) = 1024 * hmin_lower - leak_IR_s - leak_other_s - finite_s
  where hmin_lower ∈ [0,10] bits/symbol,  search for ell==0 => hmin_break_even
        leak_other_s = PE_penalty_s + EV_s + auth_s + ...  # per source, optimistic=0
        finite_s = DeltaFK_calibrated_s * n_eff_s? 或直接 bits/block (需单位已验)

# optimistic floor (必给，other=0 finite=0):
hmin_break_even_floor_s = leak_total_s / 1024  # 1M 6.9238, 1p5M 7.2637, 2M 7.5820 bits/symbol
  + margin thresholds:
    h_0% = leak/1024
    h_5% = leak/(1024*0.95)
    h_10% = leak/(1024*0.90)
  # 1M: 6.9238 / 7.2882 / 7.6931 ; 1p5M: 7.2637/7.6460/8.0707 ; 2M: 7.5820/7.9811/8.4245

# shadow descriptive interval (proxy, 不升级):
hmin_break_even_shadow_s ∈ [ (leak+other_shadow_low+finite_low)/1024,
                              (leak+other_shadow_high+finite_high)/1024 ]
  where other_shadow/finite_shadow 来自仓内 calibrated shadow 的描述性传播 (vis 区间, n_eff, post_sel)

# composable-authority interval:
hmin_break_even_composable_s = null  # 缺决定性 composable 输入（smooth H_min, phase-error 样本, EV 证明等）显式 null
```

- `leak_total ==5*m_total+64` 双校验，失败则 `EVIDENCE_INVALID`。
- `other/finite` 若权威区间缺失则 `other=0 / finite=0` 仅作 optimistic floor 占位，但 `composable` 保持 `null` 不填 0。
- 三源分别，不平均。

### 3.4 敏感性边界（Phase D，仅区间传播）

- 对仓内 authoritative 区间参数 `eps_sec ∈ [low, high]`, `eps_cor`, `vis ∈ [vis_low, vis_high]`, `n_eff` 仅传播 `optimistic_floor` 与 `shadow` 两端；`composable` 保持 `null`；**禁止网格调参**。
- 若无区间则 `shadow_low == shadow_high == optimistic_floor` 且 `interval_tag = "no_composable_interval"`，显式报告不假装 composable 区间。

## 4. 分解表与校准/验证注册表（预注册，exact 变量表 ≥11 项）

### 4.1 exact 变量表 `variable_table`（symbol / meaning / unit / source / authority / decoder-free? / minimal_new_measurement）

| symbol | meaning | unit | source (file:line) | authority | decoder-free? | minimal_new_measurement |
|---|---|---|---|---|---|---|
| `H_min^eps(A|E)` | smooth min-entropy 下界 per symbol | bits/symbol | MISSING (无仓内权威) | missing | no | 新 PE 样本估计 `H_min`，需 `n_PE` ≥? |
| `e_ph` | phase-error 率 | 无量纲 | `round3_proof_gap missing` | missing | no | 新 conjugate-basis / decoy-state 观测 |
| `vis` | Franson visibility | 无量纲 | `_security_calibrated_common:chi_from_visibility` | shadow proxy (`global 0.95`) | yes (proxy) | 每点/每 loss 实测 `vis` 链 |
| `n_PE` | PE sample 大小 | count | `calibrated_effective_sample_count` | shadow proxy | yes | 新 PE 采集 `n_PE` |
| `eps_sec` | secrecy | 无量纲 | `build_actual_ir_shadow: eps_sec=1e-10` | shadow calibrated | yes | 协议固定或新 composable 常数 |
| `eps_cor` | correctness | 无量纲 | 同上 `eps_cor=1e-10` + `epsilon_EC_bound` | shadow / verif-only | yes | 新 `epsilon_EC` 证明 |
| `DeltaFK` | finite-size 惩罚 | bits/pair | `_security_calibrated_common:delta_fk_calibrated` | shadow calibrated | yes | 需 `n_eff` 实测 |
| `EV` | error-verification 泄漏 | bits/block | `round2 audit: verification_bits` | shadow / missing | partial | 新 `verification transcript` |
| `post_sel` | post-selection 修正 | bits/pair | `round2: accepted_frame_fraction` | shadow surrogate | yes (surrogate) | 严谨 `accepted/rejected` 计数 |
| `auth` | authentication 泄漏 | bits/block | `proof_gap missing` | missing | no | 新 `auth` 观测 |
| `IAB` | Alice-Bob 互信息代理 | bits/pair | `_security_calibrated_common:dary_mutual_info_proxy` | proxy (H≠H_min) | yes | 禁当 `H_min` |
| `leak_IR` | IR 泄漏 | bits/block | `V57/V58 leak_total` | frozen (actual) | yes | 已冻，无新增 |
| ... | ... | ... | ... | ... | ... | ... |

- `authority` 列显式 `composable / shadow / proxy / missing`，`missing → composable:null`。
- `decoder-free?` 列显式 `yes/no/partial`，`no` 者需新测量。

### 4.2 公式溯源注册

- `v59_secret_key_budget_authority.json: formula_authority[{file,function,lines,expr,unit,authority}], variable_table[≥11], decomposition[per_source], break_even{optimistic_floor, shadow:[low,high], composable:null}, verdict`。
- `manifest` 含 `HEAD 2340257d, data_sha 84d62779, script_sha, formula_authority_sha, zero_decode_verified, mutual_exclusion_verified`。

## 5. 三源总体判定与后继门（first-match 四选一，按优先级互斥）

```
if not unit_ok or not formula_self_consistent or leak !=5*m+64 or tag_repeated:
    overall = EVIDENCE_INVALID  # 硬完整性：单位不一致、tag 重复、m 不自洽、H/IAB 当 H_min
elif any(ell_conservative_s <= 0 for s in sources)  # optimistic floor 的 ell≤0 即无正余量
    overall = AUTHORITY_CLOSED_NO_POSITIVE_MARGIN  # 任一源保守 ≤0 立即止路，需新 H_min 或降 leak
elif all(ell_conservative_s > 0 for s in sources) and composable_missing:
    # optimistic floor >0 但 composable null，仅 shadow 描述性正余量
    if not variable_table_ge11 or not break_even_has_floor:
        overall = EVIDENCE_INVALID  # 仅缺 H_min 而未输出清单与阈值不得判 ACTIONABLE
    else:
        overall = AUTHORITY_CLOSED_POSITIVE_POSSIBLE  # 三源>0 但仅 proxy 描述，需补最小清单才 ACTIONABLE
elif variable_table_ge11 and break_even_has_floor and break_even_has_shadow and composable_is_null_explicit:
    overall = AUTHORITY_INPUTS_ACTIONABLE  # 已输出最小清单≥11项 + 每源三档阈值，有效完成（即使不完整）
else:
    overall = AUTHORITY_INPUTS_ACTIONABLE  # 默认有效完成，若已给 floor+shadow+null

# 且：H/IAB/MAP 当 H_min 则 EVIDENCE_INVALID；proxy 升 composable 则 EVIDENCE_INVALID；missing 不为 null 则 EVIDENCE_INVALID
```

- 仅 `AUTHORITY_INPUTS_ACTIONABLE` 为**有效完成**（已输出最小清单与阈值），其余 `CLOSED_NO_MARGIN / CLOSED_POSITIVE_POSSIBLE` 均为权威闭合但需行动；`EVIDENCE_INVALID` 硬失败。
- **仅缺 `H_min` 不够**：即使 `H_min_missing` 已识别，若未同时输出 `variable_table ≥11项` + `per_source break_even floor/shadow/null + 0/5/10% 阈值` + `minimal 新测量行动表`，不得判 `ACTIONABLE`。
- V57 `H 2.3 vs NLL 30` 分裂已归档为 `ESTIMATOR_UNDERSAMPLED`；V59 预算不改该结论，仅在新 `m` 上判断阈值。

## 6. 脚本与报告（decoder-free 守卫）

- **脚本 `scripts/v59_security_budget_authority_closure.py`** (decoder-free):
  ```
  python scripts/v59_security_budget_authority_closure.py \
    [--v57-json openspec/.../v57_channel_recharacterization.json] \
    [--v58-json openspec/.../v58_secret_key_budget.json] \
    [--out-json docs/research_cycles/V59P0/v59_secret_key_budget_authority.json] \
    [--report docs/research_cycles/V59P0/SECRET_KEY_BUDGET_AUTHORITY_REPORT.md] \
    [--csv docs/research_cycles/V59P0/v59_break_even.csv]
  → fetch/HEAD 自检 (若 HEAD != origin 则 warning) → A 权威逐函数扫描 + H_min/IAB-chi 追踪 → B variable_table≥11项 + decomposition → C break_even三档(optimistic floor/shadow/null + 0/5/10% margin) → D first-match 四终态互斥 → 输出 json/report/csv + 控制台摘要
  rg "decode_" 0 hits, 仅 numpy/pandas/pyarrow，py_compile PASS，不创建 run_01
  ```

- **报告 `SECRET_KEY_BUDGET_AUTHORITY_REPORT.md`**：`formula_authority` 段（文件+函数+行号+原文 `not full niu_2016`）、`variable_table ≥11项`、`decomposition table` 三源独立、`break_even` 三档与 `0/5/10%` 阈值表、`minimal 新增测量行动表`、`overall` 终态与权威闭合声明，数据与 `json` 一致，结论不扩大为 `FER/阈值/SKR/晋升`，显式 `V57-V58 m 冻结` + `tag 已含不重复` + `三源分别不平均` + `proxy 不升级` + `missing→null`。

- **守卫**：`git diff -- src/ ==0 && git diff -- experiments/ ==0 && git diff -- tools/ ==0 && git diff -- openspec/changes/formal-ir-v5[4-8]/ ==0`，`rg "decode_" 0 hits`，`rg "import.*decoder" 0 hits`，`py_compile` PASS，`pytest -p no:cacheprovider` 关键测试 PASS，`HEAD==origin` 已验，`run_01` 不存在，`mutual_exclusion` 已验，`composable:null` 已验。

## 7. 与 V57/V58 衔接

- `V57` `PREDICTIVE_MODEL_NOT_STABLE / DECODE_FORBIDDEN` 已固化 `m` 与泄漏；`V58` `SECURITY_INPUTS_INCOMPLETE` 已止损但未给阈值；V59 以 **decoder-free 权威闭合**补齐 `H_min` 缺口与 `hmin_break_even` 阈值，**未否定 V57/V58 终态**，仅在既有 `m` 上闭合权威与 actionable 清单。
- `AUTHORITY_INPUTS_ACTIONABLE` 为**有效完成**（即使 composable null），已满足 V59 目标；`AUTHORITY_CLOSED_NO_POSITIVE_MARGIN / POSITIVE_POSSIBLE` 为权威闭合但需补测量；`EVIDENCE_INVALID` 硬失败需修单位/代理。
- 后继 `V60` 需另起 `OpenSpec` 与独立授权，**本次不自动进入 `V60`**。

## 8. 自由裁量 D1-D7

- D1 `leak_without_tag=5*m_total`, `tag=64` 仅整型算术，不引新库
- D2 `H_min` 代理判定：`IAB_est/dary_mutual_info` 与 `H(A|B)` 均标 `proxy/missing`，不自创 `H_min`，`composable:null`
- D3 `finite_penalty` 单位以权威文件为准，缺 composable 则 `null`，不假设 `per-block` composable
- D4 `other_disclosure` 无权威则 `0` 并 `no_authority_other` 标签，仅 optimistic floor
- D5 三源分别，不平均，`margin 0/5/10%` 固定阈 `h_m = leak/(1024*(1-margin))`
- D6 不产生新矩阵/码参，仅预算与权威闭合，最简闭环
- D7 本变更为 `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN`，不产生 `run_01`，后继 `V60` 时才考虑低维/新测量

