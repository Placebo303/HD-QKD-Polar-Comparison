# OpenSpec Proposal: formal-ir-v50-l2-structure-factorial

**Status**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED` — **只规划，不实现，不执行，不启动 V51。等待独立评审。**
**Domain**: Formal IR / L2 structure × prior factorial (protograph/MET vs Lane C)
**Change ID**: `formal-ir-v50-l2-structure-factorial`
**Cycle ID**: `V50P0`
**Predecessor**: `formal-ir-v48-heldout-confirm` (result SHA `28228b9d4bf158361d247aac89c1864e1b5ca9b0`) + diagnostic `c38652de9e4bca3daccbf0f9c96d7897d9199b89`, branch `formal-ir-mainline` HEAD `c38652de`
**Lifecycle**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`, `implementation_started=false`, `production_outputs_created=false`, `formal_execution_authorized=false`

> ponytail lite: 本轮仅 decoder-free 结构 spike + 单候选等泄漏 protograph/MET 与 2×2 因子计划；更懒路径是零新增矩阵直接复用 Lane C，需独立评审确认结构重构价值是否值得 90-call 预算。

## Goal

在**完全冻结 `n=1024, m2∈{184,190,192}, GF32 poly37, 无零列, 满行秩, degree-2 链/环受限, 确定性 lifting/label, 禁止 seed 搜索, 与 Lane C 相同 decoder `90/1.0`, 行度上限与边数预算冻结, 构造规则不接触 V48 outcomes, 零 formal output** 的前提下：

1. **构造唯一等泄漏 protograph/MET L2 候选 `P0-MET-1`**（主方向），与当前 Lane C 保持相同 `m2` 与泄漏 `1064/1094/1104`，显式限制 degree-2 长链/闭环，优先消除 4-cycles 并报告 6/8-cycles。
2. **规划后续 15 个未使用 held-out blocks 的 2×2 因子实验**：每块 `2×L1 +4×L2 =6` calls，共 `90` calls；因子为 **结构(Lane C vs P0-MET-1)** × **先验(TRAIN vs TRAIN+VAL)**；主效应为结构 `C−A` 与先验 `B−A`。

本轮**只产出 spike 报告 + 四 OpenSpec 工件**，状态 `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`；**不得运行 decoder、不得创建正式 output、不得启动 V51**。

## Non-Goals

- 不运行任何 decoder（结构 spike 为 decoder-free 只读校验）；不创建 `comparison_bench/outputs_comparison/formal_ir_methods/v50_*` 正式输出；不启动 V51。
- 不调泄漏、不调 `max_iter/damping`、不引入第二 protograph/MET 候选、不做 seed 搜索或阈值调优。
- 不以 V48 outcomes 选择结构或阈值；不将 V48 held-out 块复用于 V50 评估（15 块为未使用 held-out 块）。
- 不做 FER/阈值/SKR/安全/资格/晋升陈述；不做信息论 `2^-64` 安全界宣称（tag 仍 L2-only 工程近似）。
- 不改写/覆盖 V38–V48 任何已有输出与终态（只读）；不修改 `AGENT_PROJECT_MEMORY.md` / `docs/decision-log.md`（本规划轮禁改）。

## Scope

1. **唯一等泄漏结构候选** `P0-MET-1`：`n=1024, m2=184/190/192` 按源、`GF32 poly37`、`无零列`、`满行秩`、`degree-2 链≤4 / degree-2 纯环(≤12)==0`、`确定性 lifting/label`、`禁止 seed 搜索`；与 Lane C 相同 decoder `90/1.0` 与相同泄漏口径 `leak_total=5*m2+5*16+64`；`4-cycles==0` 硬门、`6/8-cycles` 报告；行度上限 `16` 与边数预算 `E=2048` 冻结。
2. **先验正交对照**：`TRAIN prior`（V25 `channel_counts.npz` 经 `load_v25_channel_counts()`）vs `TRAIN+VAL prior`（`TRAIN⊕VAL` 合并 counts，经同一 loader 接口隔离构造）；先验仅影响 `L1 APP q_i` 与 `P_i(U2)`，不改矩阵/泄漏/decoder。
3. **15 未使用 held-out blocks**（每源 5，均分，连续 deterministic IDs，与 `FORBIDDEN 141 = 96(V36..V47)+45(V48)` 零重叠、无内部重复），每块 `2×L1 (TRAIN vs TRAIN+VAL) +4×L2 (2 structures×2 priors) =6` → 总 `90` calls (`L1 30 + L2 60`)。Block 由 held-out 区间 `60/20/20` hold 帧的 4-frame 窗口派生，`256 pairs/frame, 1024/block`，`sample_empirical_block` 语义但 IDs 为未使用新区。
4. **2×2 因子主效应**：以 `exact_full = exact_u1 && exact_l2` oracle 为主判据，配对结构主效应 `C(TRAIN,P0)−A(TRAIN,LaneC)` 与先验主效应 `B(TRAIN+VAL,LaneC)−A(TRAIN,LaneC)`，交互 `D−C − (B−A)`；同时报告 `exact_u1/exact_l2/exact_full`、四类 `exact/detected/decoder_non_syndrome/undetected`、迭代/运行时、`APP entropy/||q-p||1`。
5. **Lifecycle 冻结**：`PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`，`implementation_started=false`，`production_outputs_created=false`；任何实现/执行需独立 plan ACCEPT + 显式 `EXECUTE_AUTH` 绑定到精确实现 SHA；不启动 V51。

## Impact Scope

- **新增（本轮）**：`openspec/changes/formal-ir-v50-l2-structure-factorial/` 四工件（`proposal.md, design.md, tasks.md, specs/.../spec.md`）+ `spike_report.md`（decoder-free 结构 spike）。
- **未来实现（本轮不创建）**：`comparison_bench/src/comparison_bench/formal_ir/v50_l2_structure_factorial.py`（仅组合 P0-MET-1 确定性矩阵 + Lane C 复用 + 双 prior loader + 90-call 2×2 runner，不新增 decoder）+ `scripts/execute_v50_structure_factorial.py`；均直接 import `v38_architecture_triage` (Lane C 常量) 与 `v35_algorithm_development::compute_tag_64` (L2-only tag)。
- **只读依赖**：`v38_architecture_triage.py` (Lane C `SOURCE_CHECKS/LANE_C_*` 常量)、`v35_algorithm_development.py` (tag 源)、`nonbinary_v31.py` (H1 物料 `16×1024` 若需 L1)、`load_v25_channel_counts()` (TRAIN) 与 `TRAIN+VAL` 合并 counts 构造、held-out frame 池（1683 frames / 430k 结构 P0 仅作块可达校验，不读 V48 outcomes）。
- **不修改**：任何既有 spec/代码/测试/输出、V46–V48 输出、`AGENT_PROJECT_MEMORY.md`、`docs/decision-log.md` 以外；不 import `v39..v48` 模块作生产解码（仅模式拷贝）。

## Acceptance Criteria

- [ ] 四工件 + spike 报告齐全一致且 lifecycle 为 `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`，HEAD 绑定 `c38652de9e4bca3daccbf0f9c96d7897d9199b89`，明确“不实现不执行不启动 V51，等待独立评审”。
- [ ] 单一等泄漏 protograph/MET 候选 `P0-MET-1` 冻结：`n=1024, m2=184/190/192` 按源、`GF32 poly37`、`无零列`、`满行秩`、`degree-2 链≤4 / 纯环(≤12)==0`、`确定性 lifting/label`、`禁止 seed 搜索`；与 Lane C 相同 `m2` 与泄漏 `1064/1094/1104`，行度上限 `16` 与边数预算 `E=2048` 冻结，`4-cycles==0` 硬门、`6/8-cycles` 报告，构造规则不接触 V48 outcomes。
- [ ] Spike 可构造性已判定（decoder-free 结构校验：shape/rank/零列/行度/边数/4-cycle/链环），报告参数完整，无 decoder 调用，无正式 output。
- [ ] 15 未使用 held-out blocks 冻结：与 `FORBIDDEN 141` 零重叠、无内部重复、每源均分 5、连续 IDs，确定性窗口可达，采样模式与 frame_ids 可机械校验；每块 `2×L1+4×L2=6` → 总 `90` calls (`L1 30 / L2 60`) 的 2×2 因子 workload 冻结。
- [ ] 2×2 因子与主效应定义冻结：`A=TRAIN×LaneC, B=TRAIN+VAL×LaneC, C=TRAIN×P0, D=TRAIN+VAL×P0`，结构主效应 `C−A`、先验主效应 `B−A`、交互 `D−C−(B−A)`，以 `exact_full` 为主判据，同时报告 `exact_u1/exact_l2` 与四类/G3'。
- [ ] 禁止清单冻结：禁止 seed 搜索、禁止第二候选、禁止调参/调泄漏/调 decoder、禁止用 V48 outcomes 选结构、禁止创建正式 output、禁止启动 V51。

## Tasks

见 `tasks.md`（Phase A 冻结单候选等泄漏 protograph/MET 与 15 块未使用 held-out 与 90-call 2×2 结构；Phase B 仅 fake-runner 聚焦测试含 90-call 帽与门禁与链环与 4-cycle；Phase C decoder-free preflight 含秩/零列/4-cycle/链环；Phase D 需 EXECUTE_AUTH 的恰好 90 calls 2×2 factorial；Phase E 结果复核；显式禁止清单含“禁止 seed 搜索、禁止 V48 outcome 接触、禁止正式 output、禁止 V51”）。

## Lifecycle

V48 前代 result `28228b9d4bf158361d247aac89c1864e1b5ca9b0` + 诊断 `c38652de`，分支 `formal-ir-mainline`；V50 当前 `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`，修订后仍保持不实现不执行、等待独立 plan 评审；实现候选止于 `IMPLEMENTATION_CANDIDATE / EXECUTE_NOT_AUTHORIZED`；任何执行需显式用户 `EXECUTE_AUTH` 绑定到精确实现 SHA；不启动 V51。
