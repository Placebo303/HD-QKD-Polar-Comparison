# OpenSpec Tasks: formal-ir-v58-secret-key-budget-stoploss — V58 decoder-free 密钥预算止损

**Lifecycle**: `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN` — decoder-free 预算止损，不改 decoder/矩阵/信道估计器，三源独立止损门
**HEAD**: `337e3a79` → 新 SHA (branch `formal-ir-mainline`, 实施前以 `git fetch && git rev-parse HEAD == origin/formal-ir-mainline` 重核，不一致阻塞) + data SHA `84d62779` (84d62779 200ps legacy_v1 nearest 1024)
**Predecessor**: `formal-ir-v57-channel-recharacterization` `PREDICTIVE_MODEL_NOT_STABLE / DECODE_FORBIDDEN` (m1 981/1024/1024, m2 424/451/516, leak 7089/7439/7764, n1024, tag64, GF32 5bits)
**Boundary**: V57 披露完全冻结零改；每 block 1024 符号，64-bit tag 已含不得重复扣除，仅预算诊断；三源独立不平均；缺 H_min/缺单位/缺有限项权威则 `SECURITY_INPUTS_INCOMPLETE / DATA_INCOMPLETE` 止损；仅三源保守>0且margin≥0.10且权威闭合才允后继低维（仍不自动 decoder），`rg "decode_" 0 hits`，`git diff -- src/ ==0` 等

## Phase A — 只读公式调查（decoder-free，禁止自创，缺则 INCOMPLETE）

- [ ] **A1 fetch 与 HEAD 自检（阻塞门）**：`git fetch origin && git rev-parse HEAD == origin/formal-ir-mainline == 337e3a79`（或新 SHA），不一致则 `EVIDENCE_INVALID` 阻塞；记录 `HEAD/origin/implementation SHA` 至 `v58_secret_key_budget.json: provenance`，`rg "337e3a79" 0 hits` 旧 SHA 无残留
- [ ] **A2 权威公式 rg 定位（只读）**：`rg "DeltaFK|delta_fk|chi_E|PIE_secure|IAB_est|_security_calibrated_common|build_actual_ir_finite_key"` 定位候选权威文件，记录 `formula_authority = {delta_fk: {file, lines, expr, unit}, pie_secure: {file, lines}, chi_E, iab}`，明确 `bits/block` vs `bits/pair` vs `bits/symbol` 单位；禁止自创公式
- [ ] **A3 H_min^epsilon(A|E) 权威判定**：在仓内 `rg "H_min|min_entropy|H_min.*epsilon|secret.*key.*length|PA.*penalty"` 查找 `H_min` 定义；若仅有 `IAB_est` / `H(A|B)` 则标记 `weak_proxy=true` 且后继封顶 `FRAGILE`，若 `IAB_est` 未声明为 `H_min` 代理或 `epsilon` 预算缺失则直接 `SECURITY_INPUTS_INCOMPLETE` 分支（`DATA_INCOMPLETE` 子类），不造参数；落盘 `h_min_source` 与 `weak_proxy` 判定
- [ ] **A4 PE/finite/auth/EC 单位闭合**：明确 `PE penalty` / `finite-key` / `auth` / `EC leakage` 各自是否已含 `tag`、单位是否已统一到 `bits/block`，`n_eff` / `eps_sec/eps_cor/vis` 是否有仓内区间；缺决定性输入终态 `SECURITY_INPUTS_INCOMPLETE`，不 grid 调参；落盘 `unit_table`

## Phase B — 单位与重复扣除审计（decomposition table，三源独立）

- [ ] **B1 GF32 与 tag 校验**：逐源校验 `m_total == m1+m2` (`1405/1475/1540`) 且 `leak_total == 5*m_total+64` (`7089/7439/7764`)，`leak_without_tag =5*(m1+m2)` (`7025/7375/7700`)，`tag=64` 单计不重复；`log2 q=5` 显式记录；失败则 `EVIDENCE_INVALID`
- [ ] **B2 H(A|B) 不当 H_min 审计**：检查若 `min_entropy_budget` 借用 `H(A|B)` / `IAB_est` 则显式 `weak_proxy=true` 并报告 `H(A|B) != H_min` 语义差，且终态最高 `POSITIVE_BUT_FRAGILE`，不允 `POSITIVE_KEY_MARGIN`；正宗 `H_min` 需有权威文件行号支撑
- [ ] **B3 不跨 source 平均校验**：分解表三源独立列，禁止 `mean(ell)` 替代逐源 `ell_final`；脚本内 `assert` 三源分别计算，报告不出现总体平均替代
- [ ] **B4 decomposition table 落盘**：`v58_secret_key_budget.json: decomposition [ {source, min_entropy_budget, ell_before_IR, leak_without_tag, tag64, other, finite, ell_final, per_pair, margin_ratio, weak_proxy} ]` 三源独立，`py_compile` 前已验

## Phase C — 三源机械重算（ell_final = min_entropy - ir - other - finite）

- [ ] **C1 每源 ir_disclosure**：`ir = leak_total =5*m_total+64` (已含 tag)，三源 `7089/7439/7764`，不重复扣 tag
- [ ] **C2 每源 budget 与 other/finite**：`min_entropy_budget = n * h_min_per_symbol` (或权威 `per-block` 直接值，单位已验)，`other = auth + PE` (权威区间，无则 0 + `no_authority_other` 标签)，`finite = DeltaFK` (单位已验，无权威则 `SECURITY_INPUTS_INCOMPLETE` 分支)；落盘三源 `ell_before_IR = budget - other - finite`
- [ ] **C3 ell_final 与诊断**：逐源 `ell_final = ell_before_IR - ir`，`per_pair = ell_final/1024`, `margin_ratio = ell_final / min_entropy_budget`，报告 `ell_before_IR / leak_without_tag / tag64 / other / finite / ell_final / per_pair / margin_ratio`；三源独立
- [ ] **C4 零边界自检**：`ell_final ==0` 归为 `NO_POSITIVE_KEY_MARGIN`（`≤0` 含 0），`margin ==0.10` 恰为 `POSITIVE_KEY_MARGIN` 下界（含），单测覆盖

## Phase D — 敏感性边界（仅区间传播，禁止网格）

- [ ] **D1 区间传播**：仅对仓内权威区间 `[low, high]`（`eps_sec/eps_cor/vis/IAB_est` 若有）做 `conservative`（`h_min low, other high, finite high, ir high`）与 `optimistic` 两端传播；`rg "grid|param_grid|GridSearch" 0 hits`（禁止网格），落盘 `sensitivity: {conservative:{ell, margin}, optimistic:{ell, margin}, cross_zero_flag}`
- [ ] **D2 无区间占位**：若无权威区间则 `conservative==optimistic` 且 `interval_tag="no_interval"`，显式报告不假装区间
- [ ] **D3 weak_proxy 敏感性**：若 `weak_proxy` 则同时报告 `with_proxy` 与 `without_proxy (=INCOMPLETE)` 对比，证明 `FRAGILE` 封顶

## Phase E — 终态 first-match 与报告交付（DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN）

- [ ] **E1 总体判定（优先级互斥 first-match）**：
  ```
  if not unit_ok or leak !=5*m+64 or m_total != m1+m2:
      overall = EVIDENCE_INVALID
  elif h_min_missing or unit_missing or finite_coeff_missing:
      overall = SECURITY_INPUTS_INCOMPLETE  # 含 DATA_INCOMPLETE
  elif any(ell_conservative_s <= 0 for s in sources):  # 含 0
      overall = NO_POSITIVE_KEY_MARGIN  # 任一源保守 ≤0 立即止路
  elif any(weak_proxy_s) or any(margin_conservative_s < 0.10) or any(cross_zero_s):
      overall = POSITIVE_BUT_FRAGILE  # >0但薄或跨0或弱代理
  else: # 三源均 conservative>0 && margin≥0.10 && !weak_proxy && !incomplete
      overall = POSITIVE_KEY_MARGIN  # 才允后继低维模型，仍不自动 decoder
  ```
  落盘 `overall` 与 `shunt_per_source` 至 `v58_secret_key_budget.json: verdict`，`first_match` 显式记录
- [ ] **E2 仅 POSITIVE_KEY_MARGIN 才允后继**：报告显式声明“**仅 POSITIVE_KEY_MARGIN 才允许另起后继（低维 decomposition）且仍需新 OpenSpec + DECODE_FORBIDDEN + 双重 review，不自动 decoder**”；其余四态均“**不允许 decoder / 不进入后继**”
- [ ] **E3 编写 `scripts/v58_secret_key_budget_stoploss.py`** (decoder-free): `python scripts/v58_secret_key_budget_stoploss.py [--v57-json ...] [--out-json ...] [--report ...] [--csv ...]` → A1 fetch/HEAD → A2 rg → A3 H_min 决策 → B 分解表 → C ell 重算 → D 区间 → E first-match → 输出 `v58_secret_key_budget.json + SECRET_KEY_BUDGET_REPORT.md + csv` + 控制台摘要，`rg "decode_" 0 hits`，`py_compile` PASS，未创建 `run_01`，不改 `src//experiments//tools/`
- [ ] **E4 撰写 `docs/research_cycles/V58P0/SECRET_KEY_BUDGET_REPORT.md`**：`formula_authority` 段（文件+行号）、`decomposition table` 三源独立、`ell` 明细与 `per_pair/margin`、`sensitivity` 上下界、`overall` 终态与止损声明，数据与 `json` 一致，显式 `V57 m 冻结` + `tag已含不重复` + `三源分别不平均` + `弱代理封顶`，不扩大为 `FER/SKR`
- [ ] **E5 自检（gate）**：`py_compile` PASS, `rg "decode_" 0 hits && rg "import.*decoder" 0 hits`, `git diff -- src/ ==0 && git diff -- experiments/ ==0 && git diff -- tools/ ==0`, 三源 `leak_without_tag/tag` 不重复已验，`GF32 5bits` 已验，`H(A|B)!=H_min` 已验，不跨源平均已验，`ell=0` 与 `margin 0.10` 边界已验，`source一正两负不平均` 反例已验，缺 `H_min` 必 `INPUTS_INCOMPLETE` 已验，`HEAD==origin` 已验，`run_01` 不存在已验
- [ ] **E6 推送新 SHA 并停留 `DIAGNOSIS_PLAN_READY / DECODE_FORBIDDEN`**，未创建任何 `run_01` decoder 执行，不碰 `V57 m`，`src//experiments//tools/` 零改，推送后等待独立审核（`Pre-RESULT` 独立线程复核 `HEAD/ACCEPTED_PLAN_SHA/rg 0 hits/run_01不存在/py_compile+关键测试 PASS`），`V59` 仍 `PENDING`

## 本变更显式禁止

decoder 调用（`decode_* / construct_*` 等）；改 `V57 m1/m2/leak` 或 `H1/Lane C/Δ/decoder` 冻参或新增矩阵；自创 `H_min / finite-key` 公式或造 `eps_sec/vis` 参数；重复扣除 `tag 64`；把 `H(A|B)` 当 `H_min` 不加 `weak_proxy`；跨 source 平均 `ell`；网格调参；宣称 `FER/SKR/阈值/晋升`；创建正式 `run_01` decoder 执行；改 `src//experiments//tools/`；将总体平均掩盖单源负余量；将 `POSITIVE_BUT_FRAGILE` 误升为 `POSITIVE_KEY_MARGIN`。

## 验收

- proposal/design/tasks/specs 一致 HEAD 337e3a79→新SHA 84d62779 lifecycle DIAGNOSIS_PLAN_READY DECODE_FORBIDDEN 终态 5 选 1 按 `EVIDENCE_INVALID > SECURITY_INPUTS_INCOMPLETE > NO_POSITIVE_KEY_MARGIN(任一 conservative ≤0) > POSITIVE_BUT_FRAGILE(>0但 margin<0.10或跨0或弱代理) > POSITIVE_KEY_MARGIN(三源 conservative>0&&margin≥0.10全权威闭合)` 互斥先匹配，显式三源分别、tag 不重复、弱代理封顶、仅 `POSITIVE_KEY_MARGIN` 才允后继低维且仍不自动 decoder
- Phase A 权威 `H_min/finite/PE/auth/EC` 单位已落盘 `formula_authority`，缺 `H_min` 则 `SECURITY_INPUTS_INCOMPLETE` 已验，禁止自创
- Phase B 分解表三源独立 `leak_without_tag 7025/7375/7700 +tag64=7089/7439/7764` 自洽，`GF32 5bits` 与 `H(A|B)!=H_min` 已验，不跨源平均
- Phase C `ell_final = budget - ir - other - finite` 三源分别已落盘 `ell_before_IR/leak_without_tag/tag/other/finite/ell_final/per_pair/margin_ratio` 与 `conservative/optimistic` 两端，`ell=0` 归 `NO_MARGIN` 已验
- Phase D 仅区间上下界传播已验，`margin 0.10` 阈已验，无网格
- Phase E 脚本 `rg 0 hits` `py_compile` PASS 报告与 json 一致 未建 `run_01` 已推新 SHA DIAGNOSIS_PLAN_READY/DECODE_FORBIDDEN 仅改本目录+`scripts/`+`docs/research_cycles/V58P0/`（`src//experiments//tools/` 零改），`HEAD==origin` 已验，推送后等待独立审核
