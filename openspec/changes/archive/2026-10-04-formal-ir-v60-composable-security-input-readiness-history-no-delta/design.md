# OpenSpec Design: formal-ir-v60-composable-security-input-readiness

**Lifecycle**: `PLAN_CANDIDATE / DECODE_FORBIDDEN` — composable secret-key 权威输入就绪度判定，不改码/不跑 decoder
**Cycle**: `V60P0` (composable-security-input-readiness), predecessor `V59` `formal-ir-v59-security-budget-authority-closure` `910d921b` 前 `SECURITY_INPUTS_ACTIONABLE`
**Branch**: `formal-ir-mainline` HEAD `910d921b` (需 `git fetch && git rev-parse HEAD == origin/formal-ir-mainline` 重核) data SHA `84d62779` (200ps legacy_v1 nearest 1024)
**Feasibility**: `V57/V59` 已披露 `m1 981/1024/1024, m2 424/451/516, leak 7089/7439/7764 bits/block (n=1024, GF32 5bits, tag64 已含)`；仓内既有 `tools/security_reports/_security_calibrated_common.py` 的 `DeltaFK/chi/IAB` 与 `round3_build_proof_gap_matrix.py` 的缺口矩阵为候选权威；但 `composable theorem` 是否明确、`phase-error/conjugate/n_PE/visibility` 是否有权威实测将决定 `READY` 与否，缺则 `null` 不自填、不跑 decoder。
**Key judgement**: **V60 不是密钥计算，而是输入就绪度判定**：在完全冻结 `V57/V59` 泄漏口径（`leak=5*m_total+64`，tag 不重复）与仓内公式下，先逐项裁决 10 项权威输入的 `composable` 就绪度，仅全部关键项 `ready` 才计算 `ell =1024*hmin_lower - leak_IR - leak_other - finite`，否则精确输出最小新增测量清单；任何 `composable theorem` 或 `decisive PE` 缺失立即停 `PARTIAL/DATA_NOT_READY`，禁 shadow 填充与 decoder，缺口用 `null` 保留。

## 1. 科学问题与关键判断

> 在**完全冻结 V57/V59 方法与泄漏**（`m1/m2/m_total/leak 7089/7439/7764, n1024, GF32 5bits, tag64 L2-only 仅 total 计一次`）与**仓内既有记录/数据**下：**现有数据/记录能否提供 composable secret-key 的权威输入（逐源 `H_min lower` lower bound 与有限码预算 `leak_other+finite`）？若不可，需新增哪些最小参数/测量才能闭合？**

- **不变量**：`dimension 1024 / block_len 1024 symbols / bin_width 200ps / pairing nearest / legacy_v1 / GF32 poly37 / tag 64` 为名义不变量；`V60` 不改任一码参，仅做就绪度判定。
- **止损性质**：纯 **decoder-free**，`rg "decode_" 0 hits`，`py_compile PASS`，`git diff -- src/ ==0` 且 `git diff -- openspec/changes/formal-ir-v5[4-9]/ ==0`；缺 `composable theorem` 或 `decisive PE` 则 `PARTIAL/DATA_NOT_READY`，`ell=null`，`optimistic floor` 必给但不冒充 composable 余量。
- **禁把 H/IAB/MAP/visibility 当 H_min**：`H(A|B)` (`V25/V57` 经验熵) 与 `IAB_est = dary_mutual_info_proxy(d, SER)` 与 `MAP_acc` 与 `visibility=0.95 shadow` 均为**代理/描述**，未被声明为 `H_min^epsilon(A|E)` 下界；借用即 `proxy` 且封顶非 `READY`，最高不升 `READY` 的密钥计算。
- **仅 READY 才算 ell**：`V59` 的 `hmin_break_even` 三档为预算门限，`V60` 的 `ell` 为 composable 密钥余量；二者分离 — 阈值描述永远可算，`ell` 仅 `READY` 权威可算。

## 2. 冻结语义 — V57/V59 与仓内记录零改

| 项 | 冻结值 | 来源 |
|---|---|---|
| n | 1024 symbols/block | V31/V57/V59 |
| log2 q | 5 (GF32) | GF2mField poly37 |
| tag | 64 bits/block, L2-only, 仅 total 计一次 | V28/V54/V57/V59 |
| V57 m1 per source | 981 (1M) 1024 (1p5M) 1024 (2M) | `v57_channel_recharacterization.json` |
| V57 m2 per source | 424 / 451 / 516 | 同上 |
| V57/V59 m_total / leak_total | 1405/1475/1540, 7089/7439/7764 (=5*m_total+64) | 同上, per-layer ceil `m_i=min(1024,ceil(1.3*n*H_i/5))` |
| 候选权威公式 | `chi_from_visibility(d, vis) = h2((1-vis)/2)+e*log2(d-1)`；`DeltaFK=4*sqrt(log2(2/eps_sec)/n_eff)+2*log2(2/eps_cor)/n_eff`；`dary_mutual_info(d,ser)=log2 d+(1-e)log(1-e)+e log(e/(d-1))`；`ell =1024*hmin - leak_IR - leak_other - finite` | `tools/security_reports/` 只读 |
| 禁止 | 任何 `decode_* / construct_* / 信道估计器` 改造；改 `m1/m2/leak`；自创 `H_min` 或把 `H/IAB/MAP/visibility` 当 `H_min`；跑 decoder；进 `V61` | 本变更 |

## 3. 就绪度裁决模型 — Phase A 10项逐项只读追踪

### 3.1 输入与单位先验

- 每源 `block =1024 symbols`，`GF32 log2q=5`，故 `raw block bits =1024*10=10240` 仅作 `hmin` 上界校验（`hmin ≤10 bits/symbol`）。
- 单位统一到 **`bits/block`**：`hmin_per_symbol *1024 = bits/block`；`leak_EC` 已是 `bits/block`；`DeltaFK` 在 `_security_calibrated_common.delta_fk_calibrated` 为 **`bits/pair (= bits/symbol)`**，需 `*n_eff` 或 `*1024` 转块时显式记录；`chi_E` 为 `bits/pair`；`post_sel` 为 `bits/pair` 或无量纲分数取决于文件；调查阶段必须显式记录权威单位。
- `GF32 5bits` 校验：`leak_without_tag =5*(m1+m2)` (`1M 7025, 1p5M 7375, 2M 7700`)，`tag=64` 单加；`leak_total 7089/7439/7764` 双校验。
- **关键追踪**：`H_min^epsilon(A|E)` 在仓内是否有**明确 composable 下界声明**（文件行号+表达式+`eps` 预算+适用定理），若仅有 `IAB_est/H/MAP/vis` 则判 `proxy_missing`，`readiness=missing`，后续 `READY` 不可达。

### 3.2 10项逐项定位（只读，禁止自创）

| # | item | symbol | 调查路径（只读，行号+表达式） | authority 判定 | readiness | minimal_new_measurement 若 missing |
|---|---|---|---|---|---:|---|
| 1 | phase-error / conjugate | `e_ph` / `e_p` | `rg "phase.error|conjugate|e_ph|phase_error" + round3 proof_gap` | `composable` 需共轭基实测+定理假设链；否则 `missing` | `missing→PARTIAL` | 新共轭基观测 + decoy-state `e_ph` 估计，`n_PE` 同 |
| 2 | n_PE | `n_PE` | `calibrated_effective_sample_count / registry / data_inventory` | `shadow proxy` 若仅 `n_eff` 代理，`composable` 需 PE 样本权威数 | `partial/missing` | 新 PE 采集 `n_PE` 权威数 |
| 3 | visibility 区间与来源 | `[vis_low, vis_high]`, `vis_src` | `_security_calibrated_common:chi_from_visibility` + 实验记录 | `shadow proxy (global 0.95)` 仅 proxy，需每点实测链才 `composable` | `proxy→partial` | 每点/每 loss 实测 `vis` 链与区间 |
| 4 | eps_sec / eps_cor | `eps_sec`, `eps_cor` | `build_actual_ir_shadow: eps=1e-10 + epsilon_EC_bound` | `shadow calibrated` | `ready/shadow` | 协议固定或新 composable 常数声明 |
| 5 | finite-size authority | `DeltaFK`, `n_eff` | `_security_calibrated_common:delta_fk_calibrated` | `shadow calibrated` 若仅 calibrated penalty | `shadow→partial` | 需 `n_eff` 实测 + composable 系数权威 |
| 6 | EV bound | `epsilon_EC`, `tag_verify` | `round2 audit: verification_bits` | `shadow/missing` | `partial/missing` | 新 `verification transcript` + `epsilon_EC` 证明 |
| 7 | auth leakage | `leak_auth` | `proof_gap missing` | `missing` | `missing` | 新 `auth` 观测与计费 |
| 8 | post-selection / accepted-frame | `accepted_frame_fraction` | `round2: accepted_frame_fraction` | `shadow surrogate` | `partial` | 严谨 `accepted/rejected` 计数与 `post_sel` 修正证明 |
| 9 | composable theorem 及假设 | `theorem_id, assumptions[]` | `round3_build_proof_gap_matrix / Renner/Niu/Tomamichel` | `missing` 若无明确定理声明 | `missing→DATA_NOT_READY` | 新 `composable theorem` 绑定与假设验证 |
| 10 | 单位 per-frame/block 换算 | `unit_map` | 权威文件单位声明 | `shadow/proxy` 若仅推断 | `partial` | 权威文件补 `bits/block vs bits/symbol` 声明 |

- 调查产出 `readiness_10items[] = {item, symbol, meaning, unit, source(file:function:lines:expr or data_path:provenance), authority: composable|shadow|proxy|missing, readiness: ready|partial|missing|invalid, decoder_free?: yes/no/partial, minimal_new_measurement}`；`h_min_source = MISSING` 若仓内 `rg H_min|min_entropy` 无权威下界声明，`IAB-chi ≟ H_min` 未声明则 `proxy_missing`。
- **决策**：`IAB_est/dary_mutual_info` 与 `H(A|B)` 与 `MAP_acc` 与 `visibility=0.95` 均标 `proxy/missing`，不自创 `H_min`，`composable:null`；`phase-error/conjugate` 无共轭基观测则 `readiness=missing` 且 `DATA_NOT_READY` 不可升 `PARTIAL` 之上。

### 3.3 预算重算（Phase B，仅 READY 时逐源机械，tag 不重复）

```
# 对每源 s ∈ {1M,1p5M,2M}:
m1_s, m2_s, m_total_s = V57 冻值
leak_without_tag_s = 5*(m1_s+m2_s)  # 7025 / 7375 / 7700
tag_s = 64
leak_total_s = leak_without_tag_s + tag_s  # 校验 == 7089/7439/7764
leak_IR_s = leak_total_s  # bits/block, 已含 tag, 不重复扣除

# 统一预算（仅 READY 可算）
if overall == V60_SECURITY_INPUTS_READY:
    ell_s(hmin_lower) = 1024 * hmin_lower - leak_IR_s - leak_other_s - finite_s
      where hmin_lower ∈ [0,10] bits/symbol,  search for ell==0 => hmin_break_even_ready
            leak_other_s = PE_penalty_s + EV_s + auth_s + ...  # per source, authoritative
            finite_s = DeltaFK_authoritative_s + ...  # bits/block, 单位已验
else:
    ell_s = null  # 非 READY 时保持 null，不以 floor 冒充

# 阈值锚点（必给，仅门限描述，不升密钥）:
hmin_break_even_floor_s = leak_total_s / 1024  # 1M 6.9238, 1p5M 7.2637, 2M 7.5820 bits/symbol
  + margin thresholds (other=0 finite=0 占位):
    h_0% = leak/1024 = 6.9238 / 7.2637 / 7.5820
    h_5% = leak/(1024*0.95) = 7.2882 / 7.6460 / 7.9811
    h_10% = leak/(1024*0.90) = 7.6931 / 8.0707 / 8.4245  # 必给，落盘校验 h*1024==leak/(1-margin)

# 非 READY 时 hmin_break_even_composable = null (JSON null) 而非 0
hmin_break_even_composable_s = null  if not READY else hmin_break_even_ready_s
log2 d =10 上界校验: hmin <10
```

- `leak_total ==5*m_total+64` 双校验，失败则 `EVIDENCE_INVALID`。
- 三源分别，不平均；`other/finite` 若权威区间缺失则 `0` 仅作 floor 锚点，但 `composable` 保持 `null` 不填 0。

### 3.4 敏感性仅作阈值描述（Phase B，不入 ell）

- 对仓内 authoritative 区间参数 `eps_sec ∈ [low, high]`, `vis ∈ [vis_low, vis_high]`, `n_eff` 仅传播 `floor / 5% / 10%` 阈值描述；`ell` 仅 `READY` 时可传播真实区间；**禁止网格调参**。
- 若无区间则 `shadow_low == shadow_high == floor` 且 `interval_tag = "no_composable_interval"`，显式报告不假装 composable 区间。

## 4. 分解表与校准/验证注册表（预注册，10项就绪度表）

### 4.1 readiness 10项表 `readiness_10items`（item / symbol / meaning / unit / source / authority / readiness / decoder_free? / minimal_new_measurement）

| item | symbol | meaning | unit | source | authority | readiness | decoder-free? | minimal_new_measurement |
|---|---|---|---|---|---|---|---|---|
| 1 phase-error/conjugate | `e_ph` | phase-error 率 | 无量纲 | `round3_proof_gap missing` | missing | missing | no | 新 conjugate / decoy-state `e_ph` 链 |
| 2 n_PE | `n_PE` | PE sample 大小 | count | `calibrated_effective_sample_count` | shadow proxy | partial | partial | 新 PE 采集数 |
| 3 visibility | `[vis_low,vis_high]` | Franson visibility 区间 | 无量纲 | `_security_calibrated_common:chi_from_visibility` | shadow proxy (`global 0.95`) | partial | yes(proxy) | 每点实测 `vis` 链 |
| 4 eps_sec/cor | `eps_sec, eps_cor` | secrecy/correctness | 无量纲 | `build_shadow: 1e-10` | shadow calibrated | ready/shadow | yes | 协议固定或 composable 常数 |
| 5 finite-size | `DeltaFK, n_eff` | finite-size 惩罚 | bits/pair | `delta_fk_calibrated` | shadow calibrated | shadow→partial | yes | 需 `n_eff` 实测+权威系数 |
| 6 EV | `epsilon_EC` | error-verification 界 | bits | `round2 audit` | shadow/missing | partial | partial | `verification transcript` |
| 7 auth | `leak_auth` | authentication | bits/block | `proof_gap missing` | missing | missing | no | 新 `auth` 观测 |
| 8 post-selection | `accepted_frame_fraction` | post-selection | 无量纲/bits | `round2 audit` | shadow surrogate | partial | yes | `accepted/rejected` 计数 |
| 9 composable theorem | `theorem_id` | composable 定理与假设 | — | `proof_gap missing` | missing | missing | no | 定理绑定+假设验证 |
| 10 units | `unit_map` | 单位换算 | bits/* | 权威单位声明 | shadow/proxy | partial | yes | 单位声明补全 |

- `authority` 列显式 `composable / shadow / proxy / missing`，`missing → composable:null`，`proxy 不升级`。
- `readiness` 列显式 `ready / partial / missing / invalid`，任一 `decisive` 项 `missing` 则 `READY` 不可达。

### 4.2 公式与就绪度溯源注册

- `v60_composable_security_readiness.json: {provenance: {HEAD, origin, implementation_SHA, data_sha 84d62779}, readiness_10items[10], formula_authority[{file,function,lines,expr,unit,authority}], decomposition[per_source], break_even{ floor, margin_5%, margin_10%, hmin_lower_authority, ell_or_null }, verdict}`。
- `manifest` 含 `HEAD 910d921b, data_sha 84d62779, script_sha, formula_authority_sha, zero_decode_verified, mutual_exclusion_verified, only_READY_ell_verified`。

## 5. 三源总体判定与后继门（first-match 四选一，按优先级互斥，仅 READY 算 ell）

```
if not unit_ok or not formula_self_consistent or leak !=5*m+64 or tag_repeated or IAB/H/MAP/vis_as_Hmin or proxy_upgraded:
    overall = V60_EVIDENCE_INVALID  # 硬完整性：单位不一致、tag 重复、m 不自洽、H/IAB/MAP/vis 当 H_min、proxy 升级
elif composable_theorem_missing or decisive_PE_missing:  # 决定性：theorem 无声明 或 e_ph/conjugate/n_PE/vis 权威缺
    overall = V60_DATA_NOT_READY  # 缺决定性输入，不可算 ell，需新定理或新 PE 采集
elif not all_decisive_ready or not finite_authority_ready or not eps_EV_auth_postSel_ready:
    # 部分项 partial 但 decisive 已部分，需补清单才 READY
    if not readiness_10items_ge10 or not break_even_floor_done:
        overall = V60_DATA_NOT_READY
    else:
        overall = V60_PARTIAL  # 部分 ready，不足 composable，输出最小清单与阈值
elif readiness_10items_all_critical_ready and composable_theorem_declared and break_even_floor_done and minimal_action_table_done and unit_ok:
    overall = V60_SECURITY_INPUTS_READY  # 唯一 READY，才允许 ell =1024*hmin - leak - other - finite
else:
    overall = V60_PARTIAL
# 且：H/IAB/MAP/vis 当 H_min 则 EVIDENCE_INVALID；proxy 升 composable 则 EVIDENCE_INVALID；missing 不为 null 则 EVIDENCE_INVALID
# 且：非 READY 时 ell_* 保持 null，不以 floor/shadow 填；仅 READY 时逐源 hmin_lower 比 floor/10% 判定 ell>0
```

- 仅 `V60_SECURITY_INPUTS_READY` 才允许 `ell` 计算与密钥余量判定（逐源 `hmin_lower` vs `floor 6.9238 vs 10% 7.6931` 等）；其余三态为就绪度闭合但需新测量。
- **仅缺 `H_min` 不够**：即使 `H_min_missing` 已识别，若未同时输出 `readiness 10项 + per_source break_even floor/5%/10% + minimal 新测量清单`，不得判 `PARTIAL` 完成。
- `V57` `H 2.3 vs NLL 30` 分裂已归档为 `ESTIMATOR_UNDERSAMPLED`；`V60` 预算不改该结论，仅在新 `m` 上判断就绪度。

## 6. 脚本与报告（decoder-free 守卫）

- **脚本 `scripts/v60_composable_security_input_readiness.py`** (decoder-free):
  ```
  python scripts/v60_composable_security_input_readiness.py \
    [--v57-json openspec/.../v57_channel_recharacterization.json] \
    [--v59-json openspec/.../v59_secret_key_budget_authority.json] \
    [--out-json docs/research_cycles/V60P0/v60_composable_security_readiness.json] \
    [--report docs/research_cycles/V60P0/V60_COMPOSABLE_SECURITY_INPUT_READINESS_REPORT.md] \
    [--csv docs/research_cycles/V60P0/v60_break_even_readiness.csv] \
    [--checklist docs/research_cycles/V60P0/v60_minimal_new_measurement_checklist.csv]
  → fetch/HEAD 自检 (若 HEAD != origin 则 warning) → Phase A 10项逐项扫描 + H_min 下界追踪 → Phase B 四终态互斥 + floor/5%/10% 阈值 → 仅 READY 算 ell → 输出 json/report/csv/checklist + 控制台摘要
  rg "decode_" 0 hits, 仅 numpy/pandas/pyarrow，py_compile PASS，不创建 run_01，不进 V61
  ```

- **报告 `V60_COMPOSABLE_SECURITY_INPUT_READINESS_REPORT.md`**：`formula_authority` 段（文件+函数+行号+原文 `not full niu_2016 / proof_gap missing`）、`readiness 10项表`、`decomposition table` 三源独立、`break_even` `floor/5%/10%` 阈值表（`6.9238/7.2637/7.5820` 与 `7.6931/8.0707/8.4245` 锚点）、`minimal 新增测量行动表`（按优先级排序，最小可执行采样/校准/定理验证）、`overall` 终态与权威闭合声明，数据与 `json` 一致，结论不扩大为 `FER/阈值/SKR/晋升`，显式 `V57/V59 m/leak 冻结` + `tag 已含不重复` + `三源分别不平均` + `proxy 不升级` + `missing→null` + `仅 READY 算 ell`。

- **守卫**：`git diff -- src/ ==0 && git diff -- experiments/ ==0 && git diff -- tools/ ==0 && git diff -- openspec/changes/formal-ir-v5[4-9]/ ==0 && git diff -- openspec/changes/formal-ir-v60*/ ==0`（除本变更外零改），`rg "decode_" 0 hits`，`rg "import.*decoder" 0 hits`，`py_compile` PASS，`pytest -p no:cacheprovider` 关键测试 PASS，`HEAD==origin` 已验，`run_01` 不存在，`mutual_exclusion` 已验，`composable:null` 已验，`only_READY_ell` 已验。

## 7. 与 V57/V59 衔接与 V61 边界

- `V57` `PREDICTIVE_MODEL_NOT_STABLE / DECODE_FORBIDDEN` 已固化 `m` 与泄漏；`V59` `AUTHORITY_INPUTS_ACTIONABLE` 已闭合口径与阈值但 `H_min/null`；`V60` 以 **decoder-free 就绪度审查**补齐 `composable 输入` 是否权威可用的判定，**未否定 V57/V59 终态**，仅在既有 `m/leak` 上闭合就绪度与最小行动清单。
- `V60_SECURITY_INPUTS_READY` 为**可算 ell**（即使 `ell` 不完整，需另起密钥计算）；`V60_PARTIAL / V60_DATA_NOT_READY` 为权威闭合但需补测量；`V60_EVIDENCE_INVALID` 硬失败需修单位/代理。
- 后继 `V61`（密钥计算/采集）需另起 `OpenSpec` 与独立授权，**本次不自动进入 `V61`**，禁 `decoder` 隐式触发。

## 8. 自由裁量 D1-D7

- D1 `leak_without_tag=5*m_total`, `tag=64` 仅整型算术，不引新库；`hmin_floor` 仅除法 `leak/1024` 与 `/(1-margin)`。
- D2 `H_min` 代理判定：`IAB_est/dary_mutual_info` 与 `H(A|B)` 与 `MAP` 与 `visibility` 均标 `proxy/missing`，不自创 `H_min`，`composable:null`。
- D3 `finite_penalty` 单位以权威文件为准，缺 composable 则 `null`，不假设 `per-block` composable。
- D4 `other_disclosure` 无权威则 `0` 并 `no_authority_other` 标签，仅 floor 锚点占位。
- D5 三源分别，不平均，`margin 0/5/10%` 固定阈 `h_m = leak/(1024*(1-margin))`。
- D6 不产生新矩阵/码参，仅就绪度与阈值，最简闭环。
- D7 本变更为 `PLAN_CANDIDATE / DECODE_FORBIDDEN`，不产生 `run_01`，后继 `V61` 时才考虑新测量/密钥计算。
