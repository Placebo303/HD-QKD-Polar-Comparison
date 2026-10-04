# OpenSpec Tasks: formal-ir-v59-security-budget-authority-closure — V59 decoder-free 安全预算权威闭合

**Lifecycle**: `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN` — decoder-free 安全预算权威闭合，主动闭合 V58 缺失输入并给出每源 `hmin_break_even`
**HEAD**: `2340257d` → 新 SHA (branch `formal-ir-mainline`, 实施前以 `git fetch && git rev-parse HEAD == origin/formal-ir-mainline` 重核，不一致阻塞) + data SHA `84d62779` (84d62779 200ps legacy_v1 nearest 1024)
**Predecessor**: `formal-ir-v58-secret-key-budget-stoploss` `SECURITY_INPUTS_INCOMPLETE / DECODE_FORBIDDEN` (m1 981/1024/1024, m2 424/451/516, leak 7089/7439/7764, n1024, tag64, GF32 5bits)
**Boundary**: V57/V58 披露完全冻结零改；每 block 1024 符号，64-bit tag 已含不得重复扣除，仅预算诊断；统一 `ell=1024*hmin_lower - leak_IR - leak_other - finite`；三档阈值 `optimistic floor(other=0 finite=0) / shadow descriptive / composable:null`；每源 0/5/10% margin；禁把 `H/IAB/MAP` 当 `H_min`；四互斥终态按序 `EVIDENCE_INVALID > AUTHORITY_CLOSED_NO_POSITIVE_MARGIN > AUTHORITY_CLOSED_POSITIVE_POSSIBLE > AUTHORITY_INPUTS_ACTIONABLE`；仅缺 `H_min` 不足以判 `ACTIONABLE`；`rg "decode_" 0 hits`，`git diff -- src/ ==0` 且 `git diff -- openspec/changes/formal-ir-v5[4-8]/ ==0`，禁 `V60`

## Phase A — 逐函数权威裁决（decoder-free，禁止自创，proxy 不升级，missing→null）

- [ ] **A1 fetch 与 HEAD 自检（阻塞门）**：`git fetch origin && git rev-parse HEAD == origin/formal-ir-mainline == 2340257d`（或新 SHA），不一致则 `EVIDENCE_INVALID` 阻塞；记录 `HEAD/origin/implementation SHA` 至 `v59_secret_key_budget_authority.json: provenance`，`rg "2340257d" 0 hits` 旧 SHA 无残留（除历史记录）
- [ ] **A2 权威逐函数扫描（只读）**：对 `tools/security_reports` 下 4 文件逐函数阅读并记录 `formula_authority[{file,function,lines,expr,unit,authority}]`：
  - `_security_calibrated_common.py: chi_from_visibility / dary_mutual_info_proxy / calibrated_effective_sample_count / delta_fk_calibrated`
  - `build_actual_ir_finite_key_shadow.py: _build_shadow` (`PIE_secure = IAB - leak - chi_E - DeltaFK`, `surrogate_from_best_hard_pie_gap`, `not full niu_2016 composable proof`)
  - `round2_build_finite_key_audit_table.py: main` (`leak_EC_actual_bits = total_leak_ec_bits/n_pairs else surrogate`, `DeltaFK` 显式 `n_eff`, `post_selection = accepted_frame_fraction`, `epsilon_EC_bound`)
  - `round2_build_actual_ir_finite_key_shadow.py: main` (`PIE_secure_actual_ir = IAB - leak - chi_E - DeltaFK - post_sel`, `strict_zhong_like_actual_ir_finite_key_calibrated`)
  - 关联 `round3_build_proof_gap_matrix.py` 与 `build_beta_baseline_finite_key_shadow.py` 作缺口佐证；明确 `bits/block` vs `bits/pair` vs `bits/symbol` 单位
- [ ] **A3 `PIE_secure` composable 裁决**：裁决 `PIE_secure = IAB - leak - chi_E - DeltaFK - post_sel` 在仓内是否被**明确授权为 composable**；以文件原文为凭：`build_actual_ir_finite_key_shadow.py L116 "not full niu_2016 composable proof"` / `round2 ... strict_zhong_like ... calibrated` / `proof_gap_matrix: decoy_state/conjugate_basis/composable_constants missing` 证明**仅 shadow/proxy**，落盘 `pie_secure_authority = "shadow_proxy_only"`，禁止自行认定为 composable；若 `rg "composable.*PIE_secure|PIE_secure.*composable"` 无明确授权声明则 `missing`
- [ ] **A4 `IAB - chi_E ≟ H_min^epsilon(A|E)` 追踪**：在仓内 `rg "H_min|min_entropy|H_min.*epsilon|secret.*key.*length|IAB.*chi|chi.*IAB"` 查找 `H_min` 定义与等价声明；确认 `dary_mutual_info_proxy`（`IAB_est`）与 `chi_from_visibility`（`chi_E`）均未被声明为 `H_min^epsilon(A|E)` 的等价或下界；若仅有 `IAB_est` / `H(A|B)` / `MAP` 则标记 `h_min_source = "MISSING"` 且 `iab_chi_to_hmin = "no_declaration_proxy_missing"`，不自行等价，禁把 `H/IAB/MAP` 当 `H_min`（违规则 `EVIDENCE_INVALID`）
- [ ] **A5 单位闭合校验**：明确 `chi_E`(bits/pair)、`DeltaFK`(bits/pair, 需 `*n_eff` 转块)、`IAB_est`(bits/pair)、`post_sel`(bits/pair)、`leak_IR`(bits/block) 各自单位与是否已含 `tag`；若权威未显式单位则 `unit_missing → EVIDENCE_INVALID` 或 `SHADOW_unit_assumed` 并 `weak_proxy` 标记；落盘 `unit_table`

## Phase B — 统一预算与 exact 变量表（`ell=1024*hmin - leak_IR - leak_other - finite`，≥11 项，三源独立）

- [ ] **B1 统一预算冻结**：冻结 `ell_s = 1024 * hmin_lower_s - leak_IR_s - leak_other_s - finite_s`，其中 `leak_IR_s = leak_total_s =5*m_total+64` 已含 `tag`，`hmin_lower` 为 `bits/symbol` 下界 (搜索 `ell=0` 得 `hmin_break_even`)，单位全 `bits/block`
- [ ] **B2 GF32 与 tag 不重复校验**：逐源校验 `m_total == m1+m2` (`1405/1475/1540`) 且 `leak_total ==5*m_total+64` (`7089/7439/7764`)，`leak_without_tag =5*(m1+m2)` (`7025/7375/7700`)，`tag=64` 单计不重复；`log2 q=5` 显式记录；失败则 `EVIDENCE_INVALID`
- [ ] **B3 exact 变量表 `variable_table` ≥11 项落盘**：`symbol / meaning / unit / source(file:function:lines:expr) / authority(composable/shadow/proxy/missing) / decoder_free?(yes/no/partial) / minimal_new_measurement` 逐项精确，至少覆盖：
  1) `H_min^epsilon(A|E)` smooth min-entropy per symbol — `MISSING` — `no` — 需新 PE 样本估计
  2) `e_ph` phase-error 率 — `MISSING` — `no` — 需 conjugate-basis / decoy-state
  3) `vis` Franson visibility 区间 `[vis_low,vis_high]` — `shadow proxy (global 0.95)` — `partial` — 需每点实测 vis 链
  4) `n_PE` PE sample 大小 — `shadow proxy (n_eff)` — `partial` — 需新 PE 采集数
  5) `eps_sec` — `shadow calibrated 1e-10` — `yes` — 协议固定
  6) `eps_cor` — `shadow calibrated 1e-10 + epsilon_EC_bound` — `yes/partial` — 需验证证明
  7) `DeltaFK` finite-size 惩罚 — `shadow calibrated` — `yes` — 需 `n_eff` 实测
  8) `EV` error-verification tag bits — `shadow/missing` — `partial` — 需 `verification transcript`
  9) `post_sel` post-selection fraction — `shadow surrogate (accepted_frame_fraction)` — `yes` — 需严谨 `accepted/rejected` 计数
  10) `auth` authentication bits — `MISSING` — `no` — 需新 `auth` 观测
  11) `IAB`/`H(A|B)` — `proxy` — `yes` — **禁当 `H_min`**
  12) `leak_IR` — `frozen 7089/7439/7764` — `yes` — 已冻
  每项 `missing → composable:null`，`proxy 不升级为 composable` 已验
- [ ] **B4 `H(A|B) ≠ H_min` 审计**：检查若 `min_entropy_budget` 借用 `H(A|B)` / `IAB_est` / `MAP` 则显式 `weak_proxy=true` 并报告语义差，且 `composable` 区间保持 `null` 不填；正宗 `H_min` 需有权威文件行号支撑，否则 `missing`
- [ ] **B5 不跨 source 平均校验**：`variable_table` 与 `decomposition table` 三源独立列，禁止 `mean(hmin)` 替代逐源 `hmin_break_even`；脚本内 `assert` 三源分别计算，报告不出现总体平均替代
- [ ] **B6 decomposition table 落盘**：`v59_secret_key_budget_authority.json: decomposition[{source, leak_without_tag, tag64, leak_total, n, log2q}]` 三源独立，`py_compile` 前已验

## Phase C — 三档 break-even 阈值（optimistic floor 必给 / shadow descriptive / composable null，每源 0/5/10%）

- [ ] **C1 optimistic floor（必给，other=0 finite=0）**：逐源 `hmin_break_even_floor_s = leak_total_s /1024` bits/symbol，`1M 6.9238, 1p5M 7.2637, 2M 7.5820`，与 `leak` 锚点双校验（`floor*1024 == leak`），`log2 d=10` 上界校验（`floor <10`），落盘 `break_even.optimistic_floor[]`
- [ ] **C2 shadow descriptive 区间（proxy，不升级）**：`hmin_break_even_shadow_s = (leak_IR_s + other_shadow_s + finite_shadow_s)/1024` 用仓内 calibrated shadow 的 `chi/delta/post_sel/vis` 描述性传播得 `[low, high]`（如 `vis ∈ [0.93,0.97]` 时 `chi_E` 区间），显式 `proxy` 标签，**不升级为 `composable`**，落盘 `break_even.shadow[{low,high}]`，若无区间则 `shadow==optimistic_floor` 且 `interval_tag="no_shadow_interval"`
- [ ] **C3 composable-authority 区间 `null`（缺则显式 null）**：若 `H_min` / `e_ph` / `composable_constants` 缺决定性输入，则 `hmin_break_even_composable_s = null`（JSON `null`）而非 `0`，落盘 `break_even.composable = [null, null]`，并显式 `composable_missing_reasons[]`
- [ ] **C4 每源 0/5/10% margin 阈值**：`h_m(margin) = (leak+other+finite)/(1024*(1-margin))`，`margin 0% = floor, 5% => /0.95, 10% => /0.90`，逐源三行三列成表：
  - `1M: 6.9238 / 7.2882 / 7.6931` (floor/5%/10% optimistic)
  - `1p5M: 7.2637 / 7.6460 / 8.0707`
  - `2M: 7.5820 / 7.9811 / 8.4245`
  `shadow` 与 `composable:null` 同理派生，`log2 d=10` 上界校验，三源独立
- [ ] **C5 单位换算与锚点双校验**：`leak_total_s ==5*m_total+64` 且 `h_floor_s *1024 == leak_total_s` 整点校验；`bits/block = bits/symbol *1024` 显式换算记录
- [ ] **C6 紧凑CSV**：`v59_break_even.csv` 列 `source, leak_total, optimistic_floor, optimistic_5%, optimistic_10%, shadow_low, shadow_high, shadow_5_low/high, shadow_10_low/high, composable_low, composable_high, gate`，`composable` 列显式空或 `null`

## Phase D — 四互斥终态 first-match（按序优先级，不可共存，proxy 不升级）

- [ ] **D1 总体判定（first-match 互斥）**：
  ```
  if not unit_ok or leak !=5*m+64 or m_total != m1+m2 or H_or_IAB_as_Hmin or not formula_self_consistent:
      overall = EVIDENCE_INVALID
  elif h_min_missing or composable_missing or any(ell_conservative_s <=0 with optimistic floor):
      # optimistic floor 已是最小惩罚，若仍 ≤0 则无正余量
      if any((leak_total_s/1024*1024 - leak_total_s) <=0 or optimistic_floor_s*1024 - leak_total_s <=0): # 即 leak本身
          # 实际判断：若 optimistic floor 的 ell =1024*floor - leak ==0 边界，margin 0% 为临界；但是否存在 finite/other 使 ell<0？
          # 以保守传播为准：任一源 conservative ell ≤0
      overall = AUTHORITY_CLOSED_NO_POSITIVE_MARGIN  # 任一源保守 ≤0 立即止路
  elif variable_table_ge11 and break_even_has_floor and all_conservative_gt0:
      if composable_is_null:
          overall = AUTHORITY_CLOSED_POSITIVE_POSSIBLE  # 三源>0 但仅 proxy 描述，需补清单才 ACTIONABLE 的中间态
      else:
          overall = AUTHORITY_CLOSED_POSITIVE_POSSIBLE
  elif variable_table_ge11 and break_even_has_all and minimal_action_table_done:
      overall = AUTHORITY_INPUTS_ACTIONABLE  # 已输出最小清单≥11项 + 每源三档阈值，有效完成（即使 composable null）
  ```
  实际落盘逻辑为严格按序 `EVIDENCE_INVALID > AUTHORITY_CLOSED_NO_POSITIVE_MARGIN (任一 conservative ≤0 止路) > AUTHORITY_CLOSED_POSITIVE_POSSIBLE (三源>0) > AUTHORITY_INPUTS_ACTIONABLE (已输出最小清单与阈值，有效完成)`，`first_match` 显式记录，**仅缺 `H_min` 而未输出清单与阈值不得判 `ACTIONABLE`** 已验
- [ ] **D2 互斥性校验**：脚本内 `assert overall in [...] 且仅一态`，`proxy_missing 保持 missing/null`，`shadow 不升级为 composable`，`missing 不填 0`，`rg "H_min.*=.*IAB|IAB.*H_min"` 无自行等价
- [ ] **D3 仅 `ACTIONABLE` 为有效完成**：报告显式声明“**已输出最小新增测量清单≥11项 + 每源 optimistic/shadow/composable(null) 与 0/5/10% 阈值表，有效完成；仅声明缺 `H_min` 不够**”，其余三态均为权威闭合或硬失败

## Phase E — 脚本与报告交付（DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN）

- [ ] **E1 编写 `scripts/v59_security_budget_authority_closure.py`** (decoder-free): `python scripts/v59_security_budget_authority_closure.py [--v57-json ...] [--v58-json ...] [--out-json ...] [--report ...] [--csv ...]` → A1 fetch/HEAD → A2 逐函数扫描 → A3 PIE_secure 裁决 → A4 IAB-chi 追踪 → B variable_table≥11 + decomposition → C break_even三档 + 0/5/10% margin → D first-match 四终态互斥 → 输出 `v59_secret_key_budget_authority.json + SECRET_KEY_BUDGET_AUTHORITY_REPORT.md + v59_break_even.csv` + 控制台摘要，`rg "decode_" 0 hits`，`py_compile` PASS，未创建 `run_01`，不改 `src//experiments//tools/` 且 `openspec/changes/formal-ir-v5[4-8]/` 零改
- [ ] **E2 撰写 `docs/research_cycles/V59P0/SECRET_KEY_BUDGET_AUTHORITY_REPORT.md`**：`formula_authority` 段（文件+函数+行号+原文 `not full niu_2016`）、`variable_table ≥11项`（symbol/meaning/unit/source/authority/decoder_free/minimal_new_measurement）、`decomposition table` 三源独立、`break_even` 三档与 `0/5/10%` 阈值表（含 `6.9238/7.2637/7.5820` 锚点）、`minimal 新增测量行动表`（按优先级排序，最小可执行采样/校准）、`overall` 终态与权威闭合声明，数据与 `json` 一致，显式 `V57-V58 m 冻结` + `tag已含不重复` + `三源分别不平均` + `proxy 不升级` + `missing→null`，不扩大为 `FER/SKR/晋升`
- [ ] **E3 自检（gate）**：`py_compile` PASS, `rg "decode_" 0 hits && rg "import.*decoder" 0 hits`, `git diff -- src/ ==0 && git diff -- experiments/ ==0 && git diff -- tools/ ==0 && git diff -- openspec/changes/formal-ir-v5[4-8]/ ==0`, 三源 `leak_without_tag/tag` 不重复已验，`GF32 5bits` 已验，`H/IAB/MAP !=H_min` 已验，不跨源平均已验，`break_even 锚点 leak/1024` 已验，`missing→null` 已验，`proxy 不升级` 已验，`四终态互斥 first-match` 已验，`variable_table≥11` 已验，`HEAD==origin` 已验，`run_01` 不存在已验
- [ ] **E4 推送新 SHA 并停留 `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN`**，未创建任何 `run_01` decoder 执行，不碰 `V57-V58 m`，`src//experiments//tools//V54-V58` 零改，普通推送（非 force）至 `formal-ir-mainline`，推送后等待独立审核（`Pre-RESULT` 独立线程复核 `HEAD/ACCEPTED_PLAN_SHA/rg 0 hits/run_01不存在/py_compile+关键测试 PASS`），`V60` 仍 `PENDING`，返回 `Plan SHA / implementation SHA / 权威裁决 / 三源阈值 / 行动表 / 终态`

## 本变更显式禁止

decoder 调用（`decode_* / construct_*` 等）；改 `V57-V58 m1/m2/leak` 或 `H1/Lane C/Δ/decoder` 冻参或新增矩阵；自创 `H_min / finite-key / composable` 公式或造 `eps_sec/vis` 参数；重复扣除 `tag 64`；把 `H/IAB/MAP` 当 `H_min` 不加 `missing`；将 `shadow` 升级为 `composable`；将 `missing` 填 `0` 而非 `null`；跨 source 平均 `hmin`；网格调参；宣称 `FER/SKR/阈值/晋升`；创建正式 `run_01` decoder 执行；改 `src//experiments//tools//V54-V58`；将总体平均掩盖单源阈值；将 `POSITIVE_POSSIBLE` 误升为 `ACTIONABLE`（未输出清单与阈值）；自动进入 `V60`。

## 验收

- proposal/design/tasks/specs 一致 HEAD 2340257d→新SHA 84d62779 lifecycle DIAGNOSIS_PLAN_READY DECODE_FORBIDDEN 四终态按 `EVIDENCE_INVALID > AUTHORITY_CLOSED_NO_POSITIVE_MARGIN(任一 conservative ≤0) > AUTHORITY_CLOSED_POSITIVE_POSSIBLE(三源>0) > AUTHORITY_INPUTS_ACTIONABLE(已输出最小清单≥11项 + 每源三档阈值，有效完成)` 互斥先匹配，**仅缺 `H_min` 不足以判 `ACTIONABLE`**，显式三源分别、tag 不重复、proxy 不升级、missing→null
- Phase A 逐函数权威 `H_min/finite/PE/auth/EV/post_sel` 单位已落盘 `formula_authority`，`PIE_secure` 裁决为 **仅 shadow/proxy** 已验，`IAB-chi ≟ H_min` 无声明已验，禁止 `H/IAB/MAP` 当 `H_min`
- Phase B exact 变量表≥11项（smooth min-entropy、phase-error、visibility 区间、PE sample、eps_sec/cor、finite、EV、post-selection、auth）已落盘，三源 `leak_without_tag 7025/7375/7700 +tag64=7089/7439/7764` 自洽，`GF32 5bits` 与 `H≠H_min` 已验，不跨源平均
- Phase C `hmin_break_even` 三档已落盘 `optimistic floor 6.9238/7.2637/7.5820 + shadow区间 + composable null`，`0/5/10% margin` 阈值 `h_m = (leak+other+finite)/(1024*(1-m))` 已算，锚点 `leak/1024` 双校验，`missing→null` 已验
- Phase D 四互斥 `first-match` 已验，`proxy 不升级` 已验，无网格
- Phase E 脚本 `rg 0 hits` `py_compile` PASS 报告与 json 一致 未建 `run_01` 已推新 SHA DIAGNOSIS_PLAN_READY/DECODE_FORBIDDEN 仅改本目录+`scripts/`+`docs/research_cycles/V59P0/`（`src//experiments//tools//V54-V58` 零改），`HEAD==origin` 已验，推送后等待独立审核，**不自动进入 `V60`**

