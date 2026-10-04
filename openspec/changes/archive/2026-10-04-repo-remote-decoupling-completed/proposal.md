# Proposal: repo-remote-decoupling

- Change: `repo-remote-decoupling`
- Status: EXECUTED-PARTIAL (the planning proposal was later executed under a
  separately authorized operator task; T7/archive remains incomplete)
- Date: 2026-09-05
- Decided by: 主线程裁决（planner 不复议，只引用）

## Goal

彻底解耦当前双 checkout 共享同一 GitHub remote + 同一 `main` 造成的串扰风险（2026-08-12..22 研究内容 swept into shared mainline），使
Release（Polar 主线）与 Comparison（Formal IR / LDPC 研究主线）各有独立
private 远端、各有默认分支与专属分支归属，tag 按精选推送 B 方案处理。
本 change 只做 OpenSpec 冻结 + 操作清单，远程改动按 tasks.md T0–T7 由主线程显式授权后另行执行。

## Non-Goals

- 不写任何生产代码；不改 `src/`、`experiments/`、`tools/`、`results/`、`comparison_bench/` 逻辑与数据。
- 不改任何本地/远端 git 配置；不执行 push/fetch；不做历史重写（rebase/filter/rewrite 全部 out of scope）。
- 不碰 `D:\Code\HD-QKD_Polar_Release` 工作树。
- 不在本 change 内做 tag 全量迁移、全量 mirror、历史清理；如需历史重写必须另起 change（见 tasks.md T6）。
- 不执行任何decoder/benchmark长跑/run_01，T0-T7之外不加执行任务（Comparison HEAD a393f839 正处 R2 授权态，防误触发）。

## What（做什么）

1. 冻结远端解耦方案：远端布局、分支归属、tag 精选原则、GitHub 设置清单、回滚点、安全禁令（见 design.md）。
2. 输出可执行的 T0–T7 任务序列，每任务带前置门与“阻塞即停”规则（见 tasks.md）。
3. 本 planner 产出仅为 `openspec/changes/repo-remote-decoupling/` 下 proposal/design/tasks 三文件。

## Why（为什么）

- AGENTS.md §0 记录：双 checkout 历史共享一个 remote + 一个 `main` 已造成 crosstalk incident。
- 当前 Comparison（`main`：formal Cascade/LDPC、binary-LDPC v3+、nonbinary-LDPC ladder）与
  Release（`polar-mainline`：mature binary Polar、frozen baseline、security tooling）必须物理隔离，
  否则任何 `--all` / `--mirror` / 默认 push 都可能再次串扰。
- 专属分支已分化（`codex/security-workbench-master-roadmap@6f40e54` 只属 Release；
  `formal-ir-v72p1-addendum-clean` 只属 Comparison），需要书面归属矩阵防止误合并/误推送。

## Scope

### In scope

- `openspec/changes/repo-remote-decoupling/proposal.md`（本文件）
- `openspec/changes/repo-remote-decoupling/design.md`（remote 布局表、分支归属矩阵、tag 原则、设置清单、回滚点、安全禁令）
- `openspec/changes/repo-remote-decoupling/tasks.md`（T0–T7，前置门 + 阻塞即停）

### Out of scope

- 任何 `src/`、`experiments/`、`tools/`、`results/`、`comparison_bench/`、`AGENTS.md` 的修改。
- `docs/decision-log.md` 与 `AGENT_PROJECT_MEMORY.md` 本Turn不写，T6/T7按条件写decision-log/memory（见 tasks.md T6/T7）。
- 任何 git 操作（config/remote add/push/fetch/tag push/分支删除/默认分支切换）。
- 任何历史重写与 `--all` / `--mirror` 推送。
- 对 `D:\Code\HD-QKD_Polar_Release` 的任何读写。
- GitHub 上的实际建仓/改名/设置变更（只在 design/tasks 中规定，不在本 planner Turn 内执行）。

## Affected specs

- `openspec/project.md`：Architecture（frozen baseline + comparison layer）与 Key Constraints 不变，本 change 只加远端归属约束，不改动代码架构。
- `AGENTS.md` §0 Repository Scope：本 change 落实其边界规则，不修改其文字（如需改 AGENTS.md 必须另起 change）。
- `AGENT_PROJECT_MEMORY.md`：本 change 完成后由 memory triage 决定是否追加一条远端解耦记录（见 tasks.md T7）；本 Turn 不写。
- 无新增 delta spec（纯运维解耦，无行为/接口变更，故无 `specs/` delta）。

## 已定决策引用（主线程裁决，D1=A，不再讨论）

- D1=A：原 GitHub 仓库 `Placebo303/HD-QKD-Polar-pipeline` 复用做 Release；Comparison 新建 `HD-QKD-Polar-Comparison`。
- 仓库名：`HD-QKD-Polar-Release`（即原仓改名或保持 URL 复用）/ `HD-QKD-Polar-Comparison`（新仓），双 private。
- Release 默认分支 `polar-mainline`；Comparison 默认分支 `main`。
- 专属分支：`codex/security-workbench-master-roadmap@6f40e54` 只属 Release；
  `formal-ir-v72p1-addendum-clean` 只属 Comparison。
- tag 采用精选推送 B 方案（只推精选 tag，禁止全量 tag 迁移；详见 design.md）。

## Impact Scope

- 文件：仅 `openspec/changes/repo-remote-decoupling/{proposal,design,tasks}.md` 三个新文件。
- 模块/系统：无代码模块影响；影响对象是 GitHub 远端归属与分支/tag 管理约定。
- 风险：本 Turn 零风险（纯文本产出，无 git/远端/文件系统副作用）。

## Acceptance Criteria

- P1：上述三文件存在，且 proposal 含 What/Why/Scope in-out/Affected specs/已定决策引用；
  design 含 remote 布局表、分支归属矩阵、tag 精选原则、GitHub 设置清单、回滚点、
  无备份不推送原则、禁用 `--all`/`--mirror`，另含 `legacy-origin` 审计残留保留与 Comparison 空仓首推专线；
  tasks 含 T0–T7、每任务前置门 + 阻塞即停、T1 更名审计链（rename/add origin/`remote -v`/`remote\..*`/`ls-remote` 验空存证）、
  T3 空仓首推专线（先推 `main`→设默认→开保护，非空另行）、T5 §4.1 不迁移验收、T6 声明另起 change、T7 archive 条件含 memory triage
 （`git status` 口径：除本 change 三文件外无未提交改动，或已逐项记录）。
- 原始 planner Turn 未改三文件之外的任何文件，未执行 push/fetch，也未碰
  Release 工作树；后续经单独授权执行的远端操作见本文件末尾的
  `Execution evidence`，不应与 planner Turn 的零副作用声明混淆。

## Tasks（索引，详情见 tasks.md）

- T0 只读核验 → T1 建仓/改名准备 → T2 Release 侧收敛 → T3 Comparison 侧收敛 →
  T4 tag 精选推送 → T5 GitHub 设置锁定 → T6 历史重写声明（另起 change）→ T7 archive（含 memory triage）。

## Execution evidence (2026-09-05)

The three planning files were created before remote execution. The following
operations were performed later under the parent task's explicit scope; this
section is evidence of the observed state, not a self-approval:

- Both repositories remain private. Release default branch is
  `polar-mainline`; Comparison default branch is `main`.
- Release `codex/security-workbench-master-roadmap` was pushed exactly at
  `546beb8d476db04d3301c6403e7f878873f46872`. A later local-only commit
  `4c7911713bcc51e70d575495aadceb5757757793` appeared after that push and was
  not pushed by this task.
- `formal-ir-mainline@d7acfd28df80c5a1d5e22b4e77a3fa578105c25a` was first
  pushed exactly to Comparison and then deleted from Release. The same
  recovery SHA was verified on Comparison before deletion.
- `formal-ir-v72p1-addendum-clean@a393f83960c8434495fd0b43fb831dc7cf0442ce`
  was verified on Comparison and then deleted from Release.
- The ambiguous Release branch `feat/consolidate-cascade-single-kernel` was
  retained. No tag push, force push, mirror push, history rewrite, or cleanup
  command was used.
- Both checkouts retain `legacy-origin` for fetch-only audit and have its push
  URL set to `no_push://legacy-origin-disabled`. The active Release security
  branch and Comparison `formal-ir-v72p1-addendum-clean` track their respective
  `origin` remotes.

T4 tag selection was not executed, T7 archive conditions are not met, and the
  dirty Comparison worktree was preserved. Final remote heads, protection JSON,
  upstreams, and status were independently re-read after the operations.
