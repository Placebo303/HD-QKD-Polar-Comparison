# Tasks: workspace-hygiene-result-archival

> Do NOT mark any task complete without evidence (command output, file listing, or reviewer report). Checkbox format. **T0 is the hard precondition for every git write operation in T2/T3/T4/T6** — if it fails, stop and report; do not proceed.

## Allowed New Files

- `openspec/changes/workspace-hygiene-result-archival/{proposal.md,design.md,tasks.md,specs/workspace-hygiene-result-archival/spec.md}` — this change's four docs
- `comparison_bench/outputs_comparison/result_archive_summaries/**` — A-class compact summaries + `index.csv` (tracked)
- `workspace/workspace-hygiene-result-archival/classification.md` — classification table (untracked scratch)
- `comparison_bench/src/comparison_bench/cli/make_result_archive_summaries.py` — OPTIONAL one-off archival script (only if A-set makes manual copying tedious; see design §5)

## Forbidden (MUST NOT be edited/deleted/staged at any stage)

- 删除或覆盖 `comparison_bench/outputs_comparison/**`、`workspace/**` 本地任何内容（D2：append-only，永不删除）
- Untrack / ignore / commit D1 范围之外的任何文件
- 提交 parquet/npz/pkl/h5/ttbin、任何 >1 MB 文件、任何整目录原始输出
- `AGENT_PROJECT_MEMORY.md`（只读输入）、`src/**`、`experiments/**`、`tools/**`、`results/**`、既有 OpenSpec changes
- `docs/` 下除 decision-log 追加一节外的任何路径
- 未过静默门执行任何 git 写操作

## Frozen Constants (identical across proposal/design/spec/tasks)

- Goal: 见 `proposal.md §Goal`（逐字）。
- D1/D2/D3 与静默期门控：见 `proposal.md §Frozen User Decisions`（逐字落实，不得偏离）。
- Untrack 目标（唯一）：`workspace/pytest-evidence-test/output/expanded_evidence_manifest.json`。
- 归档根：`comparison_bench/outputs_comparison/result_archive_summaries/`；总索引：该根下 `index.csv`，列集见 design §2.3。
- 分类判据 A-crit-1..4 / B / C / 平局降级为 B：见 design §2.2；分类必须基于执行时实时 `git status --porcelain -- comparison_bench/outputs_comparison/`。
- 大小护栏：单文件 >1 MB 排除；parquet/npz/pkl/h5/ttbin 扩展名直接排除。
- 提交计划：C1 = untrack+.gitignore；C2 = 摘要+索引(+脚本)；C3 = decision-log 条目。顺序 C1→C2→C3，各自独立过静默门。

---

### P1 — Specification Freeze (planner) ✅ 2026-08-26

- [x] P1.1 Create the four files (proposal/design/tasks/spec) aligned with existing change format. — Evidence: files written this session; structure mirrors `formal-nonbinary-ldpc-v32-operating-point-consistency-audit` 四件套.
- [x] P1.2 Consistency self-check: D1/D2/D3 + quiet-gate verbatim in proposal §Frozen User Decisions and tasks §Frozen Constants; Forbidden lists aligned across all four docs; no forbidden item appears as allowed.
- **Done when**: main reviews and accepts the freeze.

### T0 — Quiet-Period Gate (main thread) — HARD PRECONDITION

- [ ] T0.1 Confirm: (a) 无其他 agent/后台任务运行；(b) 连续两次 `git status --porcelain`（间隔 ≥60 s）输出逐字节一致。记录两条命令输出与时间戳作为证据。任一不满足 → 中止并报告 blocker（附两次输出），不得自行等待重试超过一轮。
- [ ] T0.2 Capture the live untracked inventory: `git status --porcelain -- comparison_bench/outputs_comparison/` full output saved to `workspace/workspace-hygiene-result-archival/classification.md` header. This list, not the proposal's background facts, is the classification input.
- **Done when**: gate evidence recorded AND live inventory captured. Must be re-passed before EACH of C1/C2/C3 (T3.3/T4.3/T5.1).

### T1 — Classification (coder-fast/operator, read-only on outputs)

- [ ] T1.1 For every live-inventory entry assign A/B/C per design §2.2 (A-crit-1..4 checked against `final_ir_method_selection/`, `docs/decision-log.md`, `AGENT_PROJECT_MEMORY.md`; borderline → B). Write table to `classification.md`: run_dir | class | criterion | one-line justification.
- [ ] T1.2 Enumerate the exact file list for each A run (metrics CSV / manifest / provenance json), applying size/extension guards. Append to `classification.md`.
- **Done when**: every inventory entry has a class + criterion; A-set file enumeration complete; table reviewed by main before any staging.

### T2 — Group 1: Untrack Volatile Manifest (operator; gated)

- [ ] T2.1 Re-pass quiet gate for C1.
- [ ] T2.2 Execute C1: `git rm --cached workspace/pytest-evidence-test/output/expanded_evidence_manifest.json` + add the `.gitignore` entry with comment line (design §1); commit per message style from `git log --oneline -15`.
- [ ] T2.3 Read-only verification: `git ls-files -- workspace/` does not contain the manifest; working-tree file still present on disk; noise diff gone (`git status` no longer lists it). If OTHER tracked paths exist under `workspace/`: report the full `git ls-files -- workspace/` output, do not act (D1).
- **Done when**: C1 committed; verification commands' outputs cited in the completion report.

### T3 — Group 2: Selective Archival (coder-fast/operator; gated)

- [ ] T3.1 Produce A-class summaries under `result_archive_summaries/` mirroring original relative paths (manual copy, or via the optional script per design §5); write `index.csv` with the frozen column set.
- [ ] T3.2 Self-check staged set: enumerated files == classification A-set; zero files >1 MB; zero forbidden extensions; index rows == archived runs.
- [ ] T3.3 Re-pass quiet gate; execute C2 (summaries + index [+ script]).
- **Done when**: C2 committed; T3.2 checks cited with command output; nothing outside `result_archive_summaries/**` staged.

### T4 — Group 3: Retention Decision Record (operator; gated)

- [ ] T4.1 Draft the decision-log entry per design §3 (template-compliant, records D2 verbatim intent + rejected alternatives).
- [ ] T4.2 Main reviews the draft text BEFORE it touches `docs/decision-log.md` (sole docs touchpoint).
- [ ] T4.3 Re-pass quiet gate; execute C3 appending exactly that entry.
- **Done when**: C3 committed; `git diff HEAD~1 -- docs/decision-log.md` shows only the appended entry.

### T5 — Final Read-Only Verification & Closeout

- [ ] T5.1 Full-status check: `git status --porcelain` delta == {openspec 四文件, `.gitignore`, `docs/decision-log.md`, `result_archive_summaries/**` 新增} exactly; zero `D` entries anywhere under `outputs_comparison/`; frozen zones (`src/`, `experiments/`, `tools/`, `results/`) untouched.
- [ ] T5.2 Fill the acceptance-ID table below (P1–P4) with evidence pointers.
- [ ] T5.3 Memory triage via memory agent (mandatory closeout); conclusions only — no edit to `AGENT_PROJECT_MEMORY.md` inside this change.
- **Done when**: all checks green and triage returned.

## Acceptance ID Mapping (fill at T5.2)

| ID | Criterion | Evidence |
|---|---|---|
| P1 | 四类文档齐全且格式与现有 changes 一致 | P1.1 |
| P2 | D1/D2/D3 + 静默期门控明确落入 tasks.md 且无偏离 | 本文件 §Frozen Constants + T0/T2/T3/T4 gates |
| P3 | 任务有序、可独立验收、每条有完成判据 | 各任务 "Done when" |
| P4 | delta specs 覆盖跟踪政策与归档政策行为变化点 | spec.md SHALL-T*/SHALL-A* |

---

**Do not mark tasks complete without evidence. Each checkbox requires a cited command output, file listing, or reviewer report.**
