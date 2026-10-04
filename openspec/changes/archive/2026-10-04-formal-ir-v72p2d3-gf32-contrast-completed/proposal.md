# V72P2D3 GF32 对照计划候选（基于 D1 映射表冻结）

- Change：`formal-ir-v72p2d3-gf32-contrast`
- Base：`e094f7e548380db4bfcbc1fe73472e670c32379a`
- Branch：`formal-ir-v72p1-addendum-clean`
- Cycle：`V72P2D3-GF32`
- Lifecycle：`PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`
- 当前计划不实现、不运行 decoder、不读 raw/parquet、不创建结果目录、不授予 development 或 formal execution。

Base/accepted-plan/implementation SHA 只承担 AGENTS 要求的 Git 版本绑定；它们不承担数据或 artifact 内容校验。本计划不新增数据或 artifact 内容摘要、签名或其他校验字段。

Ponytail lite：算法模块、runner 和 focused test 各一个；薄 adapter 优先复用历史 kernel；不用框架、插件、事件总线、缓存、锁、retry 或完整消息持久化。不预设优胜者。

## Goal

在同一非新鲜 D1 诊断块上冻结一次二臂对照，区分 binary 基线是否被困在 Bob-oriented fixed point，而 balanced 5+5 GF32 表示能否带来候选移动：

- **A**：只读复用 D1 baseline（原 9036x10240 mother + D1 M0 + decoder0 flooding），禁止重跑。
- **G**：GF32 两层增量对照（q=32 poly37 + 5+5 `symbol=low+32*high` + H_base184+H1-16 nested Δ8+8 + 两层增量 decoder，上限 90，damping 1.0，无 tolerance），同 VAL 块、同 CAL prior 域，不调参。

G 与 A 仅作描述性对照，不作单因素因果断言，不预设 G 或 A 优胜。

D1 已明确并冻结为本计划唯一映射/方法基线：GF32 q32 poly37 可复用、5+5 表示 `s=32*u1+u2`、H_base184/190/192+H1-16、nested Δ8+8、layered vs incremental 正交、90 为硬帽 damping1.0 无 tolerance、prior TRAIN-only VAL 需适配 CAL 禁回灌、泄漏 `5*m+80+64`、V64 verify 纯函数可复用、V64 归因禁定论。任一与 D1 不一致即 REVISE。

## Non-goals

本 change 不重跑 A，不做九块确认、FER、SKR、信息极限、方法定级或跨 session 推广；不混合表示，不重选 prior 参数，不实现 grouped-symbol mask BP，不修复 V72P1 adapter 的 deferred stale-return bug，不改原始 `src/experiments/tools/results` 或既有输出；不作 Polar/Cascade/LDPC 跨方法 rank；不将 V64 归因写成定论；不将 V67–V72P1 写成真实纠错成功。

## 固定实验设计

共同 block 是 session `20260123_1M_600k_0dB` 的 D1 `VAL1726..1729` 四帧连续 1024-symbol 块，明确 `non_fresh=true`。CAL 为同 session `CAL702..1725`，仅用于 G prior 适配与 A 的 D1 M0 复用 comparison；禁止用 VAL 选参、调参或回灌 prior。

- **A**：复用 D1 Arm A 已存共同指标（outcome、iterations、candidate-vs-Bob、D1 APP、D1 single-edge c2v、O1 `POSTHOC_RECONSTRUCTED violation`），禁止重跑。数值 `float64/clip20/tol1e-6`、ladder `range(160,8993,128)+[9032,9036]` 72 点、每 ckpt 10 次、每臂 720 次，均只作复用比较口径。
- **G**：GF32 两层增量，同 VAL 块、同 CAL 域，一次运行，无 rerun、无事后调参。Alice 仅提供 syndrome prefix + 结束后 posthoc oracle；Bob + CAL 仅提供 prior；诊断中无 tag（`tag_bits=0`、`tag_ok=NOT_APPLICABLE`），不生成 tag 泄漏。

映射冻结：`low=bits0..4`、`high=bits5..9`、`bit0=LSB`、`symbol=low+32*high`（即 `s=32*u1+u2` 其中 `u1=high`、`u2=low`），同方向、无 Gray、无置换、`+1024 roundtrip`（pack/unpack 往返一致）。H_base 冻结为 1M Lane C `184` 行（`190/192` 为他 session 参照，不执行），`H1=16` 行，`H_total=200` 行，nested 前缀 `184/192/200`（Δ8+8）。layered（A decoder0 flooding/layered 家族）vs incremental（G 两层增量）正交，不得混合。

G decoder 冻结：`max_iter=90` 为硬帽、`damping=1.0`、无 residual tolerance（仅 syndrome 停止 + 90 硬停），自然 log 域 BP，CE 以 log2 报告。prior 冻结为 TRAIN-only 数学 + 当前 CAL 适配：方向必须明确为 `P(high|Bob_side)` 与 `P(low|high,Bob_side)`（即 `P(U1|B)` 与 `P(U2|U1,B)`），禁 Alice、禁旧 session、禁 VAL 选参；方向有歧义则 `REVISE`，不得猜测。报告 `joint/low/high CE` 的 log2 链式关系，decoder 内部自然 log 转换显式。

泄漏冻结：`leak = 5*m_total + 64 = 5*m_base + 80 + 64`（`m_total` 含 H1：`200/208/216 → 1064/1104/1144`；等价 L2-only 行 `184/192/200 → 1064/1104/1144` 经 `leak_for_base`）。1M 基线 `5*184+80+64=1064`，stage1 `+40=1104`，stage2 `+80=1144`。V64 `compute_tag_64` 纯函数可复用为只读 helper，但 D3 不生成 tag、不计 tag 泄漏、不作验证成功语义。V64 归因禁定论，不得引用为确定根因。

## 历史 kernel 与薄 adapter 冻结（R1–R5）

- **R1**：`HISTORICAL_KERNEL=v35 decode_row_layered_fftqspa`（码字域：长度 `n=1024` 的 GF32 码字向量，非比特向量）。输入 `(H, prior P(X), syndrome H*x)`，输出 `DecoderResult(x_hat, syndrome_ok, iterations 0..max, final_beliefs + runtime/status)`；`0` 为初值即满足（无更新），`1..max` 为整层扫描后满足，`max` 为耗尽；仅 syndrome 等式停止，无 residual tolerance；`warm_beliefs` 仅为 `(n,32)` log-belief 初值（非 message carry，`check_to_var` 恒零初值），V54 生产路径（`_dec_l1` 与 L2 `_dec` 调用）实际恒为冷启动（`warm_beliefs=None`）。
- **R2**：唯一 kernel 精确复用 V54 链：L1 `_dec_l1/H1`（`P(U1|B)` 经 `get_l1_prior_p_u1_given_b`，`q=softmax(final_beliefs)`），L2 三 stage `H_base/H_joint/H_total` 且 `prior_l2=q@P`（经 `get_l1_app_prior_l2` 精确复用），`max90/damping1.0`。生产恒 `decode_fn=None` 直调真迭代函数。禁 argmax 冒充、固定 hard、写死 iters、mock 进生产、简化 decoder、称 binary 为 GF32（binary helper 仅 Arm A）、改历史 kernel。
- **R3**：薄 adapter 只做映射/矩阵/prior 方向/syndrome/调真核/字段统一（`get_gf32_field` 即 v35 `GF2mField.create(32)` poly37）/stage 编排/diagnostics；生产直调真迭代函数；返回 `x_hat/syndrome_observed/ok/iterations_used/residual 或 NOT_RECORDED/finite/runtime/stop/candidate_changed/vs_bob`，不伪造缺失字段（`residual` 恒 `NOT_RECORDED` 因真核无 residual；`vs_bob/candidate_changed` 无 Bob 层时为 null；`hard/iters/syndrome_satisfied` 仅为 `x_hat/iterations_used/syndrome_ok` 的 D6 回兼容视图）。
- **R4**：每 stage cold start 严格复用：生产每 stage 恒传 `belief_warm=None`（与 V54 一致），`belief_warm` 不称 message carry，加 cold 语义测试（cold/warm 初值一致性 + 形状/有限性拒绝 + 生产 `belief_warm=None` 计数探针）。
- **R5**：冻结历史顺序与每层五元组（GF32 定义/Bob side/prior/syndrome/输出/下层条件/重组）：L1（`U1=high/MSB`，Bob 侧 `y1`，`P(U1|B)`，`s1=H1*u1` Alice，输出 `x_hat_u1+q`，无门控恒进 L2，重组 `q=softmax`）→ L2（`U2=low/LSB`，Bob 侧 `(u1,b)` 经 `q`，`prior_l2=q@P`，`s_base=H_base*u2/s_joint/s_total` Alice，输出各 stage `x_hat`，下层条件 base-失败→joint、joint-失败→total，重组 `layers_to_symbols`）；L1 失败仍按历史进入 L2（L2 恒用 `q`，不门控），L2 base 满足跳过 joint/total、joint 满足跳过 total（syndrome-only 短路；V54 另含 tag，本计划无 tag）。

调用图（生产，`decode_fn=None`）：`symbols_to_layers/factorize_f03 绑定（u1=high/u2=low）→ get_gf32_field（v35 poly37 统一）→ nested H（H1-16 + H_base184/joint192/total200）→ V54 P(U1|B)/q@P（s1/s_base/s_joint/s_total 经 gf32_syndrome，Alice 侧）→ history_decode（真核，belief_warm=None cold）→ run_g_layer/run_l1_stage/run_l2_incremental_chain 诊断（含 q 重组与短路）→ write_contrast_outputs`。

## 固定接口与范围

新模块固定为 `v72p2d3_gf32_contrast`（算法）+ runner 脚本 + focused test 各一个；cycle 薄 adapter 唯一复用 `v35 decode_row_layered_fftqspa` 经 V54 链（L1/H1 + L2 三 stage + q@P），零新框架，不改历史 kernel。真实输出固定为新目录 `comparison_bench/outputs_comparison/v72p2d3_gf32_contrast_20260904/` 下 `manifest.json`、`results.json`、`table.csv`、`report.md` 四文件，不覆盖 D1/D2 输出且不创建 `run_01`。manifest 只保留 `base_sha/accepted_plan_sha/implementation_sha` Git 版本绑定字段。

真实执行固定为 G 一次；A 只读。G 每层独立报告 `rows/iters/syndrome/candidate-vs-Bob/posthoc/total/control/runtime`（low/high 分层 + total/control 公开计费 + runtime/RSS）。预算：全双层 synthetic/真实 G 墙钟、peak RSS `<2GiB`，见 design §7 / tasks D7/D9。执行前必须通过独立 Plan Review、Implementation Review、Pre-EXECUTE，发布前必须通过 Pre-RESULT；本计划不授任何执行权限。

## 判别与出口（D10 四分支）

- `G_EXACT`：final syndrome 满足且 posthoc oracle exact → 允许进入同路线小样本 confirmation plan，不直接进入 V73。
- `G_COLLISION`：syndrome 满足但 oracle wrong → 记 syndrome-collision-wrong，仅描述性，不称验证成功。
- `G_IMPROVED_NO_SYNDROME`：syndrome 未满足但 candidate-vs-Bob 残留下降或 hard-bit escape → 支持继续 GF32 表示路线诊断，不称优胜。
- `G_NO_MOTION`：无 escape、无 violation 下降、无 syndrome → 停止 binary edge-level / GF32 小参微调，后继限定为 grouped-symbol mask BP tiny exhaustive 或同块表示消融（按任务书）。

禁止 FER、SKR、信息极限、LDPC 无效、图结构因果、GF32 优胜或跨 session 推广断言。successor/文献/历史边界按任务书（D2T4-3 延续：PEG `10.1109/TIT.2004.839541`、layered `10.1109/SIPS.2004.1363033`、spatial coupling `arXiv:1001.1826`、HD-QKD NB-LDPC `arXiv:2305.08631`，以及 V54 `43/45`、V64 `22/24`、V5-C2 `384/384` 限定域，V67–V72P1 不写成真实纠错成功）。

完整数学、计量、测试和 schema 见同目录 `design.md`、`tasks.md`、`specs/spec.md`。

## R2 真实输入适配（prepare-only，additive，不改冻结语义）

- R1 fail-closed（`registry/frames/matrices=None`，exit2）之后，R2 仅增加 prepare-only 链：
  registry JSON -> parquet 受限 4 列读 -> CAL/VAL 校验 -> prior 拟合 -> block 组装 ->
  D1 A 标量复用 -> words 方向检查 -> matrix/syndrome 形状校验 -> workspace `READY`。
- R2 不运行 decoder（`decoder_calls=0`），不发布 syndrome/tag（`published_bits=0`），
  不创建正式输出根四文件，不创建 `run_01`，不消耗执行授权，不授予 decoder 执行。
- Registry 无 checksum/hash/tag（多余键忽略）；parquet 仅 4 列，数据行不落盘；
  summary 仅标量（`PREP_ONLY_SUMMARY.json`），禁 Alice/Bob 数组与 prior/syndrome/matrix 值。
- 预算 prep300/G300/invocation600/RSS2GiB，超限 `BLOCKED` 保留计数。实现仍精确三文件。
- 证据：`docs/research_cycles/V72P2D3-GF32/PREP_ONLY_SUMMARY.json`、
  `CORRIGENDUM_R2_REAL_INPUT_ADAPTER.md`、`R2_IMPLEMENTATION_REVIEW.md`、
  `cycle_state.yaml`（`PREP_READY`，`real_execution_authorized=false`）。

## R5 数学接口与码率审计修订（当前路线）

R4 已关闭为 `BLOCKED_FINAL_WRITE_MISMATCH`：入口曾放行，但 terminal writer 仍以
`synthetic-only` 规则拒绝正式根；命令返回 `exit=2`，未读取本轮真实数据，未进入
GF32 kernel，`decoder_attempts=0`、披露 `0`、正式输出 `0`，Pre-RESULT 为
`FAIL/BLOCKED`。该事实由现有 `OPERATOR_RETURN_R4.md` 保留；不重试、不把它写成
算法结果。terminal writer 是后续工程 blocker，延后到数学/码率审计之后处理。

在重新开放任何 D3 真实执行以前，必须先闭合以下三个科学 blocker：

1. **Prior 轴方向**：当前审查发现 CAL 统计按 `counts[Bob,Alice]` 填充，而 V54
   消费方按 `counts[Alice,Bob]` reshape/解释，生产 prior 因而可能发生转置。R5
   冻结唯一约定 `counts[a,b] = count(Alice=a, Bob=b)`，并用刻意不对称、可手算的
   联合分布同时验证 `P(U1|B)` 与 `P(U2|U1,B)`；转置输入必须被反例捕获。
2. **H1 输入**：当前真实 CLI 组装路径发现使用了 `zeros((16,1024))` 的风险，不能
   作为历史方法的 H1。R5 必须恢复 V31/V54 的 QC-cyclic-projective rank-16 H1，
   验证非零、每行非零、GF(32) 元素范围 `0..31`、GF(32) rank `16`，并验证 CLI
   实际传入的矩阵来自该 builder；全零 H1 必须拒绝。
3. **码率匹配**：旧 GF32 预算为 H1 `16*5=80` bit、L2 最多 `200*5=1000`
   bit、总 `1080` bit，即 `1.0546875 bit/symbol`（`N=1024`）。当前数据域必须
   用与生产完全相同的 prior 链做 CAL-only 4-fold CV，分别审计
   `CE_L1`、`CE_L2_oracle`、`CE_joint` 及其预算 margin。模型 CE 不是信息论下界；
   只能标记 `MODEL_BUDGET_MISMATCH`，禁止写成 information limit、GF32 failed
   或 LDPC impossible。若 L1 不足，不能只增加 L2 冗余。

R5 只允许文档/计划和 CAL-only 审计状态：不读 VAL、不运行 decoder、不创建正式
输出、不修 writer、不授权。NB-LDPC 主线保留，但 D3 真实执行和通用化暂停。顺序
冻结为：数学接口修复 -> CAL-only 码率匹配 -> 匹配合成信道 -> 一个预注册真实诊断
-> 有真实信号后再做跨 session/扩维。目标是识别数据适用性并匹配参数，不保证任意
数据都能高效纠错。

未来扩维仍是 backlog：先以 `d=256,[4,4]`、`N=1024` 验证，再考虑
`d=512,[5,4]`；三层以上 APP 相关性必须另立数学合同并用微型枚举验证，不能直接
重复套用两层 `q@P`。

R5 的详细任务、停止条件和验收矩阵见 `design.md`、`tasks.md`、`specs/spec.md`
以及 `docs/research_cycles/V72P2D3-GF32/R5_MATH_INTERFACE_AND_RATE_AUDIT.md`。
