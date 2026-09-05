# D5 任务与验收（PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED）

本轮只完成计划冻结任务（D5-T1..T7，本 turn 内闭环）；D5-T8 待 main thread 独立 Plan Review。
实现任务（apply 阶段）只列名不授权，Review ACCEPT 前不得启动。
计划文件固定为（Review 只审这 5 文件）：

1. `openspec/changes/formal-ir-v72p2d5-gf32-rate-mother-plan/proposal.md`
2. `openspec/changes/formal-ir-v72p2d5-gf32-rate-mother-plan/design.md`
3. `openspec/changes/formal-ir-v72p2d5-gf32-rate-mother-plan/tasks.md`
4. `openspec/changes/formal-ir-v72p2d5-gf32-rate-mother-plan/specs/spec.md`
5. `openspec/changes/formal-ir-v72p2d5-gf32-rate-mother-plan/PLAN_FREEZE.md`

## 计划冻结任务（本轮，全部只读/写作档）

- [x] D5-T1 只读 survey 与能力表：已读 AGENTS.md / AGENT_PROJECT_MEMORY.md / research-cycle-sop.md /
  D4R2 四工件与 RESULT_SUMMARY_R2 / D3 提案与 R5 修订 / V72P0 提案 /
  GF32 field·H1·Lane-C·incremental·FFT-QSPA·prior·CLI/test 签名（grep 级，不猜测）。
  验收：`PLAN_FREEZE.md` §1 能力表 11 列逐项填写，覆盖函数/文件·输入·输出·任意 m·nested·rank·
  行列重·n 绑定·700–1000 适配·已有测试·复用风险。
- [x] D5-T2 prior 合同冻结：`A=32*U1+U2`，`P1=Σ_u2 P_F`，`P2=P_F/P1`，求和轴/归一化时机/
  概率-log 双域/floor 双轨/形状 `(32,1024)/(N,32)`/V54-v35 接口映射五项显式 + 唯一 adapter delta（`lambda*`）。
  验收：spec S-PRIOR-01..08 与 design §1 一致；对齐结论为“对齐+单 delta”。
- [x] D5-T3 行数表冻结：`rows=ceil(N*CE*f/5)`，`f=1.0/1.05/1.1/1.2`（+1.3 参照），分层独立 ceil 权威，
  旧 216 禁真实，per-layer `M_max=1000` 解读冻结。
  验收：与 D4R2（`1467 vs 216 / margin −1251`，`1907 vs 216 / −1691`）bit 级自洽；spec S-BUDGET 全过。
- [x] D5-T4 嵌套 mother 设计冻结：V31-QC 基线 + Lane-C 备份 + 否决清单 + V72P0 四边界；
  nested 前缀语义、稀疏目标、逐前缀 `gf_rank` 验证步骤、最小披露 API、L1-then-L2 顺序。
  验收：spec S-MOTHER-01..06 可验收；一句话定义存在。
- [x] D5-T5 三级门控冻结：G0 tiny（数学）/ G1 n=64（集成趋势）/ G2 n=256（性能+杀权），
  matched-to-F 生成、真 prior、行数 scaled 表、阈值、失败三分法、n=1024 前置条件。
  验收：spec S-SYNTH/S-GATE-01..02/04 与 design §5 一致。
- [x] D5-T6 生死实验冻结：唯一杀实验 = G2（n=256 + 前缀 + f 三点），PASS ≥90%@f=1.2，
  FAIL 双分支（`<50%` / `50–90%`），禁多实验铺开。
  验收：spec S-GATE-03 与 design §6 一字一致。
- [x] D5-T7 四工件 + PLAN_FREEZE 落盘：本 tasks.md + proposal/design/spec/PLAN_FREEZE 一致性自查
  （5 文件交叉引用无矛盾数字）；`REAL_EXECUTION_AUTHORIZED=false`，`DECODER_EXECUTED=false`，
  `VAL_LOADER_CALLS=0`；停于 `NEXT_GATE: INDEPENDENT_PLAN_REVIEW`。
- [ ] D5-T8 独立 Plan Review（main thread）：审 5 文件 + 单点决策 OQ1（per-layer 解读确认）
  与 OQ2（90% 线确认）；ACCEPT / REVISE / CLOSED 三选一；本 agent 不得执行。

## 实现任务（deferred，Review ACCEPT 前禁止启动，仅列名）

- D5-I1：`lambda*` 平滑 adapter（单函数，V54 下游逐字复用）+ 转置反例测试。
- D5-I2：V31-QC `M_max=1000` 双层 mother 构建 + 逐前缀 `gf_rank` 验证脚本（配预算）。
- D5-I3：matched synthetic 生成器（`B∼P_CAL(B)` + `A∼P_F(·|B)`，冻结种子）+ tiny/G1/G2 runner 各一。
- D5-I4：G0/G1/G2 按冻结阈值执行（development only），失败进三分归因，不调阈值。
- D5-I5：Pre-EXECUTE review（如 G2 PASS 且 main thread 授权 n=1024 计划）。

## 停止条件（任一即 BLOCKED，不猜测不替代）

counts 轴不唯一、prior 与 decoder 形状失配且无显式 delta、行数表与 D4R2 不自洽、
构造器无任意-m 证据、披露 API 引入框架、synthetic 用替代信道、阈值被回写、
任何 decoder/VAL/`run_01` 执行。
