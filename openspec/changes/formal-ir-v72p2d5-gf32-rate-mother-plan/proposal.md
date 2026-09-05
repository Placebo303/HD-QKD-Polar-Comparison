# D5 计划 R1：F 模型两层 GF32 码率与嵌套母矩阵设计（只冻结计划，不实现）

- Change：`formal-ir-v72p2d5-gf32-rate-mother-plan`
- Predecessor：`formal-ir-v72p2d4-cal-gf32-model-rate-audit`（D4R2，route C，`MODEL_BUDGET_MISMATCH` 描述性预算失配，非失败定论）
- Cycle：`V72P2D5-GF32-RATE-MOTHER`
- Lifecycle：`PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`
- 本 change 只冻结计划：不写生产代码、不运行 decoder、不读 VAL、不创建结果目录、不授予任何执行。
- `base_sha/accepted_plan_sha/implementation_sha` 只承担 AGENTS 要求的 Git 版本绑定，不承担数据或内容校验。本计划不新增任何数据或内容摘要、签名、checksum/hash 字段。
- Ponytail lite：未来实现至多算法脚本 + focused test 各一个；复用 V31/V54 历史链；不用框架、缓存、锁、retry、持久化。不预设优胜路线。
- R1 修订直接在当前分支工作树上改，不单独 push REVISE 中间态，等待独立 Plan Review PASS 后由后续 operator 统一 commit+push。

## 背景（frozen input，不得重新推导）

- 字母表 `d=1024`，分层 `U1/U2=[5,5]`，`GF(32)`，`N=1024`。
- D4R2 选中模型 F（full-symbol hierarchical `P(A|B)`），outer frame-blocked nested CV：
  `CE_L1=3.814742`、`CE_L2_oracle=3.347605`、`CE_joint=7.162347` bit/symbol，
  worst joint `7.178766`，std `0.0158`，range `0.0423`，`lambda*=137.3823795883264`。
- 历史码率 `L1=16 / L2=200 / Total=216` GF32 行在 `f=1.0` 已严重不足（见 design §2 的 bit 对比）；
  禁止继续用旧 216 行做当前域真实实验。
- D4 没有证明信息论极限，只证明 `MODEL_BUDGET_MISMATCH`。

## OQ 决策（R1 冻结）

- OQ1 接受但限定：L1 mother 最大 `1000x1024`、L2 mother 最大 `1000x1024`，仅用于 D5 matched synthetic 探索，覆盖 `f<=1.2` mean-CE 候选。
  `M_max=1000 is a D5 synthetic construction cap, not a production sufficiency claim.`
  明确不代表生产充分 / 传播税覆盖 / worst-fold 或 finite-size margin 充分，不授权 `n=1024` 真实，不允许 `f=1.3`（L1 需 1016 行超 cap）。
- OQ2 不接受 90% 路线死亡线，改为四态（design §6 + spec S-GATE-03）：
  `>=90% G2_SYNTHETIC_QUALIFIED`（允许起草 `n=1024` synthetic 计划，不授权执行）；
  `50-90% G2_INCONCLUSIVE`（保留路线，停止本轮，仅按预注册诊断判断图/APP 传播税/迭代不足，不自动调参）；
  `<50% G2_CURRENT_CONFIGURATION_FAILED`（只否定当前 F prior+mother+decoder+预算组合）；
  crash/非有限/数学不一致 `IMPLEMENTATION_OR_NUMERICAL_BLOCKED`。
  删除 `GF32_ROUTE_DEAD`、“失败后仅 d=256 backlog”、“低于 90% 即放弃 GF32”。

## Goal（回答 6 问，答案位置）

1. F 模型怎样无歧义转成两层 decoder prior？→ design §1 + spec S-PRIOR（轴合同：`counts.shape=(Alice,Bob)`，`P_F.shape=(Alice,Bob)`，`axis0=Alice, axis1=Bob`，每列 `sum_a P_F[a,b]=1`）。
2. L1/L2 各需要多少 GF32 校验行？→ design §2 + spec S-BUDGET（`f=1.0/1.05/1.1/1.2` 行数表；`f=1.3` 仅参照且禁入 synthetic，因 L1 1016 超 cap）。
3. 仓库哪个现有构造器最适合扩展到约 700–1000 行？→ design §3 + `PLAN_FREEZE.md` 能力表（结论：V31 `build_layer(m,n=1024,*,family,field,require_full_rank)` 为基线，family 显式传参不依赖默认；Lane-C 仅备份）。
4. 如何构造嵌套、满秩、稀疏且可增量披露的 GF32 mother？→ design §4 + spec S-MOTHER（M0-STRUCTURE 两阶段 + 13 项 prefix 结构门禁 + row ordering 合同）。
5. 跑 `n=1024` 前怎样用 tiny/`n=64`/`n=256` matched synthetic 排除数学或性能错误？→ design §5 + spec S-SYNTH/S-GATE（含 P0 COST-PREFLIGHT、冻结种子、调用数、预算、oracle/APP 诊断合同、`exact_failure_fraction` 命名）。
6. 哪一个最小 synthetic 实验可给出分级结论？→ design §6（`n=256` 四态分级，非路线死亡杀实验；无论结果不自动进 `n=1024`）。

## Non-Goals

- 不实现任何构造器/decoder/prior 适配代码；不修改 `src/ experiments/ tools/ comparison_bench/src/` 下任何 `.py`。
- 不运行 decoder（未来测试的显式注入 fake 也不在本轮），不读 VAL，不创建正式结果，不授权真实执行（`run_01` / `EXECUTE_AUTH` 禁止）。
- 不做跨 session 推广、扩维（无 VAL 真实扩维）、SKR/信息极限断言、方法定级。
- 不实现后反向修改计划：本轮冻结的阈值（`SELECT` 类常量、`PASS/FAIL` 门限、行数表、种子、门禁）在 apply 阶段不得回写放宽；若实现发现歧义，停下返回 planner/OpenSpec 修订（新 SHA 重审），不猜测绕过。
- 不新增任何防御性/审计/校验框架（无 hash/checksum/tag/签名/锁/retry/缓存）。
- 禁止 seed search（运行后禁换 seed）；禁止 `f=1.3` synthetic；禁止一次授权 G0/G1/G2；Review PASS 不自动授权实现。

## 范围

- 新增/修改文件仅限：本目录 `proposal.md / design.md / tasks.md / specs/spec.md / PLAN_FREEZE.md`（5 文件）。
- 只读引用：`AGENTS.md`、D4R2/D3/V72P0 OpenSpec 与 cycle docs、历史 GF32 构造器与 decoder 接口（grep 级签名确认，不复制大段代码）。
- V72P0 mother（`9036x10240` binary IRA）仅作嵌套/秩证明模式的结构参考；明确记录“禁止直接假设适用于 GF32”的边界（design §3.5）。
- V31 `build_layer(1000,1024)` 任意前缀视为 nested mother 是未验证假设，本计划改为 M0-STRUCTURE 两阶段验证（design §4）。

## Impact Scope

- 修改 `openspec/changes/formal-ir-v72p2d5-gf32-rate-mother-plan/` 下 5 个文档文件（proposal/design/tasks/specs/spec/PLAN_FREEZE）。
- 零生产代码修改，零测试执行，零数据读取，零输出目录创建。

## Acceptance Criteria

- [ ] 四工件 + PLAN_FREEZE 一致：OQ1 synthetic cap 句、`M_max=1000 is a D5 synthetic construction cap, not a production sufficiency claim.` 四工件统一；OQ2 四态无死亡线措辞。
- [ ] 概率轴无歧义：`counts.shape=(Alice,Bob)`，`P_F.shape=(Alice,Bob)`，`axis0=Alice, axis1=Bob`，`assert_allclose(P_F.sum(axis=0),1.0)`；P1/P2 合同与 design §1 一致；无“axis1 列归一”歧义表述。
- [ ] prefix 门全：L1/L2 每个 `k` 13 项报告 + 最低 PASS 五项；natural prefix 非假设；row ordering 不用 decoder；M0 全 PASS 才进 G0。
- [ ] 种子全冻结：graph L1/L2、G0/G1/G2 列表与 design §5 一致；运行后禁换 seed。
- [ ] oracle 非硬门：G1/G2 PASS 只用 APP-fed 端到端 exact；oracle 仅诊断，同时报告 9 项指标。
- [ ] 预算完整：P0 + 单 call 120s + G1 ≤900s + G2 ≤3600s + RSS<2GiB + RESOURCE_PROJECTION_BLOCKED；调用数明确（G1 APP 100x2 + oracle 前 20x2；G2 APP 200x3 + oracle 前 40x3）。
- [ ] 命名：`exact_failure_fraction=1-exact_count/attempted_blocks`，不称真实 FER；G2 单调 raw inequality + Wilson 区间并报。
- [ ] 生命周期：`PLAN_ACCEPTED + implementation_authorized:false + synthetic_execution_authorized:false + real_execution_authorized:false`；Review PASS 不自动授权实现。
- [ ] 独立 Plan Review（main thread）ACCEPT 前不进入 apply；`REAL_EXECUTION_AUTHORIZED=false`，`DECODER_EXECUTED=false`，`VAL_LOADER_CALLS=0`。
