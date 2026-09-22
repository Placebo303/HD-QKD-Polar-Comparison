# OpenSpec Proposal: formal-ir-v52-rate-adaptive-l2-rescue

**Status**: `PLAN_REVISE_REQUIRED / EXECUTE_NOT_AUTHORIZED` — **已按阻塞点修订（去重 old 臂、修正泄漏分类），仍不实现不执行 decoder，不创建正式 run_01。等待独立复审。**
**Domain**: Formal IR / Rate-adaptive L2 incremental rescue (nested HARQ)
**Change ID**: `formal-ir-v52-rate-adaptive-l2-rescue`
**Cycle ID**: `V52P0`
**Predecessor**: `6aa33eadc872bb4551f458ee750a94cd24566314` (HEAD `formal-ir-mainline`, 含 V50/V51 规划), branch `formal-ir-mainline`, plan HEAD `6aa33eadc872bb4551f458ee750a94cd24566314`
**Lifecycle**: `PLAN_REVISE_REQUIRED / EXECUTE_NOT_AUTHORIZED`, `implementation_started=false`, `production_outputs_created=false`, `formal_execution_authorized=false`

> ponytail lite: 本轮仅 decoder-free 嵌套矩阵 spike + 单增量 L2 rescue 计划；更懒路径是零新增校验行直接复用 Lane C，需独立评审确认增量冗余价值是否值得增量泄漏与二次译码预算。

## Goal

在**完全冻结第一遍 `H1-16 + L1-APP + 原 Lane C (m2∈{184,190,192}, GF32 poly37, 无零列, 满行秩, L=8 w=2 support/标签/prior/MET 图全部不改, decoder 90/1.0, 泄漏 `leak_base=5*m2+80+64` → 1064/1094/1104, tag L2-only)** 的前提下：

1. **仅对第一遍未通过 `syndrome/tag verification` 的帧**，额外公开一小组独立 L2 校验行 `Δm` (冻结 `Δm=8` per source, `GF32 poly37`, 行度≤16, 与原 Lane C 联合满秩、嵌套) 构成联合矩阵 `H_joint=[H_base; H_inc]` (`m_joint=m2+Δm`) 并**重译码一次第二遍**；已通过帧**不增加泄漏、不重译**。
2. **规划后续 fres h held-out 15 未使用 blocks 的配对实验**：每块 `old Lane C (单遍)` vs `V52 incremental (首遍 + 条件二遍)` 同 `bob`/同 prior/同 H1，在相同 held-out 配对上度量**纠错成功率与平均泄漏的折中**；不重复比较 prior、标签或另一张全新 MET 图。
3. 本轮**只产出 decoder-free 嵌套 spike + 四 OpenSpec 工件**，状态 `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`；**不得运行 decoder、不得创建正式 `.../v52_*/run_01/` 输出、不得评估 FER 全集**。

**报告承诺（shall）**：proposal/design/tasks/specs 显式承诺最终报告 SHALL 包含 — 第一遍成功数；增量校验救回数；最终 `exact_full`；每源表现（1M/1p5M/2M 分源）；平均泄漏与失败帧条件泄漏；增量行满秩、嵌套性及真实 tag acceptance；fresh held-out 配对结果（old Lane C vs V52 incremental paired）。

## Non-Goals

- 不改第一遍的 support/标签/prior/MET 图/`m2`/H1/`max_iter/damping`；不引入第二增量候选或多档率自适应搜索；不做 seed 搜索或阈值调优。
- 不以 V48/V50/V51 outcomes 选择 `Δm` 或增量位置；不将 V50/V51  held-out 块复用于 V52 评估（15 块为未使用 fresh held-out）。
- 不做 broad FER/阈值/SKR/安全/资格/晋升陈述；tag 仍 L2-only `≈2^-64` 工程近似；不做信息论安全界宣称。
- 不改写/覆盖 V38–V51 任何已有输出与终态（只读）；本规划轮不修改 `AGENT_PROJECT_MEMORY.md` / `docs/decision-log.md`。
- 不运行 decoder（spike 为 decoder-free 只读校验）；不创建正式输出；不启动 V53。

## Scope

1. **冻结第一遍**：`n=1024, m2=184(1M)/190(1p5M)/192(2M), GF32 poly37, Lane C ordinal-2 support+label, H1 16×1024 rank16 80b, L1-APP `q_i` via `BP_i`, decoder 90/1.0 early-stop, verification `tag_scope=l2_only compute_tag_64(empty,x2) trunc64, syndrome_ok && tag_ok 判通过`；`leak_base=5*m2+80+64`。
2. **增量 L2 行 `H_inc` (Δm=8)**：每源确定性 `8×1024` `GF32 poly37`，`col_degree_inc ∈{0,1}` (每列至多一新增边)、`row_degree≤16`、无零增量行、与 `H_base` 联合 `rank==m2+Δm`、嵌套 `H_base` 为 `H_joint` 前缀、独立性 `rank(H_inc \ rowspace(H_base))==Δm`；构造确定性、与 V50/V51 资源零重叠、禁止 seed 搜索；`leak_joint=5*(m2+Δm)+80+64 = leak_base+40`，`first_pass_success_leak=leak_base (1064/1094/1104)`，`rescued_success_leak=leak_joint (1104/1134/1144)`，`final_failure_leak=leak_joint`；`avg_leak = leak_base + 40 × N_rescue_attempted /15`（`N_rescue_attempted = N - N_first_pass_success`，含救回与仍失败）。
3. **15 fresh held-out blocks**（每源 5，均分，连续 deterministic IDs `393001..393005 / 393101..393105 / 393201..393205` 与 `FORBIDDEN 171 = 156(V36..V51)+15(V51 392xxx)+?` 零重叠，实际 `FORBIDDEN 171` 含 `96(V36..V47)+45(V48)+15(V50 391xxx)+15(V51 392xxx)=171` 且与 V48/V50/V51 帧 `frame_ids` 零重叠 per source；每块写死 `4` 真实 `frame_ids`、`held_out_ordinal_start/end`、`pairs_count=1024`，与 V38–V51 终态帧查重），每块 `old` 单遍 vs `V52` 首遍+条件二遍，同 `bob` 同 prior。
4. **两遍协议（去重后）**：`base/pass1 = decode(H_base, prior, s_base)`（同一次确定性译码兼作 old Lane C baseline 与 V52 pass1，old 结果确定性复用，不重复译码）→ `verify = syndrome_ok && tag_ok`；若 `verify` 且 `exact` 预留 oracle 统计但以 `tag` 判公开成功，则停 `leak=leak_base (=first_pass_success_leak 1064/1094/1104)`；否则 `pass2/rescue = decode(H_joint, prior, s_joint)` where `s_joint=[s_base; s_inc]`（`s_inc = H_inc * u2_true`），`leak=leak_joint (=rescued_success_leak 1104/1134/1144 若救回 else final_failure_leak)`；`leak = leak_base if verify else leak_joint` 等价 `avg_leak = leak_base + 40 × N_rescue_attempted/15`；每块 `L1 1 + base 1 + rescue ≤1`，总 `15 L1+15 base+≤15 rescue=30–45 硬帽45`（已删除此前 60 L2+15 L1 或每块≤4 L2 表述）；报告 `first_pass_success / rescued_by_increment / final_exact_full`。
5. **Lifecycle 冻结**：`PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`，`implementation_started=false`，任何实现/执行需独立 plan ACCEPT + 显式 `EXECUTE_AUTH` 绑定到精确实现 SHA；不启动 V53。

## Impact Scope

- **新增（本轮）**：`openspec/changes/formal-ir-v52-rate-adaptive-l2-rescue/` 四工件（`proposal.md, design.md, tasks.md, specs/spec.md`）+ `spike_nested_rescue.py` + `spike_report.md`（decoder-free 嵌套 spike）。
- **未来实现（本轮不创建）**：`comparison_bench/src/comparison_bench/formal_ir/v52_rate_adaptive_l2_rescue.py`（仅组合 Lane C 复用 + 确定性 `H_inc 8×1024` + 两遍 runner，不新增 decoder）+ `scripts/execute_v52_nested_rescue.py`；均直接 import `v38_architecture_triage` (Lane C) 与 `v35_algorithm_development::compute_tag_64`。
- **只读依赖**：`v38_architecture_triage.py` (Lane C 常量/构造器)、`v35_algorithm_development.py` (tag/Field)、`nonbinary_v31.py` (H1 `16×1024` 若需)、`load_v25_channel_counts()` (TRAIN prior)、held-out frame 池（1683 frames / 430k pairs 未使用校验）。
- **不修改**：任何既有 spec/代码/测试/输出、V38–V51 输出、`outputs_comparison`/`workspace`/`V50` 目录以外；不 import `v50/v51` 模块作生产解码。

## Acceptance Criteria

- [ ] 四工件 + spike 脚本/报告齐全一致且 lifecycle 为 `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`，plan HEAD 绑定 `6aa33eadc872bb4551f458ee750a94cd24566314`，`implementation_started=false`，明确“不实现不执行不创建 run_01，等待独立评审；严格 decoder-free”。
- [ ] 第一遍冻结可机械校验：`H1-16 rank16`、`m2 184/190/192`、`Lane C support/label/prior/MET` 零改、`decoder 90/1.0`、`leak_base 1064/1094/1104`、`tag L2-only`。
- [ ] 增量矩阵冻结可机械校验：`Δm=8` per source、`H_inc 8×1024 GF32 poly37`、`row_degree≤16`、`col_degree_inc≤1`、`joint rank==m2+Δm`、嵌套 `H_base == H_joint[:m2]`、独立性 `rank_inc_independent==Δm`、`E_inc` 报告；`leak_joint = leak_base+40` 公式冻结；禁止 seed 搜索与第二候选。
- [ ] Spike 可构造性已实证（decoder-free 三源实际生成 `H_base+H_inc` 联合秩/嵌套/独立性/泄漏公式，零 decoder 调用，无正式 output；失败则 `sys.exit(1)` 并标记 `NESTED_NOT_CONSTRUCTIBLE`）。
- [ ] 15 fresh held-out blocks 冻结：与 `FORBIDDEN 171` block ID 零重叠、无内部重复、每源均分 5、连续 IDs `393001..` 且每块写死 `4` 真实 `frame_ids` 与 `ordinal`，与 V48/V50/V51 `frame_ids` 零重叠 per source 可机械校验；`sampling_mode=deterministic_four_consecutive_frames_heldout_fresh`，每块 `1024` pairs。
- [ ] 报告承诺显式 SHALL：`first_pass_success_count / incremental_rescue_count / final_exact_full / per_source (1M/1p5M/2M) / first_pass_success_leak(1064/1094/1104) / rescued_success_leak(1104/1134/1144) / final_failure_leak(leak_joint) / average_leakage(=leak_base+40×N_rescue_attempted/15) / failed_conditional_leakage(leak_joint) / joint_rank+nested+independence / real_tag_acceptance / paired_old_vs_incremental (fresh held-out，去重：old 与 pass1 同一次译码)`；`old Lane C vs V52 incremental` 配对效应冻结为 `Δexact = final_V52 - old` per block 描述性；不得再用 `successful_conditional=leak_base` 单一口径。
- [ ] 禁止清单冻结：禁止改第一遍矩阵/先验/标签、禁止多候选/搜 seed、禁止调 `Δm`/decoder/泄漏口径、禁止用 outcomes 定增量、禁止创建正式输出、禁止运行 decoder、禁止启动 V53。

## Tasks

见 `tasks.md`（Phase A 冻结首遍+增量嵌套+15 fresh 块；Phase B 仅 fake-runner 聚焦测试含嵌套/秩/泄漏门；Phase C decoder-free preflight；Phase D 需 EXECUTE_AUTH 的至多 15 块两遍条件执行；Phase E 结果复核；显式禁止清单）。

## Lifecycle

前代 `6aa33eadc872bb4551f458ee750a94cd24566314` (含 V50 规划 + V51 规划) 位于分支 `formal-ir-mainline`；V52 修订后 `PLAN_REVISE_REQUIRED / EXECUTE_NOT_AUTHORIZED`，仍保持不实现不执行、等待独立复审；实现候选止于 `IMPLEMENTATION_CANDIDATE / EXECUTE_NOT_AUTHORIZED`；任何执行需显式用户 `EXECUTE_AUTH` 绑定到精确未来实现 SHA；不启动 V53。本次修订仅修正去重旧臂与泄漏分类（总 30–45 硬帽45，`first_pass_success_leak=leak_base / rescued_success_leak=leak_joint / final_failure_leak=leak_joint / avg_leak=leak_base+40×N_attempt/15`），不改 Δm=8/矩阵/样本/参数或执行实验。Spike 已修复为确定性嵌套 `H_joint` `rank==m2+8` + 非零退出 + 泄漏公式校验。
