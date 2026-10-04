# OpenSpec Proposal: formal-ir-v51-lane-c-label-nbace

**Status**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED` — **只规划，不实现，不执行。等待独立评审。**
**Domain**: Formal IR / Lane C label-only optimization (degenerate-cycle spectrum)
**Change ID**: `formal-ir-v51-lane-c-label-nbace`
**Cycle ID**: `V51P0`
**Predecessor**: `formal-ir-v50-l2-structure-factorial` (result `V50_FACTORIAL_COMPLETE` E_structure=-6, E_prior=0, HEAD `e3e14c9518bf44d03054e720a6230ea11d08f99a`, branch `formal-ir-mainline`)
**Plan commit**: resolved externally by independent PLAN_ACCEPT record; implementation SHALL bind the accepted full SHA. — **EXECUTE_NOT_AUTHORIZED**
**Lifecycle**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`, `implementation_started=false`, `production_outputs_created=false`, `formal_execution_authorized=false`

> ponytail lite: 本轮仅 decoder-free 的确定性标签优化 spike + 单条件 45-call 配对计划；更懒路径是零新增执行直接复用 Lane C 原标签，需独立评审确认标签重标价值是否值得 45-call 预算。

## Goal

在**完全冻结 `n=1024, m2∈{184,190,192}, GF32 poly37, Lane C support/位置置换/m2/decoder=90/1.0` 全部冻结、仅优化 GF32 边标签**的前提下：

1. **对 V50 三源 Lane C ordinal-2 support**（`lane_c_1M_s383102 / lane_c_1p5M_s383202 / lane_c_2M_s383302`）各执行**一次确定性标签优化**（主目标为真实可重算的词典序 `(degenerate_4 ↓, degenerate_6 ↓, degenerate_8 ↓, label)` 优先消除 4-环；自定义 `check_extrinsic_score(C)=ACE(C)-100 若退化 else ACE(C)` 仅作次级报告量，不得声称为文献标准 NB-ACE；只运行一次确定性优化，不根据译码结果搜索 seed）。
2. **decoder-free 输出原标签 vs 新标签**的：`support_exact_equal`, `rank`, `4/6/8 支撑环数量不变`, `degenerate_4/6/8 数量`, `generalized_girth`, `nondegenerate_fraction` 等可验证量；自定义 `check_extrinsic_score` 谱（`min_check_extrinsic6/8`, `min_deg_ace6/8`）仅作次级报告。三源均不得按词典序恶化且至少一源严格改善，才具备进入实验资格。
3. 条件实验：**15 个新 held-out blocks**（每块共享一次 L1，Lane C 原标签一次 L2，Lane C 新标签一次 L2，总计 `15×3=45` calls），**主判 paired `exact_full`，同时报告 discordance、残留误码、runtime；不再加入 TRAIN+VAL 臂**。
4. **若标签优化无法满足准入（存在源恶化或无源改善），则不进入实验，直接报告 blocker**（`V51_LABEL_NO_IMPROVEMENT`）。

本轮**只产出 spike 报告 + 四 OpenSpec 工件**，状态 `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`；**不得运行 decoder、不得创建正式 output、不得启动 V52**。

## Non-Goals

- 不改 support/置换/行列度/`m2`/泄漏/`max_iter/damping`；不引入第二标签候选或多候选对比；不做 seed 搜索或阈值调优。
- 不以译码结果回搜 seed/重标；标签优化为 decoder-free 一次确定性过程。
- 不做 TRAIN+VAL 先验臂、H1 压缩、FER/阈值/SKR/安全/资格/晋升陈述；tag 仍 L2-only 工程近似。
- 不改写/覆盖 V38–V50 任何已有输出与终态（只读）；不修改 `AGENT_PROJECT_MEMORY.md` / `docs/decision-log.md`（本规划轮禁改）。
- 不创建 `comparison_bench/outputs_comparison/formal_ir_methods/v51_*` 正式输出。
- 不声称自定义 `check_extrinsic_score` 为文献标准 NB-ACE；文献 NB-ACE 声称在本变更中删除。

## Scope

1. **冻结基座**：`n=1024, m2=184(1M)/190(1p5M)/192(2M), GF32 poly37, 无零列, 满行秩, degree-2 正则, 泄漏 1064/1094/1104, decoder 90/1.0 early-stop`；三源 Lane C support 与位置置换（`position_permutations`）与 `SOURCE_CHECKS` 精确冻结，仅边标签 `1..31` 可变。
2. **确定性标签优化器**：输入为各源二值 support，二值支撑 4/6/8 环枚举（`enumerate_canonical_simple_cycles`）+ 代数退化分类（`classify_cycle_algebraic_degeneracy`）+ 行度基 ACE（`ACE(c)=Σ_{check∈cycle}(row_deg-2)`）→ 自定义 `check_extrinsic_score(C)=ACE-100 若 is_deg else ACE`（仅次级报告，非文献 NB-ACE）；主优化目标为可重算词典序 `(degenerate_4, degenerate_6, degenerate_8, cand)` 越小越好，优先消除 4-环（1M 2个deg4、2M 1个需优先处理），次级报告 `check_extrinsic_score` 不参与主词典序；按 canonical 边序 greedy 扫描 `1..31`，至多 2 sweeps，零随机回搜；实现上复用 `edge_to_cycle_ids` 仅重算包含该边的环、维护全局 `deg4/6/8` 增量，不为每个候选复制完整 `is_deg` 数组；support/秩/`4/6/8` 数量不变由构造保证。
3. **decoder-free 谱对比**：每源输出 `support_exact_equal (=True), rank==m2, support_cycles_4/6/8 不变, degenerate_4/6/8, generalized_girth (=min degenerate length), nondeg_frac6/8` 原 vs 新并列（可验证主量）；`min_check_extrinsic6/8, min_deg_ace6/8` 作为自定义次级报告量并列，不得标注为文献 NB-ACE。
4. **条件准入（三源一致性）**：三源均不得按词典序 `(deg4,deg6,deg8,cand)` 恶化（新 ≤ 旧）且至少一源严格改善（新 < 旧），否则 `V51_LABEL_NO_IMPROVEMENT` blocker，不建 45-call 实验。原“至少一源改善即准入”会允许另两源恶化，已废止。
5. **条件实验（仅当准入通过且获 EXECUTE_AUTH）**：15 个新未使用 held-out blocks（每源 5，连续 deterministic IDs `392001..392005 / 392101..392105 / 392201..392205` 与 `FORBIDDEN 156 = 141(V36..V50)+15(V50 391xxx)` 零重叠 per source 且与 V48/V50 180+60 帧 `frame_ids` 零重叠），每块确定性 4 帧 `frame_ids/ordinal` 冻结（见 design §3），每块 `1×L1 shared +2×L2 (old vs new)=3` → 总 `45` calls (`L1 15 + L2 30`)，同块同 `bob` 同 prior（TRAIN only），仅标签不同；主判 paired `exact_full`，报告 discordance/residual/runtime。

## Impact Scope

- **新增（本轮）**：`openspec/changes/formal-ir-v51-lane-c-label-nbace/` 四工件（`proposal.md, design.md, tasks.md, specs/.../spec.md`）+ `spike_label_nbace.py` + `spike_report.md`（decoder-free 支撑冻结与标签优化 spike）。
- **未来实现（本轮不创建）**：`comparison_bench/src/comparison_bench/formal_ir/v51_lane_c_label_nbace.py`（仅组合 Lane C 重建 + 确定性标签重标 + 45-call paired runner，不新增 decoder）+ `scripts/execute_v51_label_nbace.py`；均直接 import `v38_architecture_triage` (Lane C) 与 `v35_algorithm_development::compute_tag_64`。
- **只读依赖**：`v38_architecture_triage.py` (Lane C 常量/枚举器)、`v35_algorithm_development.py` (tag/Field)、V25 `channel_counts.npz` TRAIN、`split_manifest` hold 区间。
- **不修改**：任何既有 spec/代码/测试/输出、V48–V50 输出、内存文档以外。

## Acceptance Criteria

- [ ] 四工件 + spike 脚本/报告齐全一致且 lifecycle 为 `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`，明确“不实现不执行，等待独立评审；若谱无改善或存在恶化则 blocker 不实验”；四工件中已删除 NB-ACE 文献声称，`check_extrinsic_score` 明确标注为自定义量。
- [ ] 三源 Lane C support/置换/`m2=184/190/192`/`90/1.0` 冻结不可调，仅标签可变可校验。
- [ ] 确定性标签优化器冻结：主目标词典序 `(deg4 ↓, deg6 ↓, deg8 ↓, cand)` 优先 4-环再 6/8-环，自定义 `check_extrinsic_score` 仅次级报告；一次确定性运行、禁止根据译码结果搜 seed；实现复用 `edge_to_cycle_ids` 增量维护全局 `deg4/6/8`；decoder-free 谱对比字段冻结（support_equal/rank/4/6/8 不变/deg 4/6/8/girth/nondeg_frac 为主，自定义 score 为次级）。
- [ ] Spike 可行性已实证（decoder-free 三支撑重建 + 三标签重标，报告 rank/support/cycles/deg/custom_score/girth 原 vs 新；准入为三源均不恶化且至少一源词典序严格改善，否则 verdict 为 `BLOCKER`）。
- [ ] 15 新 held-out blocks 冻结（与 `FORBIDDEN 156` 零重叠、无内部重复、每源均分 5、连续 IDs `392001..` 且每块写死 `4` 真实 `frame_ids` 与 `ordinal start/end`，与 V48/V50 `frame_ids` 零重叠可机械校验）；每块 `1×L1+2×L2=3` → 总 `45` calls 条件 workload 冻结；无 TRAIN+VAL 臂。
- [ ] 禁止清单冻结：禁止改 support/置换/m2/decoder、禁止第二候选、禁止译码驱动的 seed 搜索、禁止创建正式 output、禁止声称自定义量为文献 NB-ACE。

## Tasks

见 `tasks.md`（Phase A 冻结支撑/泄漏/decoder 与单次确定性标签优化器；Phase B 仅 fake-runner 聚焦测试；Phase C decoder-free preflight；Phase D 需 EXECUTE_AUTH 的至多 45 calls paired；Phase E 结果复核；显式禁止清单）。

## Lifecycle

V50 前代 `V50_FACTORIAL_COMPLETE` (E_structure=-6, E_prior=0)，分支 `formal-ir-mainline`, Plan commit: resolved externally by independent PLAN_ACCEPT record; implementation SHALL bind the accepted full SHA.；V51 当前 `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`，`implementation_started=false`，`production_outputs_created=false`；任何执行需独立 plan ACCEPT + 显式 `EXECUTE_AUTH` 绑定到精确未来实现 SHA；谱不满足三源一致性准入时终态 `V51_LABEL_NO_IMPROVEMENT`，否则条件实验终态 `V51_PAIRED_COMPLETE / V51_EVIDENCE_INVALID`。
