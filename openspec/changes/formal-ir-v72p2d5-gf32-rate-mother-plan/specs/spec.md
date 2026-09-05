# D5 Spec Delta R2：F 模型两层 GF32 码率与嵌套母矩阵合同（计划冻结；PLAN_REVISE_REQUIRED）

状态：`PLAN_REVISE_REQUIRED`（R2；R1 已被 `PLAN_CORRIGENDUM_R2.md` 宣告 superseded，仅作历史保留）。本 delta 只冻结数学与接口合同，
不合并、不替代 D1/D3/D4 行为。本周期不实现、不运行 decoder、不读 VAL、不创建输出、不构建 full mother。
`M_max=1000 is a D5 synthetic construction cap, not a production sufficiency claim.`

## S-PRIOR：F → 两层 prior 合同

- S-PRIOR-01：映射 SHALL 为 `A=32*U1+U2`（`U1=high/MSB`，`U2=low/LSB`，`bit0=LSB`），
  同方向、无 Gray、无置换；`counts.shape` SHALL 为 `(Alice,Bob)`，`P_F.shape` SHALL 为 `(Alice,Bob)`，
  `axis0` SHALL 为 Alice，`axis1` SHALL 为 Bob；对 every `b` SHALL 有 `sum_a P_F[a,b]=1`，
  即 `assert_allclose(P_F.sum(axis=0),1.0)`。SHALL NOT 使用“axis1 列归一”歧义表述。
- S-PRIOR-02：canonical counts SHALL 唯一采用 `counts[a,b]=count(Alice=a,Bob=b)`；
  `P_reshaped` SHALL 为 `P_F.reshape(32,32,1024)=(U1,U2,Bob)`；
  `P1` SHALL 为 `P_reshaped.sum(axis=1)`（形状 `(32,1024)`），且 `assert_allclose(P1.sum(axis=0),1)`；
  `P2[u1,b,u2]` SHALL 为固定 `(u1,b)` 后沿 `u2` 和为 1（逻辑形状 `(32,1024,32)=(U1,B,U2)`）；
  转置输入 SHALL 被不对称手算反例捕获。
- S-PRIOR-03：平滑 SHALL 为 D4R2 frozen `lambda*=137.3823795883264` 单系数，
  施加于 counts 列方向后沿 `axis=0` 归一；SHALL 先归一后 floor。
- S-PRIOR-04：floor SHALL 双轨分离：审计/CE 用 `1e-300`（`max(P,1e-300)` 后取 log2，
  floor 后重归一）；decoder 通路用 `1e-15`（V54/v35 历史语义，floor 后重归一）；
  零质量 `(U1,B)` 切片 SHALL 回退均匀 `1/32`，SHALL NOT 删样本。
- S-PRIOR-05：`CE_L2_oracle` SHALL 用真实 `U1`（`v35.get_conditional_posterior_l2` 语义），
  仅作分层预算诊断；生产 L2 prior SHALL 为 `prior_l2=q@P`（`q=softmax(L1 final_beliefs)`，
  `v54.get_l1_app_prior_l2` 语义，签名禁 Alice/oracle）；SHALL NOT 把 oracle CE 引用为生产可达性能。
- S-PRIOR-06：存储与传递 SHALL 为概率域；decoder 入口 SHALL 为 `(N,32)` 概率域
  （decoder 内部转 log-belief）；CE SHALL 为 log2；`P1` 表 SHALL 为 `(32,1024)` 且 `P1.sum(axis=0)==1`。
- S-PRIOR-07：链式 SHALL 满足 `|CE_joint-CE_L1-CE_L2_oracle|<1e-10`（float64）；超限 SHALL 为 `BLOCKED`（数学错）。
- S-PRIOR-08：与现有接口的唯一 delta SHALL 为 design §1.6 的 `lambda*` 平滑插入声明；
  下游 `reshape` 求和 / `q@P` / `decode_row_layered_fftqspa(H(m,n),priors(N,32),syndromes(m,))`
  SHALL 逐字复用历史语义（`max_iter=90`，`damping_alpha=1.0`，`warm_beliefs=None` cold）；
  若接口形状不一致 SHALL 报 `BLOCKED`，SHALL NOT 猜测绕过。

## S-BUDGET：行数合同

- S-BUDGET-01：`rows_required(layer)` SHALL 为 `ceil(N*CE_layer*f/5)`；
  分层独立 ceil SHALL 为权威口径，`m_total=m1+m2`；joint-ceil 仅对照，0–1 行差异 SHALL 记录为 ceil 伪影。
- S-BUDGET-02：`n=1024` 行数表 SHALL 为 design §2.1（`f=1.0`：`m1=782/m2=686`；
  `f=1.05`：`821/720`；`f=1.1`：`860/755`；`f=1.2`：`938/823`；`f=1.3` L1=1016 超 cap，禁入 synthetic，仅参照）。
- S-BUDGET-03：旧 `16/200/216` 行 SHALL 禁止用于当前域真实实验；
  不足 SHALL 只记 `MODEL_BUDGET_MISMATCH`；SHALL NOT 称信息论极限/GF32 失败/LDPC 不可能；
  L1 不足 SHALL NOT 只加 L2。
- S-BUDGET-04：“约 700–1000 行” SHALL 按 per-layer `M_max=1000` synthetic 构造 cap 解释（design §2.3）；
  `M_max=1000 is a D5 synthetic construction cap, not a production sufficiency claim.`；
  SHALL NOT 代表生产充分/传播税覆盖/worst-fold 或 finite-size margin 充分；
  SHALL NOT 授权 `n=1024` 真实；统一 total 解读 SHALL 维持 route C 不进入真实实验；实现阶段 SHALL NOT 重新解释。

## S-MOTHER：嵌套母矩阵合同（R2：单 dv3 mother，无 row ordering）

- S-MOTHER-01：每层 mother SHALL 为一次性构建的单个 `(1000,1024)` uint8 矩阵（值域 `0..31`），
  SHALL 为单新家族 `G2_MINIMAL_NESTED_DV3_GF32`（列重恰 3，GF32 非零系数）；无并行家族；
  Lane-C SHALL 仅为备份（D5 内不并行）。
  V31 degree-2 support SHALL NOT 作为 D5 嵌套 mother（状态 `EXIT_PREFIX_CONNECTIVITY_IMPOSSIBLE`）；
  V31 field/rank/decoder 方法复用保留。
  `M_max=1000 is a D5 synthetic construction cap, not a production sufficiency claim.`
- S-MOTHER-02：披露 SHALL 为行前缀 `H[:k]`（自然序 = 构造序：base 先、suffix 扩展后），`k` SHALL 取自冻结集合
  `L1 {782,821,860,938}` / `L2 {686,720,755,823}`；对一切已披露 `k` SHALL 有 `gf_rank(H[:k])==k`；
  后增行 SHALL NOT 改动前缀行。degree-2 自然前缀与重排修复路线 SHALL 关闭（corrigendum §2 不可能性证明）。
- S-MOTHER-03：M0-STRUCTURE SHALL 为：只构建一次 `1000x1024` dv3 候选 → 检查所有冻结 prefix → 全 PASS 才进 G0；
  SHALL NOT 换 seed 搜索、SHALL NOT 每 `k` 独立矩阵冒充 nested、SHALL NOT support 追 rank 重抽、SHALL NOT decoder 引导调图；
  任一冻结 prefix 秩不足 SHALL 为 `G2_PREFIX_RANK_BLOCKED` 停止返回 planner，SHALL NOT 进 decoder。
- S-MOTHER-04：每个 prefix SHALL 报告 13 项（rank==k / zero rows=0 / zero cols=0 / 列 active degree min-median-max /
  degree-1 count / degree-2 count / connected component count / largest component fraction /
  isolated==0 / check row-degree histogram / 4-cycle count / duplicate-projective-equivalent col count==0 / GF32 系数非零）。
  最低 PASS SHALL 为：`zero_columns==0`，`isolated==0`，`largest_fraction==1.0`，`rank==k`，`duplicate==0`，
  新增硬门 `variable_degree_min>=2`（2 base 边保证），且随 `k` 非递减。
  `degree-1` SHALL 只披露不设阈值（R2 下 PASS 要求隐含 `degree-1==0`，仍如实报告三档计数）；大量 `degree-1` SHALL 在 G1 前标注结构风险。
- S-MOTHER-05：row ordering SHALL NOT 存在。SHALL NOT 有 `order_rows_for_prefix_coverage`；
  SHALL NOT 有后构造重排；SHALL NOT 有 decoder 驱动重排。披露 SHALL 直接用构造序 `H[:k]`。
- S-MOTHER-06：稀疏/支撑度 SHALL 为：每变量恰 3 边（`base1 in [0,k_min)`、`base2 in [0,k_min)` 不同于 edge1、`expansion in [k_min,1000)` 允许必要 spill 但 suffix 行全非零；
  `k_min` L1 `782` / L2 `686`）；每行度 SHALL >=2；SHALL 无重复 `(check,variable)` 边；
  SHALL 无两变量共享同一无序 check-support 三元组；构造 SHALL 全确定性（L1 seed `2026090501`、L2 seed `2026090502`；SHALL NOT seed search）；
  最小确定性贪心 SHALL 按 design §4.3（变量 `0..1023` 顺序；edge1 最小度 base；edge2 不重复 base 对→优先异分支→最小度→最小索引；
  edge3 先覆盖未覆盖 suffix 行否则最小度；收尾确定性边交换保列重 3；修不好 => `BLOCKED`）；
  SHALL NOT 用 PEG 库/通用框架；构造期 SHALL NOT 查看 decoder/syndrome/Alice/Bob/exact。
- S-MOTHER-06b：GF32 系数 SHALL 与 support 分离：每非零系数 SHALL 为 `1..31` 经冻结 seed 确定性 PRNG 恰生成一次；
  零 SHALL forbidden；SHALL NOT rank-fail 重播种；SHALL NOT decoder 引导搜索；SHALL NOT support 追 rank；
  任一冻结 prefix 秩不足 SHALL 为 `G2_PREFIX_RANK_BLOCKED`（不自动重抽）。
- S-MOTHER-06c：4-cycle SHALL 按变量对共享 check 对机械计数（`sum_C(shared,2)`）；base 禁重复 base 对 SHALL 使 base-only 目标为 0；
  expansion 共享对 SHALL 如实计数报告（含总数 / 每变量 incidence / 最大 incidence）；SHALL NOT 发明绝对 PASS 阈值；
  rank/覆盖/连通 PASS 但 cycle 非零 SHALL 为 `STRUCTURE_PASS_WITH_CYCLE_RISK`（G1/G2 趋势裁判，不回头调图）。
- S-MOTHER-07：披露 API SHALL 为最小形状 `m_max: int + prefix_rows: int + extra_rows: list[int] | None`
  （默认 None = 前缀 `0..k-1`，生产恒 None）；SHALL NOT 引入通用框架/注册表/版本包装。
- S-MOTHER-08：披露顺序 SHALL 为 L1 先收敛再开 L2（L1 APP `q` 恒喂 L2；L2 内 base→joint→total 短路）；
  联合同步披露 SHALL deferred。
- S-MOTHER-09：V72P0 binary IRA mother SHALL 只作结构参考；SHALL NOT 直接假设适用于 GF32
  （域/维度/码率 regime/decoder 四边界见 design §3.3）。

## S-SYNTH：matched synthetic 合同（含种子/P0/计数/预算/命名）

- S-SYNTH-01：synthetic 生成 SHALL matched to F（`B∼P_CAL(B)` CAL-only 边际 + `A∼P_F(·|B)` 采样，
  真值表取 `lambda*` 平滑表）；SHALL NOT 用 AWGN/BSC/QSC 替代；SHALL NOT 碰 VAL；SHALL NOT 做 VAL 真实扩维。
- S-SYNTH-02：门控 prior SHALL 用真 `P_F` 表（无估计误差）；`max_iter` SHALL 为 90，
  `damping_alpha` SHALL 为 1.0，`warm_beliefs` SHALL 为 None，tag SHALL 不生成不计费。
- S-SYNTH-03：种子 SHALL 冻结：graph L1 `2026090501`、L2 `2026090502`；
  G0 `2026090510..2026090517`；G1 `2026090600..2026090699`（100 blocks）；
  G2 `2026091000..2026091199`（200 blocks）。SHALL NOT seed search；运行后 SHALL NOT 换 seed。
- S-SYNTH-04：P0 COST-PREFLIGHT SHALL 为 `n=64` 2 blocks `f=1.0` 和 `1.2` APP 与 oracle 都跑，
  记录 `wall/iterations/RSS`，SHALL NOT 计入 G1；SHALL 基于 P0 外推 G1/G2 projected wall。
  资源门 SHALL 为单 call timeout `120s`、G1 总 `≤900s`、G2 总 `≤3600s`、peak RSS `<2GiB`；
  G2 `projected>3600s` SHALL 为 `RESOURCE_PROJECTION_BLOCKED` 不启动；
  SHALL NOT 降 block/rate 点绕过、SHALL NOT 自动并行、SHALL NOT 改 `max_iter=90`。
- S-SYNTH-05：调用数 SHALL 为 G1 APP-fed `100 blocks x 2 rates` + oracle 前 20 同 seed `x 2 rates` 仅诊断；
  G2 APP-fed `200 x 3 rates` + oracle 前 40 同 seed `x 3 rates` 仅诊断；oracle 子集 SHALL 仅诊断不计入 PASS。
- S-SYNTH-06：本轮 matched synthetic development SHALL 统一 `exact_failure_fraction=1-exact_count/attempted_blocks`，
  可注 synthetic block error fraction；SHALL NOT 称真实 FER 或外推真实。
  G2 单调 SHALL 为 `exact_rate(1.2)>=exact_rate(1.1)>=exact_rate(1.0)`；1–2 block 反转 SHALL 报告 Wilson 区间与 raw counts，
  仍按预注册 raw inequality 决定 qualified。
- S-SYNTH-07：oracle/APP SHALL 同时报告 `oracle_L2_exact/app_fed_exact/oracle_minus_app/oracle_syndrome_ok/app_syndrome_ok/`
  `L1 exact/L1 syndrome_ok/L1 posterior NLL/q entropy mean/p95`；
  oracle SHALL 仅为诊断上界，APP-fed SHALL 为生产语义；有限 BP 非单调 SHALL 允许，
  `oracle<APP` SHALL NOT 自动判错，异常 SHALL 标 `ORACLE_APP_NONMONOTONIC_DIAGNOSTIC` 并查合同/seed 配对/syndrome 重算，
  仅数学/输入不一致 SHALL 为 `BLOCKED`。G2 PASS SHALL 只用 APP-fed 端到端 exact；SHALL 删除 oracle>=APP 硬门。

## S-GATE：三级门控与分级实验

- S-GATE-01：G0 tiny SHALL 验证边际/条件与暴力误差 `<1e-12`、链式 `<1e-10`、syndrome 重算一致、
  tree/tiny exhaustive 一致、无噪精确恢复 100%；失败 SHALL 为 `BLOCKED`。
- S-GATE-02：G1 `n=64` SHALL 为 APP-fed 100 paired `f={1.0,1.2}`，验证单调
  `exact_rate(1.2)>=exact_rate(1.0)` 且零 crash/非有限 + 结构趋势检查；
  G1 SHALL 无路线死亡权，失败 SHALL 只进诊断（数学错 vs 图/scale 错 vs 实现错，prior 错 excluded）。
- S-GATE-03：G2 `n=256` SHALL 为 D5 唯一分级实验：APP-fed 200 paired `f∈{1.0,1.1,1.2}` 三点扫描，
  行数 `m1={196,215,235}` / `m2={172,189,206}`；
  `>=90%@1.2` 且单调 SHALL 为 `G2_SYNTHETIC_QUALIFIED`（允许起草 `n=1024` synthetic 计划，不授权执行）；
  `50-90%` SHALL 为 `G2_INCONCLUSIVE`（保留路线，停止本轮，仅按预注册诊断判断，不自动调参）；
  `<50%` SHALL 为 `G2_CURRENT_CONFIGURATION_FAILED`（只否定当前组合）；
  crash/非有限/数学不一致 SHALL 为 `IMPLEMENTATION_OR_NUMERICAL_BLOCKED`。
  SHALL 删除 `GF32_ROUTE_DEAD`、“失败后仅 d=256 backlog”、“低于 90% 即放弃 GF32”。
  无论结果 SHALL NOT 自动进 `n=1024`。
- S-GATE-04：`n=1024` 真实执行前置 SHALL 为 G0+G1+G2 全过 + Pre-EXECUTE review 通过；
  本计划 SHALL NOT 一次授权 G0/G1/G2。

## S-STOP：边界与停止

- S-STOP-01：本轮 SHALL 只做文档计划；SHALL NOT 写 `.py` 生产文件、调用 decoder、读 VAL、
  创建正式输出/`run_01`、授予执行。
- S-STOP-02：SHALL NOT 引入 checksum/hash/tag/签名或内容校验字段。
- S-STOP-03：冻结阈值（行数表、floor、`lambda*`、PASS/FAIL 线、披露集合、种子、门禁、预算、调用数）SHALL NOT 在实现后回写放宽；
  歧义 SHALL 停下返回 planner/OpenSpec 修订（新 SHA 重审）。
- S-STOP-04：本计划只可变为 `PLAN_ACCEPTED + implementation_authorized:false + synthetic_execution_authorized:false + real_execution_authorized:false`；
  Review PASS SHALL NOT 自动授权实现；后续 SHALL 分开 `implementation packet→review→M0/G0 auth→G0 review→P0/G1 auth→G1 review→G2 auth→G2 Pre-RESULT`，SHALL NOT 一次授权 G0/G1/G2。
- S-STOP-05：R2 本轮修改文件 SHALL 仅为 5 计划文件 + `docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/PLAN_CORRIGENDUM_R2.md`（新）+ 同目录 `cycle_state.yaml`（改）；
  SHALL NOT 触碰 3 `.py` 候选、`IMPLEMENTATION_REVIEW.md`、旧 `PLAN_REVIEW_VERDICT.md`、旧 `IMPLEMENTATION_PACKET.md`、
  `AGENT_PROJECT_MEMORY.md`、`docs/decision-log.md`、任何其它代码/输出；SHALL NOT 新增 hash/checksum/tag 字段。
