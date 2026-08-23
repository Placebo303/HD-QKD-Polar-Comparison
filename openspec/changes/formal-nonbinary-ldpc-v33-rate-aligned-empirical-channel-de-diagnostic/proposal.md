# Proposal: formal-nonbinary-ldpc-v33-rate-aligned-empirical-channel-de-diagnostic

> **Status: DRAFT_PENDING_FREEZE_REVIEW** — 本四件套为 freeze-review 候选。
> 主控 ACCEPT_FREEZE 前：§Candidate Call Matrix 仍为候选值；不得实现任何代码；
> 不得执行任何 DE（含 smoke）；OpenCode 无权自行宣告 ACCEPT_FREEZE。

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

## Input Bindings

输入绑定以 **spec.md 的 canonical Binding Registry R1–R7 为唯一规范定义**
（SHALL-BIND1：完整路径、精确 key、用途与边界均在表中）。本文件不维护缩略
registry 副本。关键语义重述（规范文本见 spec）：

- 全部只读；persisted terminal distrust 惯例沿用。
- **仅使用三源 train 键**（逐字字面量见 spec Source ID 绑定表）；
  validation/holdout 一律不得进入 DE channel construction。
- 语义：行=Alice label A，列=Bob symbol B；P(A,B)=N_ab/total；简称 1M/1p5M/2M
  仅为标签，实现必须按完整 source ID 映射。
- R5 仅 allocation/packet identity 核对，非任何 DE 输入；
- R6 仅读 source/allocation ID、m1、m2、rate、H identity，禁止继承 V31 DE 参数；
- R7 仅只读方法身份对照，不可外推至 V31 层率。

## Factorization Identity

`F03_natural_MSB_to_LSB_GF32_plus_GF32`；A02=F03；解码序 L1 then L2；q=32、
width=5；L2=true-predecessor-conditioned（P(U2|B,U1)）。
GF(32) 身份冻结：`GF2mField.create(32)`、primitive polynomial = **37**
（0b100101）、polynomial basis；symbol encoding / field_id =
`c3a3660aa3cfbf788568cf366ee5de345ddc6be0372154a702c9e244a53bc6cf`
（与 V31 manifest 一致）。

## Actual-Rate Construction（禁止 f=1.3 反推）

- n=1024；m1=16；
- m2 按 source ID 精确绑定（canonical registry 表）：184/190/192；
- R_i = 1 − m_i/1024（per source、per layer）；
- ρ_i 仅由 `make_rho(R_i, lambda={2:1})` 构造；
- **禁止**以历史 f=1.3 反推或校验 rate；V26 f=1.3 仅作只读历史对照（R7）。

## DE Identity

V26 posterior-population full-vector MC-DE（与 V26 同族方法、经验总体注入）：
每次抽取自 flatten 后的 P_s(A,B)；三源独立永不合并；L1 用 P(U1|B)；L2 用同一
真实 A 的真实 U1 构造 P(U2|B,U1)；后验按真实 layer symbol GF-XOR centering
（真值 index 0）；PCG64 固定 draw order。非 fixed-packet DE、非 QC matrix DE、
非 finite graph 仿真。

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

- **PASS**（call 级）：数值全程有效且达到 streak（判敛判据见 design §2 步骤 4：
  population mean categorical entropy H_t 连续 20 iterations < 0.01 bits/symbol）；
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

## Exact-Once Execution 与 Official Run Lifecycle

固定顺序枚举 30 calls（source 序 1M→1p5M→2M × 层序 L1→L2 × seed 升序）；每 call
持久化完成后才进入下一 call；禁止 run_02、rerun、tuning、补 seed、screen/rank/select。

Official run lifecycle（fix B4）：一次正式 execute 的入口检查 run_01——已存在 ⇒
collision STOP；否则创建 run_01 → 写 pre-execution manifest → 按固定顺序执行
30 calls。同一次 execute 内的后续阶段不再重新触发 root collision。所有 fake tests
只写 workspace fresh root，绝不创建 official run_01。

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
即上节 official run lifecycle 所指的唯一 additive 根；所有写操作仅限该根。

## Lifecycle Gates 与 Review IDs

1. **FR1 freeze review**：reviewer-go 只读审查本四件套 → 主控 ACCEPT_FREEZE 前不得
   实现；
2. 实现 acceptance（测试全过 + **IR1 implementation candidate review**）前不得
   execute；candidate 完成后停在 `IMPLEMENTATION_ACCEPTED / EXECUTE_NOT_AUTHORIZED`；
3. 执行后由独立 reviewer 做 **ER1 post-execution read-only evidence review**；
4. OpenCode 无权自行 ACCEPT_FREEZE、implementation ACCEPT 或授权执行。
