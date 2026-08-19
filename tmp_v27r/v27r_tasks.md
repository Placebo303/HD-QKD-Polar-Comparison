# Tasks: formal-nonbinary-ldpc-v27-finite-leakage-margin-de-gate  (V27R revision)

Status: **V27R DRAFT — source-adaptive 修订版，PENDING_FREEZE_REVIEW（2026-08-19）**。
本修订取代 change 内先前 worst-source 草案。只创建 OpenSpec；freeze review ACCEPT 前
**不实现、不执行**。ACCEPT 后按以下顺序实现。

## Phase A — V27R OpenSpec freeze（主线程只写，Luna 独立 review）
- [ ] **P001** 只读复核 V26 归档（evidence/v26r_closeout.md、report、run_01/run_02
      readonly_verify）确认 A02 渐近 30/30 与 H 常数来源；**不重跑 V26 DE**。
- [ ] **P002** 冻结 V27R 参数：F03 GF32+GF32；`lambda={2:1}`；
      block_len={1024,2048,4096,8192}；**source-adaptive** `m_total=
      floor((1.3·block_len·H_source−64)/5)`；冻结预算表
      1M:200/413/840/1693、1p5M:206/426/866/1745、2M:208/430/873/1760；
      m1_ep=round(m_total·H1/H_source)（Python round）；候选 m1∈{m1_ep−2…m1_ep+2}、
      m2=m_total−m1；64-bit 块级验证 tag 计入整块总泄漏（不在层间使用）；
      screen seeds 27001–27002；confirm seeds 27101–27105；排序 keys 与终态集合。
- [ ] **P102** 仅当 P0/P1 全部关闭后由**主线程**记录 P102 ACCEPT；在此之前不得开始
      实现。

## Phase B — implementation & execution（ACCEPT 后）
## M0 — channel（复用 V26，只读）
- [ ] 复用 `nonbinary_v26_channel.ChannelAdapter`（F03 GF32+GF32）与 `SOURCE_METADATA`
      （source↔delay 显式元数据）；不新造信道。
- [ ] 确认每-source full-precision `H1/H2`（1M:0.024280547/0.776757278、
      1p5M:0.025199497/0.800366555、2M:0.025662049/0.806900673）从 V25/V26 证据追溯。
      **不重跑 V26 DE。**

## M1 — mechanism（复用 V26，只读）
- [ ] 复用 V26 M1 机制测试（bruteforce check-node、all-one、iteration-0、centered
      GF2 BSC reference、seed replay）；不新增内核。

## M2 — finite budget planner
- [ ] 实现 **source-adaptive** `m_total = floor((1.3·block_len·H_source − 64)/5)`
      预算函数与冻结预算表（source/block_len 上表）。
- [ ] 实现 `m1_ep=round(m_total·H1/H_source)`（Python round，round-half-to-even），
      候选 `m1 ∈ {m1_ep−2,…,m1_ep+2}`、`m2=m_total−m1`。
- [ ] 实现 `block_len` 与 `mc_samples` **两个不同字段**（不混用）。
- [ ] candidate_id=`(block_len, source, m1)`；去重、合法性守卫
      (`0<=m1,m2<=m_total` 且 `R_i=1−m_i/n∈(0,1)`)、排序 keys：
      `worst_final_entropy`、`mean_final_entropy`、`abs(offset)`、`m1`（升序）。
- [ ] T0/T1 测试：预算表数值、candidate enumeration、去重、合法性、排序确定性、
      rate/rho reconstruction、source metadata、terminal precedence、资源门与
      checkpoint 绑定（见 M5）。

## M3 — screen（完整执行后 confirmation）
- [ ] **screen 完整执行**全部候选：4 block_len × 3 source × 5 候选 × 2 层 ×
      screen_seeds [27001,27002]，mc_samples=400，max_iter=100，local tol=0.01，
      streak=20。
- [ ] 每 (block_len, source, candidate) 记录 worst_final_entropy / mean_final_entropy、
      各层 entropy 轨迹、rate、f（含块级 tag）。

## M4 — confirmation（每个 (block_len, source) 按排序依次）
- [ ] screen 全部跑完后，对每个 (block_len, source) 按排序 keys 从第 1 名依次确认；
      失败则继续下一个，直到通过或 5 个候选全失败。
- [ ] 单候选通过 = 2 层 × confirm_seeds [27101..27105] 全收敛且无错误/非有限值
      （mc_samples=2000，max_iter=200，local tol=0.01，streak=20）。
- [ ] **pass = 存在同一 block_len 使三 source 均有确认通过候选**；多块长满足取最小
      block_len。

## M5 — terminal & evidence
- [ ] 判定终态（仅允许）：`pass_finite_budget_ready` / `de_pass_no_finite_headroom` /
      `implementation_blocked` / `resource_blocked`（优先级：先实现/资源阻塞，
      再找 passing block_len）。
- [ ] **24h 全局 completed-call 累计资源门**（`RESOURCE_LIMIT_SECONDS`）：超限 →
      `resource_blocked`，dir 记录 blocked=true。
- [ ] checkpoint 必须绑定完整 frozen configuration（source-adaptive 预算表、rounding
      规则、候选、screen/confirm 参数、排序 keys、终态、资源门）。
- [ ] 独立只读 verifier 重建完整计划、预算、调用、排序、resource/checkpoint 与终态；
      持久化 RUN_MANIFEST（role + source↔delay 元数据 + 资源门结果）与 reports。

## Luna worker 独立 review
- [ ] Phase A：Luna worker 做**独立 freeze review**（V27R OpenSpec）。
- [ ] Phase B：Luna worker 做**完整 candidate-delivery review**（budget planner、
      candidate enumeration、排序、seeds、资源门、checkpoint）。
- [ ] 主线程拥有 ACCEPT 与科学结论。

## Stop rules
- freeze review ACCEPT 前不实现/不执行。
- 全程不搜索 degree/m1/m2、不构造有限矩阵、不跑 FER/MET/qual/promo、**不重跑 V26**、
  不读 raw `.ttbin`、不改 factorization、不用 holdout、不 push。
- 失败/资源阻塞证据全保留，不调参、不重跑、不覆盖现有 output root。
