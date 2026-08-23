# Proposal: formal-nonbinary-ldpc-v33-rate-aligned-empirical-channel-de-diagnostic

> **Status: DRAFT_PENDING_FREEZE_REVIEW** — 本四件套为 freeze-review 候选。
> 主控 ACCEPT_FREEZE 前：§5 调用矩阵仍为候选值；不得实现任何代码；不得执行任何 DE
> （含 smoke）；OpenCode 无权自行宣告 ACCEPT_FREEZE。

## Positioning

V32 operating-point audit correction（ACCEPTED，归档于
`openspec/changes/archive/2026-08-23-formal-nonbinary-ldpc-v32-operating-point-audit-correction/`）
确立的唯一下一问题在本变更中给出定义与执行方案：

> 在 V25 empirical joint P(A,B)、F03/A02 分配和 V31 实际层率下，
> 对应 ensemble DE 是否在三源、两层全部收敛？

本变更是 **ensemble/channel 层 diagnostic**：DE 是 ensemble 分析
（`not_fixed_packet_de=true`），不是 fixed QC packet / QC matrix / finite graph 的
任何计算。不做码构造、decoder、FER、性能预测、sweep 调参；不启动 corrected
matched-B1、NB-Polar 或任何 successor。

## Frozen Input Bindings（只读）

1. **R3**：V25 `run_04/channel_counts.npz`，**仅使用三源 `{sid}_N_ab_train_N_ab_train`
   键**（train split）；validation/holdout 一律不得进入 DE channel construction。
2. 语义：行=Alice label A，列=Bob symbol B；P(A,B)=N_ab/total。
3. **R6/R7**：V31 `RUN_MANIFEST.json` / `m1_registry.json`（allocation
   `m1_16_n1024` 过滤）/ `matrix_audits.json` packet_id——仅用于层率与分配恒等校验。
4. **R5**：V26 run_02 gate/best_passing_f——仅只读历史对照，不得外推至 V31 层率，
   不得替代本轮 exact-rate 结果。

## Factorization Identity

`F03_natural_MSB_to_LSB_GF32_plus_GF32`；A02=F03；解码序 L1 then L2；q=32、
width=5；L2=true-predecessor-conditioned（P(U2|B,U1)）。

## Actual-Rate Construction（禁止 f=1.3 反推）

- n=1024；m1=16；
- m2 按 source 精确绑定：1M→184、1p5M→190、2M→192；
- R_i = 1 − m_i/1024（per source、per layer）；
- ρ_i 仅由 `make_rho(R_i, lambda={2:1})` 构造；
- **禁止**以历史 f=1.3 反推或校验 rate；V26 f=1.3 仅作只读历史对照。

## DE Identity

V26 posterior-population full-vector MC-DE（与 V26 同族方法、经验总体注入）。
非 fixed-packet DE、非 QC matrix DE、非 finite graph 仿真。

## Candidate Call Matrix（ACCEPT_FREEZE 前为候选值）

3 sources × 2 layers × 5 seeds = **30 calls**：

| 参数 | 候选冻结值 |
|---|---|
| seeds | 33101–33105（升序） |
| n_samples | 2000 |
| max_iter | 200 |
| entropy_tol | 0.01 bits/symbol |
| streak | 20 |
| RNG | PCG64 |

主控 ACCEPT_FREEZE 可在 freeze 前修订上表；freeze 后即为不可变冻结值。

## Terminal States 与聚合（恰三类 + reason codes）

- **PASS**（call 级）：数值全程有效且达到 streak；
- **FAIL**（call 级）：有效运行至 max_iter 仍未达 streak，含有限振荡；
- **INCONCLUSIVE**：binding 漂移 / NaN / Inf / 负概率 / 归一化失败 / 异常 /
  资源中断；零分母情形 reason=`inconclusive_input_binding`（见 §Zero-Denominator）。

聚合规则与优先级（candidate，freeze review 定稿）：
- **cell=(source,layer)**：任一 seed-call INCONCLUSIVE ⇒ cell INCONCLUSIVE（携带
  reasons）；否则 5 calls 全 PASS ⇒ cell PASS；否则 cell FAIL。
- **overall**：任一 cell INCONCLUSIVE ⇒ overall INCONCLUSIVE；否则全部 cell PASS ⇒
  overall PASS(`pass_rate_aligned_empirical_de`)；否则 overall
  FAIL(`rate_allocation_or_ensemble_fail`)。
- 优先级：INCONCLUSIVE > FAIL > PASS；未覆盖组合 → inconclusive with reasons。

## Exact-Once Execution

固定顺序枚举 30 calls（source 序 1M→1p5M→2M × 层序 L1→L2 × seed 升序）；每 call
持久化完成后才进入下一 call；输出根已存在 ⇒ STOP collision；禁止 run_02、rerun、
tuning、补 seed、screen/rank/select。

## Zero-Denominator Rule

正概率抽样点出现非法 L2 conditional denominator 时，该 call 必须终止并标记
INCONCLUSIVE(reason=`inconclusive_input_binding`)；**禁止静默 one-hot fallback**，
禁止跳过样本继续统计。

## Claim Boundary

即使未来 overall PASS，也只说明 exact-rate empirical-P ensemble DE 通过；
**不证明** finite code、decoder、FER、QKD qualification 或 promotion；fixed-packet
结论须另行授权 finite-control change。

## Output Root（唯一）

`comparison_bench/outputs_comparison/nonbinary_diagnostics/nbldpc_v33_rate_aligned_empirical_de/run_01/`
已存在 ⇒ STOP collision；禁覆盖禁自动 run_02；所有写操作仅限该根。

## Lifecycle Gates

1. 主控 ACCEPT_FREEZE 前不得实现；
2. 实现 acceptance（测试全过 + 独立候选验收）前不得 execute；
3. OpenCode 无权自行 ACCEPT_FREEZE 或授权执行。
