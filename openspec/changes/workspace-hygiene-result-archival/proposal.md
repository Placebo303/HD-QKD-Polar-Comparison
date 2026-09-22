# Change: workspace-hygiene-result-archival

Status: PLANNER SPEC FREEZE (2026-08-26) — planner-authored. Documentation-only planning phase: no production code, no experiment runs, no deletion of any data, no git write operations in this phase. All git write operations are deferred to implementation and gated on the quiet-period rule (see Frozen Decisions).

## Positioning (authoritative)

This is a **repository-hygiene change**, not an algorithm change. It does two things and nothing else: (1) removes one recurring git noise-diff source by untracking a single volatile test manifest; (2) converts conclusion-bearing but untracked experiment outputs into compact tracked summaries plus one index, while leaving all raw outputs in place locally forever. It deletes nothing, reruns nothing, modifies no IR method, and touches no frozen baseline.

Per frozen decision **D3**, both hygiene points are handled in this single change; no second change will be opened for either of them.

Motivation (reviewer read-only recheck, 2026-08-26, branch `formal-ir-mainline`): every run of the pytest evidence test refreshes `workspace/pytest-evidence-test/output/expanded_evidence_manifest.json` (diff is a single `"git_commit"` line flip), producing perpetual noise diffs in `git status`; meanwhile 38 untracked entries accumulate under `comparison_bench/outputs_comparison/` with no tracked, compact record of which runs actually carry recorded scientific conclusions.

## Goal (verbatim, frozen)

> 消除 evidence 测试造成的周期性噪音 diff（untrack 单个易变 manifest 并加 ignore 条目），并把已产生但未入库的实验输出按结论承载价值做选择性归档——仅 A 类提交紧凑摘要与总索引，B/C 类留在本地无限保留、永不删除——同时把该保留政策写入 docs/decision-log.md。

## Frozen User Decisions (不得重新定义，只能落实)

- **D1 — Untrack 范围**: 仅限唯一文件 `workspace/pytest-evidence-test/output/expanded_evidence_manifest.json`（`git rm --cached`，工作区文件保留）+ 在 `.gitignore` 加对应条目。不扩大到其他任何 `workspace/` 文件。
- **D2 — 保留政策**: B/C 类实验数据本地无限保留。本变更永不删除 `comparison_bench/outputs_comparison/` 下任何内容（append-only 政策不变）。
- **D3 — 合并**: 本条与选择性归档两点合并为本变更，不开第二个变更。
- **执行门控（硬前置）**: 所有 git 写操作仅在仓库静默期执行（无其他任务运行、`git status` 连续稳定）。当前有后台任务运行中，因此 tasks.md 的第一个实现任务必须是"确认静默"，且为后续每个 git 写操作的前置条件。

## Background Facts (orientation only — NOT frozen data)

来自 2026-08-26 reviewer 只读复查，仅作执行时的对照起点：

- 分支 `formal-ir-mainline`；无 staged/deleted/stash。
- 唯一 modified：上述 manifest，diff 仅一行 `"git_commit": "b639e3d" -> "5f506c9e"`。
- untracked 共 38 条，全部在 `comparison_bench/outputs_comparison/` 下：
  - `formal_ir_methods/` 下 28 个日期目录（20260725..20260813）+ 2 个 `*.partial_state.execution.log`；
  - `nonbinary_diagnostics/` 下 5 个子条目（nbldpc_v25_20260818/run_01..03、nbldpc_v32_finite_de_bridge、nbldpc_v32_operating_point_audit）;
  - 具名项 3 个：`e2e_16dB_pairing_v2_rematerialize/`、`final_ir_method_selection/`、`transfer_evaluation/`。
- **分类必须在执行时对照当时的实时 `git status` 重新采集**；上表不是死数据，条目可能已增减。
- frozen 区（`src/`、`experiments/`、`tools/`、`results/`）、`openspec/`（本变更四文件除外）、`docs/` 当前干净，必须保持。

## Deliverables (three task groups)

- **G1（D1 落实）**: untrack 该 manifest + `.gitignore` 显式条目 + 只读验证（`git ls-files` 确认生效；若发现 `workspace/` 下还有其他被跟踪的易变测试产物，只报告不处理）。
- **G2（选择性归档）**: 将 untracked 输出分为三类——
  - **A = 结论承载型**: 被 `final_ir_method_selection/`、`docs/decision-log.md`、`AGENT_PROJECT_MEMORY.md` 引用，或直接支撑现有已记录结论的 run（精确判据见 design §3）；
  - **B = 中间诊断**；
  - **C = 半成品日志**（`*.partial_state.execution.log`）。
  仅 A 类提交紧凑摘要（每 run 的 metrics CSV / run_manifest.json / provenance+seed+命令）加一个总索引文件（run 目录 → 结论 → provenance 映射）。B/C 不入库、不删除、无限本地保留。禁止整目录提交 parquet/大二进制。
- **G3（保留政策记录）**: 把 D2 决定写入 `docs/decision-log.md`（本变更唯一允许触碰 `docs/` 的点），使用该文件的既有 Template 格式。

## Non-Goals

1. 不删除任何文件或数据；尤其不动 `comparison_bench/outputs_comparison/**` 与 `workspace/**` 的本地内容（D2）。
2. 不扩大 untrack 范围到其他 `workspace/` 文件（D1）。
3. 不提交 parquet / npz / pkl / 任何大二进制 / 任何整目录原始输出。
4. 不修改 `AGENT_PROJECT_MEMORY.md`（仅作 A 类判定的只读输入）、`src/**`、`experiments/**`、`tools/**`、`results/**`、既有 OpenSpec changes。
5. 不重跑任何实验、不产生新实验数据、不调用任何 decoder/pipeline/longrun 入口。
6. 不改任何 schema：CSV 列名、JSON/YAML keys、CLI 参数、核心函数签名（AGENT_PROJECT_MEMORY.md §6）。
7. 不为本两点评述开第二个变更（D3）。

## Impact Scope

| Path | Change |
|---|---|
| `openspec/changes/workspace-hygiene-result-archival/**` | 本变更四类文档（新建） |
| git index | untrack 恰好 1 个文件 |
| `.gitignore` | +1 条显式条目（附注释行） |
| `comparison_bench/outputs_comparison/result_archive_summaries/**` | 新建 tracked 紧凑摘要 + 总索引 `index.csv`（additive，不触碰既有输出） |
| `comparison_bench/src/comparison_bench/cli/make_result_archive_summaries.py` | 可选新建：一次性、可重跑、只读原输出的最小归档脚本（`make_*` 惯例位；若 A 类 run 很少可手工替代，见 design §5） |
| `docs/decision-log.md` | 追加 1 条 D2 保留政策记录（唯一 docs 触点） |

No impact on `src/**`, `experiments/**`, `tools/**`, `results/**`, `AGENT_PROJECT_MEMORY.md`, any archived OpenSpec change, or any existing file under `comparison_bench/outputs_comparison/**`（零覆盖、零删除）。

## Forbidden (must appear consistently in all four docs)

- 删除或覆盖 `comparison_bench/outputs_comparison/**`、`workspace/**` 本地任何内容。
- Untrack / ignore / commit 任何 D1 范围之外的文件。
- 提交 parquet、npz、pkl、h5、ttbin 或任何 >1 MB 文件、任何整目录原始输出。
- 修改 `AGENT_PROJECT_MEMORY.md`、frozen 区、既有 OpenSpec changes、本变更允许触点之外的 `docs/` 路径。
- 在未通过静默期确认的情况下执行任何 git 写操作（rm --cached / add / commit）。
