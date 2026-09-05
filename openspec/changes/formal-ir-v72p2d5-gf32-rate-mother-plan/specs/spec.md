# D5 Spec Delta：F 模型两层 GF32 码率与嵌套母矩阵合同（计划冻结）

状态：`PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`。本 delta 只冻结数学与接口合同，
不合并、不替代 D1/D3/D4 行为。本周期不实现、不运行 decoder、不读 VAL、不创建输出。

## S-PRIOR：F → 两层 prior 合同

- S-PRIOR-01：映射 SHALL 为 `A=32*U1+U2`（`U1=high/MSB`，`U2=low/LSB`，`bit0=LSB`），
  同方向、无 Gray、无置换；`P_F(A|B)` SHALL 为 `(1024,1024)` 列归一（`axis1=Bob`）。
- S-PRIOR-02：canonical counts SHALL 唯一采用 `counts[a,b]=count(Alice=a,Bob=b)`；
  `P1(U1|B)` SHALL 为 `reshape(32,32,1024)=(U1,U2,Bob)` 后对 U2 轴求和再列归一；
  `P2(U2|U1,B)` SHALL 为固定 `(U1,B)` 切片行归一；转置输入 SHALL 被不对称手算反例捕获。
- S-PRIOR-03：平滑 SHALL 为 D4R2 frozen `lambda*=137.3823795883264` 单系数，
  施加于 counts 列方向后列归一；SHALL 先归一后 floor。
- S-PRIOR-04：floor SHALL 双轨分离：审计/CE 用 `1e-300`（`max(P,1e-300)` 后取 log2，
  floor 后重归一）；decoder 通路用 `1e-15`（V54/v35 历史语义，floor 后重归一）；
  零质量 `(U1,B)` 切片 SHALL 回退均匀 `1/32`，SHALL NOT 删样本。
- S-PRIOR-05：`CE_L2_oracle` SHALL 用真实 `U1`（`v35.get_conditional_posterior_l2` 语义），
  仅作分层预算诊断；生产 L2 prior SHALL 为 `prior_l2=q@P`（`q=softmax(L1 final_beliefs)`，
  `v54.get_l1_app_prior_l2` 语义，签名禁 Alice/oracle）；SHALL NOT 把 oracle CE 引用为生产可达性能。
- S-PRIOR-06：存储与传递 SHALL 为概率域；decoder 入口 SHALL 为 `(N,32)` 概率域
  （decoder 内部转 log-belief）；CE SHALL 为 log2；`P1` 表 SHALL 为 `(32,1024)` 列和 1。
- S-PRIOR-07：链式 SHALL 满足 `|CE_joint-CE_L1-CE_L2_oracle|<1e-10`（float64）；超限 SHALL 为 `BLOCKED`（数学错）。
- S-PRIOR-08：与现有接口的唯一 delta SHALL 为 §1.6 的 `lambda*` 平滑插入声明；
  下游 `reshape` 求和 / `q@P` / `decode_row_layered_fftqspa(H(m,n),priors(N,32),syndromes(m,))`
  SHALL 逐字复用历史语义（`max_iter=90`，`damping_alpha=1.0`，`warm_beliefs=None` cold）；
  若接口形状不一致 SHALL 报 `BLOCKED`，SHALL NOT 猜测绕过。

## S-BUDGET：行数合同

- S-BUDGET-01：`rows_required(layer)` SHALL 为 `ceil(N*CE_layer*f/5)`；
  分层独立 ceil SHALL 为权威口径，`m_total=m1+m2`；joint-ceil 仅对照，0–1 行差异 SHALL 记录为 ceil 伪影。
- S-BUDGET-02：`n=1024` 行数表 SHALL 为 design §2.1（`f=1.0`：`m1=782/m2=686`；
  `f=1.05`：`821/720`；`f=1.1`：`860/755`；`f=1.2`：`938/823`）。
- S-BUDGET-03：旧 `16/200/216` 行 SHALL 禁止用于当前域真实实验；
  不足 SHALL 只记 `MODEL_BUDGET_MISMATCH`；SHALL NOT 称信息论极限/GF32 失败/LDPC 不可能；
  L1 不足 SHALL NOT 只加 L2。
- S-BUDGET-04：“约 700–1000 行” SHALL 按 per-layer `M_max=1000` 解释（design §2.3）；
  统一 total 解读 SHALL 维持 route C 不进入真实实验；实现阶段 SHALL NOT 重新解释。

## S-MOTHER：嵌套母矩阵合同

- S-MOTHER-01：每层 mother SHALL 为一次性构建的单个 `(1000,1024)` uint8 矩阵（值域 `0..31`），
  基线构造器 SHALL 为 V31 QC-cyclic-projective `build_layer`；Lane-C SHALL 仅为备份（D5 内不并行）。
- S-MOTHER-02：披露 SHALL 为行前缀 `H[:k]`，`k` SHALL 取自冻结集合
  `L1 {782,821,860,938}` / `L2 {686,720,755,823}`；对一切已披露 `k` SHALL 有 `gf_rank(H[:k])==k`；
  后增行 SHALL NOT 改动前缀行。
- S-MOTHER-03：稀疏度 SHALL 为列重恒 2、行重目标 2–4、零行/零列为 0、`support occupancy≤31`。
- S-MOTHER-04：披露 API SHALL 为最小形状 `m_max: int + prefix_rows: int + extra_rows: list[int] | None`
 （默认 None = 前缀 `0..k-1`，生产恒 None）；SHALL NOT 引入通用框架/注册表/版本包装。
- S-MOTHER-05：披露顺序 SHALL 为 L1 先收敛再开 L2（L1 APP `q` 恒喂 L2；L2 内 base→joint→total 短路）；
  联合同步披露 SHALL deferred。
- S-MOTHER-06：V72P0 binary IRA mother SHALL 只作结构参考；SHALL NOT 直接假设适用于 GF32
 （域/维度/码率 regime/decoder 四边界见 design §3.3）。

## S-SYNTH：matched synthetic 合同

- S-SYNTH-01：synthetic 生成 SHALL matched to F（`B∼P_CAL(B)` CAL-only 边际 + `A∼P_F(·|B)` 采样，
  真值表取 `lambda*` 平滑表）；SHALL NOT 用 AWGN/BSC/QSC 替代；SHALL NOT 碰 VAL。
- S-SYNTH-02：门控 prior SHALL 用真 `P_F` 表（无估计误差）；`max_iter` SHALL 为 90，
  `damping_alpha` SHALL 为 1.0，`warm_beliefs` SHALL 为 None，tag SHALL 不生成不计费。
- S-SYNTH-03：种子 SHALL 为冻结列表；`n=64` SHALL ≥100 blocks；`n=256` SHALL ≥200 blocks。

## S-GATE：三级门控与生死实验

- S-GATE-01：G0 tiny SHALL 验证边际/条件与暴力误差 `<1e-12`、链式 `<1e-10`、无噪精确恢复 100%。
- S-GATE-02：G1 `n=64` SHALL 验证单调 `FER(1.2)≤FER(1.0)` 且 oracle-L2 ≥ APP-fed 且零 crash/非有限；
  G1 SHALL 无杀权，失败 SHALL 只做三分归因（数学错 vs 图/scale 错 vs 实现错，prior 错 excluded）。
- S-GATE-03：G2 `n=256` SHALL 为 D5 唯一杀实验：`f∈{1.0,1.1,1.2}` 三点扫描，
  行数 `m1={196,215,235}` / `m2={172,189,206}`；
  PASS SHALL 为 `f=1.2` 端到端精确恢复率 ≥90% 且单调且 oracle-L2 ≥ APP-fed；
  否则 SHALL 为 FAIL（`<50%` 记 `GF32_ROUTE_DEAD`，`50–90%` 记 `GF32_INSUFFICIENT_AT_BUDGET`，
  两者均放弃 n=1024 真实，后继仅 `d=256` backlog，不调参不加行不重跑）。
- S-GATE-04：`n=1024` 真实执行前置 SHALL 为 G0+G1+G2 全过 + Pre-EXECUTE review 通过。

## S-STOP：边界与停止

- S-STOP-01：本轮 SHALL 只做文档计划；SHALL NOT 写 `.py` 生产文件、调用 decoder、读 VAL、
  创建正式输出/`run_01`、授予执行。
- S-STOP-02：SHALL NOT 引入 checksum/hash/tag/签名或内容校验字段。
- S-STOP-03：冻结阈值（行数表、floor、`lambda*`、PASS/FAIL 线、披露集合）SHALL NOT 在实现后回写放宽；
  歧义 SHALL 停下返回 planner/OpenSpec 修订（新 SHA 重审）。
