# V72P2D2 Spec Delta：正交单块 syndrome-only 分诊

状态：`PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`。本 delta 绑定 base
`e094f7e548380db4bfcbc1fe73472e670c32379a`，不合并、不替代已接受的 V72P1、
V72P2 或 D1 行为。本周期不实现、不运行 decoder、不读取 raw/parquet、不创建
结果目录。

`base_sha`、`accepted_plan_sha`、`implementation_sha` 只承担 AGENTS 要求的
Git commit/计划/实现版本绑定，不承担 data/artifact 内容校验。输出不得包含
数据或 artifact 内容摘要、签名或其他校验字段。

## S-ARM：四臂正交性

- **S-ARM-01**：系统 SHALL 以已存 D1 Arm A 作为 baseline A；A SHALL 只读复用，
  SHALL NOT 重跑。
- **S-ARM-02**：L SHALL 使用原 H、M0 prior 和其他共同参数，只改变为本 spec
  `S-LAY` 定义的真正 row-serial layered 调度。
- **S-ARM-03**：I SHALL 使用 `S-INT` 定义的 full-column degree-balanced H_I、
  M0 prior 和原 flooding；不得改变其他因素。
- **S-ARM-04**：P SHALL 使用原 H、`S-M2` 冻结 prior 和原 flooding；不得使用
  layered 或 interleaver。
- **S-ARM-05**：L/I/P SHALL 使用同一 D1 非新鲜 block、同一 72 checkpoint
  ladder、每 checkpoint 10 次完整更新、每臂 720 次、`float64`、clip 20、
  tolerance 1e-6、syndrome-only 诊断和计费语义；L/I/P 的 c2v SHALL 独立。
- **S-ARM-06**：不得创建 layered+I、I+M2 或 layered+M2 混合臂；不得事后调参、
  重跑或扩展 block。

## S-COMMON：输入、更新和状态

- **S-COMMON-01**：block SHALL 是 session `20260123_1M_600k_0dB` 的
  `VAL1726..1729` 四帧连续 1024-symbol D1 诊断块，并标记 `non_fresh=true`；
  计划和测试阶段 SHALL NOT 读取 raw/parquet。
- **S-COMMON-02**：mother SHALL 为 `9036x10240`、`nnz=49620`，check degree
  `{4:1,5:4594,6:4441}`，degree-2 列 9035。ladder SHALL 为
  `range(160,8993,128)+[9032,9036]`，共 72 点。
- **S-COMMON-03**：每次完整更新 SHALL 更新每个 active edge 一次；L 的完整
  更新是一个 active-row sweep，I/P 的一次完整更新是一次 flooding iteration。
  partial update SHALL NOT 启动。
- **S-COMMON-04**：checkpoint 间 SHALL 携带同一臂的 active c2v；新边 SHALL
  置零；L/I/P 间 SHALL NOT 共享可变状态；不跨 block 携带。
- **S-COMMON-05**：residual SHALL 是完整更新前后 active c2v snapshot 的全边
  L-infinity 差；`residual<1e-6` SHALL 只表示 converged，不表示 syndrome
  满足或 oracle 正确。
- **S-COMMON-06**：一个 factor target evaluation SHALL 严格定义为一个
  `f2b[sym,b]` over `Q=1024` states 的完整 marginal。核心 factor work SHALL 只
  统计实际 decoder update evaluations；一次性 L0、checkpoint rebuild 和纯 readout
  SHALL NOT 混入核心。这些操作分别进入 diagnostic factor/state/readout 字段。

## S-LAY：layered 数学合同

- **S-LAY-01**：L SHALL 提供
  `run_layered_decoder(prior_logp, syndrome_target, indptr, indices,
  max_sweeps, warm_start_c2v)`；L SHALL 只调用此新 API，adapter SHALL NOT 修改。
- **S-LAY-01a**：`warm_start_c2v.shape` SHALL 严格等于 `(len(indices),)`；首
  checkpoint SHALL 传全零数组，后续 checkpoint SHALL 只复制同一臂上一 checkpoint
  的 active 前缀并将新边置零。返回值 SHALL 包含
  `bit_to_factor`、`factor_to_bit`、`variable_to_check`、`check_to_variable`、
  `app_llr`、`hard_bits`、`hard_symbols`、`syndrome_observed`、`finite`、
  `residuals`、`converged`、`max_llr` 以及核心/diagnostic factor 计数字段。
- **S-LAY-02**：内部 SHALL 保留未裁剪
  `APP_raw=factor_to_bit+bit_to_factor`，其中
  `bit_to_factor[v]=sum incident c2v`；不得以 `APP_clipped` 参与消息计算。
- **S-LAY-03**：每条 row edge 的 v2c SHALL 为
  `factor_to_bit[v]+bit_to_factor[v]-c2v_old[e]`；不得使用
  `APP_clipped-c2v_old`。
- **S-LAY-04**：每 row SHALL 先从 row-start snapshot 计算全部 v2c，再用这一
  整行 v2c 同时计算全部新 c2v，最后一次性提交整行；同 row edge 顺序 SHALL
  不产生顺序污染。
- **S-LAY-05**：新 c2v SHALL 使用
  `sign=(-1)**(syndrome+degree%2)` 与除目标 edge 外的 v2c tanh product；
  atanh 输入 SHALL clip 到 `[-1+1e-12,1-1e-12]`，输出 SHALL clip 到 `[-20,20]`。
- **S-LAY-06**：整行提交后 SHALL 更新受影响变量的 bit_to_factor；受影响的每个
  symbol SHALL 重算全部 10 个 factor_to_bit，目标 bit SHALL self-exclude；
  然后 SHALL 更新该 symbol 全部 10 个 APP_raw。
- **S-LAY-07**：APP_clipped 只可用于诊断、输出和 hard sign；clip SHALL NOT
  改变 sign。syndrome 0/1、check degree 1/2/3 的 sign 语义 SHALL 一致。
- **S-LAY-08**：一 sweep SHALL 按 active row `0..r-1` 执行，每 active edge
  一次 c2v/v2c；每 checkpoint 最多 10 sweep，每 L 臂最多 720 sweep。
- **S-LAY-09**：L SHALL 记录 `edge_updates`、核心
  `local_factor_target_updates` 和 `state_evaluations=1024*local_factor_target_updates`。
  每 row 的核心 target 增量 SHALL 为 `10*distinct_affected_symbols`；L 的
  factor work SHALL 与 I/P 的 edge/sweep work 分开报告。一个 target 必须是一个
  `f2b[sym,b]` 的完整 1024-state marginal。
- **S-LAY-09a**：L 的核心 target/state 只含实际 decoder update evaluations；
  一次 L0 full `[1024,10]` batch 每臂严格只计算一次并缓存，固定为
  `diagnostic_L0_target_updates=10240`；后续 checkpoint metrics 只能读取该缓存，
  任何重复计算都必须另加 10240 diagnostic targets，且 T2 失败。L 的每个实际
  checkpoint SHALL 强制从 active state 完整 rebuild f2b，固定增加
  `diagnostic_checkpoint_rebuild_target_updates=10240`，不得在 cache/recompute
  间选择。L final readout 复用最后状态，固定为 0。三阶段相加为
  `diagnostic_factor_target_updates`，并满足
  `diagnostic_state_evaluations=1024*diagnostic_factor_target_updates`；纯
  readout 另列，所有阶段和 core 总计均须输出。成本投影固定按
  `D=10240*(1+72)` 保守计。全 ladder active-row 总和 `338388`、每 row 至多 6
  个 distinct symbols、10 sweeps 的静态上界为 `203032800` targets、
  `207905587200` state evaluations，且只作上界。
- **S-LAY-10**：若实现不能证明 S-LAY-02 至 S-LAY-09 使用最新消息并保持自排除，
  SHALL 为 BLOCKED；不得将 row loop 包装 flooding 宣称 layered。
- **S-LAY-11**：`run_incremental_decoder` 的 stale-return bug SHALL 在本周期
  deferred；新实现不得调用或修复该接口。

## S-INT：唯一 interleaver

- **S-INT-01**：high 集合 SHALL 固定为 old columns `0..1203`；degree SHALL
  由原 H bincount；处理顺序 SHALL 是 `(-degree,old_col)` 升序。
- **S-INT-02**：维护 `info_count` 和 `info_load`；每列选择满足
  `info_count<2` 且字典序最小 `(info_load,info_count,symbol_id)` 的 symbol，
  写入该 symbol 的 slot `bit_id=info_count`，再递增 count 并加 degree load。
- **S-INT-03**：固定 `np.random.default_rng(20260902)`；old parity columns
  `1204..10239` 经一次 permutation 后，按 `(symbol_id,bit_id)` 升序填满剩余
  physical slots；bit 0 SHALL 是 LSB。
- **S-INT-04**：`old_to_phys` SHALL 覆盖全部 10240 列并 bijective，
  `phys_to_old` SHALL 是其互逆；重复构造 SHALL 得到相同映射。
- **S-INT-05**：映射 SHALL 满足
  `H_I[:,old_to_phys[j]]=H_old[:,j]`、
  `x_old[j]=x_phys[old_to_phys[j]]` 和
  `H_I@x_phys=H_old@x_old (mod 2)`。syndrome 使用 H_I 与 physical Alice，
  prior 与 Bob/candidate 比较使用 physical 坐标。
- **S-INT-06**：H_I SHALL 保持 shape、nnz、row/column degree multiset、rank
  和 prefix nesting；每 symbol 恰 10 physical bits，high 集合每 symbol 1 或
  2 列。`41/47/65`、`95/95` 只能作为重算后的参考，不能作为门槛。

## S-M2：prior

- **S-M2-01**：参数 SHALL 固定为 `family=laplace`、`mu=0.0`、
  `scale=0.2714417616594907`、`eps=0.562251256281407`、`Q=1024`，来源为
  V70R1 1M CAL-only 结果，禁止重选。
- **S-M2-02**：`signed_disp[d]=((d+Q//2)%Q)-Q//2`；
  `shape[d]=sum(exp(-abs(signed_disp[d]+period*Q-mu)/scale), period=-1,0,1)`；
  shape 正常归一；`K=(1-eps)*shape+eps/Q` 后正常归一。
- **S-M2-03**：prior SHALL 为
  `log(max(K[(a-int(bob_phys[sym]))%1024],1e-300))`；K SHALL 先归一，不能
  在 K 阶段 floor 或 floor 后重归一；floor 只保护 log，当前 eps>0 不应触发。
- **S-M2-04**：builder 只接 physical Bob 和冻结参数，不接 Alice；Alice 只进入
  runner 的 syndrome/oracle 边界。BP 输入用 natural log，CE 用 log2。
- **S-M2-05**：历史 M2 CE `6.787126437359054` 是非门槛背景；M2 变差或
  不改变候选均是合法观测，不得写成优胜。
- **S-M2-06**：I/P 的 `actual_iterations` SHALL 等于既有 `run_decoder` 返回的
  `len(residuals)`；每个实际 flooding iteration SHALL 增加核心
  `local_factor_target_updates=1024*10=10240`，并保持
  `state_evaluations=1024*local_factor_target_updates`。每一次实际
  `run_decoder` 调用末尾 adapter SHALL 重算完整 `factor_to_bit` batch，另增加
  `diagnostic_final_readout_target_updates=10240` 和
  `10240*1024` diagnostic state evaluations；其余 L0、rebuild 和纯 readout
  只能进入对应 diagnostic 计数，I/P final readout 不得记为 0。
- **S-M2-07**：synthetic 验收 SHALL 断言 K、P 和 `prior_logp` finite；K 与
  每个 P 行 SHALL strictly positive 且 sum=1，且
  `exp(prior_logp)` SHALL 逐元素匹配 P 并逐行归一。不得要求 logp 为正。

## S-MET：诊断字段

- **S-MET-01**：quantiles SHALL 固定为
  `[0,0.01,0.05,0.25,0.5,0.75,0.95,0.99,1]`，`zero_tol=1e-15`，sign SHALL
  按负/零/正三类定义。
- **S-MET-02**：L0 SHALL 是 prior-only local-factor target LLR
  `local_factor_extrinsic(prior_row,zeros(10),target_bit)`，不得称 APP。
  F SHALL 是 f2b；S SHALL 是 signed incident c2v sum；A_raw SHALL 是 F+S。
- **S-MET-03**：每个新臂 checkpoint SHALL 在首 sweep 前记录 pre、最后完整
  sweep 后记录 post；L0、F、S、A_raw、`delta_app=A_raw_post-A_raw_pre` 均需
  signed/absolute quantiles、max_abs、zero_count。
- **S-MET-04**：每 checkpoint SHALL 记录当前 L0→F_post、F_post→A_raw_post
  两个 3x3 sign transition；不得改为相对首 checkpoint。
- **S-MET-05**：每 checkpoint SHALL 记录 violation
  `weight(((H_arm[:r]@hard_bits)%2) XOR syndrome_target[:r])`、candidate-vs-Bob
  bit/symbol flips、residual、sweeps、edge_updates、factor target updates、
  state evaluations、finite、clip、syndrome_satisfied 和 `tag_ok=NOT_APPLICABLE`；
  核心 target/state 与 diagnostic target/state/readout 增量 SHALL 分开。`oracle_exact`
  在 checkpoint 层 SHALL 为 null，并附
  `not_recorded_reason=oracle_runs_after_arm_end`；单边 max c2v 与变量
  incident sum max SHALL 分开。
- **S-MET-05a**：每 arm SHALL separately report core
  `local_factor_target_updates`/`state_evaluations`,
  `diagnostic_L0_target_updates=10240`（每臂严格一次并缓存；重复计算另加
  10240 且 T2 失败）、`diagnostic_checkpoint_rebuild_target_updates`（L 每个实际
  checkpoint 固定 10240，不允许 cache/recompute 二选一）、
  `diagnostic_final_readout_target_updates`（L final readout 复用最后状态为 0；I/P
  为 `10240*actual_run_decoder_calls`），`diagnostic_factor_target_updates`、
  `diagnostic_state_evaluations`、`diagnostic_readout_evaluations`,
  `total_target_updates` 和 `total_state_evaluations`。I/P decoder factor batches
  SHALL belong to core based on actual `len(residuals)` iterations；每次调用末尾
  的完整 factor batch 另属 diagnostic final-readout，不能漏计或重复计数。
- **S-MET-06**：clip 字段 SHALL 包含 c2v/f2b `abs>=20-1e-12` 计数和
  `abs(A_raw)>20` 计数；APP 输出可 clip 到 20，但不得声称保存 factor preclip。
- **S-MET-07**：结果 SHALL NOT 保存秘密数组、Alice/Bob symbols、syndrome
  bytes、完整 prior、完整消息或逐 symbol 数组；D1 O1 只能标
  `POSTHOC_RECONSTRUCTED`。
- **S-MET-08**：arm 结束 SHALL 只使用最后一个已完成 checkpoint candidate，
  同时报告 `final_checkpoint_rows`、`final_syndrome_satisfied`、
  `final_oracle_exact`、`diagnostic_exact` 和 `syndrome_collision_wrong`。不得把
  first checkpoint 的 syndrome 与 final candidate 的 oracle 混合；
  `first_syndrome_satisfied_ckpt` 仅为传播诊断。

## S-ACCT：公开计费

- **S-ACCT-01**：L/I/P SHALL 各自维护
  `syndrome_rows_published`、`syndrome_bits_published`、
  `tag_bits_published=0`、`control_bits_sent`、`disclosed_rows`；三臂
  counterfactual 计数 SHALL NOT 相加。
- **S-ACCT-02**：每 checkpoint 发布新增 syndrome rows；不发布 tag bits；只有
  进入下一 checkpoint 才增加 1 CONTINUE bit。
- **S-ACCT-03**：公开计费 SHALL 为
  `syndrome_bits_published+control_bits_sent`。完整 ladder 正常达到的名义值
  为 `9036+71=9107`；预算中断、exception、timeout SHALL 保留已发布计数，
  不得固定写成 9100；A 的历史计量不重解释为新臂计量。
- **S-ACCT-04**：首次 `syndrome_satisfied` 只记录 checkpoint，不停止 ladder，
  不改变计费，也不称协议接受。oracle 只在 arm 结束后运行。
- **S-ACCT-05**：每个 checkpoint 及 arm 终态 SHALL 满足
  `disclosed_rows == syndrome_rows_published == syndrome_bits_published`，且三者
  单调不减；L/I/P 计数 SHALL 独立，不得相加。

## S-IO：未来实现、执行和 schema

- **S-IO-01**：实现精确只有：
  `comparison_bench/src/comparison_bench/formal_ir/v72p2d2_orthogonal_triage.py`、
  `scripts/v72p2d2_orthogonal_triage.py`、
  `comparison_bench/tests/test_v72p2d2_orthogonal_triage.py`。不得新增 config、
  fixture，或修改 adapter、src、experiments、tools、results、旧输出。
- **S-IO-02**：输出根 SHALL 是
  `comparison_bench/outputs_comparison/v72p2d2_orthogonal_oneblock_20260904/`，
  且只含 `manifest.json`、`results.json`、`table.csv`、`report.md`；不得覆盖
  D1 输出或创建 `run_01`。
- **S-IO-03**：manifest/results 顶层 SHALL 含 schema、cycle、
  `base_sha`、`accepted_plan_sha`、`implementation_sha`、source registry、
  session/block provenance、`non_fresh`、mother shape/nnz、ladder、预算、
  数值、arm order、invocation status、cost preflight、projected L wall、RSS
  sampling、arms 和 claim boundary。上述三个字段仅是 Git 版本绑定，不承担
  artifact/data 内容校验；不得添加其他内容校验字段。
- **S-IO-04**：每 arm SHALL 含 status、graph/prior/schedule、attempted
  checkpoints、stop、first_syndrome_satisfied_ckpt、final_checkpoint_rows、
  final_syndrome_satisfied、final_oracle_exact、diagnostic_exact、
  syndrome_collision_wrong、sweeps、edge/factor work、核心与 diagnostic factor
  counters（含 L0/rebuild/final-readout 分阶段计数与 core+diagnostic 总计）、
  peak RSS、accounting、checkpoint metrics、common metrics、new metrics 和 posthoc
  oracle。`tag_bits=0`、`tag_ok=NOT_APPLICABLE` SHALL 固定出现；
  checkpoint oracle SHALL 为 null 并附 `oracle_runs_after_arm_end`。
- **S-IO-05**：A 的新指标 SHALL 为 null 并附
  `not_recorded_reason="D1 baseline did not record this metric; A was not rerun"`；
  A 只允许比较 D1 的 outcome、iterations、candidate-vs-Bob、APP、single-edge
  c2v 和 `POSTHOC_RECONSTRUCTED` O1 violation。L/I/P SHALL 填实际标量聚合。
  科学字段 replay 排除 wall、RSS、timestamp、临时 path，不要求整文件字节一致。
- **S-IO-06**：RSS sampling SHALL 使用当前进程
  `psutil.Process(os.getpid()).memory_info().rss`，在 prep、每 checkpoint 后和
  arm 结束采样；`peak_rss_bytes` SHALL 是这些样本的最大值。不得以 Python
  对象大小或其他进程口径替代。

## S-STOP：真实执行状态机

- **S-STOP-01**：单次 invocation 的 prep allowance 为 600 s，L/I/P 各 soft
  wall 600 s，总墙钟上限 2400 s，peak RSS 硬上限 2 GiB。
- **S-STOP-01a**：Pre-EXECUTE 前 SHALL 完成 synthetic cost-preflight，仅使用
  真实 mother 结构、合成 prior/syndrome 与零/非零 warm state，固定代表点
  `active_rows=160,2048,4096,8192,9036`，不运行正式三臂且不读取 raw/parquet。
  preflight SHALL 记录实际 target/state 计数、wall/RSS 并外推
  `projected_L_wall_s`；硬门槛为 `projected_L_wall_s<=600`，`<=480` 为建议的
  20% 余量目标。超过 600 SHALL 返回 `PLAN_REVISE_REQUIRED`，不得改科学算法
  绕过；真实 L 超过 600 s SHALL 标记 `RESOURCE_BLOCKED`，不得作为路线失败。
- **S-STOP-02**：准备/输入校验失败时三臂 SHALL 为 `NOT_ATTEMPTED` 并返回
  非零；任一新臂 exception、nonfinite、RSS 超限或 timeout 时该臂 SHALL 为
  `BLOCKED`，立即停止 invocation，后续臂 SHALL 为 `NOT_ATTEMPTED`，已生成的
  四臂 artifact SHALL 保留。
- **S-STOP-03**：普通 `LADDER_EXHAUSTED` 或达到 720 的正常终态允许继续下一臂；
  A 不运行；L/I/P 各运行一次；首次 syndrome_satisfied 不停止；不得 rerun 或
  调参。
- **S-STOP-04**：执行前 SHALL 通过独立 Plan Review、Implementation Review、
  Pre-EXECUTE，发布前 SHALL 通过 Pre-RESULT；本计划 SHALL NOT 授权执行。

## S-CLAIM：判别和科学边界

- **S-CLAIM-01**：L 只有 candidate escape、violation 下降或
  `syndrome_satisfied` 才支持调度路线；仅 runtime 变快不算纠错改善。
- **S-CLAIM-02**：I 只有 escape、violation 下降或 `syndrome_satisfied` 才支持
  该映射；单块不得证明普遍图因果。
- **S-CLAIM-03**：P 的消息/翻转变化但未满足 syndrome 只能归为 prior 影响；完全
  不变只削弱 prior-only 解释；不得宣称 M2 优胜。
- **S-CLAIM-04**：L/I/P 均无 hard-bit escape 时 SHALL 停止 binary edge-level
  flooding/layered/damping 微调，后继限定为 grouped-symbol mask BP tiny
  exhaustive 或同块 GF32 对照。
- **S-CLAIM-05**：任一臂出现 syndrome_satisfied 只允许进入同路线小样本
  confirmation plan，不直接进入 V73；不得作 FER、SKR、信息极限、LDPC 无效或
  跨 session 推广断言。

## S-TEST：未来 synthetic 验收

- **S-TEST-01**：T0 SHALL 覆盖 py_compile/import 无副作用、字段/母图/预算常量、
  tiny mixed/pure cycle 口径和 M2 归一；M2/K/P/prior_logp SHALL 分别满足
  finite、strictly positive、sum=1，且 `exp(prior_logp)` 与 P 逐元素匹配并
  逐行归一；不得要求 logp 为正，也不得出现数据或 artifact 内容校验字段。
- **S-TEST-02**：T1-L SHALL 覆盖 layered 顺序、row snapshot、非零 prior/c2v、
  最新消息可见性、stale flooding 差异、APP_raw 25 减旧 c2v 1 得 24、
  self-exclusion、syndrome/degree sign、warm-start rebuild（首 ck 全零且
  `shape==(len(indices),)`）、edge/factor budget、L 的每 row
  `10*distinct_affected_symbols` 计数与 static 上界计算。T1-L SHALL 另运行
  cost-preflight 代表点并断言每点恰 1 sweep、
  `U_r=10*sum(distinct_affected_symbols(row) for row<r)`、
  `tau=max(elapsed/U_r)`、`W=sum(10*sum(distinct_affected_symbols(row) for row<ck)
  for ck in ladder)`、`D=10240*(1+72)`、独立 timer 的非负
  `h=max(observed_noncore_overhead)`、`tau_diag` 及
  `projected_L_wall_s=(tau*W+tau_diag*D+72*h)*1.2`；断言
  `projected_L_wall_s<=600` 和 RSS 采样口径。
- **S-TEST-03**：T1-I SHALL 覆盖全列 bijection、互逆、seed 确定性、high 分布、
  LSB、映射代数、tiny syndrome oracle、H 不变量、prefix 和 mixed/pure cycle
  口径分离。
- **S-TEST-04**：T1-P SHALL 覆盖冻结参数、wrapped Laplace、K floor 阶段、
  1024 循环平移、Bob-only、natural-log/log2 分离、K/P/prior_logp
  finite/strictly-positive/sum=1 与 `exp(prior_logp)` 对齐，并允许结果变差。
- **S-TEST-05**：T1-METRICS SHALL 覆盖 quantiles/sign/zero、手算 F/S/A、
  单边与变量聚合分离、violation、clip 计数、candidate 直接比较、无 tag
  字段语义、一个 target 对应一个 1024-state f2b marginal、核心与 diagnostic
  factor 计数分离、L0=10240、rebuild/final-readout 实际阶段计数、core+diagnostic
  总计、`disclosed_rows == syndrome_rows_published == syndrome_bits_published`
  单调断言和敏感数组禁止。
- **S-TEST-06**：T2 SHALL 使用显式 fake runner 和 fresh workspace，覆盖三臂
  full ladder、首次 syndrome 满足不早停、动态计数（tag=0）、满梯/异常/timeout/
  RSS/NOT_ATTEMPTED、结束后 final-candidate oracle 分类、baseline null 原因、
  四文件 schema、production path 门禁和科学字段 replay。fake 反例 SHALL 构造
  早期 syndrome 满足而后续 candidate 改变，断言 first checkpoint 仅作传播诊断，
  最终分类只使用 final candidate，不跨 checkpoint 混合。replay 排除 wall/RSS/
  timestamp/path，不要求整文件字节一致。
- **S-TEST-07**：T2 SHALL 机械断言 I/P 的 core target 增量为
  `10240*actual_iterations`，且 `diagnostic_final_readout_target_updates` 等于
  `10240*actual_run_decoder_calls`；L 的 core target 按每 row
  `10*distinct_affected_symbols`，L0 每臂恰一次 10240、L 每个实际 checkpoint
  恰一次 10240 rebuild、L final readout 为 0。T2 必须断言三臂阶段计数无漏计/重复，
  及 `diagnostic_factor_target_updates`、`diagnostic_state_evaluations`、
  `total_target_updates`/`total_state_evaluations` 求和关系，并断言
  `disclosed_rows == syndrome_rows_published == syndrome_bits_published` 单调不减。
