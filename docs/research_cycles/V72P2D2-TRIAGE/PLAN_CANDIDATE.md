# V72P2D2 正交单块分诊计划候选

状态：`PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`。本入口仅记录待独立审查的
计划，不是接受记录、实现授权或 decoder 授权。

- Repository：`HD-QKD_Polar_Comparison`
- Branch：`formal-ir-v72p1-addendum-clean`
- Base SHA：`e094f7e548380db4bfcbc1fe73472e670c32379a`
- Cycle：`V72P2D2-TRIAGE`
- `development_execution_authorized: false`
- `formal_execution_authorized: false`
- `scientific_promotion: false`
- `accepted_plan_sha: null`
- `implementation_sha: null`

上面的 SHA 字段仅是 AGENTS 要求的 Git commit/计划/实现版本绑定，不承担数据或
artifact 内容校验。计划阶段只保留本入口和 OpenSpec 四工件共 5 个新增文件。
禁止实现代码、decoder、真实数据或 parquet 读取、结果目录创建，以及对 V72P1、
V72P2、D1 已接受文件、`cycle_state.yaml`、memory、`src/`、`experiments/`、
`tools/`、`results/`和既有 comparison 输出的修改。

## 目标与科学问题

V72P2D1 的已接受单块事实是：原 binary flooding 的候选在 72 个 checkpoint
逐 bit 等于 Bob，APP 约 `0.8`，单边 c2v 约 `0.025`，Arm A 和旧 Arm B
均为 `LADDER_EXHAUSTED`。这些事实只用于提出诊断问题，不在本计划重跑。

本计划只在同一固定非新鲜诊断块上比较四臂：已存的 Arm A、仅改变调度的 L、
仅改变物理 bit 分组的 I、仅改变 prior 的 P。目标是区分调度、图的
degree-role/symbol 对齐和 prior 三个假设；不预设任一臂优胜。

## 冻结的四臂

| 臂 | 图 | prior | decoder | 唯一变化 |
|---|---|---|---|---|
| A | 已接受 D1 Arm A | 已接受 M0 | 已存结果 | 只读复用，不重跑 |
| L | 原 H | M0 | 新 `run_layered_decoder` | 调度 |
| I | full-column degree-balanced H_I | M0 | 既有 flooding `run_decoder` | 物理列映射 |
| P | 原 H | 冻结 M2 | 既有 flooding `run_decoder` | prior |

L/I/P 使用相同 block、72 点 ladder、每 checkpoint 10 次完整更新、每臂
720 次完整更新、`float64`、`llr_clip=20.0`、`convergence_tol=1e-6`，以及
syndrome-only 诊断和公开计费规则。每臂 c2v 状态独立。L 的 factor work
单独计量，不把相同更新次数描述为相同总计算量。

## 固定输入

- session：`20260123_1M_600k_0dB`。
- diagnostic block：D1 已使用的 `VAL1726..1729` 四帧连续块，非 fresh，
  仅用于诊断可比性。
- mother：`9036x10240`、`nnz=49620`，check degree
  `{4:1,5:4594,6:4441}`，degree-2 列 `9035`。
- ladder：`range(160,8993,128) + [9032,9036]`，共 72 点。
- 预算单位：L 的一次完整 sweep；I/P 的一次完整 flooding iteration，
  两者都必须更新当前全部 active edges 一次。
- 各 checkpoint 上限 10，单臂总上限 720；剩余预算不足一个完整更新时不启动
  partial update。

## L layered 数学要求

L 必须实现真正使用最新消息的 row-serial layered decoder。内部保留未裁剪的
`APP_raw = factor_to_bit + bit_to_factor`，且每条 v2c 使用
`factor_to_bit[v] + bit_to_factor[v] - c2v_old[e]`。不得使用
`APP_clipped - c2v`。每行从 row-start snapshot 计算整行 v2c，再同时计算整行
新 c2v 后一次性提交；随后更新 b2f、该行影响的每个 symbol 的全部 10 个
f2b 和全部 10 个 APP_raw。APP 只在诊断、输出和 hard sign 处裁剪，裁剪不改变 sign。

每 checkpoint 只携带 active c2v；新增 edge 置零，并从 active c2v 完整重建
b2f、f2b、APP_raw。每个完整 sweep 的 residual 是 sweep 前后 active c2v
snapshot 的最大绝对差。syndrome-aware sign、目标 bit self-exclusion 和
收敛语义必须与 V72P1 一致；本计划固定无 tag 诊断。

接口固定为 A：adapter 零改动；新模块提供
`run_layered_decoder(prior_logp, syndrome_target, indptr, indices,
max_sweeps, warm_start_c2v)`。L 只调用该接口，I/P 只调用既有 `run_decoder`。
`run_incremental_decoder` 的 stale-return bug 本周期 deferred，不得顺手修复。

## I interleaver 与 P prior

I 的唯一映射算法、方向、seed、LSB bit 顺序和不变量完整定义于
OpenSpec `design.md` §4。实现必须对全部 10240 列使用 `old_to_phys`，并验证
`phys_to_old` 互逆；参考的 `41/47/65` 与 `95/95` 不是门槛。

P 固定使用 V70R1 1M CAL-only 选择的 M2 Laplace 参数：`mu=0.0`、
`scale=0.2714417616594907`、`eps=0.562251256281407`、`Q=1024`。M2 的
kernel、floor 阶段、自然 log 和 Bob-only builder 见 OpenSpec `design.md` §5。
历史 VAL CE `6.787126437359054` 只作背景，不是门槛或优胜证明。

## 诊断、计费与结果边界

每个新臂每 checkpoint 只保存标量聚合：candidate syndrome violation、
candidate-vs-Bob bit/symbol flips、L0、F、S、A、delta APP 的固定分位数和
幅度统计、sign transitions、zero/clip、residual、sweeps/edge updates、
factor target updates/state evaluations、finite、`syndrome_satisfied`、
`tag_bits=0`、`tag_ok=NOT_APPLICABLE`，以及结束后的 oracle 状态。
不保存秘密数组、Alice/Bob 符号、syndrome bytes、完整 prior 或消息数组。

`syndrome_satisfied` 定义为 `finite && candidate syndrome 与公开 syndrome
prefix 一致`。首次满足只记录 `first_syndrome_satisfied_ckpt` 和当前候选快照
的标量，不早停，继续预注册 ladder 观察稳定性，直到 9036 或预算/异常停止。
结束后才使用 oracle：`diagnostic_exact = syndrome_satisfied && oracle_exact`，
`syndrome_collision_wrong = syndrome_satisfied && !oracle_exact`；二者仅是
描述性事后分类，不称为未检测错误、协议失败或验证成功。

公开计费按每臂 counterfactual 独立计算：`syndrome_bits_published +
control_bits_sent`，无 tag bits。每 checkpoint 发布新增 syndrome rows，进入
下一 checkpoint 才发送并计入 1 个 CONTINUE control bit；成功描述改为首次满足
syndrome 的 checkpoint，不作协议接受。满 ladder 正常达到的名义计费为
`9036+71=9107`，异常/timeout/预算中断保留已发布计数。不得将三臂计数相加，
不得称其为真实 session leakage。

A 只允许使用 D1 已存的共同指标比较：`outcome`、`iterations`、
`candidate-vs-Bob`、D1 APP、D1 single-edge c2v 和 O1 的
`POSTHOC_RECONSTRUCTED violation`。新 F/S/A/L0 指标在 A 中为 `null`，并带
`not_recorded_reason`，不得补造或与 A 做定量差分。

## 未来实现和执行的固定边界

独立接受本计划后，未来实现精确使用 3 个文件：

1. `comparison_bench/src/comparison_bench/formal_ir/v72p2d2_orthogonal_triage.py`
2. `scripts/v72p2d2_orthogonal_triage.py`
3. `comparison_bench/tests/test_v72p2d2_orthogonal_triage.py`

禁止 config/fixture、adapter 或 frozen baseline 改动。真实诊断输出根固定为
`comparison_bench/outputs_comparison/v72p2d2_orthogonal_oneblock_20260904/`，
只含 `manifest.json`、`results.json`、`table.csv`、`report.md`，不覆盖 D1
输出且不创建 `run_01`。manifest 只保留 AGENTS 要求的
`base_sha`、`accepted_plan_sha`、`implementation_sha` Git 版本绑定字段；
它们仅是 Git 版本来源，不是数据或 artifact 内容字段。

真实执行固定为 L/I/P 各一次；A 只读。准备失败使三臂为 `NOT_ATTEMPTED` 并
返回非零；任一新臂 exception、nonfinite、RSS 超限或 600 秒 soft wall 超时使
该臂 `BLOCKED`，停止本次 invocation，其余臂为 `NOT_ATTEMPTED`，四个 arm
artifact 均保留。普通 `LADDER_EXHAUSTED` 或预算正常耗尽才继续下一臂。单臂
soft wall 为 600 秒，invocation 为 2400 秒（prep 600 + 三臂各 600），peak
RSS 硬上限 2 GiB。执行前必须通过独立 Plan Review、Implementation Review、
Pre-EXECUTE，发布前必须通过 Pre-RESULT；本计划不授任何执行权限。

## 审查出口

独立 Plan Review 必须覆盖四臂正交性、layered 11 点数学顺序、interleaver
代数等价、M2 参数与 floor、无 tag syndrome-only 语义、完整 metrics、动态计费、
异常停机、schema、测试和禁止文件范围。任一合同无法证明即 `BLOCKED`，不得用
默认值或未冻结文字绕过。
