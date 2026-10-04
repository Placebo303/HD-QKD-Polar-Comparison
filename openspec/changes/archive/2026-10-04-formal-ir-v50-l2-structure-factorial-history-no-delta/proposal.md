# OpenSpec Proposal: formal-ir-v50-l2-structure-factorial

**Status**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED` — **只规划，不实现，不执行，不启动 V51。等待独立评审。**
**Domain**: Formal IR / L2 structure × prior factorial (protograph/MET vs Lane C)
**Change ID**: `formal-ir-v50-l2-structure-factorial`
**Cycle ID**: `V50P0`
**Predecessor**: `formal-ir-v48-heldout-confirm` (result SHA `28228b9d4bf158361d247aac89c1864e1b5ca9b0`) + diagnostic `f58955f3e794dbde11b4d813eec061182319846d` (deprecated), branch `formal-ir-mainline` plan HEAD `d95d46ac559ac9e5860ebcc793abc0500ba9b09b` (future implementation SHA to be bound at EXECUTE_AUTH)
**Lifecycle**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`, `implementation_started=false`, `production_outputs_created=false`, `formal_execution_authorized=false`

> ponytail lite: 本轮仅 decoder-free 结构 spike + 单候选等泄漏 protograph/MET 与 2×2 因子计划；更懒路径是零新增矩阵直接复用 Lane C，需独立评审确认结构重构价值是否值得 90-call 预算。

## Goal

在**完全冻结 `n=1024, m2∈{184,190,192}, GF32 poly37, 无零列, 满行秩, degree-2 链/环受限, 确定性 lifting/label, 禁止 seed 搜索, 与 Lane C 相同 decoder `90/1.0`, 行度上限冻结、同 `m2` 等泄漏（泄漏仅由 `m2` 决定，不冻结边数 `E`）, 构造规则不接触 V48 outcomes, 零 formal output** 的前提下：

1. **构造唯一等泄漏 protograph/MET L2 候选 `P0-MET-1` = 真 MET 混合度 `{dv2:512,dv3:512}, E=2560, dv_mean=2.5`**（主方向；1024 全 `dv=2` 非 MET，若坚持全 `dv=2` 则改名 `PEG-dv2`），与当前 Lane C 保持相同 `m2` 与泄漏 `1064/1094/1104`（`leak=5*m2+80+64` 与 `E` 无关），显式限制 degree-2 长链/闭环，优先消除 4-cycles 并报告 6/8-cycles。
2. **规划后续 15 个未使用 held-out blocks 的 2×2 因子实验**：每块 `2×L1 +4×L2 =6` calls，共 `90` calls；因子为 **结构(Lane C vs P0-MET-1)** × **先验(TRAIN vs TRAIN+VAL)**；冻结主效应 `E_structure=(C+D-A-B)/2`, `E_prior=(B+D-A-C)/2`, `E_interaction=(D-C)-(B-A)`，并保留四个 simple effects `C-A(TRAIN下结构) / D-B(TRAIN+VAL下结构) / B-A(LaneC下先验) / D-C(P0下先验)`。

本轮**只产出 spike 报告 + 四 OpenSpec 工件**，状态 `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`；**不得运行 decoder、不得创建正式 output、不得启动 V51**。

## Non-Goals

- 不运行任何 decoder（结构 spike 为 decoder-free 只读校验）；不创建 `comparison_bench/outputs_comparison/formal_ir_methods/v50_*` 正式输出；不启动 V51。
- 不调泄漏、不调 `max_iter/damping`、不引入第二 protograph/MET 候选、不做 seed 搜索或阈值调优。
- 不以 V48 outcomes 选择结构或阈值；不将 V48 held-out 块复用于 V50 评估（15 块为未使用 held-out 块）。
- 不做 FER/阈值/SKR/安全/资格/晋升陈述；不做信息论 `2^-64` 安全界宣称（tag 仍 L2-only 工程近似）。
- 不改写/覆盖 V38–V48 任何已有输出与终态（只读）；不修改 `AGENT_PROJECT_MEMORY.md` / `docs/decision-log.md`（本规划轮禁改）。

## Scope

1. **唯一等泄漏结构候选** `P0-MET-1`：`n=1024, m2=184/190/192` 按源、`GF32 poly37`、`无零列`、`满行秩`、真 MET 混合度 `{dv2:512,dv3:512}, E=2560, dv_mean=2.5`（`E` 不冻结泄漏；若坚持全 `dv2` 则为 `PEG-dv2 E=2048` 并改名）、`degree-2 链≤4 / 纯 degree-2 环(≤12)==0`（精确定义见 design §2.2：仅 `dv=2` 变量诱导子图 `G2` 内，链为内部校验度 2 的极大路径，环为全 `dv=2` 且双分长度 `≤12` 的闭环）、`确定性 lifting/label`、`禁止 seed 搜索`；与 Lane C 相同 decoder `90/1.0` 与相同泄漏口径 `leak_total=5*m2+5*16+64`；`4-cycles==0` 硬门、`6/8-cycles` 报告；行度上限 `16` 冻结。
2. **先验正交对照**：`TRAIN prior`（V25 `channel_counts.npz` 经 `load_v25_channel_counts()`）vs `TRAIN+VAL prior`（`TRAIN⊕VAL` 合并 counts，经同一 loader 接口隔离构造）；先验仅影响 `L1 APP q_i` 与 `P_i(U2)`，不改矩阵/泄漏/decoder。
3. **15 未使用 held-out blocks**（每源 5，均分，连续 deterministic IDs `391001..391005 / 391101..391105 / 391201..391205` 与 `FORBIDDEN 141 = 96(V36..V47)+45(V48)` block ID 零重叠、无内部重复，且与 V48 180 帧 `frame_ids` 零重叠 per source；每块写死 `4` 真实 `frame_ids`、`held_out_ordinal_start/end`、`pairs_count=1024`，与 V38–V48 终态帧查重，不仅 `FORBIDDEN` seeds），每块 `2×L1 (TRAIN vs TRAIN+VAL) +4×L2 (2 structures×2 priors) =6` → 总 `90` calls (`L1 30 + L2 60`)。Block 由 held-out 区间 `60/20/20` hold 帧的 4-frame 窗口派生，`256 pairs/frame, 1024/block`，`sampling_mode=deterministic_four_consecutive_frames_heldout_unused`，新窗口与 V48 `HELDOUT_STARTS` 分散窗口零重叠（见 spike_report §8 冻结表）。
4. **2×2 因子效应**：以 `exact_full = exact_u1 && exact_l2` oracle 为主判据，冻结主效应 `E_structure=(C+D-A-B)/2`、`E_prior=(B+D-A-C)/2`、`E_interaction=(D-C)-(B-A)`，并保留四个 simple effects `C-A(TRAIN先验下结构) / D-B(TRAIN+VAL下结构) / B-A(LaneC下先验) / D-C(P0下先验)`；`C-A` 为 simple effect 非主效应；同时报告 `exact_u1/exact_l2/exact_full`、四类 `exact/detected/decoder_non_syndrome/undetected`、迭代/运行时、`APP entropy/||q-p||1`。
5. **Lifecycle 冻结**：`PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`，`implementation_started=false`，`production_outputs_created=false`；任何实现/执行需独立 plan ACCEPT + 显式 `EXECUTE_AUTH` 绑定到精确实现 SHA；不启动 V51。

## Impact Scope

- **新增（本轮）**：`openspec/changes/formal-ir-v50-l2-structure-factorial/` 四工件（`proposal.md, design.md, tasks.md, specs/.../spec.md`）+ `spike_report.md`（decoder-free 结构 spike）。
- **未来实现（本轮不创建）**：`comparison_bench/src/comparison_bench/formal_ir/v50_l2_structure_factorial.py`（仅组合 P0-MET-1 确定性矩阵 + Lane C 复用 + 双 prior loader + 90-call 2×2 runner，不新增 decoder）+ `scripts/execute_v50_structure_factorial.py`；均直接 import `v38_architecture_triage` (Lane C 常量) 与 `v35_algorithm_development::compute_tag_64` (L2-only tag)。
- **只读依赖**：`v38_architecture_triage.py` (Lane C `SOURCE_CHECKS/LANE_C_*` 常量)、`v35_algorithm_development.py` (tag 源)、`nonbinary_v31.py` (H1 物料 `16×1024` 若需 L1)、`load_v25_channel_counts()` (TRAIN) 与 `TRAIN+VAL` 合并 counts 构造、held-out frame 池（1683 frames / 430k 结构 P0 仅作块可达校验，不读 V48 outcomes）。
- **不修改**：任何既有 spec/代码/测试/输出、V46–V48 输出、`AGENT_PROJECT_MEMORY.md`、`docs/decision-log.md` 以外；不 import `v39..v48` 模块作生产解码（仅模式拷贝）。

## Acceptance Criteria

- [ ] 四工件 + spike 报告齐全一致且 lifecycle 为 `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`，plan HEAD 绑定 `d95d46ac559ac9e5860ebcc793abc0500ba9b09b`（旧 `f58955f...` 已清理，正式执行绑定未来 implementation SHA），明确“不实现不执行不启动 V51，等待独立评审”。
- [ ] 单一等泄漏 protograph/MET 候选 `P0-MET-1` 冻结：`n=1024, m2=184/190/192` 按源、`GF32 poly37`、`无零列`、`满行秩`、真 MET `{dv2:512,dv3:512} E=2560`（全 `dv2` 则改名 `PEG-dv2`）、`degree-2 链≤4 / 纯环(≤12)==0`（`G2` 精确定义）、`确定性 lifting/label`、`禁止 seed 搜索`；与 Lane C 相同 `m2` 与泄漏 `1064/1094/1104`（`E` 不决定泄漏），行度上限 `16` 冻结，`4-cycles==0` 硬门、`6/8-cycles` 报告，构造规则不接触 V48 outcomes。
- [ ] Spike 可构造性已实证（decoder-free 三矩阵实际生成，报告 rank/E/度分布/4,6,8-cycle/degree-2 chain/pure ring，无 decoder 调用，无正式 output；失败则换规划，删除未经验证的 `Constructible: YES`）。
- [ ] 15 未使用 held-out blocks 冻结：与 `FORBIDDEN 141` block ID 零重叠、无内部重复、每源均分 5、连续 IDs `391001..` 且每块写死 `4` 真实 `frame_ids` 与 `ordinal start/end`，与 V48 180 帧 `frame_ids` 零重叠 per source 可机械校验；每块 `2×L1+4×L2=6` → 总 `90` calls (`L1 30 / L2 60`) 的 2×2 因子 workload 冻结。
- [ ] 2×2 因子与效应定义冻结：`A=TRAIN×LaneC, B=TRAIN+VAL×LaneC, C=TRAIN×P0, D=TRAIN+VAL×P0`，主效应 `E_structure=(C+D-A-B)/2`、`E_prior=(B+D-A-C)/2`、`E_interaction=(D-C)-(B-A)`，simple effects `C-A(TRAIN下结构) / D-B / B-A / D-C`（`C-A` 非主效应），以 `exact_full` 为主判据，同时报告 `exact_u1/exact_l2` 与四类/G3'。
- [ ] 禁止清单冻结：禁止 seed 搜索、禁止第二候选、禁止调参/调泄漏/调 decoder、禁止用 V48 outcomes 选结构、禁止创建正式 output、禁止启动 V51。

## Tasks

见 `tasks.md`（Phase A 冻结单候选等泄漏 protograph/MET 与 15 块未使用 held-out 与 90-call 2×2 结构；Phase B 仅 fake-runner 聚焦测试含 90-call 帽与门禁与链环与 4-cycle；Phase C decoder-free preflight 含秩/零列/4-cycle/链环；Phase D 需 EXECUTE_AUTH 的恰好 90 calls 2×2 factorial；Phase E 结果复核；显式禁止清单含“禁止 seed 搜索、禁止 V48 outcome 接触、禁止正式 output、禁止 V51”）。

## Lifecycle

V48 前代 result `28228b9d4bf158361d247aac89c1864e1b5ca9b0` + 诊断 `f58955f` (已弃用)，分支 `formal-ir-mainline` plan HEAD `d95d46ac559ac9e5860ebcc793abc0500ba9b09b`；V50 当前 `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`，修订后仍保持不实现不执行、等待独立 plan 评审；实现候选止于 `IMPLEMENTATION_CANDIDATE / EXECUTE_NOT_AUTHORIZED`；任何执行需显式用户 `EXECUTE_AUTH` 绑定到精确未来实现 SHA；不启动 V51。Spike 已修复为确定性 4-cycles 0 + 非零退出 + 唯一 pure-ring 权威定义。
