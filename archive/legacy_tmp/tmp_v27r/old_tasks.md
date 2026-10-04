# Tasks: formal-nonbinary-ldpc-v27-finite-leakage-margin-de-gate

Status: **DRAFT_PENDING_FREEZE_REVIEW（2026-08-19）**。只创建 OpenSpec；freeze review
ACCEPT 前**不实现、不执行**。ACCEPT 后按以下顺序实现。

## P0 — frozen inputs & freeze gate
- [ ] **P001** 只读复核 V26 归档（evidence/v26r_closeout.md、report、run_01/run_02
       readonly_verify）确认 A02 渐近 30/30 与 H_total 常数来源。
- [ ] **P002** 冻结 V27 参数：F03 GF32+GF32；`lambda={2:1}`；n={1024,2048,4096,8192}；
       64-bit 公开验证 tag 计入总泄漏；m_total 公式与预算表；entropy-proportional
       m1/m2 ±1/±2；screen seeds 27001–27002；confirm seeds 27101–27105；五层角标。
- [ ] **P102** 独立 freeze review ACCEPT 前不得开始实现。

## M0 — channel（复用 V26，只读）
- [ ] 复用 `nonbinary_v26_channel.ChannelAdapter`（F03 GF32+GF32）与
      `SOURCE_METADATA`（source↔delay 显式元数据）；不新造信道。
- [ ] 确认 worst-source `H1/H2`（0.02566205 / 0.80690067）与 `H_total` 从 V25/V26
      证据追溯。

## M1 — mechanism（复用 V26，只读）
- [ ] 复用 V26 M1 机制测试（bruteforce check-node、all-one、iteration-0、
      centered GF2 BSC reference、seed replay）；不新增内核。

## M2 — finite budget planner
- [ ] 实现 `m_total = floor((1.3·n·H_total − 64)/5)` 预算函数与冻结预算表
      （1024→208 / 2048→430 / 4096→873 / 8192→1760）。
- [ ] 实现 entropy-proportional `m1_ep=round(m_total·H1/H_total)`，
      `m2=m_total−m1`；测试带 `m1 ∈ {m1_ep−2,…,m1_ep+2}`。
- [ ] 可行性守卫：`0<=m1,m2<=m_total` 且 `R_i=1−m_i/n ∈ (0,1)`；不可行 n/拆分标记
      并进入 no-headroom/fail 判定。
- [ ] 单元测试：预算表数值、拆分带、可行性边界、总 f（含 64-bit tag）≤1.3。

## M3 — screen（2 seeds）
- [ ] 4 n × 5 m1 × 3 source × 2 layer × 2 seeds 的 screen 运行（n_samples=400，
      max_iter=100，seeds 27001–27002，tol=0.01，streak=20）。
- [ ] 每 (n, m1) 记录各 layer/source/seed 的 entropy 轨迹、rate、f、收敛与否。

## M4 — confirmation（5 seeds）
- [ ] 对每个 n 的最先通过拆分做 5-seed confirmation（n_samples=2000, max_iter=200，
      seeds 27101–27105）。
- [ ] 通过 = 3 source × 2 layer × 5 seeds 全收敛、无错误/非有限值、每层单独留证。

## M5 — terminal & evidence
- [ ] 判定 `pass_finite_budget_ready` / `de_pass_no_finite_headroom` /
      `fixed_ensemble_margin_fail`（design §6 优先级）。
- [ ] 独立只读 verifier 重算预算表/screen/confirmation/终态并持久化。
- [ ] 输出 RUN_MANIFEST（role + source↔delay 元数据 + 资源门结果）与 reports。

## Stop rules
- freeze review ACCEPT 前不实现/不执行。
- 全程不搜索 degree/m1/m2、不构造有限矩阵、不跑 FER/MET/qual/promo、不读 raw
  `.ttbin`、不改 factorization、不用 holdout、不 push。
