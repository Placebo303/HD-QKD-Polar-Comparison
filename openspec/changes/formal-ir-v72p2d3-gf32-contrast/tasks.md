# V72P2D3 任务与验收（基于 D1 映射表冻结）

状态：`PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`。本任务表绑定 base `e094f7e548380db4bfcbc1fe73472e670c32379a` 和分支 `formal-ir-v72p1-addendum-clean`。本轮只审查计划，不实现、不运行 decoder、不读 raw/parquet、不创建结果目录、不改 adapter、memory、cycle_state、`src/`、`experiments/`、`tools/`、`results/`或既有输出。

`base_sha/accepted_plan_sha/implementation_sha` 只承担 Git 版本绑定，不承担数据/artifact 内容校验；不引入数据或 artifact 内容摘要、签名或其他校验字段。Ponytail lite：禁框架，不预设优胜者。

本变更的计划文件固定为：

1. `openspec/changes/formal-ir-v72p2d3-gf32-contrast/proposal.md`
2. `openspec/changes/formal-ir-v72p2d3-gf32-contrast/design.md`
3. `openspec/changes/formal-ir-v72p2d3-gf32-contrast/tasks.md`
4. `openspec/changes/formal-ir-v72p2d3-gf32-contrast/specs/spec.md`
5. `docs/research_cycles/V72P2D3-GF32/PLAN_CANDIDATE.md`

独立 Plan Review 只在这 5 个文件上进行。任一数学合同无法证明则返回 `BLOCKED`，不得用默认值、未冻结文字或缩小测试范围绕过。方向歧义则 `REVISE`。

## D3T0：结构、数值和无副作用

- **D3T0-1**：未来 3 个实现文件可 `py_compile`/import，import 不进入真实 decoder、raw/parquet 或生产输出路径；测试只能显式注入 fake runner。
- **D3T0-2**：断言 A 为 D1 只读复用（9036x10240、nnz49620、72 点 ladder、10/ckpt、720/arm、float64/clip20/tol1e-6）；G 为 GF32（q32 poly37、184/192/200 nested、90 硬帽、damping1.0、无 tolerance）。
- **D3T0-3**：断言二臂为已存 A 与新 G；A 只读，G 一次；禁止混合臂、禁止 VAL 调参、禁止回灌。
- **D3T0-4**：断言映射 `low=bits0..4/high=5..9/bit0 LSB/symbol=low+32*high` 同方向、`+1024 roundtrip` 全值往返一致。
- **D3T0-5**：断言泄漏公式 `5*m+80+64`（1064/1104/1144）与 `tag_bits=0`；V64 verify 仅只读 helper；V64 归因禁定论文字存在。

## D6：15 项 synthetic（冻结清单，R1–R5 修订）

- **D6-1**：GF32 场 `q32 poly37` 创建与乘加逆元 tiny 已知答案；字段统一为 v35（`nonbinary_field` 零命中）。
- **D6-2**：映射 pack/unpack `+1024 roundtrip` 全值一致，LSB 口径。
- **D6-3**：`s=32*u1+u2` 与 `low+32*high` 同方向一致（`u1=high/u2=low`），绑定 v35 `factorize_f03`。
- **D6-4**：H_base184+H1-16 形状/秩/nested 前缀 `184/192/200`（Δ8+8）。
- **D6-5**：prior Stage1 `P(high|B)=P(U1|B)` 归一（finite/positive/sum=1）。
- **D6-6**：prior Stage2 `P(low|high,B)=P(U2|U1,B)` 归一（同上，逐 high 行）；生产 `prior_l2=q@P` 经 V54 精确复用。
- **D6-7**：`K/P/prior_logp` finite，`exp(prior_logp)` 与 P 逐行相等并归一；不测 logp 正号。
- **D6-8**：`joint/low/high CE` log2 链式 `|Δ|<1e-9`，decoder 自然 log 转换显式。
- **D6-9**：builder 只接 Bob+CAL，Alice/旧 session/VAL 选参探针拒绝。
- **D6-10**：G 真核 90 硬帽（第 91 次拒绝）、damping1.0、无 tolerance；`iterations_used 0..max`（`0` 为初值即满足）；`residual=NOT_RECORDED`（真核无 residual）；生产恒 `decode_fn=None` 直调真核；`belief_warm` 仅 `(n,32)` 初值、生产恒 `None`，加 cold 语义测试；禁 argmax 冒充/固定 hard（源码探针）。
- **D6-11**：Arm A syndrome `H@x==s (mod2)` tiny oracle 同方向；G syndrome 经 `syndrome_of_gf32` 历史 oracle（`s1=H1*u1/s_base=H_base*u2/s_joint/s_total`，禁 binary 冒充 GF32）。
- **D6-12**：Arm A violation `weight((H[:r]@hard)%2 XOR target[:r])` 手算一致；G 另有 `gf32_prefix_violation`（GF32 等式）。
- **D6-12b**：短路遵循 V54 顺序：L1 失败仍进 L2（L2 恒用 `q`，不门控）；L2 base 满足跳过 joint/total、joint 满足跳过 total（syndrome-only）；每 stage cold（生产 `belief_warm=None` 计数探针 ≥4）。
- **D6-13**：V64 `compute_tag_64` 只读 import 探针（纯函数，不计泄漏、不进门禁）。
- **D6-14**：candidate-vs-Bob 直接比较（不由等误差数推断相等）；诊断含 `candidate_changed/vs_bob`。
- **D6-15**：四文件 schema 空跑（fake 仅显式注入的 schema 路径，workspace 临时目录，不碰生产根；`history_kernel=V35-...-via-V54-chain`）。

## D7：全双层门禁（≤300s/<2GiB/误差≤15%）

- **D7-1**：synthetic 全双层（low+high，两层增量）在冻结 budget 内完成：`wall ≤ 300s`、`peak_rss < 2GiB`（当前进程 RSS 采样口径：prep/每阶段后/arm 结束，取 max）。
- **D7-2**：数值/先验相对误差 `≤15%`（相对 brute-force 或解析参照，口径在 report 显式；超限即 FAIL）。
- **D7-3**：超限必须 `PLAN_REVISE_REQUIRED`，不得改科学算法偷过；真实 G 超时只记 `RESOURCE_BLOCKED`，不作路线失败。

## D8：三审查核真 kernel（R1–R2 唯一绑定）

- **D8-1**：Plan Review 核映射/方向/H/泄漏文字无歧义，否则 REVISE；核 R1 码字域语义与 R5 顺序/短路文字。
- **D8-2**：Implementation Review 核薄 adapter 调用唯一真核 v35 `decode_row_layered_fftqspa` 经 V54 链（生产恒 `decode_fn=None`；import 探针 + tiny 已知答案含 `iterations==0` 初值满足 + `rg stub/mock` 零命中 + `np.argmax(prior` 零命中 + `nonbinary_field` 零命中 + cold 语义测试 PASS + 泄漏映射 `leak_for_base(184/192/200)=1064/1104/1144`）。
- **D8-3**：Pre-EXECUTE 核 `HEAD==origin/branch==implementation SHA`、`ACCEPTED_PLAN_SHA` 重推导一致且 `rg 旧SHA` 零命中、目标输出目录不存在、`py_compile` + D6/D7 PASS，否则阻塞执行。

## D9：真实执行门禁（VAL1726..1729，G 一次）

- **D9-1**：实现精确只有 3 个文件：`comparison_bench/src/comparison_bench/formal_ir/v72p2d3_gf32_contrast.py`、`scripts/v72p2d3_gf32_contrast.py`、`comparison_bench/tests/test_v72p2d3_gf32_contrast.py`。不改 adapter/config/fixture/src/experiments/tools/results/旧输出。
- **D9-2**：真实输出根固定为 `comparison_bench/outputs_comparison/v72p2d3_gf32_contrast_20260904/`，恰 `manifest/results/table/report` 四文件，不覆盖 D1/D2、不建 `run_01`。
- **D9-3**：G 一次，A 不重跑；准备失败则 G 为 `NOT_ATTEMPTED` 非零返回；G exception/nonfinite/RSS 超限/timeout 则 `BLOCKED` 保留 artifact；普通 `LADDER_EXHAUSTED`/增量耗尽为正常终态。
- **D9-4**：报告 low/high 分层 `rows/iters/syndrome/candidate-vs-Bob/posthoc/total/control/runtime` + total/control 公开计费 + claim boundary；A 新指标 null 附 `not_recorded_reason`。
- **D9-5**：执行前依次通过独立 Plan Review、Implementation Review、Pre-EXECUTE，发布前通过 Pre-RESULT；本计划不授执行权限。

## D10：四分支判别与边界

- **D10-1**：机械执行 `G_EXACT / G_COLLISION / G_IMPROVED_NO_SYNDROME / G_NO_MOTION` 四分支（定义见 proposal），不预设优胜者。
- **D10-2**：`G_EXACT` 仅允许同路线小样本 confirmation plan，不直接进入 V73；其余分支仅描述性；禁止 FER/SKR/信息极限/LDPC 无效/图因果/GF32 优胜/跨 session 断言。
- **D10-3**：计划文本保留 PEG DOI `10.1109/TIT.2004.839541`、layered DOI `10.1109/SIPS.2004.1363033`、spatial coupling `arXiv:1001.1826`、HD-QKD NB-LDPC `arXiv:2305.08631`，以及 V54 `43/45`、V64 `22/24`、V5-C2 `384/384` 限定域；V67–V72P1 不写成真实纠错成功。
- **D10-4**：计划提交前只对 5 个计划文件执行 `git diff --check`、完整 `git status --short`、基线范围审查和 staged manifest 检查；不 add 任何 untracked 历史文件，不运行 decoder。

完成条件：5 个计划文件内容一致、`REAL_EXECUTION_AUTHORIZED=false`、`DECODER_EXECUTED=false`，然后停止于 `NEXT_GATE: INDEPENDENT_PLAN_REVIEW`。

## R2 prepare-only 验收（additive，decoder0）

- **R2-T1**：registry 合同（schema/session/1M/CAL702..1725/VAL1726..1729/禁 1730+/used_2m false/4 列；
  多余 checksum/hash/tag 忽略；缺失/非法为 `PREP_FAILED`）。
- **R2-T2**：parquet 受限 4 列读（CAL1024x256+VAL4x256，pair 有序无 dup/NaN，symbols0..1023；
  `n_read/n_retained` 标量记录，数据行不落盘）。
- **R2-T3**：prepare-only workspace `READY`（prior 拟合 + block 组装 + A 标量复用 + words +
  matrix/syndrome 形状校验；恰一文件 `prepare_summary.json`；`decoder_calls=0`，
  `published_bits=0`，`formal=false`；禁 `run_01` 与生产根；预算 prep300/G300/inv600/RSS2GiB）。
- **R2-T4**：`py_compile` + 47 项 focused 测试 PASS（含 R2-R6 prepare-only 与 R7 fake-E2E），
  `git diff --check` 干净，staged manifest 精确 11 文件（3 代码 + 4 openspec + cycle_state +
  CORRIGENDUM_R2 + PREP_ONLY_SUMMARY + R2_IMPLEMENTATION_REVIEW）。
