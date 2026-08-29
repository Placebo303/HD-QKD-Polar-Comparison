# OpenSpec Design: formal-ir-v61-security-measurement-specification

**Lifecycle**: `PLAN_CANDIDATE / DECODE_FORBIDDEN / MEASUREMENT_SPEC_ONLY` — 仅定义新实验最小采集规范，不改码/不跑 decoder/不进 V62
**Cycle**: `V61P0` (security-measurement-specification), predecessor `V60` `formal-ir-v60-composable-security-input-readiness` `9f1fb02c` 已固化 `V60_DATA_NOT_READY / ell=null`，当前起点 `7b476f62368a410722ab1e0d65ea2709e423d848`（`R61` 修订起点）
**Branch**: `formal-ir-mainline` HEAD `7b476f62368a410722ab1e0d65ea2709e423d848` (需 `git fetch && git rev-parse HEAD == origin/formal-ir-mainline` 重核) data SHA `84d62779` (200ps legacy_v1 nearest 1024)
**Feasibility**: `V57/V60` 已披露 `m1 981/1024/1024, m2 424/451/516, leak 7089/7439/7764 bits/block (n=1024, GF32 5bits, tag64 已含)`；仓内 `tools/security_reports/` 的 `DeltaFK/chi/IAB` 与 `round3_build_proof_gap_matrix` 的 `per_point_franson_pe_chain missing / conjugate_basis_stats missing` 为 `V60` 缺口权威；`V61` 不补数值，仅把缺口固化为可勾选的 10 类采集字段与唯一的 decoder-free 验收公式；`R61` 两项最小修订：`R61-01 dependency-aware readiness` + `R61-02 verification 口径冻结`。
**Key judgement**: **V61 不是密钥计算，也不是数据就绪度重判，而是输入采集规范**：在完全冻结 `V57/V60` 泄漏口径（`leak=5*m_total+64`，tag 不重复，`R61-02` 冻结 `leak_other = max(0,actual-64)`、`epsilon` 概率不入 `bits`）下，定义下一轮物理实验的 10 类字段与如何机械判定三源 `10% H_min` 门槛，`R61-01` 将“全部 ready”改为 dependency-aware（`required_core` 全 ready + 所选定理条件依赖 ready，与定理无关的 `visibility/decoy` 允许 `N/A` 不阻塞 `V62_OPEN`）；任何 `composable theorem` 或 `decisive core PE` 缺失则 `V62 PENDING`，禁旧数据 `shadow` 填充与 decoder，缺口用 `null` 保留。

## 1. 科学问题与关键判断

> 在**完全冻结 V57/V60 方法与泄漏**（`m1/m2/m_total/leak 7089/7439/7764, n1024, GF32 5bits, tag64 L2-only 仅 total 计一次`）与**仓内 V60 缺口**下：**下一轮实验最少需要记录哪些字段，才能使 composable 密钥 `ell =1024*hmin_lower - leak_IR - leak_other - finite` 可被机械计算并逐源判定 `margin≥10%`？**

- **不变量**：`dimension 1024 / block_len 1024 symbols / bin_width 200ps / pairing nearest / legacy_v1 / GF32 poly37 / tag 64` 为名义不变量；`V61` 不改任一码参，仅定义采集。
- **止损性质**：纯 **decoder-free**，`rg "decode_" 0 hits`，`py_compile PASS`，`git diff -- src/ ==0` 且 `git diff -- openspec/changes/formal-ir-v5[5-9]/ ==0 && git diff -- openspec/changes/formal-ir-v60*/ ==0`（除本变更外零改）；缺 `composable theorem` 或 `decisive core PE`（`required_core` 中 `e_ph/conjugate/n_PE`）则 `V62 PENDING`，条件依赖 `visibility/decoy` `N/A` 不阻塞，`ell=null`，`optimistic floor` 必给但不冒充 composable 余量；`R61-02` verification 已冻 `leak_IR含tag / leak_other=max(0,actual-64) / epsilon不入bits`。
- **禁把 H/IAB/MAP/visibility 当 H_min**：`H(A|B)` (`V25/V57` 经验熵) 与 `IAB_est = dary_mutual_info_proxy(d, SER)` 与 `MAP_acc` 与 `visibility=0.95 shadow` 均为**代理/描述**，未被声明为 `H_min^epsilon(A|E)` 下界；新实验若仍仅有代理则 `hmin_lower_authority=proxy/missing → V62` 不可算。
- **仅新数据 READY 才算 ell**：`V60` 的 `hmin_break_even` 三档为阈值锚点，`V61` 的 `ell` 为新数据就绪后的 composable 余量；二者分离 — 阈值描述永远可给，`ell` 仅新数据 `READY` 时权威可算。

## 2. 冻结语义 — V57/V60 与仓内记录零改

| 项 | 冻结值 | 来源 |
|---|---|---|
| n | 1024 symbols/block | V31/V57/V60 |
| log2 q | 5 (GF32) | GF2mField poly37 |
| tag | 64 bits/block, L2-only, 仅 total 计一次 | V28/V54/V57/V60 |
| V57 m1 per source | 981 (1M) 1024 (1p5M) 1024 (2M) | `v57_channel_recharacterization.json` |
| V57 m2 per source | 424 / 451 / 516 | 同上 |
| V57/V60 m_total / leak_total | 1405/1475/1540, 7089/7439/7764 (=5*m_total+64) | 同上, per-layer ceil `m_i=min(1024,ceil(1.3*n*H_i/5))` |
| 候选权威公式（仅作验收，不自创） | `chi_from_visibility(d, vis) = h2((1-vis)/2)+e*log2(d-1)`；`DeltaFK=4*sqrt(log2(2/eps_sec)/n_eff)+2*log2(2/eps_cor)/n_eff`；`dary_mutual_info(d,ser)=log2 d+(1-e)log(1-e)+e log(e/(d-1))`；`ell =1024*hmin - leak_IR - leak_other - finite` | `tools/security_reports/` 只读 |
| 禁止 | 任何 `decode_* / construct_* / 信道估计器` 改造；改 `m1/m2/leak`；自创 `H_min` 或把 `H/IAB/MAP/visibility` 当 `H_min`；跑 decoder；重跑 `V55`；用旧数据伪造 `PE`；无新数据进 `V62` | 本变更 |

## 3. 最小采集规范 — 10 类字段定义

### 3.1 单位与换算先验

- 每源 `block =1024 symbols`，`GF32 log2q=5`，故 `raw block bits =1024*10=10240` 仅作 `hmin` 上界校验（`hmin ≤10 bits/symbol`）。
- 单位统一到 **`bits/block`**：`hmin_per_symbol *1024 = bits/block`；`leak_EC` 已是 `bits/block`；`DeltaFK` 在 `_security_calibrated_common.delta_fk_calibrated` 为 **`bits/pair (= bits/symbol)`**，需 `*n_eff` 或 `*1024` 转块时显式记录；`chi_E` 为 `bits/pair`；`post_sel` 为 `bits/pair` 或无量纲分数取决于新实验权威声明；规范阶段必须要求新实验对每项显式声明单位。
- `GF32 5bits` 校验：`leak_without_tag =5*(m1+m2)` (`1M 7025, 1p5M 7375, 2M 7700`)，`tag=64` 单加；`leak_total 7089/7439/7764` 双校验。
- **关键新增**：新实验必须提供 `H_min^epsilon(A|E)` 是否被**明确声明为下界**（文件行号+表达式+`eps` 预算+定理绑定），`IAB-chi ≟ H_min` 未声明则 `proxy_missing`，`V62` 不可算。

### 3.2 10 类字段逐项定义（R61-01 dependency-aware，R61-02 verification 冻结）

| # | 采集项 | 字段 `symbol` | 含义 `meaning` | 单位 `unit` | 依赖分类 `readiness_class` | 新实验来源要求 `source` | 缺失后果 |
|---|---|---|---|---|---|---|---|
| 1 | 协议/安全定理及适用假设 | `theorem_id, assumptions[], domain` | composable 定理声明与攻击模型/适用域 | — | `required_core` | 论文/报告段落+行号+表达式+假设链（`Renner/Niu/Lim` 等），声明是否依赖 `visibility/decoy` | `composable_theorem_missing → V62 PENDING` |
| 2 | conjugate-basis/phase-error 观测 | `e_ph, conjugate_basis_stats, decoy_chain[conditional]` | 共轭基实测 + phase-error 率估计链；`decoy_chain` 仅定理依赖 `decoy-state` 时适用 | 无量纲 | `e_ph+conjugate: required_core`；`decoy_chain: required_if_theorem_applicable`（否则 `not_applicable_with_theorem_reason`） | 新实验 `X/Z` 基统计 + `e_ph` 估计原文，`decoy_chain` 若适用则 `decoy 强度/统计链` + 定理依据 | `decisive_core PE missing → V62 PENDING`，禁 `SER/vis` 代理；`decoy` 无关定理时 `N/A` 不阻塞 |
| 3 | n_PE 与抽样规则 | `n_PE, sampling_rule (p_Z/p_X, random, seed)` | PE 样本大小与随机抽样规则 | count / 无量纲 | `required_core` | 新实验 `n_PE` 计数值 + `p_Z/p_X` + 无放回/有放回 + PE 帧标记可重放链 | `n_PE` 仅 `shadow` 则 `missing`，需权威 `n_PE` |
| 4 | visibility 逐源区间 | `[vis_low,vis_high], vis_source, cal_chain` | 每源每 `loss/session` Franson visibility 区间与校准链 | 无量纲 | `required_if_theorem_applicable`（定理以 `chi_from_visibility` 绑定 `vis→chi_E` 时为 `required`，否则 `not_applicable_with_theorem_reason`） | 新实验每点实测 `vis` 区间（非 `global 0.95 shadow`）+ 校准链来源；不适用时以定理行号为据记 `N/A` | 适用时无实测链则 `missing`；不适用时 `N/A` 不阻塞 `V62_OPEN` |
| 5 | eps_sec/eps_cor 分配 | `eps_sec, eps_cor, eps_PE, eps_PA, eps_EC` | secrecy/correctness 总预算及分解（含 `epsilon_EV/EC` 概率） | 无量纲 | `required_core` | 协议固定 + `DeltaFK/EV/auth` 的 `eps` 一致性声明；`epsilon_EV/EC` 仅作概率，未映射不得转 `bits` | 分解不一致则 `EVIDENCE_INVALID`；`epsilon` 不入 `bits` |
| 6 | verification/authentication 泄漏 | `leak_verif (actual_verification_bits, epsilon_EC), leak_auth` | 验证界与认证开销；`leak_IR` 已含 `tag64`，`leak_other` 仅计 `max(0,actual-64)` | `bits/block` | `required_core`（其中 `actual_verification_bits` 必记录以算 `max(0,actual-64)`） | 新实验 `verification transcript: actual_verification_bits` + `epsilon_EC` 概率 + `auth bits` 计费，明确 `tag64` 已含于 `leak_IR` 不重复扣除；`epsilon` 概率不直接计 `bits` | `missing` 则 `V62` 需补；重复扣 `tag` 或 `epsilon→bits` 无据则 `SPEC_INVALID` |
| 7 | finite-size correction | `DeltaFK_formula, n_eff, coeff_authority` | finite-size 惩罚权威系数与有效计数 | `bits/pair`→`bits/block` | `required_core` | 新实验 `n_eff` 实测 + `DeltaFK` 系数权威（与 `eps` 预算一致）；`epsilon` 仅概率 | 仅 `shadow` 则 `missing` |
| 8 | post-selection/有效帧计数 | `accepted_frame_fraction, n_block, post_sel_penalty` | post-selection 策略与有效块计数 | 无量纲/`bits` | `required_core` | 新实验 `accepted/rejected` 计数 + `N_pairs→n_block` 映射 + 弃帧规则 | `shadow surrogate` 则 `missing` |
| 9 | 单位/时间戳/session/source 绑定 | `unit_map, session_id, source_id, delay_used_ps, block_id, pairing` | 单位换算与时空绑定 | `bits/*` | `required_core` | 新实验每 `block` 的 `session/source/delay/pairing legacy_v1 nearest 200ps` 四元绑定 | 绑定缺失则 `EVIDENCE_INVALID` |
| 10 | 验收公式输入 | `hmin_lower, leak_other, finite, ell_formula` | `ell` 计算的 `H_min` 下界与 `other/finite` 输入；`leak_other` 含 `max(0,actual-64)+auth+...` | `bits/symbol`/`bits/block` | `required_core` | 新实验权威 `hmin_lower` 下界（`bits/symbol`）+ `leak_other/finite` 分解（`bits/block`，`leak_other` 按 `R61-02` 口径），`ell` 公式显式；`epsilon` 概率不入 `leak_other/finite` | `hmin_lower` 无 composable 声明则 `null` |

- 新实验每项记录 `authority: composable|shadow|proxy|missing` 与 `readiness: required_core | required_if_theorem_applicable | not_applicable_with_theorem_reason | missing` 四类（`R61-01`），`h_min_source = MISSING` 若无权威下界声明，`IAB-chi ≟ H_min` 未声明则 `proxy_missing`；`required_if_theorem_applicable` 仅当 `theorem_id.assumptions` 显式依赖该字段时才要求 `ready`，否则以 `not_applicable_with_theorem_reason: "theorem <id> line:expr declares not applicable"` 记录且不阻塞。
- **V60 衔接**：`V60` 已判 `phase-error/conjugate missing + n_PE shadow + visibility proxy + theorem missing`；`V61` 把每项的 `minimal_new_measurement` 固化为上述可勾选字段，并以 dependency-aware 判定 `V62_OPEN`（见 §3.4）。
- **R61-02 verification 冻结**：`leak_IR_s = leak_total_s = 5*m_total+64` 已含 `tag64`；`leak_other_s = max(0, actual_verification_bits - 64) + leak_auth_s + ...` bits/block；`epsilon_EV/EC` 为概率预算，未经定理显式 `bits` 映射不得直接加进 `leak_other_s/finite_s`；三边界测试见 §3.3 末。

### 3.3 验收公式冻结（decoder-free，三源独立，tag 不重复，R61-02 verification 冻结）

```
# 对每源 s ∈ {1M,1p5M,2M}:
m1_s, m2_s, m_total_s = V57 冻值
leak_without_tag_s = 5*(m1_s+m2_s)  # 7025 / 7375 / 7700
tag_s = 64
leak_total_s = leak_without_tag_s + tag_s  # 校验 == 7089/7439/7764
leak_IR_s = leak_total_s  # bits/block, 已含 tag, 不重复扣除, R61-02 冻结
actual_verification_bits_s = 新实验 verification transcript 实测值 bits/block (≥64 预期)
leak_verification_extra_s = max(0, actual_verification_bits_s - 64)  # R61-02: 仅超出部分入 leak_other

# 统一验收（仅新数据 READY 可算）
if V61_NEW_DATA_READY:  # R61-01: required_core 全 ready + 所选定理条件依赖 ready 且 composable 明确, R61-02 口径已验
    ell_s(hmin_lower) = 1024 * hmin_lower - leak_IR_s - leak_other_s - finite_s
      where hmin_lower ∈ [0,10] bits/symbol,  search for ell==0 => hmin_break_even_new
            leak_other_s = leak_verification_extra_s + PE_penalty_s + auth_s + ...  # per source, authoritative
            finite_s = DeltaFK_new_s + ...  # bits/block, 单位已验, epsilon 概率未映射不得入
            # R61-02: epsilon_EV/EC 为概率，未经定理显式 bits 映射不得直接加进 leak_other/finite
else:
    ell_s = null  # 未 READY 时保持 null，不以 floor 冒充

# 阈值锚点（必给，仅门限描述，不升密钥）:
hmin_break_even_floor_s = leak_total_s / 1024  # 1M 6.9238, 1p5M 7.2637, 2M 7.5820 bits/symbol
  + margin thresholds (other=0 finite=0 占位):
    h_0% = leak/1024 = 6.9238 / 7.2637 / 7.5820
    h_5% = leak/(1024*0.95) = 7.2882 / 7.6460 / 7.9811
    h_10% = leak/(1024*0.90) = 7.6931 / 8.0707 / 8.4245  # 必给，落盘校验 h*1024==leak/(1-margin)

# 非 READY 时 hmin_break_even_composable = null (JSON null) 而非 0
hmin_break_even_composable_s = null  if not V61_NEW_DATA_READY else hmin_break_even_new_s
log2 d =10 上界校验: hmin <10
```

- `leak_total ==5*m_total+64` 双校验，失败则 `EVIDENCE_INVALID`；`R61-02` 三边界断言必过：`tag64-only: actual==64 → leak_verification_extra==0`、`extra-verification: actual==128 → leak_verification_extra==64`、`epsilon-not-bits: 仅 epsilon 概率无 bits 映射时 leak_other/finite 不含 epsilon`。
- 三源分别，不平均；`other/finite` 若权威区间缺失则 `0` 仅作 floor 锚点，但 `composable` 保持 `null` 不填 0。
- `R61-02` 显式：`leak_IR 已含 tag64`、`leak_other = max(0, actual_verification_bits-64) + ...` bits/block 仅计超出部分、`epsilon_EV/EC` 保留为概率未经定理显式 bits 映射不得直接加进 `leak_other/finite`。

### 3.4 V62 门禁（first-match，R61-01 dependency-aware，仅新数据 READY 才进数值）

```
# R61-01: required_core 全 ready + 所选 theorem 的条件依赖 ready；无关 visibility/decoy 允许 N/A 不阻塞
if V61_spec_incomplete or unit_tag_mismatch or IAB/H/MAP/vis_as_Hmin or proxy_upgraded or verification_caliber_mismatch_R61_02:
    V61 = SPEC_INVALID  # 规范本身不自洽（含 R61-02 口径：leak_IR 已含 tag + leak_other=max(0,actual-64) + epsilon 不入 bits 未验）
elif composable_theorem_missing_in_new_data or decisive_core_PE_missing_in_new_data:  # decisive_core = required_core 中 e_ph/conjugate/n_PE
    V62 = PENDING  # 缺决定性 core 输入，需新实验补采集，ell=null，不算数值（条件依赖无关项 N/A 不判此分支）
elif not all_required_core_ready_in_new_data or not conditional_deps_ready_for_selected_theorem or not hmin_lower_composable_in_new_data:
    V62 = PENDING  # 规范已就绪但 core 或所选定理条件依赖仍不足，需清单闭合；无关的 visibility/decoy N/A 不计入此判
elif new_data_all_required_core_ready and conditional_deps_ready_for_selected_theorem and hmin_lower_composable and break_even_floor_done and verification_caliber_ok_R61_02:
    V62 = OPEN  # 唯一允许另起 V62 的 OpenSpec + 独立授权进入数值计算（无关 visibility/decoy N/A 不阻塞）
else:
    V62 = PENDING
# 且：H/IAB/MAP/vis 当 H_min 则 SPEC_INVALID；proxy 升 composable 则 SPEC_INVALID；旧数据伪造 PE 则 EVIDENCE_INVALID
# 且：非 READY 时 ell_* 保持 null，不以 floor/shadow 填；仅新数据 READY 时逐源 hmin_lower 比 floor/10% 判定 ell>0
# 且：R61-02 边界：tag64-only / extra-verification / epsilon-not-bits 三断言必过
```

- `V61_SPEC_READY` 指本规范 10 类 + 验收公式已落盘且 `readiness` 四类语义自洽（含条件依赖 `not_applicable_with_theorem_reason` 带定理依据）；`V62 OPEN` 指新实验数据 `required_core` 全 ready + 所选定理条件依赖 ready + `hmin_lower` 可算 `ell`，与定理无关的 `visibility/decoy` 以 `N/A` 不阻塞。
- **旧数据禁伪造**：若新实验记录的 `e_ph/n_PE/conjugate` 源自旧 `V55` 数据重算而无新物理观测，则 `EVIDENCE_INVALID`，`V62` 保持 `PENDING`。
- **R61-01 例**：定理 `Lim 2014` / `Renner` 若声明不依赖 Franson `visibility`，则 `visibility` 全字段以 `not_applicable_with_theorem_reason: "theorem <id> line:expr exclaims vis not used"` 记录为 `N/A`，`V62_OPEN` 不要求 `vis ready`；若定理为 `visibility→chi` 家族，则 `visibility` 按 `required_if_theorem_applicable` 要求 `ready`，缺则 `PENDING`。

## 4. 采集 Schema 与模板（预注册）

### 4.1 JSON Schema `v61_measurement_schema.json` 骨架（R61-01/02）

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "V61 HD-QKD security measurement minimal schema",
  "type": "object",
  "required": ["provenance","per_source","acceptance_formula"],
  "properties": {
    "provenance": {"head":"7b476f62368a410722ab1e0d65ea2709e423d848","data_sha":"84d62779","spec_version":"V61P0-R61"},
    "protocol_theorem": {"theorem_id":"string","assumptions":"array","domain":"string","source":"file:line:expr","visibility_dependence":"bool","decoy_dependence":"bool"},
    "conjugate_phase_error": {"e_ph":"number [0,1]","conjugate_basis_stats":"object","decoy_chain":"string|null","readiness":"required_core|required_if_theorem_applicable|not_applicable_with_theorem_reason|missing","authority":"composable|shadow|proxy|missing"},
    "n_PE_sampling": {"n_PE":"integer","p_Z":"number","p_X":"number","sampling_rule":"random_without_replacement|...","seed_or_counter":"string","readiness":"required_core|missing"},
    "visibility_per_source": {"readiness":"required_if_theorem_applicable|not_applicable_with_theorem_reason|missing","per_source":[{"source":"1M|1p5M|2M","vis_low":"number","vis_high":"number","vis_source":"string","cal_chain":"string","not_applicable_reason":"string|null"}]},
    "eps_allocation": {"eps_sec":"number","eps_cor":"number","eps_PE":"number","eps_PA":"number","eps_EC":"number","eps_EV":"number","note":"epsilon are probabilities, not bits unless theorem maps explicitly"},
    "leak_verif_auth": {"actual_verification_bits_per_block":"number","leak_verification_extra_bits_per_block":"number = max(0,actual-64)","leak_auth_bits_per_block":"number","tag_included_in_IR":"bool = true","epsilon_EC_probability":"number","epsilon_not_bits_assert":"bool"},
    "finite_size": {"DeltaFK_formula":"string","n_eff":"integer","coeff_authority":"string","unit":"bits/pair|bits/block","epsilon_not_bits_assert":"bool"},
    "post_selection": {"accepted_frame_fraction":"number","n_block":"integer","post_sel_penalty_bits_per_block":"number|null"},
    "unit_timestamp_binding": {"unit_map":"object","bindings":[{"session_id":"string","source_id":"string","delay_used_ps":"integer","block_id":"integer","pairing":"legacy_v1 nearest 200ps"}]},
    "acceptance_formula_inputs": {"hmin_lower_bits_per_symbol":"number|null","leak_other_bits_per_block":"number|null = max(0,actual-64)+auth+...","finite_bits_per_block":"number|null","ell_formula":"ell=1024*hmin_lower - leak_IR - leak_other - finite","verification_caliber":"leak_IR contains tag64, leak_other=max(0,actual-64), epsilon not bits"}
  }
}
```
- `readiness` 四类为 `required_core | required_if_theorem_applicable | not_applicable_with_theorem_reason | missing`，`required_if_theorem_applicable` 仅当 `protocol_theorem` 声明该字段为定理依赖时才要求 `ready`。

### 4.2 CSV 模板 `v61_minimal_measurement_template.csv` 列

`source, field, symbol, meaning, unit, required_class, authority, example_value, source_trace, readiness_detail`
- `required_class ∈ {required_core, required_if_theorem_applicable, not_applicable_with_theorem_reason, missing}`（`R61-01`）
- `required_core`（`theorem_id / e_ph+conjugate / n_PE / eps / actual_verification_bits+leak_auth+epsilon(not-bits) / finite / post_selection / binding / acceptance`）必 `ready` 否则 `V62 PENDING`
- `required_if_theorem_applicable`（`visibility` 全项、`decoy_chain`）仅当 `protocol_theorem` 声明依赖时必 `ready`，否则 `not_applicable_with_theorem_reason` 带定理行号为据记 `N/A` 且不阻塞 `V62_OPEN`

至少 10 类覆盖；`V62_OPEN` 判定为 `required_core` 全 `ready` + 所选定理条件依赖 `ready`，无关的 `visibility/decoy` `N/A` 不阻塞。

### 4.3 清单 `v61_minimal_new_measurement_checklist.csv` 优先级

按 `composable theorem > decisive PE (e_ph/conjugate/n_PE) > visibility chain > eps/finite > EV/auth/post_sel > units/binding` 排序，每行 `priority, item, missing_reason, minimal_new_measurement, required_sample_or_proof, acceptance_criterion, depends_on`。

## 5. 三源阈值与分解表（预注册，与 V60 一致作锚点）

- `1M: floor 6.9238 / 5% 7.2882 / 10% 7.6931`
- `1p5M: 7.2637 / 7.6460 / 8.0707`
- `2M: 7.5820 / 7.9811 / 8.4245`
- `log2 d=10` 上界校验，三源独立不平均；`leak_total ==5*m_total+64` 双校验，`GF32 5bits` 显式，`tag` 不重复。

## 6. 脚本与报告（decoder-free 守卫）

- **脚本 `scripts/v61_measurement_spec_check.py`** (decoder-free, 可选):
  ```
  python scripts/v61_measurement_spec_check.py \
    [--schema docs/research_cycles/V61P0/v61_measurement_schema.json] \
    [--template docs/research_cycles/V61P0/v61_minimal_measurement_template.csv] \
    [--thresholds] \
  → 校验 10类覆盖 + 单位显式 + 三源阈值锚点 h*1024==leak/(1-margin) + tag不重复 + proxy不升级 + R61-02 三边界(tag64-only/extra/epsilon-not-bits)
  rg "decode_" 0 hits, 仅 numpy/pandas/pyarrow，py_compile PASS，不创建 run_01，不进 V62
  ```

- **报告 `V61_SECURITY_MEASUREMENT_SPEC_REPORT.md`**：`V60 缺口溯源`、`10类字段定义表（含 required_core / required_if_theorem_applicable / not_applicable_with_theorem_reason）`、`单位/时间戳/session/source 绑定`、`验收公式与 break_even 阈值表`（`6.9238/7.2637/7.5820` floor 与 `7.6931/8.0707/8.4245` 10% 锚点，`R61-02` 口径 `leak_IR含tag / leak_other=max(0,actual-64) / epsilon不入bits`）、`V62 门禁（dependency-aware）`、`最小新增测量优先级清单`，数据与 `json/csv` 一致，显式 `V57-V60 m/leak 冻结` + `tag 已含不重复 / leak_other=max(0,actual-64) / epsilon不入bits` + `三源分别不平均` + `proxy 不升级` + `missing→null` + `仅新数据 READY 算 ell` + `V62 PENDING`。

- **守卫**：`git diff -- src/ ==0 && git diff -- experiments/ ==0 && git diff -- tools/ ==0 && git diff -- openspec/changes/formal-ir-v5[5-9]/ ==0 && git diff -- openspec/changes/formal-ir-v60*/ ==0`（除本变更外零改），`rg "decode_" 0 hits`，`rg "import.*decoder" 0 hits`，`py_compile` PASS，`pytest -p no:cacheprovider` 关键测试 PASS，`HEAD==origin` 已验，`run_01` 不存在，`V62` 未触发已验。

## 7. 与 V60 衔接与 V62 边界（R61-01/02）

- `V60` `V60_DATA_NOT_READY` 已判定现有数据仓无 composable 资格（`theorem missing + decisive PE missing → ell=null`）；`V61` 以 **最小采集规范**把 `V60` 的 `minimal_new_measurement` 可执行化，**未否定 V60 终态**，仅使下一轮实验可被机械验收；`R61-01` 细化 `V62_OPEN` 为 dependency-aware，`R61-02` 冻结 verification 口径。
- `V61_SPEC_READY` 为**规范可勾选**（即使新数据仍缺，清单已闭合，`R61-01` 四类语义自洽）；`V62 OPEN` 为新数据 `required_core` 全 ready + 所选定理条件依赖 ready + `hmin_lower` 权威可算（无关 `visibility/decoy` `N/A` 不阻塞），`R61-02` 三边界已过。`V61` 推送后不自动进入 `V62`，需新 `OpenSpec` 与独立授权，**本次普通推送新 Plan SHA 后停止于 PLAN_CANDIDATE / DECODE_FORBIDDEN**。

## 8. 自由裁量 D1-D7

- D1 `leak_without_tag=5*m_total`, `tag=64` 仅整型算术，不引新库；阈值仅除法 `leak/1024` 与 `/(1-margin)`。
- D2 `H_min` 代理判定：`IAB_est/dary_mutual_info` 与 `H(A|B)` 与 `MAP` 与 `visibility` 均 `proxy/missing`，不自创 `H_min`，`composable:null`。
- D3 `finite_penalty` 单位以新实验权威声明为准，缺 composable 则 `null`，不假设 `per-block` composable。
- D4 `other_disclosure` 无权威则 `0` 仅作 floor 锚点占位，但 `V62` 保持 `PENDING` 不算 `ell`。
- D5 三源分别，不平均，`margin 0/5/10%` 固定阈 `h_m = leak/(1024*(1-margin))`。
- D6 不产生新矩阵/码参，仅规范与阈值，最简闭环。
- D7 本变更为 `PLAN_CANDIDATE / DECODE_FORBIDDEN / MEASUREMENT_SPEC_ONLY`，不产生 `run_01`，`V62` 数值后继需 `新 OpenSpec + 独立授权 + 新数据`。
