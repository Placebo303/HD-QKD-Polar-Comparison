# OpenSpec Tasks: formal-ir-v60-composable-security-input-readiness — V60 composable 安全输入就绪度判定

**Lifecycle**: `PLAN_CANDIDATE / DECODE_FORBIDDEN` — composable secret-key 权威输入就绪度判定，不改码/不跑 decoder，仅就绪度审查
**HEAD**: `910d921b` → 新 SHA (branch `formal-ir-mainline`, 实施前以 `git fetch && git rev-parse HEAD == origin/formal-ir-mainline` 重核，不一致阻塞) + data SHA `84d62779` (84d62779 200ps legacy_v1 nearest 1024)
**Predecessor**: `formal-ir-v59-security-budget-authority-closure` `AUTHORITY_INPUTS_ACTIONABLE / DECODE_FORBIDDEN` (m1 981/1024/1024, m2 424/451/516, leak 7089/7439/7764, n1024, tag64, GF32 5bits) — V57 m 冻结，V59 已闭合口径但 H_min null
**Boundary**: 每 block 1024 符号，64-bit tag 已含不得重复扣除，仅就绪度审查；`H1/L2/Δ8/decoder 90/1.0/poly37/estimator` 全冻；禁把 `IAB/H/MAP/visibility shadow` 当 `H_min`；仅 `V60_SECURITY_INPUTS_READY` 允许 `ell=1024*hmin_lower - leak_IR - leak_other - finite`；缺 `composable theorem` 或 `decisive PE` 即停 `PARTIAL/DATA_NOT_READY`，禁 shadow 补 null，禁 `decoder/V61`；三源分别、四终态互斥、`rg "decode_" 0 hits`、`git diff -- src/ ==0` 且 `git diff -- openspec/changes/formal-ir-v5[4-9]/ ==0`

## Phase A — 10项逐项权威就绪度验证（decoder-free，禁止自创，proxy 不升级，missing→null）

- [ ] **A1 fetch 与 HEAD 自检（阻塞门）**：`git fetch origin && git rev-parse HEAD == origin/formal-ir-mainline == 910d921b`（或新 SHA），不一致则 `V60_EVIDENCE_INVALID` 阻塞；记录 `HEAD/origin/implementation SHA` 至 `v60_composable_security_readiness.json: provenance`，`rg "910d921b" 0 hits` 旧 SHA 无残留（除历史记录）；`data SHA 84d62779` 已验
- [ ] **A2 10项权威逐函数/逐数据源扫描（只读）**：对仓库内代码 + 数据仓 + 文档逐项阅读并记录 `readiness_10items[{item,symbol,meaning,unit,source(file:function:lines:expr or data_path:provenance),authority(composable/shadow/proxy/missing),readiness(ready/partial/missing/invalid),decoder_free?,minimal_new_measurement}]`：
  - `tools/security_reports/_security_calibrated_common.py: chi_from_visibility / dary_mutual_info_proxy / calibrated_effective_sample_count / delta_fk_calibrated`
  - `tools/security_reports/build_actual_ir_finite_key_shadow.py: _build_shadow` (`PIE_secure = IAB - leak - chi_E - DeltaFK`, `surrogate_from_best_hard_pie_gap`, `not full niu_2016 composable proof`)
  - `tools/security_reports/round2_build_finite_key_audit_table.py / round2_build_actual_ir_finite_key_shadow.py` (`leak_EC_actual, DeltaFK, post_selection, epsilon_EC_bound`)
  - `tools/security_reports/round3_build_proof_gap_matrix.py` (`per_point_franson_pe_chain: missing, conjugate_basis_stats: missing, decoy_state_PE: missing, protocol_specific_composable_constants: missing`)
  - `comparison_bench/outputs_comparison/v57_*` 与 `v55_intake_20260828` 数据仓 `data_inventory.json / registry / pairs`（`n_PE / visibility 来源`）
  - `docs/SECURITY_MODEL.md / openspec/changes/formal-ir-v59*/v59_secret_key_budget_authority.json`（`eps_sec/cor / finite authority` 声明）
  每项明确 `bits/block` vs `bits/pair` vs `bits/symbol` vs 无量纲，落盘 `formula_authority[]` 与 `unit_table`
- [ ] **A3 `phase-error / conjugate` 权威裁决**：裁决仓内是否有**共轭基实测 + phase-error 率估计**的 composable 权威链（`e_ph`、`e_p`、`conjugate_basis_stats`）；以文件原文为凭：`proof_gap_matrix: conjugate_basis_stats missing / per_point_franson_pe_chain missing` 若为 `missing` 则标 `authority=missing, readiness=missing`，`decisive_PE_missing=true`，禁止以 `SER / Shannon H / visibility` 代理；若 `rg "phase.error|conjugate|e_ph"` 无 composable 声明则 `missing` 且后续 `READY` 不可达
- [ ] **A4 `n_PE` 与 `visibility 区间与来源` 裁决**：裁决 `n_PE` 是否有权威样本数（`n_eff` 仅为 `shadow proxy`，需 PE 样本权威数才 `composable`）与 `visibility` 是否为**每点/每 loss 实测区间 `[vis_low, vis_high]` 带来源**（`global vis=0.95` 仅 `shadow proxy`）；明确 `vis` 单位与计费：`chi_E = h2((1-vis)/2)+e*log2(d-1)` 为 `bits/pair`，需区间时落盘 `vis_interval`，无实测链则 `proxy/missing` 且 `readiness=partial/missing`
- [ ] **A5 `eps_sec / eps_cor` 与 `finite-size authority` 裁决**：裁决 `eps_sec / eps_cor` 是否为协议固定且与 `DeltaFK` 公式 `4*sqrt(log2(2/eps_sec)/n_eff)+2*log2(2/eps_cor)/n_eff` 的 `composable` 系数权威一致；`DeltaFK` 单位为 `bits/pair` 需显式，未显式则 `unit_missing → V60_EVIDENCE_INVALID` 或 `shadow_unit_assumed` 并 `weak_proxy` 标记；若仅有 `calibrated shadow` 无 `composable` 声明则 `authority=shadow` 且 `readiness=partial`
- [ ] **A6 `EV bound` 与 `auth leakage` 裁决**：裁决 `EV bound`（`epsilon_EC / verification_bits`）是否为**已证明的 verification transcript 界**（非 surrogate gap），`auth` 是否有权威 `authentication bits` 计费；若 `proof_gap: auth missing / EV transcript missing` 则标 `missing` 且 `minimal_new_measurement = "verification transcript + auth bits"`，`readiness=missing` 阻塞 `READY`
- [ ] **A7 `post-selection / accepted-frame` 与 `composable theorem 及假设` 裁决**：裁决 `post-selection` 是否为严谨 `accepted_frame_fraction` 且是否已有 `post_sel` 修正的 composable 证明链；裁决 `composable theorem` 是否被**明确声明**（`Renner / Niu 2016 / Tomamichel` 等 `theorem_id` + `assumptions: {collective/coherent, PE model, finite-key, auth, EV}` + `适用域`），若仅有 `strict_zhong_like_calibrated` / `shadow` 描述则 `authority=shadow` 且 `composable_theorem_missing=true`，**缺此项即 `V60_DATA_NOT_READY` 停止**，禁 `IAB/Shannon/MAP` 当定理
- [ ] **A8 `单位 per-frame/block 换算` 闭合校验**：明确 `chi_E(bits/pair)`、`DeltaFK(bits/pair)`、`IAB_est(bits/pair)`、`post_sel(bits/pair or fraction)`、`leak_IR(bits/block)`、`hmin_lower(bits/symbol)` 各自单位与是否已含 `tag`；若权威未显式单位则 `unit_missing → V60_EVIDENCE_INVALID` 或 `SHADOW_unit_assumed` 并 `weak_proxy` 标记；落盘 `unit_table`，校验 `bits/block = bits/symbol *1024` 显式换算记录
- [ ] **A9 `H_min^epsilon(A|E) 下界` 追踪（禁代理）**：在仓内 `rg "H_min|min_entropy|H_min.*epsilon|secret.*key.*length|IAB.*chi|chi.*IAB|Shannon|MAP"` 查找 `H_min` 下界声明；确认 `dary_mutual_info_proxy`（`IAB_est`）与 `Shannon H` 与 `MAP_acc` 与 `visibility=0.95` 均**未被声明为 `H_min^epsilon(A|E)` 的下界或等价**；若仅有代理则标记 `h_min_source = "MISSING"` 且 `iab_h_map_vis_to_hmin = "no_declaration_proxy_missing"`，不自行等价，禁把 `IAB/H/MAP/vis` 当 `H_min`（违规则 `V60_EVIDENCE_INVALID`），`hmin_lower_authority = missing → composable:null`
- [ ] **A10 冻结零改校验**：校验 `H1 16×1024 / Lane C / H_inc1/2 / Δ8+8 / decoder 90/1.0 poly37 / V57 m1/m2/m_total/leak` 全未改（`git diff -- src/ ==0 && git diff -- openspec/changes/formal-ir-v5[4-9]/ ==0`），`rg "decode_" 0 hits`，`estimator` 未动；失败则 `V60_EVIDENCE_INVALID`

## Phase B — 统一就绪度终态与阈值（`ell` 仅 READY 可算，三源独立，tag 不重复）

- [ ] **B1 统一预算冻结（仅 READY 可算）**：冻结 `ell_s = 1024 * hmin_lower_s - leak_IR_s - leak_other_s - finite_s`，其中 `leak_IR_s = leak_total_s =5*m_total+64` 已含 `tag`，`hmin_lower` 为 `bits/symbol` composable 下界，非 `READY` 时 `ell_* = null` 不冒充；`leak_other_s = PE_s + EV_s + auth_s + ...`, `finite_s = DeltaFK_authoritative_s + ...` 单位全 `bits/block`；仅 `V60_SECURITY_INPUTS_READY` 时以权威 `hmin_lower` 计算 `ell_s`，其余态保持 `null`
- [ ] **B2 GF32 与 tag 不重复校验**：逐源校验 `m_total == m1+m2` (`1405/1475/1540`) 且 `leak_total ==5*m_total+64` (`7089/7439/7764`)，`leak_without_tag =5*(m1+m2)` (`7025/7375/7700`)，`tag=64` 单计不重复；`log2 q=5` 显式记录；`hmin ≤10 bits/symbol (log2 d)` 上界校验；失败则 `V60_EVIDENCE_INVALID`
- [ ] **B3 readiness 10项表落盘（≥10项_exact）**：`symbol / meaning / unit / source(file:function:lines:expr or data_path:provenance) / authority(composable/shadow/proxy/missing) / readiness(ready/partial/missing/invalid) / decoder_free?(yes/no/partial) / minimal_new_measurement` 逐项精确落盘 `v60_composable_security_readiness.json: readiness_10items[10]`，每项 `missing → composable:null + minimal_new_measurement`，`proxy 不升级为 composable` 已验
- [ ] **B4 `H/IAB/MAP/vis ≠ H_min` 审计**：检查若 `hmin_lower` 借用 `H(A|B)` / `IAB_est` / `MAP_acc` / `visibility shadow` 则显式 `proxy_missing` 并报告语义差，且 `composable` 区间保持 `null` 不填；正宗 `H_min` 需有权威文件行号支撑，否则 `missing`；脚本 `assert proxy_not_upgraded` 已验
- [ ] **B5 不跨 source 平均校验**：`readiness_10items` 与 `decomposition table` 三源独立列，禁止 `mean(hmin)` 替代逐源 `hmin_break_even`；脚本内 `assert` 三源分别计算，报告不出现总体平均替代
- [ ] **B6 decomposition table 落盘**：`v60_composable_security_readiness.json: decomposition[{source, leak_without_tag, tag64, leak_total, n, log2q, leak_other_or_null, finite_or_null}]` 三源独立，`py_compile` 前已验；`break_even readiness` 表 `source, leak_total, floor, margin_5%, margin_10%, hmin_lower_authority, ell_or_null, gate` 三源独立

## Phase C — 三档 break-even 阈值（optimistic floor 必给 / 10% margin 锚点，每源三源独立）

- [ ] **C1 optimistic floor（必给，other=0 finite=0，description）**：逐源 `hmin_break_even_floor_s = leak_total_s /1024` bits/symbol，`1M 6.9238, 1p5M 7.2637, 2M 7.5820`，与 `leak` 锚点双校验（`floor*1024 == leak`），`log2 d=10` 上界校验（`floor <10`），落盘 `break_even.optimistic_floor[]`，为 `READY` 与非 `READY` 共用门限参考，但非 `READY` 不升为密钥余量
- [ ] **C2 margin 阈值（10% 必比，每源三列）**：`h_m(margin) = (leak+other+finite)/(1024*(1-margin))`，`margin 0% = floor, 5% => /0.95, 10% => /0.90`，逐源三行三列成表，非 `READY` 时 `other=0 finite=0` 占位仅作锚点：
  - `1M: 6.9238 / 7.2882 / 7.6931` (floor/5%/10% optimistic)
  - `1p5M: 7.2637 / 7.6460 / 8.0707`
  - `2M: 7.5820 / 7.9811 / 8.4245`
  `READY` 时以真实 `hmin_lower/leak_other/finite` 覆盖，未 `READY` 时保持 `hmin_lower_authority=null` 且 `ell=null`；三源独立 `log2 d=10` 上界校验
- [ ] **C3 composable 显式 null（缺则 null，不填 0）**：若 `H_min` / `e_ph` / `composable theorem` 缺决定性输入，则 `hmin_lower_s = null` 且 `ell_s = null`（JSON `null`）而非 `0`，落盘 `break_even.composable = [null,null]`，并显式 `composable_missing_reasons[] = {theorem missing / decisive PE missing / proxy not H_min / finite authority missing ...}`
- [ ] **C4 单位换算与锚点双校验**：`leak_total_s ==5*m_total+64` 且 `h_floor_s *1024 == leak_total_s` 整点校验；`bits/block = bits/symbol *1024` 显式换算记录；`h_floor*1024/(1-margin)` 反算校验已验
- [ ] **C5 紧凑CSV（thresholds）**：`v60_break_even_readiness.csv` 列 `source, leak_total, floor, margin_5%, margin_10%, hmin_lower_authority, hmin_lower_null_or_value, ell_or_null, gate`，`composable` 列显式空或 `null`，`floor / 5% / 10%` 数值已落盘且与 `json` 一致
- [ ] **C6 仅 READY 比阈值判定 ell>0**：仅当 `V60_SECURITY_INPUTS_READY` 时逐源比较 `hmin_lower` vs `floor`（`6.9238 vs`）与 `10% margin`（`7.6931 vs`）判定 `ell>0` 与 `margin≥0.10`，并报告 `ell_final / per_pair / margin_ratio`；非 `READY` 时仅报告阈值锚点，不宣称 `ell>0 / SKR`

## Phase D — 四互斥终态 first-match（按序优先级，不可共存，proxy 不升级，仅 READY 算 ell）

- [ ] **D1 总体判定（first-match 互斥，仅 READY 算 ell）**：
  ```
  if not unit_ok or leak !=5*m+64 or m_total != m1+m2 or IAB/H/MAP/vis_as_Hmin or not formula_self_consistent or tag_repeated or proxy_upgraded:
      overall = V60_EVIDENCE_INVALID  # 硬完整性：单位不一致、tag 重复、m 不自洽、H/IAB/MAP/vis 当 H_min、proxy 升级
  elif composable_theorem_missing or decisive_PE_missing:  # 决定性：无 composable 定理声明 或 缺 e_ph/conjugate/n_PE/vis 权威
      overall = V60_DATA_NOT_READY  # 缺决定性输入，ell=null，需新定理或新 PE 采集，立即停
  elif not all_decisive_ready or not finite_authority_ready or not eps_EV_auth_postSel_ready:
      if not readiness_10items_ge10 or not break_even_floor_done:
          overall = V60_DATA_NOT_READY
      else:
          overall = V60_PARTIAL  # 部分 ready，不足 composable，已输出最小清单与阈值，未 ready 前 ell=null
  elif readiness_10items_all_critical_ready and composable_theorem_declared and hmin_lower_authority_composable and break_even_floor_done and minimal_action_table_done and unit_ok:
      overall = V60_SECURITY_INPUTS_READY  # 已输出 10项 + 每源 floor/5%/10% 且 H_min+finite 权威可算，已具备 ell 资格，唯一允许 ell=1024*hmin - leak - other - finite
  else:
      overall = V60_PARTIAL
  ```
  实际落盘逻辑为严格按序 `V60_EVIDENCE_INVALID > V60_DATA_NOT_READY(缺theorem或decisive PE) > V60_PARTIAL(部分ready) > V60_SECURITY_INPUTS_READY(全ready, 唯一算ell)`，`first_match` 显式记录，**仅缺 `H_min` 而未输出清单与阈值不得判 `PARTIAL`，仅 `READY` 算 `ell`，其余 `ell=null`** 已验
- [ ] **D2 互斥性校验**：脚本内 `assert overall in [EVIDENCE_INVALID, DATA_NOT_READY, PARTIAL, SECURITY_INPUTS_READY] 且仅一态`，`proxy_missing 保持 missing/null`，`shadow 不升级为 composable`，`missing 不填 0`，`rg "H_min.*=.*IAB|IAB.*H_min|MAP.*H_min|visibility.*H_min" 0 hits` 无自行等价，`only_READY_ell: assert (overall==READY) == (ell_not_null)` 已验
- [ ] **D3 仅 `READY` 为可算 ell，其余 stop**：报告显式声明“**仅 `V60_SECURITY_INPUTS_READY` 允许 `ell =1024*hmin_lower - leak_IR - leak_other - finite` 逐源判定 `ell>0` 与 `margin≥0.10`，其余 `PARTIAL/DATA_NOT_READY/EVIDENCE_INVALID` `ell=null` 仅输出 floor/5%/10% 门限与缺口清单，立即停，不进 decoder/V61**”，`DATA_NOT_READY` 与 `PARTIAL` 区分已验（`DATA_NOT_READY` 为 decisive 缺失，`PARTIAL` 为部分 ready）
- [ ] **D4 停止条件校验**：脚本模拟 `composable theorem missing` 注入 → `DATA_NOT_READY` 且 `ell=null`，`decisive PE missing` 注入 → `DATA_NOT_READY` 且未以 shadow 填 `null` 已验；`proxy 补 null` 注入 → `EVIDENCE_INVALID` 已验

## Phase E — 脚本与报告交付（PLAN_CANDIDATE / DECODE_FORBIDDEN）

- [ ] **E1 编写 `scripts/v60_composable_security_input_readiness.py`** (decoder-free): `python scripts/v60_composable_security_input_readiness.py [--v57-json ...] [--v59-json ...] [--out-json ...] [--report ...] [--csv ...] [--checklist ...]` → A1 fetch/HEAD → A2 10项逐项扫描 → A3-A9 composable/PE/vis/eps/finite/EV/auth/post_sel/theorem/H_min 裁决 → A10 冻结零改 → B1-B6 decomposition/readiness 表 → C1-C6 三档 floor/5%/10% + null → D1-D4 first-match 四终态互斥（仅 READY 算 ell）→ 输出 `v60_composable_security_readiness.json + V60_COMPOSABLE_SECURITY_INPUT_READINESS_REPORT.md + v60_break_even_readiness.csv + v60_minimal_new_measurement_checklist.csv` + 控制台摘要，`rg "decode_" 0 hits`，`py_compile` PASS，未创建 `run_01`，不改 `src//experiments//tools/` 且 `openspec/changes/formal-ir-v5[4-9]/` 零改，不进 `V61`
- [ ] **E2 撰写 `docs/research_cycles/V60P0/V60_COMPOSABLE_SECURITY_INPUT_READINESS_REPORT.md`**：`formula_authority` 段（文件+函数+行号+原文 `not full niu_2016 / proof_gap missing`）、`readiness 10项表`（item/symbol/meaning/unit/source/authority/readiness/decoder_free/minimal_new_measurement）、`decomposition table` 三源独立、`break_even readiness` 表（含 `6.9238/7.2637/7.5820` floor 与 `7.6931/8.0707/8.4245` 10% margin 锚点）、`minimal 新增测量行动表`（按优先级排序，最小可执行采样/校准/定理验证）、`overall` 终态与权威闭合声明，数据与 `json` 一致，显式 `V57/V59 m/leak 冻结` + `tag已含不重复` + `三源分别不平均` + `proxy 不升级` + `missing→null` + `仅READY算ell`，不扩大为 `FER/SKR/晋升`
- [ ] **E3 生成 `v60_minimal_new_measurement_checklist.csv`**：列 `priority, item, missing_reason, minimal_new_measurement, required_sample_or_proof, acceptance_criterion, depends_on`，按 `composable theorem > decisive PE (phase-error/conjugate/n_PE) > visibility chain > finite authority > EV/auth/post_sel > units` 优先级排序，精确列出需新采集参数（无 proxy 填充），与 `json/readiness` 一致
- [ ] **E4 自检（gate）**：`py_compile` PASS, `rg "decode_" 0 hits && rg "import.*decoder" 0 hits`, `git diff -- src/ ==0 && git diff -- experiments/ ==0 && git diff -- tools/ ==0 && git diff -- openspec/changes/formal-ir-v5[4-9]/ ==0`, 三源 `leak_without_tag/tag` 不重复已验，`GF32 5bits` 已验，`H/IAB/MAP/vis !=H_min` 已验，不跨源平均已验，`break_even 锚点 leak/1024` 与 `h*1024/(1-margin)` 已验，`missing→null` 已验，`proxy 不升级` 已验，`四终态互斥 first-match` 已验，`readiness 10项` 已验，`仅READY算ell` 已验，`HEAD==origin` 已验，`run_01` 不存在已验，`V61` 未触发已验
- [ ] **E5 推送新 SHA 并停留 `PLAN_CANDIDATE / DECODE_FORBIDDEN`**，未创建任何 `run_01` decoder 执行，不碰 `V57/V59 m/leak`，`src//experiments//tools//V54-V59` 零改，普通推送（非 force）至 `formal-ir-mainline`，推送后等待独立审核（`Pre-RESULT` 独立线程复核 `HEAD/ACCEPTED_PLAN_SHA/rg 0 hits/run_01不存在/py_compile+关键测试 PASS`），`V61` 仍 `PENDING`，返回 `Plan SHA / implementation SHA / 10项 readiness / 三源阈值 / 最小清单 / 终态`，**不自动进入 `V61`**

## 本变更显式禁止

decoder 调用（`decode_* / construct_*` 等）；改 `V57/V59 m1/m2/leak` 或 `H1/Lane C/Δ/decoder` 冻参或新增矩阵；自创 `H_min / finite-key / composable` 公式或造 `eps_sec/eps_cor/vis/phase-error` 参数；重复扣除 `tag 64`；把 `IAB/H/MAP/vis` 当 `H_min` 不加 `missing`；将 `shadow` 升级为 `composable`；将 `missing` 填 `0` 而非 `null`；跨 source 平均 `hmin`；网格调参；宣称 `FER/SKR/阈值/晋升`；创建正式 `run_01` decoder 执行；改 `src//experiments//tools//V54-V59`；将总体平均掩盖单源阈值；将 `PARTIAL` 误升为 `READY`（未 decisive ready）；非 `READY` 计算 `ell`；非 `READY` 以 `shadow` 填 `null`；自动进入 `V61`。

## 验收

- proposal/design/tasks/specs 一致 HEAD 910d921b→新SHA 84d62779 lifecycle PLAN_CANDIDATE DECODE_FORBIDDEN 四终态按 `V60_EVIDENCE_INVALID > V60_DATA_NOT_READY(缺theorem或decisive PE) > V60_PARTIAL(部分ready) > V60_SECURITY_INPUTS_READY(全ready, 唯一算ell)` 互斥先匹配，**缺 composable theorem 或 decisive PE 即停 DATA_NOT_READY/PARTIAL**，显式三源分别、tag 不重复、proxy 不升级、missing→null、仅READY算ell
- Phase A 10项就绪度 `readiness_10items`（phase-error/conjugate、n_PE、visibility区间与来源、eps_sec/cor、finite-size authority、EV bound、auth leakage、post-selection/accepted-frame、composable theorem及假设、单位换算）单位已落盘 `formula_authority`，`H_min` 下界是否明确声明已验，禁止 `IAB/H/MAP/vis` 当 `H_min`，`H1/L2/Δ8/decoder` 零改已验
- Phase B 统一就绪度 `readiness` 与 `decomposition` 三源独立 `leak_without_tag 7025/7375/7700 +tag64=7089/7439/7764` 自洽，`GF32 5bits` 与 `H≠H_min` 已验，不跨源平均，`only_READY_ell` 已验
- Phase C `hmin_break_even` 阈值已落盘 `floor 6.9238/7.2637/7.5820 + 5% 7.2882/7.6460/7.9811 + 10% 7.6931/8.0707/8.4245`，`h_m = (leak+other+finite)/(1024*(1-m))` 已算，锚点 `leak/1024` 与 `h*1024/(1-m)` 双校验，`missing→null` 已验
- Phase D 四互斥 `first-match` 已验，`proxy 不升级` 已验，`仅READY算ell` 已验，无网格，stop 条件已验
- Phase E 脚本 `rg 0 hits` `py_compile` PASS 报告与 json 一致 未建 `run_01` 未进 `V61` 已推新 SHA PLAN_CANDIDATE/DECODE_FORBIDDEN 仅改本目录+`scripts/`+`docs/research_cycles/V60P0/`（`src//experiments//tools//V54-V59` 零改），`HEAD==origin` 已验，推送后等待独立审核，**不自动进入 `V61`**
