# V72P2D2 Spec Delta：正交单块分诊

状态：`PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`。本 delta 绑定 base
`e094f7e548380db4bfcbc1fe73472e670c32379a`，不合并、不替代已接受的 V72P1、
V72P2 或 D1 行为。本周期不实现、不运行 decoder、不读取 raw/parquet、不创建
结果目录。

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
  tolerance 1e-6、验证和计费语义；L/I/P 的 c2v SHALL 独立。
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
  更新是一个 active-row sweep，I/P 的完整更新是一次 flooding iteration。
  partial update SHALL NOT 启动。
- **S-COMMON-04**：checkpoint 间 SHALL 携带同一臂的 active c2v；新边 SHALL
  置零；L/I/P 间 SHALL NOT 共享可变状态；不跨 block 携带。
- **S-COMMON-05**：residual SHALL 是完整更新前后 active c2v snapshot 的全边
  L-infinity 差；`residual<1e-6` SHALL 只表示 converged，不表示验证正确。

## S-LAY：layered 数学合同

- **S-LAY-01**：L SHALL 提供
  `run_layered_decoder(prior_logp, syndrome_target, indptr, indices,
  max_sweeps, warm_start_c2v)`；L SHALL 只调用此新 API，adapter SHALL NOT 修改。
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
  然后 SHALL 更新 APP_raw。
- **S-LAY-07**：APP_clipped 只可用于诊断、输出和 hard sign；clip SHALL NOT
  改变 sign。syndrome 0/1、check degree 1/2/3 的 sign 语义 SHALL 一致。
- **S-LAY-08**：一 sweep SHALL 按 active row `0..r-1` 执行，每 active edge
  一次 c2v/v2c；每 checkpoint 最多 10 sweep，每 L 臂最多 720 sweep。
- **S-LAY-09**：L SHALL 记录 `edge_updates`、`local_factor_target_updates`
  和 `state_evaluations=1024*local_factor_target_updates`；L 的 factor work
  SHALL 与 I/P 的 edge/sweep work 分开报告。
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
- **S-M2-04**：builder 只接 physical Bob 和冻结参数，不接 Alice；BP 输入用
  natural log；CE 报告用 log2；LSB bit 0 和现有 B_BITS 保持。
- **S-M2-05**：历史 M2 VAL CE `6.787126437359054` 是非门槛背景；M2 变差或
  不改变候选均是合法观测，不得写成优胜。

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
  state evaluations、finite、clip、syndrome_ok、tag_ok、oracle_exact、
  undetected。单边 max c2v 与变量 incident sum max SHALL 分开。
- **S-MET-06**：clip 字段 SHALL 包含 c2v/f2b `abs>=20-1e-12` 计数和
  `abs(A_raw)>20` 计数；APP 输出可 clip 到 20，但不得声称保存 factor preclip。
- **S-MET-07**：结果 SHALL NOT 保存秘密数组、Alice/Bob symbols、syndrome
  bytes、完整 prior、完整消息或逐 symbol 数组。D1 O1 只能标
  `POSTHOC_RECONSTRUCTED`。

## S-ACCT：公开计费

- **S-ACCT-01**：L/I/P SHALL 各自维护
  `syndrome_rows_published`、`syndrome_bits_published`、`tag_bits_published`、
  `control_bits_sent`、`disclosed_rows`；三臂 counterfactual 计数 SHALL NOT 相加。
- **S-ACCT-02**：每 checkpoint 发布新增 syndrome rows；首次进入 tag 验证前
  发布一次 64 tag bits；只有进入下一 checkpoint 才增加 1 CONTINUE bit。
- **S-ACCT-03**：成功、ladder exhausted、exception、timeout SHALL 保留已发布
  计数，不回滚；不得把所有臂固定写成 9100。A 的历史计量不重解释为新臂计量。

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
- **S-IO-03**：manifest/results 顶层 SHALL 含 schema、cycle、base_sha、
  implementation_sha、source registry/data_sha、session/block provenance、
  non_fresh、mother shape/nnz、ladder、预算、数值、arm order、invocation status、
  arms 和 claim boundary。每 arm SHALL 含 status、graph/prior/schedule、
  attempted checkpoints、stop、sweeps、edge/factor work、accounting、metrics、
  common metrics 和新指标。
- **S-IO-04**：A 的新指标 SHALL 为 null 并附
  `not_recorded_reason="D1 baseline did not record this metric; A was not rerun"`；
  L/I/P SHALL 填实际标量聚合。科学字段 replay 比较排除 wall、RSS、timestamp、
  临时 path；不要求整文件字节一致。

## S-STOP：真实执行状态机

- **S-STOP-01**：单次 invocation 的 prep allowance 为 600 s，L/I/P 各 soft
  wall 600 s，总墙钟上限 2400 s，peak RSS 硬上限 2 GiB。
- **S-STOP-02**：准备/输入校验失败时三臂 SHALL 为 `NOT_ATTEMPTED` 并返回
  非零；任一新臂 exception、nonfinite、RSS 超限或 timeout 时该臂 SHALL 为
  `BLOCKED`，立即停止 invocation，后续臂 SHALL 为 `NOT_ATTEMPTED`，已生成的
  四臂 artifact SHALL 保留。
- **S-STOP-03**：普通 `LADDER_EXHAUSTED` 或达到 720 的正常终态允许继续下一臂；
  A 不运行；L/I/P 各运行一次；不得 rerun 或调参。
- **S-STOP-04**：执行前 SHALL 通过独立 Plan Review、Implementation Review、
  Pre-EXECUTE，发布前 SHALL 通过 Pre-RESULT；本计划 SHALL NOT 授权执行。

## S-CLAIM：判别和科学边界

- **S-CLAIM-01**：L 只有 candidate escape、violation 下降或验证成功才支持
  调度路线；仅 runtime 变快不算纠错改善。
- **S-CLAIM-02**：I 只有 escape 或 violation 下降才支持该映射；单块不得证明
  普遍图因果。
- **S-CLAIM-03**：P 的消息/翻转变化但未验证只能归为 prior 影响；完全不变只
  削弱 prior-only 解释；不得宣称 M2 优胜。
- **S-CLAIM-04**：L/I/P 均无 hard-bit escape 时 SHALL 停止 binary edge-level
  flooding/layered/damping 微调，后继限定为 grouped-symbol mask BP tiny
  exhaustive 或同块 GF32 对照。
- **S-CLAIM-05**：任一臂成功只允许进入同路线小样本 confirmation plan，不直接
  进入 V73；不得作 FER、SKR、信息极限、LDPC 无效或跨 session 推广断言。

## S-TEST：未来 synthetic 验收

- **S-TEST-01**：T0 SHALL 覆盖 py_compile/import 无副作用、字段/母图/预算常量、
  tiny mixed/pure cycle 口径和 M2 归一。
- **S-TEST-02**：T1-L SHALL 覆盖 layered 顺序、row snapshot、非零 prior/c2v、
  最新消息可见性、stale flooding 差异、APP_raw 25 减旧 c2v 1 得 24、
  self-exclusion、syndrome/degree sign、warm-start rebuild、edge/factor budget。
- **S-TEST-03**：T1-I SHALL 覆盖全列 bijection、互逆、seed 确定性、high 分布、
  LSB、映射代数、tiny syndrome oracle、H 不变量、prefix 和 mixed/pure cycle
  口径分离。
- **S-TEST-04**：T1-P SHALL 覆盖冻结参数、wrapped Laplace、K floor 阶段、
  1024 循环平移、Bob-only、natural-log/log2 分离，并允许结果变差。
- **S-TEST-05**：T1-METRICS SHALL 覆盖 quantiles/sign/zero、手算 F/S/A、
  单边与变量聚合分离、violation、clip 计数、candidate 直接比较和敏感数组
  禁止。
- **S-TEST-06**：T2 SHALL 使用显式 fake runner 和 fresh workspace，覆盖三臂
  ladder、动态四计数器、提前成功/满梯/异常/timeout/RSS/NOT_ATTEMPTED、
  baseline null 原因、四文件 schema、production path 门禁和科学字段 replay。
  replay SHALL 排除 wall/RSS/timestamp/path，不要求整文件字节一致。
