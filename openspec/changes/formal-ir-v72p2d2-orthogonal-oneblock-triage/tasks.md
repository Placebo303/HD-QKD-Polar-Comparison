# V72P2D2 任务与验收

状态：`PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`。本任务表绑定 base
`e094f7e548380db4bfcbc1fe73472e670c32379a` 和分支
`formal-ir-v72p1-addendum-clean`。本轮只审查计划，不实现、不运行 decoder、
不读取 raw/parquet、不创建结果目录、不改 adapter、memory、cycle_state、
`src/`、`experiments/`、`tools/`、`results/`或既有输出。

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
- **D2T0-5**：按 V70R1 公式构造 M2 K，`sum(K)=1`、每个 prior 行归一，
  不触发生产输入；接口方案固定为 A，L 使用新 layered API，I/P 使用既有
  `run_decoder`，不调用 `run_incremental_decoder`。

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
- **D2T1L-4**：验证受影响 symbol 的全部 10 个 f2b 重算，目标 bit self-
  exclusion 保持；syndrome 0/1 和 check degree 1/2/3 的 sign 与手算 SPA
  一致，Numba/Python 路径（若存在）一致。
- **D2T1L-5**：验证 active c2v checkpoint rebuild：旧边完整携带、新边为零，
  从 c2v 重建 b2f/f2b/APP_raw；不跨 block 携带。
- **D2T1L-6**：验证一个完整 sweep 更新每个 active edge 一次；residual 是
  sweep 前后 active c2v snapshot 的全边 L-infinity 差，sweeps 与 edge_updates
  分开计数。
- **D2T1L-7**：验证每 checkpoint 最多 10 个完整 sweep、每臂最多 720 个，
  余量不足完整 sweep 时不启动 partial sweep；L 的 factor work 另计，不能
  以 edge budget 代替总计算量。
- **D2T1L-8**：验证 `residual<tol` 只设置 converged，不跳过 syndrome/tag
  验证；验证接受必须仍满足 finite、syndrome 和 tag 条件。
- **D2T1L-9**：只允许调用
  `run_layered_decoder(prior_logp, syndrome_target, indptr, indices,
  max_sweeps, warm_start_c2v)`。若实现不能证明上述顺序和最新消息可见性，
  结果为 `BLOCKER`，禁止把 row loop 包装 flooding 称为 layered。

## D2T1I：full-column interleaver

- **D2T1I-1**：固定 high-degree 集合 old columns `0..1203`，degree 由原 H
  `bincount` 得到，按 `(-degree,old_col)` 排序；使用
  `info_count/info_load` 和字典序 `(info_load,info_count,symbol_id)` 选择，
  高连接列放入该 symbol 的 slot `bit_id=info_count`，每次递增计数。
- **D2T1I-2**：固定 seed `20260902` 的
  `default_rng` permutation 对 old parity columns `1204..10239` 排序，
  依序填充 `(symbol_id,bit_id)` 升序剩余物理 slots；物理 bit 采用 LSB bit 0。
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
  1e-300))`，floor 只在 log 阶段；每个 Bob 值的 prior 行是循环平移，全部值
  finite/positive/归一。
- **D2T1P-4**：builder 只接收 physical Bob 与冻结参数，不接 Alice；Alice
  只能进入 runner 的 syndrome/tag/oracle 边界。BP 用自然 log，CE 只用 log2。
- **D2T1P-5**：历史 M2 VAL CE `6.787126437359054` 仅作非门槛背景；测试必须
  允许 M2 消息改变但验证变差或完全不变。

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
  updates、`state_evaluations=1024*target_updates`、finite 和 clip counts。
- **D2T1M-5**：分别记录单边 `max|c2v|` 与
  `max_v|sum incident c2v|`；记录 c2v/f2b `abs>=20-1e-12` clip count 和
  `abs(A_raw)>20` count。APP 输出可裁剪，不能声称保留 factor preclip 数组。
- **D2T1M-6**：输出不包含秘密数组、Alice/Bob symbols、syndrome bytes、
  完整 prior、完整消息或逐 symbol 数组；D1 O1 只能标
  `POSTHOC_RECONSTRUCTED`。

## D2T2：fake 端到端与公开计费

- **D2T2-1**：fake runner 使 L/I/P 在 tiny graph 完成 ladder，验证每臂状态
  独立、checkpoint 顺序、warm-start 和四文件 schema；测试只写
  `workspace/<task>/<uuid>`，不写生产输出根。
- **D2T2-2**：每个新臂独立计数 syndrome rows/bits、tag bits、CONTINUE
  control bits 和 disclosed rows；tag 在第一次验证前只发布一次 64 bits，
  进入下一 checkpoint 才加 1 CONTINUE；成功、耗尽、异常、timeout 均保留
  已发布计数，三臂不相加。
- **D2T2-3**：fake 反例覆盖：发布后异常不回滚；满 ladder 为
  `9036+64+71` 的计费结构；提前成功按 reached rows 加 tag/control；余额为
  零不发布、不调用、不增加任何计数；不能把每臂写成固定 9100。
- **D2T2-4**：测试 candidate syndrome violation、双条件 verification、
  convergence 与 verification 分离、A 新指标 null 及
  `not_recorded_reason`；baseline 只比较已存共同指标。
- **D2T2-5**：T2 只显式注入 fake runner；默认 import/CLI 不进入真实 decoder、
  raw/parquet、`run_01`或生产输出。
- **D2T2-6**：严格科学字段 replay 在相同 seed 下确定；wall、RSS、timestamp、
  临时 path 排除确定性比较。不要求整文件字节一致。

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
- **D2T3-4**：A 只读复用，L/I/P 各恰一次，无 rerun、无调参、独立 c2v；执行
  前依次通过独立 Plan Review、Implementation Review、Pre-EXECUTE，发布前
  通过 Pre-RESULT。
- **D2T3-5**：manifest/results/table/report 顶层与 per-arm 字段遵循 design §8，
  保存 provenance、base/implementation SHA、config、stop、metrics、accounting
  和 claim boundary，不保存敏感数组。

## D2T4：判别、文献和返回

- **D2T4-1**：机械执行预注册判别：L 需 escape/violation 下降/验证成功才支持
  调度路线；I 需 escape/violation 下降才支持该映射；P 只把消息/翻转变化
  标为 prior 影响，未验证不得晋级；三臂无 escape 则停止 binary edge-level
  flooding/layered/damping 微调。
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
