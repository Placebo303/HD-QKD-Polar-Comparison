# V72P2D2 正交单块分诊计划候选

- Change：`formal-ir-v72p2d2-orthogonal-oneblock-triage`
- Base：`e094f7e548380db4bfcbc1fe73472e670c32379a`
- Branch：`formal-ir-v72p1-addendum-clean`
- Lifecycle：`PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`
- 当前计划不实现、不运行 decoder、不读 raw/parquet、不创建结果目录、不授予
  development 或 formal execution。

Base/accepted-plan/implementation SHA 只承担 AGENTS 要求的 Git 版本绑定；它们
不承担数据或 artifact 内容校验。本计划不新增数据或 artifact 内容摘要、签名
或其他校验字段。

## Goal

V72P2D1 已接受的单块诊断显示，原 binary flooding 候选在 72 个 checkpoint
逐 bit 等于 Bob，APP 约 0.8，单边 c2v 约 0.025，Arm A/旧 Arm B 均耗尽 ladder。
本 change 在同一非新鲜 D1 block 上冻结一次正交四臂分诊，区分：

1. L：row-serial layered 调度是否能让最新消息传播；
2. I：mother 的 degree-role 是否被固定 symbol 分组错误对齐；
3. P：M0 prior 是否把候选锁在 Bob-oriented fixed point。

Arm A 只读复用 D1 记录，L/I/P 各只改变一个因素，不预设成功路线。

## Non-goals

本 change 不重跑 A，不做九块确认、FER、SKR、信息极限、方法定级或跨 session
推广；不混合三臂，不重选参数，不实现 grouped-symbol mask BP，不做 GF32
对照，不修复 V72P1 adapter 的 deferred stale-return bug，不改原始
`src/experiments/tools/results` 或既有输出。

## 固定实验设计

共同 block 是 session `20260123_1M_600k_0dB` 的 D1 `VAL1726..1729` 四帧
连续 1024-symbol 块，明确 `non_fresh=true`。mother 固定为
`9036x10240`、`nnz=49620`、check degree `{4:1,5:4594,6:4441}`、degree-2
列 9035。ladder 固定为
`range(160,8993,128)+[9032,9036]`，共 72 点；数值固定为 float64、clip 20、
tolerance 1e-6。

四臂固定如下：

- **A**：复用 D1 Arm A 的已存共同指标，禁止重跑。
- **L**：原 H + D1 M0 + 真正 layered row-serial decoder，只改变调度。
- **I**：全 10240 列 degree-balanced `H_I` + D1 M0 + 原 flooding，只改变
  物理列与 symbol 的分配。
- **P**：原 H + V70R1 1M CAL-only M2 + 原 flooding，只改变 prior。

每 checkpoint 最多 10 次完整更新，每臂最多 720 次；L 的更新单位是完整
active-row sweep，I/P 的更新单位是完整 active-edge flooding iteration。
三臂均不启动 partial update，c2v 状态仅在同臂相邻 checkpoint 携带，新边置零。

## 固定接口、prior 和映射

新模块固定提供
`run_layered_decoder(prior_logp, syndrome_target, indptr, indices,
max_sweeps, warm_start_c2v)`；adapter 不改，L 只调用该 API，I/P 只调用既有
`run_decoder`。`run_incremental_decoder` stale-return bug deferred。

I 使用 old high columns `0..1203`，按 `(-degree,old_col)` 排序；使用
`info_load/info_count` 的字典序 tie-break，把 high 列写入物理
`sym*10+info_count`；parity 列使用 seed `20260902` 的 `default_rng` permutation
填充 `(symbol_id,bit_id)` 升序剩余 slots。完整算法和代数方向在 design/spec
固定，参考的 symbol 边数与 cycle 数不是门槛。

P 固定为 V70R1 1M CAL-only M2：Laplace、`mu=0.0`、
`scale=0.2714417616594907`、`eps=0.562251256281407`、`Q=1024`。K 先正常
归一，log 阶段才用 `max(K,1e-300)`；builder 只接 physical Bob，不接 Alice；
BP 用自然 log，CE 用 log2。历史 CE `6.787126437359054` 不是门槛。

## 无 tag 的诊断与计费

本 change 固定 `tag_bits=0`、`tag_ok=NOT_APPLICABLE`，诊断中不生成或处理 tag。
不定义协议接受、验证成功或未检测错误语义。每个新臂
每 checkpoint 只保存标量聚合：candidate syndrome violation、
candidate-vs-Bob bit/symbol flips、L0、F、S、A、delta APP 的分位数/幅度/zero、
sign transitions、residual、sweeps/edge updates、factor target updates/state
evaluations、finite 和 syndrome 状态。quantiles 为
`[0,0.01,0.05,0.25,0.5,0.75,0.95,0.99,1]`，zero tolerance 为 `1e-15`。

`syndrome_satisfied = finite && candidate syndrome 与公开 syndrome prefix 一致`。
首次满足只记录 `first_syndrome_satisfied_ckpt` 和当前候选的标量摘要，不早停，
继续完整预注册 ladder 到 9036 或预算/异常停止。oracle 仅在结束后运行；
`diagnostic_exact = syndrome_satisfied && oracle_exact`，
`syndrome_collision_wrong = syndrome_satisfied && !oracle_exact`，二者均为
描述性事后分类，不称未检测错误、协议失败或验证成功。

每臂独立记录 `syndrome_rows_published`、`syndrome_bits_published`、
`tag_bits_published=0`、`control_bits_sent` 和 `disclosed_rows`；公开计费为
`syndrome_bits_published+control_bits_sent`。每 checkpoint 发布新增 syndrome
rows，进入下一 checkpoint 才增加 1 CONTINUE control bit；异常、timeout、预算
中断保留已发布计数。完整 ladder 正常达到的名义计费为 `9036+71=9107`，三臂
counterfactual 计数不相加，不称真实 session leakage。

A 只允许与 D1 已存共同指标比较：outcome、iterations、candidate-vs-Bob、D1
APP、D1 single-edge c2v 和 O1 的 `POSTHOC_RECONSTRUCTED violation`。新 F/S/A/L0
指标在 A 中为 null，并附 `not_recorded_reason`，不得补造或与 A 定量差分。

## 未来实现与状态门禁

接受本计划并完成后续 Implementation Review/Pre-EXECUTE，未来实现精确只有：

- `comparison_bench/src/comparison_bench/formal_ir/v72p2d2_orthogonal_triage.py`
- `scripts/v72p2d2_orthogonal_triage.py`
- `comparison_bench/tests/test_v72p2d2_orthogonal_triage.py`

禁止 config/fixture、adapter 或 frozen baseline 改动。真实输出固定为
`comparison_bench/outputs_comparison/v72p2d2_orthogonal_oneblock_20260904/`
下的 `manifest.json`、`results.json`、`table.csv`、`report.md` 四文件，不覆盖
D1 输出且不创建 `run_01`。manifest 只保留 AGENTS 要求的
`base_sha`、`accepted_plan_sha`、`implementation_sha` Git 版本绑定字段；不含
数据或 artifact 内容摘要、签名或校验字段。

真实执行固定为 L/I/P 各一次；A 只读。准备失败使三臂为 `NOT_ATTEMPTED` 并
返回非零；任一新臂 exception、nonfinite、RSS 超限或 600 秒 soft wall 超时使
该臂 `BLOCKED`，停止本次 invocation，其余臂为 `NOT_ATTEMPTED`，四个 arm
artifact 均保留。普通 `LADDER_EXHAUSTED` 或预算正常耗尽才继续下一臂。单臂
soft wall 为 600 秒，invocation 为 2400 秒（prep 600 + 三臂各 600），peak
RSS 硬上限 2 GiB。执行前必须通过独立 Plan Review、Implementation Review、
Pre-EXECUTE，发布前必须通过 Pre-RESULT；本计划不授任何执行权限。

## 判别与出口

- L 只有出现 candidate escape、violation 下降或 syndrome_satisfied，才支持
  继续调度路线；仅 runtime 变快不算纠错改善。
- I 只有出现 escape、violation 下降或 syndrome_satisfied，才支持该映射；单块
  不证明图结构因果。
- P 若改变消息或翻转但未出现 syndrome_satisfied，只能说明 prior 影响；完全
  不变则削弱 prior-only 解释；不得宣称 M2 优胜。
- L/I/P 都无 hard-bit escape 时，停止 binary edge-level flooding/layered/
  damping 微调，下一周期限定为 grouped-symbol mask BP tiny exhaustive 或同块
  GF32 对照。
- 任一臂出现 syndrome_satisfied 只允许进入同路线的小样本 confirmation plan，
  不直接进入 V73；没有协议接受语义。
- 禁止 FER、SKR、信息极限、LDPC 无效、图结构因果、M2 优胜或跨 session 推广
  断言。

完整数学、计量、测试和 schema 见同目录 `design.md`、`tasks.md`、`specs/spec.md`。
