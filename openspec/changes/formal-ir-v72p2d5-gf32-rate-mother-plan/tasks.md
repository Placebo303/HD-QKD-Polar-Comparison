# D5 任务与验收 R1（PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED）

本轮只完成计划冻结任务（D5-T1..T7，本 turn 内闭环）；D5-T8 待 main thread 独立 Plan Review。
实现任务（apply 阶段）只列名不授权，Review ACCEPT 前不得启动。
计划文件固定为（Review 只审这 5 文件）：
`M_max=1000 is a D5 synthetic construction cap, not a production sufficiency claim.`

1. `openspec/changes/formal-ir-v72p2d5-gf32-rate-mother-plan/proposal.md`
2. `openspec/changes/formal-ir-v72p2d5-gf32-rate-mother-plan/design.md`
3. `openspec/changes/formal-ir-v72p2d5-gf32-rate-mother-plan/tasks.md`
4. `openspec/changes/formal-ir-v72p2d5-gf32-rate-mother-plan/specs/spec.md`
5. `openspec/changes/formal-ir-v72p2d5-gf32-rate-mother-plan/PLAN_FREEZE.md`

## 计划冻结任务（本轮，全部只读/写作档）

- [x] D5-T1 只读 survey 与能力表：已读 AGENTS.md / research-cycle-sop.md /
  D4R2 四工件与 R2 结论（`MODEL_BUDGET_MISMATCH` 描述性失配）/ D3 提案与 R5 修订 / V72P0 提案 /
  V31 `build_layer(m,n=1024,*,family,field,require_full_rank)` 签名（grep 级，不猜测；family 显式传参）。
  验收：`PLAN_FREEZE.md` §1 能力表 11 列逐项填写，覆盖函数/文件·输入·输出·任意 m·nested·rank·
  行列重·n 绑定·700–1000 适配·已有测试·复用风险；自然前缀假设已修正为 M0 两阶段。
- [x] D5-T2 prior 合同冻结 R1：`A=32*U1+U2`，`counts.shape=(Alice,Bob)`，`P_F.shape=(Alice,Bob)`，
  `axis0=Alice, axis1=Bob`，每列 `sum_a P_F[a,b]=1`（`assert_allclose(P_F.sum(axis=0),1.0)`）；
  `P_reshaped=P_F.reshape(32,32,1024)`，`P1=P_reshaped.sum(axis=1)`（`assert_allclose(P1.sum(axis=0),1)`）；
  `P2[u1,b,u2]` 固定 `(u1,b)` 沿 `u2` 和为 1；归一化时机/概率-log 双域/floor 双轨/形状 `(32,1024)/(N,32)`/V54-v35 接口映射 + 唯一 adapter delta（`lambda*`）。
  验收：spec S-PRIOR-01..08 与 design §1 一致；无“axis1 列归一”歧义表述；对齐结论为“对齐+单 delta”。
- [x] D5-T3 行数表冻结 R1：`rows=ceil(N*CE*f/5)`，`f=1.0/1.05/1.1/1.2`（`f=1.3` 仅参照禁入，L1 1016 超 cap），分层独立 ceil 权威，
  旧 216 禁真实，per-layer `M_max=1000` synthetic 构造 cap 冻结。
  验收：与 D4R2（`1467 vs 216 / margin −1251`，`1907 vs 216 / −1691`）bit 级自洽；spec S-BUDGET 全过。
- [x] D5-T4 嵌套 mother 设计冻结 R1：V31 基线 + Lane-C 备份 + 否决清单 + V72P0 四边界；
  M0-STRUCTURE 两阶段（一次构建 1000x1024 候选 → 全 prefix PASS 才进 G0；prefix FAIL 只允许一次预注册 row ordering，仍 FAIL 则 `V31_PREFIX_FAMILY_UNSUITABLE` 返回 planner）；
  13 项 prefix 门禁 + 最低 PASS 五项；row ordering 合同（置换不改行内容，优先级覆盖→rank→连接，确定性 tie-break，不看 decoder，一次排序覆盖各自全 prefix，L1/L2 不同 seed 同算法）；
  最小披露 API、L1-then-L2 顺序。
  验收：spec S-MOTHER-01..09 可验收；一句话定义存在；无自然行序合格假设；不把换 family 写成唯一修复。
- [x] D5-T5 三级门控冻结 R1：G0 tiny（数学，`<1e-12`/`<1e-10`/syndrome 重算/tree 穷举/无噪 100%，失败 BLOCKED）/
  P0 COST-PREFLIGHT（n=64 2 blocks f=1.0+1.2，APP+oracle，wall/iterations/RSS，外推，不计入 G1）/
  G1 n=64（APP-fed 100 paired f={1.0,1.2}，单调+零 crash/nonfinite+结构趋势，无杀权）/
  G2 n=256（APP-fed 200 paired f={1.0,1.1,1.2}，四态分级），
  matched-to-F 生成、真 prior、行数 scaled 表、冻结种子（graph L1 2026090501/L2 2026090502；G0 2026090510..0517；G1 2026090600..0699；G2 2026091000..1199）、
  调用数（G1 APP 100x2+oracle 前 20x2；G2 APP 200x3+oracle 前 40x3，仅诊断）、预算（单 120s/G1 ≤900s/G2 ≤3600s/RSS<2GiB/RESOURCE_PROJECTION_BLOCKED）、
  oracle/APP 诊断合同（9 项同报，删除硬门，G2 PASS 只用 APP-fed）、命名（`exact_failure_fraction`，不称真实 FER）、n=1024 前置条件。
  验收：spec S-SYNTH/S-GATE-01..02/04 与 design §5 一致。
- [x] D5-T6 分级实验冻结 R1：唯一分级实验 = G2（n=256 + 前缀 + f 三点），四态：
  `>=90%@1.2` 且单调 `G2_SYNTHETIC_QUALIFIED` / `50-90% G2_INCONCLUSIVE` / `<50% G2_CURRENT_CONFIGURATION_FAILED` /
  crash-非有限-数学不一致 `IMPLEMENTATION_OR_NUMERICAL_BLOCKED`；单调 raw inequality + Wilson 并报；禁多实验铺开；无论结果不自动进 n=1024。
  验收：spec S-GATE-03 与 design §6 一字一致；无 `GF32_ROUTE_DEAD`/backlog 唯一后继/放弃 GF32 表述。
- [x] D5-T7 四工件 + PLAN_FREEZE 落盘 R1：本 tasks.md + proposal/design/spec/PLAN_FREEZE 一致性自查
  （5 文件交叉引用无矛盾数字；`M_max=1000 is a D5 synthetic construction cap, not a production sufficiency claim.` 四工件统一）；
  `REAL_EXECUTION_AUTHORIZED=false`，`DECODER_EXECUTED=false`，
  `VAL_LOADER_CALLS=0`；生命周期冻结为 `PLAN_ACCEPTED + implementation_authorized:false + synthetic_execution_authorized:false + real_execution_authorized:false`；
  Review PASS 不自动授权实现；停于 `NEXT_GATE: INDEPENDENT_PLAN_REVIEW`。
- [ ] D5-T8 独立 Plan Review（main thread）：审 5 文件 + R1 自查清单逐项（见 PLAN_FREEZE §8）；
  ACCEPT / REVISE / CLOSED 三选一；本 agent 不得执行；PASS 后由后续 operator 统一 commit+push（本轮不 push 不 commit）。

## 实现任务（deferred，Review ACCEPT 前禁止启动，仅列名）

- D5-I1：`lambda*` 平滑 adapter（单函数，V54 下游逐字复用）+ 转置反例测试（含轴合同 assert）。
- D5-I2：V31 `M_max=1000` 双层 mother 构建 + M0 13 项 prefix 验证 + 一次预注册 row ordering（如需）+ `gf_rank` 验证脚本（配预算）。
- D5-I3：matched synthetic 生成器（`B∼P_CAL(B)` + `A∼P_F(·|B)`，冻结种子）+ P0/G0/G1/G2 runner 各一（P0 成本预检先行）。
- D5-I4：P0→G0→G1→G2 按冻结阈值/种子/调用数/预算执行（development only），失败进归因/停止规则，不调阈值不换 seed。
- D5-I5：分阶段授权链（如 G2 QUALIFIED 且 main thread 另批：implementation packet→review→M0/G0 auth→G0 review→P0/G1 auth→G1 review→G2 auth→G2 Pre-RESULT；禁止一次授权 G0/G1/G2）。

## 停止条件（任一即 BLOCKED，不猜测不替代）

counts 轴不唯一、prior 与 decoder 形状失配且无显式 delta、行数表与 D4R2 不自洽、
构造器无任意-m 证据、披露 API 引入框架、synthetic 用替代信道、阈值/种子/门禁被回写、
seed search、f=1.3 synthetic、任何 decoder/VAL/`run_01` 执行、G2 projected 超 3600s 强行启动、
一次授权 G0/G1/G2。
