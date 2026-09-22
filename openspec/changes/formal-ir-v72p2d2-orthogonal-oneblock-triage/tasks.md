# V72P2D2 任务与验收

状态：`PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`。本任务表绑定 base
`e094f7e548380db4bfcbc1fe73472e670c32379a` 和分支
`formal-ir-v72p1-addendum-clean`。本轮只审查计划，不实现、不运行 decoder、
不读 raw/parquet、不创建结果目录、不改 adapter、memory、cycle_state、
`src/`、`experiments/`、`tools/`、`results/`或既有输出。

`base_sha`、`accepted_plan_sha`、`implementation_sha` 只承担 AGENTS 要求的
Git 版本绑定，不承担数据/artifact 内容校验；本计划不引入数据或 artifact
内容摘要、签名或其他校验字段。

本变更的计划文件固定为：

1. `openspec/changes/formal-ir-v72p2d2-orthogonal-oneblock-triage/proposal.md`
2. `openspec/changes/formal-ir-v72p2d2-orthogonal-oneblock-triage/design.md`
3. `openspec/changes/formal-ir-v72p2d2-orthogonal-oneblock-triage/tasks.md`
4. `openspec/changes/formal-ir-v72p2d2-orthogonal-oneblock-triage/specs/spec.md`
5. `docs/research_cycles/V72P2D2-TRIAGE/PLAN_CANDIDATE.md`

独立 Plan Review 只在这 5 个文件上进行。任一数学合同无法证明则返回
`BLOCKED`，不得用默认值、未冻结文字或缩小测试范围绕过。

## D2T0：结构、数值和无副作用

- **D2T0-1**：未来 3 个实现文件可 `py_compile`/import，import 不进入真实
  decoder、raw/parquet 或生产输出路径；测试只能显式注入 fake runner。
- **D2T0-2**：断言固定母图 `9036x10240`、`nnz=49620`、check degree
  `{4:1,5:4594,6:4441}`、degree-2 列 `9035`，72 点
  `range(160,8993,128)+[9032,9036]`，每 checkpoint 10、每臂 720，
  `float64/llr_clip=20.0/convergence_tol=1e-6`。
- **D2T0-3**：断言四臂为已存 A、L、I、P；A 只读复用，L/I/P 各只改变一个
  因素；禁止 layered+I、I+M2、layered+M2。
- **D2T0-4**：tiny 1-check 双 bit 同 symbol 只用于统计口径，断言 pure-H
  check-pair 为 0、mixed symbol `sum C(k,2)` 为 1。
- **D2T0-5**：按 V70R1 公式构造 M2 K 与每个条件分布 P，分别断言 finite、
  strictly positive、sum=1；断言 `prior_logp` finite，且
  `exp(prior_logp)` 与 P 逐元素相等并逐行归一，不把 log-probability 的正号
  作为条件。整个测试不触发生产输入；接口固定为 A，L 使用新 layered API，
  I/P 使用既有 `run_decoder`，不调用 `run_incremental_decoder`。

## D2T1L：layered 数学和状态

- **D2T1L-1**：在至少两个有序 checks 的 tiny 图上构造共享 bit 且包含同
  symbol 多 bit、非零 prior、非零初始 c2v。check 0 更新后 check 1 必须读到
  新 c2v 和新 f2b；与显式 serial reference 一致，且与 stale flooding 结果
  不同。
- **D2T1L-2**：验证每 row 先从 row-start snapshot 计算全部 v2c，再同时求整行
  c2v_new，整行结束才 commit；同一 row 的 edge order 改变不会改变该 row
  的 c2v 结果。
- **D2T1L-3**：验证内部使用
  `APP_raw=f2b+b2f`，`v2c=f2b+b2f-c2v_old`；构造
  `APP_raw=25,c2v_old=1`，断言 v2c 为 24，即不能使用 clipped APP。
- **D2T1L-4**：验证受影响 symbol 的全部 10 个 f2b 与全部 10 个 APP_raw 重算，
  目标 bit self-exclusion 保持；syndrome 0/1 和 check degree 1/2/3 的 sign
  与手算 SPA 一致，Numba/Python 路径（若存在）一致。
- **D2T1L-5**：验证 active c2v checkpoint rebuild：旧边完整携带、新边为零，
  从 c2v 重建 b2f/f2b/APP_raw；不跨 block 携带。
- **D2T1L-6**：验证一个完整 sweep 更新每个 active edge 一次；residual 是
  sweep 前后 active c2v snapshot 的全边 L-infinity 差，sweeps 与 edge_updates
  分开计数。
- **D2T1L-7**：验证每 checkpoint 最多 10 个完整 sweep、每臂最多 720 个，
  余量不足完整 sweep 时不启动 partial sweep；L 的 factor work 另计，不能
  以 edge budget 代替总计算量。
- **D2T1L-8**：验证 `residual<tol` 只设置 converged，不改变 syndrome-only
  诊断；syndrome 满足也不提前结束 ladder。
- **D2T1L-9**：只允许调用
  `run_layered_decoder(prior_logp, syndrome_target, indptr, indices,
  max_sweeps, warm_start_c2v)`。若实现不能证明上述顺序和最新消息可见性，
  结果为 `BLOCKER`，禁止把 row loop 包装 flooding 称为 layered。
- **D2T1L-10**：一个 factor target evaluation 严格定义为一个
  `f2b[sym,b]` over `Q=1024` states 的完整 marginal。冻结
  `warm_start_c2v.shape == (len(indices),)`；首 checkpoint
  必须传全零数组，后续只复制同臂上一 checkpoint 的 active 前缀并将新边置零。
  `run_layered_decoder` 返回 `bit_to_factor`、`factor_to_bit`、
  `variable_to_check`、`check_to_variable`、`app_llr`、`hard_bits`、
  `hard_symbols`、`syndrome_observed`、`finite`、`residuals`、`converged`、
  `max_llr` 及完整核心/diagnostic factor 计数，所有计数可机械复算。
- **D2T1L-11**：按每 row `10*distinct_affected_symbols` 复算 L 核心
  `local_factor_target_updates`；I/P 每个实际 flooding iteration 为 10240 核心
  targets；统一 `state_evaluations=1024*target_updates`。每臂 L0 full batch 严格
  只计算一次并缓存，固定 `diagnostic_L0_target_updates=10240`；后续 checkpoint
  metrics 只能读缓存，重复计算须另加 10240 diagnostic targets 并使 T2 失败。
  L 每个实际 checkpoint 强制完整 rebuild f2b，固定增加
  `diagnostic_checkpoint_rebuild_target_updates=10240`，不允许 cache/recompute
  二选一；L final readout 复用最后状态为 0。I/P 每一次实际 `run_decoder` 调用
  末尾由 adapter 重算完整 `factor_to_bit` batch，固定增加
  `diagnostic_final_readout_target_updates=10240` 和对应
  `10240*1024` diagnostic state evaluations，I/P 不得写成 final readout=0。
  三阶段相加为 `diagnostic_factor_target_updates`，并有对应 diagnostic state
  evaluations；纯 readout 另列。每臂输出阶段计数和 core+diagnostic 总计，并由
  T2 机械断言无漏计或重复计数。
  断言结构上界 `338388*6*10*10=203032800` targets、`207905587200` state
  evaluations，并标为上界而非测量值。
- **D2T1L-12**：cost-preflight 使用真实 mother 结构和合成 prior/syndrome、
  零/非零 warm state，在 `active_rows=160,2048,4096,8192,9036` 每点恰测 1
  个完整 sweep。记录 `U_r=10*sum(distinct_affected_symbols(row) for row<r)`
  和 elapsed，`tau=max(elapsed/U_r)`；另测完整 rebuild 的
  `tau_diag=max(seconds/target)`，用独立 timer 取非核心每-checkpoint overhead
  `h=max(observed_noncore_overhead)`。令
  `W=sum(10*sum(distinct_affected_symbols(row) for row<ck) for ck in ladder)`、
  `D=10240*(1+72)`，断言
  `projected_L_wall_s=(tau*W+tau_diag*D+72*h)*1.2`。超过 600 s 必须
  `PLAN_REVISE_REQUIRED`，不准改算法偷过预算；`<=480 s` 是 20% 余量目标。
  真实 L 超时只能是 `RESOURCE_BLOCKED`。

## D2T1I：full-column interleaver

- **D2T1I-1**：固定 high-degree 集合 old columns `0..1203`，degree 由原 H
  `bincount` 得到，按 `(-degree,old_col)` 排序；使用 `info_count/info_load`
  和字典序 `(info_load,info_count,symbol_id)` 选择，高连接列放入该 symbol
  的 slot `bit_id=info_count`，每次递增计数。
- **D2T1I-2**：固定 seed `20260902` 的 `default_rng` permutation 对 old
  parity columns `1204..10239` 排序，依序填充 `(symbol_id,bit_id)` 升序剩余
  物理 slots；物理 bit 采用 LSB bit 0。
- **D2T1I-3**：断言 `old_to_phys` 是全 10240 列 bijection，
  `phys_to_old[old_to_phys[j]]=j` 且反向同样成立；重复构造得到相同映射。
- **D2T1I-4**：断言每个 symbol 恰有 10 个物理 bit，前 1204 old high
  columns 每 symbol 为 1 或 2；prior、Bob 和 candidate 比较均在 physical
  坐标，不能随 H 错误置换 prior。
- **D2T1I-5**：用
  `H_I[:,old_to_phys[j]]=H_old[:,j]`、
  `x_old[j]=x_phys[old_to_phys[j]]`验证
  `H_I@x_phys == H_old@x_old (mod 2)`，tiny oracle 也验证同一方向。
- **D2T1I-6**：断言 H_I 的 shape、nnz、row-degree multiset、column-degree
  multiset、rank 和 checkpoint prefix nesting 与 H_old 保持；不要求整文件
  字节相同。
- **D2T1I-7**：实现重算每 symbol 总边数 min/median/max、high-column 分布、
  mixed symbol `sum C(k,2)`、symbol collision rows 和 pure-H cycle；
  `41/47/65`、`95/95` 仅参考非门槛，禁止手填或写成性能结论。

## D2T1P：M2 prior

- **D2T1P-1**：逐字段断言 `family=laplace`、`mu=0.0`、
  `scale=0.2714417616594907`、`eps=0.562251256281407`、`Q=1024`；参数
  来自 V70R1 1M CAL-only 结果，禁止重新选择。
- **D2T1P-2**：按 design §5 的 wrapped Laplace shape、`K` 混合公式和循环
  位移构造；K 先正常归一，不能对 K floor 或 floor 后重归一。
- **D2T1P-3**：断言 `prior_logp[sym,a]=log(max(K[(a-bob_phys[sym])%1024],
  1e-300))`，floor 只在 log 阶段；K、P 和每个 Bob 值的 prior 行必须 finite、
  strictly positive、sum=1；`prior_logp` 必须 finite，且
  `exp(prior_logp)` 与 P 逐元素相等并逐行归一。不得测试 logp 的正号。
- **D2T1P-4**：builder 只接收 physical Bob 与冻结参数，不接 Alice；Alice
  只能进入 runner 的 syndrome/oracle 边界。BP 用 natural log，CE 用 log2。
- **D2T1P-5**：历史 M2 CE `6.787126437359054` 仅作非门槛背景；测试必须
  允许 M2 消息改变但 syndrome-only 结果变差或完全不变。
- **D2T1P-6**：I/P 核心 factor 计数只按既有 `run_decoder` 返回的
  `actual_iterations=len(residuals)` 计；每次实际 iteration 增加
  `local_factor_target_updates=1024*10=10240`，并满足
  `state_evaluations=1024*local_factor_target_updates`。L0、rebuild、readout
  另列 diagnostic 计数；每次实际 `run_decoder` 调用末尾的完整
  `factor_to_bit` batch 固定增加 `diagnostic_final_readout_target_updates=10240`
  （state evaluations 为 `10240*1024`），runner L0 每臂只计一次 10240。

## D2T1M：metrics 与敏感数据边界

- **D2T1M-1**：固定 quantiles
  `[0,0.01,0.05,0.25,0.5,0.75,0.95,0.99,1]` 和 `zero_tol=1e-15`；
  sign 按负、零、正三类映射，手算 fixture 验证。
- **D2T1M-2**：L0 必须来自 prior-only local factor
  `local_factor_extrinsic(prior_row,zeros(10),target_bit)`，不得命名或记录为
  APP；F 是 f2b，S 是 signed incident c2v sum，A_raw=F+S。
- **D2T1M-3**：每 checkpoint 记录 L0、F_pre/post、S_pre/post、A_raw_pre/post、
  delta_app 的 signed/absolute quantiles、max_abs、zero_count；记录两组 3x3
  sign transition，基准为当前 checkpoint 的 L0/F_post，不是首 checkpoint。
- **D2T1M-4**：记录 violation
  `weight(((H_arm[:r]@hard_bits)%2) XOR syndrome_target[:r])`、candidate-vs-
  Bob bit/symbol flips、residual、sweeps、edge_updates、local-factor target
  updates、`state_evaluations=1024*target_updates`、finite 和 clip counts；
  核心 target/state 只含 actual decoder updates，另列
  `diagnostic_factor_target_updates`、`diagnostic_state_evaluations` 和
  `diagnostic_readout_evaluations`。
- **D2T1M-5**：分别记录单边 `max|c2v|` 与
  `max_v|sum incident c2v|`；记录 c2v/f2b `abs>=20-1e-12` 计数和
  `abs(A_raw)>20` 计数。APP 输出可 clip 到 20，不能声称保留 factor preclip。
- **D2T1M-6**：输出不包含秘密数组、Alice/Bob symbols、syndrome bytes、
  完整 prior、完整消息或逐 symbol 数组；D1 O1 只能标
  `POSTHOC_RECONSTRUCTED`。
- **D2T1M-7**：冻结当前进程 RSS 采样为
  `psutil.Process(os.getpid()).memory_info().rss`，在 prep、每 checkpoint 后和
  arm 结束采样；`peak_rss_bytes` 取样本最大值，不能混用 Python 对象大小或
  子进程口径。

## D2T2：fake 端到端与 syndrome-only 计费

- **D2T2-1**：fake runner 使 L/I/P 在 tiny graph 完成 full ladder，验证每臂
  状态独立、checkpoint 顺序、warm-start 和四文件 schema；测试只写
  `workspace/<task>/<uuid>`，不写生产输出根。
- **D2T2-2**：固定 `tag_bits=0`、`tag_bits_published=0`、`tag_ok=NOT_APPLICABLE`；
  每个 checkpoint 报告 `syndrome_satisfied=finite && candidate syndrome 与
  公开 prefix 一致`，并记录首次满足点但继续 ladder，不因 syndrome 满足早停。
- **D2T2-3**：每个新臂独立计数 syndrome rows/bits、零 tag bits、CONTINUE
  control bits 和 disclosed rows；进入下一 checkpoint 才加 1 CONTINUE；
  满 ladder 正常计费结构为 `9036+71=9107`，预算中断/异常/timeout 保留
  已发布计数，三臂不相加；每个 factor target evaluation 必须对应一个
  `f2b[sym,b]` 的 1024-state marginal。T2 机械断言每臂 L0 严格一次且
  `diagnostic_L0_target_updates=10240`、L 的每个实际 checkpoint
  `diagnostic_checkpoint_rebuild_target_updates=10240`、L final readout 为 0，
  I/P 的 `diagnostic_final_readout_target_updates=10240*actual_run_decoder_calls`
  （每次对应 `10240*1024` state evaluations），以及 diagnostic/core/total 求和
  关系；任何 L0 重算、rebuild 漏计或重复计数均失败。
- **D2T2-4**：fake 反例覆盖：发布后异常不回滚；零余额不发布、不调用、不增加
  任何计数；candidate syndrome violation、syndrome 满足与收敛分离；
  oracle 只在 arm 结束后运行，不参与停止或 ladder 决策。
- **D2T2-5**：结束后事后分类仅使用
  `final_syndrome_satisfied` 与同一 final candidate 的
  `final_oracle_exact`：`diagnostic_exact=final_syndrome_satisfied &&
  final_oracle_exact`，`syndrome_collision_wrong=final_syndrome_satisfied &&
  !final_oracle_exact`。`first_syndrome_satisfied_ckpt` 只作传播诊断；构造
  “早期满足、后续 candidate 改变”的 fake 反例，断言最终分类只使用最后一个
  已完成 checkpoint，不跨 checkpoint 混合。
- **D2T2-6**：A 新指标为 null 并附
  `not_recorded_reason="D1 baseline did not record this metric; A was not rerun"`；
  baseline 只比较已存共同指标：outcome、iterations、candidate-vs-Bob、D1
  APP、D1 single-edge c2v 和 `POSTHOC_RECONSTRUCTED` O1 violation。
- **D2T2-7**：T2 只显式注入 fake runner；默认 import/CLI 不进入真实 decoder、
  raw/parquet、`run_01`或生产输出。
- **D2T2-8**：严格科学字段 replay 在相同 seed 下确定；wall、RSS、timestamp、
  临时 path 排除确定性比较；不要求整文件字节一致，也不使用数据或 artifact
  内容校验。
- **D2T2-9**：每个 checkpoint 及 arm 终态断言
  `disclosed_rows == syndrome_rows_published == syndrome_bits_published`，三者
  单调不减；full ladder 名义公开计费固定为 `9036+71=9107`，三臂计数独立。
- **D2T2-11**：T2 synthetic cost-preflight 必须使用真实 mother 结构与合成输入，
  五个代表点各跑 1 sweep，机械复算 U、W、D、`tau`、`tau_diag`、独立计时的
  `h` 及 `(tau*W+tau_diag*D+72*h)*1.2`；断言硬门槛 `projected_L_wall_s<=600`
  和 RSS 采样口径，禁止用修改科学算法降低投影。
- **D2T2-10**：验证每个 checkpoint 的 `final_checkpoint_rows`、
  `final_syndrome_satisfied`、`final_oracle_exact`、`diagnostic_exact` 和
  `syndrome_collision_wrong` 字段绑定同一 final candidate；checkpoint 层
  oracle 必须为 null，并附 `oracle_runs_after_arm_end`。

## D2T3：未来真实执行门禁（本计划不执行）

- **D2T3-1**：实现精确只有 3 个文件：
  `comparison_bench/src/comparison_bench/formal_ir/v72p2d2_orthogonal_triage.py`、
  `scripts/v72p2d2_orthogonal_triage.py`、
  `comparison_bench/tests/test_v72p2d2_orthogonal_triage.py`。不改 adapter、
  config、fixture、src、experiments、tools、results 或旧输出。
- **D2T3-2**：真实输出根固定为
  `comparison_bench/outputs_comparison/v72p2d2_orthogonal_oneblock_20260904/`，
  恰有 manifest/results/table/report 四文件，不覆盖 D1、不建 `run_01`。
- **D2T3-3**：准备 allowance 600 s，L/I/P 各 soft wall 600 s，invocation
  上限 2400 s，peak RSS 2 GiB。准备失败为三臂 `NOT_ATTEMPTED` 并非零；新臂
  exception、nonfinite、RSS 或 timeout 使该臂 `BLOCKED`，立即停止 invocation，
  后续为 `NOT_ATTEMPTED`；普通 `LADDER_EXHAUSTED` 继续下一臂。
- **D2T3-3a**：Pre-EXECUTE 前必须完成 synthetic cost-preflight；使用真实
  mother 结构、合成 prior/syndrome 与零/非零 warm state，在
  `active_rows=160,2048,4096,8192,9036` 测 layered kernel，记录实际
  target/state 计数、wall 和当前进程 RSS，并外推 `projected_L_wall_s`。硬门槛
  为 `projected_L_wall_s<=600`，`<=480` 为建议的 20% 余量目标；超过 600 必须
  `PLAN_REVISE_REQUIRED`，不得改变科学算法绕过。preflight 不运行正式三臂、不
  读取 raw/parquet；真实 L 超过 600 s 只能为 `RESOURCE_BLOCKED`，不作路线失败。
- **D2T3-4**：A 只读复用，L/I/P 各一次，无 rerun、无调参、独立 c2v；首次
  `syndrome_satisfied` 只记录不停止；执行前依次通过独立 Plan Review、
  Implementation Review、Pre-EXECUTE，发布前通过 Pre-RESULT。
- **D2T3-5**：manifest/results/table/report 顶层与 per-arm 字段遵循 design §8，
  保存 provenance、Git revision binding、config、stop、metrics、accounting
  和 claim boundary，不保存敏感数组或数据/artifact 内容校验字段；RSS 字段
  遵循 D2T1M-7 的采样口径。

## D2T4：判别、文献和返回

- **D2T4-1**：机械执行预注册判别：L 需 escape/violation 下降/syndrome 满足
  才支持调度路线；I 需 escape/violation 下降/syndrome 满足才支持该映射；P
  只把消息/翻转变化标为 prior 影响，未满足 syndrome 不得晋级；三臂无 escape
  则停止 binary edge-level flooding/layered/damping 微调。
- **D2T4-2**：三无 escape 后继只记录 grouped-symbol mask BP tiny exhaustive
  或同块 GF32 对照；不能从单块作 FER、SKR、信息极限、LDPC 无效、图因果、
  M2 优胜或跨 session 结论。
- **D2T4-3**：计划文本保留 PEG DOI `10.1109/TIT.2004.839541`、layered
  DOI `10.1109/SIPS.2004.1363033`、spatial coupling `arXiv:1001.1826`、
  HD-QKD NB-LDPC `arXiv:2305.08631`，以及 V54 `43/45`、V64 `22/24`、
  V5-C2 `384/384` 的限定域边界；V67–V72P1 不写成真实纠错成功。
- **D2T4-4**：计划提交前只对 5 个计划文件执行 `git diff --check`、完整
  `git status --short`、基线范围审查和 staged manifest 检查；不 add 任何
  untracked 历史文件，不运行 decoder。

完成条件：5 个计划文件内容一致、R1–R13 合同均有对应任务和验收、
`REAL_EXECUTION_AUTHORIZED=false`、`DECODER_EXECUTED=false`，然后停止于
`NEXT_GATE: INDEPENDENT_PLAN_REVIEW`。
