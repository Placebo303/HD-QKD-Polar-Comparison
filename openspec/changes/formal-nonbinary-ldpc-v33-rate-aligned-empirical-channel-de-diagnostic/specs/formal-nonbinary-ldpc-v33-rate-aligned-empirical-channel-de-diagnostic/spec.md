# Spec Delta: formal-nonbinary-ldpc-v33-rate-aligned-empirical-channel-de-diagnostic

> **Status: DRAFT_PENDING_FREEZE_REVIEW** — SHALL 条款候选；判敛公式细节于
> freeze review 逐字定稿。

## Scope

ensemble/channel 层 DE diagnostic（V26 posterior-population full-vector MC-DE）：
在 V25 empirical joint P(A,B)（仅 train N_ab）、F03/A02 分配、V31 实际层率下，
判定三源两层 DE 是否全部收敛。非 fixed-packet / 非 QC matrix / 非 finite graph；
无码构造/decoder/FER/性能预测。DE 执行需冻结 + 显式授权。

## Definitions

- 输入语义：A=Alice label，B=Bob symbol；P(A,B)=N_ab/total，仅
  `{sid}_N_ab_train_N_ab_train` 三键；validation/holdout 禁入。
- Factorization：F03_natural_MSB_to_LSB_GF32_plus_GF32；A02=F03；L1 then L2；
  q=32/width=5；L2=true-predecessor-conditioned。
- Actual rate：n=1024；m1=16；m2 绑定 source ID {1M:184, 1p5M:190, 2M:192}；
  R_i=1−m_i/1024；ρ_i=make_rho(R_i, lambda={2:1})；禁止 f=1.3 反推。
- 调用矩阵（候选）：3 sources × 2 layers × seeds 33101–33105 = 30 calls；
  n_samples=2000；max_iter=200；entropy_tol=0.01 bits/symbol；streak=20；
  RNG=PCG64。
- Run root = `.../nbldpc_v33_rate_aligned_empirical_de/run_01/`。
- Terminal 恰三类：PASS / FAIL(`rate_allocation_or_ensemble_fail`) /
  INCONCLUSIVE(`de_diagnostic_inconclusive`，reason codes 含
  `inconclusive_input_binding`)；聚合优先级 INCONCLUSIVE > FAIL > PASS。

## Requirements (SHALL)

### Inputs & Identity
- **SHALL-IN1**：DE channel construction SHALL 仅使用三源 train 计数矩阵；
  validation/holdout SHALL NOT 进入任何构造路径。
- **SHALL-ID1**：DE SHALL 标识为 posterior-population full-vector MC-DE；
  `not_fixed_packet_de=true` SHALL 出现于输出；fixed-packet/QC-matrix/
  finite-graph 结论 SHALL NOT 出现。
- **SHALL-FAC1**：层映射 SHALL 为 F03(A02)、L1→L2、q=32/width=5、L2 true-
  predecessor-conditioned。
- **SHALL-RATE1**：R_i 与 ρ_i SHALL 分别按 R_i=1−m_i/1024 与
  make_rho(R_i, lambda={2:1}) 构造并绑定精确 source ID；f=1.3 历史值 SHALL NOT
  参与任何 rate 推导或校验。

### Call Matrix & Exact-Once
- **SHALL-MC1**：调用矩阵 SHALL 采用候选冻结值（seeds 33101–33105/n_samples=
  2000/max_iter=200/entropy_tol=0.01/streak=20/RNG=PCG64），ACCEPT_FREEZE 前
  为主控可修订候选，之后不可变。
- **SHALL-X1**：30 calls SHALL 按固定顺序 exact-once 执行；每 call 持久化后方
  进入下一 call；重复 call 或缺失序号 ⇒ evidence inconsistent STOP。
- **SHALL-X2**：run root 已存在 ⇒ collision STOP；禁覆盖禁 run_02。

### Terminals & Aggregation
- **SHALL-T1**：call 三态定义 SHALL 按 PASS(有效+streak)/FAIL(max_iter 未达
  streak 含有限振荡)/INCONCLUSIVE(NaN/Inf/负概率/归一化/异常/资源中断) 机械判定。
- **SHALL-ZD1**：正概率抽样点命中非法 L2 conditional denominator 时，该 call
  SHALL 终止为 INCONCLUSIVE(reason=inconclusive_input_binding)；one-hot fallback
  或静默跳过 SHALL 被实现禁止并有测试覆盖。
- **SHALL-AGG1**：cell=(source,layer) SHALL 由 5 seeds 聚合（任一 INCONCLUSIVE ⇒
  cell INCONCLUSIVE；全 PASS ⇒ cell PASS；否则 FAIL）；overall SHALL 由 cells
  按优先级 INCONCLUSIVE > FAIL > PASS 机械映射；未覆盖组合 ⇒ inconclusive with
  reasons；禁止事后发明终态。

### Claim Boundary
- **SHALL-CB1**：即使 overall PASS，本变更结论 SHALL 仅限 "exact-rate
  empirical-P ensemble DE 通过"；不得声称 finite code/decoder/FER/QKD
  qualification/promotion 可行。

### Execution Authorization
- **SHALL-AU1**：主控 ACCEPT_FREEZE 前不得实现；实现 acceptance 前不得执行真实
  DE（含 smoke）；测试 SHALL 仅使用显式 fake DE runner。
- **SHALL-H1**：closeout 交付 candidate_only=true / main_acceptance_pending=true /
  qualification=false / promotion=false；最终声明逐字：
  「candidate_only，等待 Codex 主控 ACCEPT/REJECT；未运行 DE，未运行 decoder，未启动 successor。」

## Acceptance Mapping

| AC 组 | SHALL | 验证 |
|---|---|---|
| 输入/恒等 | IN1, ID1, FAC1, RATE1 | stage-0 + T0 断言 |
| 调用矩阵 | MC1, X1 | T2 fake 全流程 + 顺序断言 |
| 零分母 | ZD1 | T2 NaN/denominator fixture |
| 终态聚合 | T1, AGG1 | T2 三通道路由 + 重算 |
| 授权门 | AU1 | 守卫测试 + R1 报告 |
| 输出/handoff | X2, H1 | 目录清单 + 标志断言 |
