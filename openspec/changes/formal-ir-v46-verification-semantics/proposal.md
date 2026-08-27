# OpenSpec Proposal: formal-ir-v46-verification-semantics

**Status**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED` — **只规划、不实现、不执行、不启动 V47。**
**Domain**: Formal IR / verification semantics
**Change ID**: `formal-ir-v46-verification-semantics`
**Cycle ID**: `V46P0`
**Predecessor**: `formal-ir-v45-l1-app-soft-transfer` (PLAN_CANDIDATE, HEAD `f59ab60a`) — V45 已冻结 27-invocation 诊断；验证语义仅记账未落地
**Investigation SHA**: `f59ab60a`（三项只读结论锚点）
**Branch / HEAD**: `Placebo303/HD-QKD-Polar-pipeline` `formal-ir-mainline`, HEAD `f59ab60a`（规划冻结时绑定，执行时精确重绑）
**Lifecycle**: `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`, `implementation_started=false`, `production_outputs_created=false`

> ponytail lite: 最懒路径是零新增语义、沿用 V45 exact_l2 oracle 判真并把 wrong_codeword 口头记为 detected；本规划仅在需把 64-bit tag 从记账转为可执行验证时才值得落地——否则不建。

## Goal

在**不新增 decoder、不改 V45 已有输出、不新增泄漏**的前提下，把 `+64 tag` 从纯记账（`SOURCE_L2_TAG_BITS` → 984/1014/1024，已计入 `leak_total`，未生成/未传输/未参与 acceptance，路径 `v45:216-222,598,1182-1242`）补为**可执行的确定性 64-bit verification**，并把 LDPC 错误陪集解 `wrong_codeword = syndrome_ok && !exact` 从静默陪集错误转为**可检测失败（detected failure）**。`exact_l2` 仍为 oracle 判真（ground truth），`tag mismatch` 为 detected、`tag match && !exact` 为约 `2^-64` 的 undetected error，不宣称提升 decoder exact rate。

单一机制判据：`tag = trunc64(SHA256(canonical_bytes(x_hat)))` 确定性生成→传输→重算比对；`wrong_codeword_l2 / G3 / exact_l2` 时序保持 pre-tag（已正确），verification 仅在其后增加一层 acceptance gate。

## Non-Goals

- 不新增 decoder / 矩阵 / 参数网格 / 调参 / 联合图 / 真帧 FER / 阈值 / SKR / 安全 / 资格 / 晋升陈述。
- 不改写/覆盖 V45 任何已有输出（`results/`、`comparison_bench/outputs_comparison/` 只读）；V46 证据隔离新根。
- 不新增泄漏：64-bit 已计入 `leak_total = 5·m + 64`，V46 不重复计费。
- 不把 `exact_l2` 替换为 tag acceptance；不把 `390221 errors_final=3` 的“相同残留数”等同于“同一码字”（未保存 `x_hat/hash`，路径缺口不变）。
- 不启动 V47；不并行第二分支（若 tag 已实际执行则应走“保存最小 decoded-difference 诊断 + L2 图陪集调查”分支，本轮不走）。

## Scope

1. **单一机制**：确定性 64-bit verification（SHA-256 截断 64-bit，canonical bytes 归一化冻结），单一验收门，不做多 tag/多哈希对比。
2. **最小 workload**：对 V45 已有 18 L2 records 的只读复核 + 确定性 tag 重放校验（零新 decoder invocations）；可选至多 1 次 decoder-free 的 tag 生成一致性自检（fake 亦可）。不重跑 V45 27 invocations。
3. **时序冻结**：`wrong_codeword_l2 / G3 / exact_l2` 保持 pre-tag 计算；verification 在其后追加 `tag_mismatch → detected failure`，`tag_match && !exact → undetected error (~2^-64)`。
4. **产出隔离**：新根 `comparison_bench/outputs_comparison/formal_ir_methods/v46_verification_semantics/run_01/`，最小三件套（records 复核视图 + summary 增量 + notice），不写 NPZ，不改 V45 文件 byte-identical。
5. **终态可区分**：`verification failure`（tag mismatch 的 detected）与 `structure failure`（pre-tag 已 `!exact` 且 syndrome 亦失败）在 summary 终态/原因码正交区分。

## Impact Scope

- **新增**：`openspec/changes/formal-ir-v46-verification-semantics/` 四工件（本轮仅此）。
- **未来实现（本轮不创建）**：`comparison_bench/src/comparison_bench/formal_ir/v46_verification_semantics.py`（纯 verification 语义层）+ 可选 `scripts/verify_v46_tags.py`（decoder-free 重放）；均不引入新 decoder。
- **只读依赖**：V45 `v45_records.json/.csv`、`v45_summary.json`、V45 模块常量（`SOURCE_L2_TAG_BITS`）、V31/V38 结构权威（仅溯源）。
- **不修改**：任何既有 spec/代码/测试/输出、V45 输出、`AGENT_PROJECT_MEMORY.md`、`docs/decision-log.md` 以外。

## Acceptance Criteria

- [ ] 四工件齐全一致且 lifecycle 为 `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`，HEAD `f59ab60a` 绑定，明确“不实现不执行不启动 V47”。
- [ ] Tag 语义冻结：来源（`x_hat` canonical bytes）、归一化（大小端/定长/截断位置）、泄漏已计（`984/1014/1024` 含 64，不重复计）、确定性重算路径可复现。
- [ ] 区分 `detected failure`（`syndrome_ok && !exact && tag_mismatch`）与 `undetected error`（`tag_match && !exact ≈2^-64`），`wrong_codeword` 转为前者为主。
- [ ] `exact_l2` 仍为 oracle 判真，verification 不覆盖/不重定义 exact；pre-tag 时序声明与 V45 一致。
- [ ] 终态可区分 `verification failure` vs `structure failure`，且 V45 输出 byte-identical 不变。
- [ ] Workload 最小（只读复核、零新 decoder invocations）且单机制、无第二分支。

## Tasks

见 `tasks.md`（Phase A 冻结语义常量、Phase B 只读复核、Phase C decoder-free 自检、Phase D 需 EXECUTE_AUTH 的隔离写出；显式禁止清单）。

## Lifecycle

V45 前代 `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`（`f59ab60a`）；V46 当前同为 `PLAN_CANDIDATE / EXECUTE_NOT_AUTHORIZED`，等待独立 plan ACCEPT；实现候选止于 `IMPLEMENTATION_CANDIDATE / EXECUTE_NOT_AUTHORIZED`；任何执行需显式用户 `EXECUTE_AUTH` 绑定到精确实现 SHA；不启动 V47。
