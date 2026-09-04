# Design: repo-remote-decoupling

- Change: `repo-remote-decoupling`
- Status: EXECUTED-PARTIAL (remote operations were later performed under a
  separately authorized task; this change is not archived)
- Authority: 主线程已定决策 D1=A；本文件只做冻结记录，不复议。

## Goal

给出远端解耦的唯一可执行布局：两个 private 远端、各自默认分支、专属分支归属、
tag 精选 B 方案、GitHub 设置清单、回滚点与安全禁令，供 tasks.md T0–T7 逐项执行。

## Non-Goals

- 不规定任何代码/算法/输出 schema 变更；不改分支内容本身，只规定归属与推送边界。
- 不做历史重写方案（T6 声明另起 change）。
- 不在本 Turn 执行任何 git/GitHub 写操作。
- 不执行任何decoder/benchmark长跑/run_01，T0-T7之外不加执行任务（Comparison HEAD a393f839 正处 R2 授权态，防误触发）。

## 1. Remote 布局表（目标态）

| 本地 checkout | 远端仓库（目标） | 来源 | 可见性 | 默认分支 | 用途 |
|---|---|---|---|---|---|
| `D:\Code\HD-QKD_Polar_Release` | `Placebo303/HD-QKD-Polar-Release`（由原 `HD-QKD-Polar-pipeline` 改名或保持 URL 复用） | 原仓复用（D1=A） | private | `polar-mainline` | Binary Polar 主线：mature Polar 用法、frozen baseline、security tooling |
| `D:\Code\HD-QKD_Polar_Comparison` | `Placebo303/HD-QKD-Polar-Comparison`（新建空仓） | 新建（D1=A） | private | `main` | Formal IR / LDPC 研究主线：formal Cascade/LDPC、binary-LDPC v3+、nonbinary-LDPC ladder |

约束：

- 两个远端之间永不 `--all` / `--mirror` 互推；永不互相设为对方的 `origin`。
- 本地每个 checkout 只保留指向自家远端的 `origin`（另允许 `legacy-origin` 仅作改名审计残留，指向原 URL，永久保留、禁止删除/覆盖，详见 tasks T1 更名审计链）；不添加对方远端为 `upstream`/`mirror`（如需对照只做本地只读 diff，不加 remote）。
- 改名前/建仓前必须先满足“无备份不推送原则”（见 §5）。
- Comparison 空仓首推专线（见 tasks T3）：空仓（`defaultBranchRef` 为空）先单推 `main` → 设默认 `main` → 开保护，再推其余白名单分支；非空仓走常规收敛，不得套用本专线。

## 2. 分支归属矩阵（唯一真源）

| 分支 | 归属远端 | 说明 | 禁止事项 |
|---|---|---|---|
| `polar-mainline` | Release | Release 默认分支；Binary Polar 主线 | 禁止 merge 入 Comparison `main`；禁止从 Comparison checkout 向 Release push 该分支以外的研究分支 |
| `main` | Comparison | Comparison 默认分支；Formal IR / LDPC 研究主线 | 禁止 sweep 入 Release；禁止把研究 commits 推向 Release 远端 |
| `codex/security-workbench-master-roadmap@6f40e54` | Release 专属 | 只属 Release | 禁止出现在 Comparison 远端；禁止 cherry-pick/merge 入 Comparison `main`（如需参照只读 diff，另起评审） |
| `formal-ir-v72p1-addendum-clean` | Comparison 专属 | 只属 Comparison | 禁止出现在 Release 远端；禁止 merge 入 `polar-mainline` |
| 其他历史研究分支（Comparison `main` 演进线） | Comparison | 随 Comparison 远端收敛 | 禁止推向 Release；清理/删除需主线程逐个点名，默认保留 |
| 其他 Polar 基线/工具分支（若存在） | Release | 随 Release 远端收敛 | 禁止推向 Comparison |

合并禁令（重申 AGENTS.md §0）：

- 永不把 `polar-mainline` merge 入 Comparison `main`，永不把 Comparison `main`/研究分支 merge 入 `polar-mainline`。
- 2026-08-12..22 crosstalk 不得重演：任何“把一边的线 sweep 进另一边的默认分支”的操作一律禁止。

## 3. Tag 精选原则（B 方案）

- 原则：只推送主线程点名的精选 tag；默认一个不推；禁止全量 tag 迁移。
- 禁止：`git push --tags`（全量）、`--all`、`--mirror` 附带 tag 的任何形式。
- 精选 tag 必须逐个显式推送：`git push <remote> refs/tags/<tag>:refs/tags/<tag>`，一次一个，可审计。
- Release 精选候选（示例方向，需主线程在 T4 点名）：Polar 基线可复现点 / security workbench 里程碑 tag。
- Comparison 精选候选（示例方向，需主线程在 T4 点名）：与已固化 result 绑定的 qualification/acceptance tag。
- 任何含研究内容的 tag 不得推向 Release；任何 Polar-only 里程碑 tag 不得推向 Comparison（除非主线程书面点名交叉引用，且以新建 annotated tag 说明代替移动原 tag）。
- 推送前必须 `git tag --list` 与远端 tag 列表双人核对（主线程 + 执行者），数量一致才继续；计数命令tag --list|wc -l vs ls-remote --tags（即 `git tag --list|wc -l` vs `git ls-remote --tags <remote>`），两侧计数一致才继续。

## 4. GitHub 设置清单（逐项验收）

- [ ] 两个仓库均为 private（Organization/个人可见性检查）。
- [ ] Release 默认分支 = `polar-mainline`；Comparison 默认分支 = `main`（Settings → General → Default branch 截图/记录）。
- [ ] 默认分支保护：require PR / 禁止 force-push / 禁止 deletion（至少对默认分支开启）；开启时机：首次 push 前开启，或在 T2/T3 前置门中显式豁免声明（无开启且无豁免不得 push）。
- [ ] Collaborator/Team 权限最小化：无多余 admin；Comparison 与 Release 授权集合分别记录。
- [ ] Actions/Secrets（如有）：不继承、不复制对方 secrets；按需重建。
- [ ] 本地 `git remote -v` 核对：Release checkout 的 origin 仅指向 Release URL；
  Comparison checkout 的 origin 仅指向 Comparison URL；无 `push --mirror` 残留配置。
- [ ] `git config --get-regexp 'remote\..*'` 檢查：无 `mirror = true`；无多余 pushurl。
- [ ] 归档前 `git status` 双 checkout 均干净（除本 change 三文件外无未提交改动，或已逐项记录）。

### 4.1 Issue/PR 与附属资源不迁移原则

- 不迁移，原仓研究类Issue打标签关闭/另建，Comparison按需新建；Wiki/Projects/Releases/Actions/Secrets同理不互拷（不批量搬运、不复刻评论历史；Secrets 不复制、按需重建；Actions 配置不继承）。

## 5. 回滚点与无备份不推送原则

- 回滚点定义：任何首次 push/改名/默认分支切换之前，必须存在可恢复点：
  1. 双 checkout 各自最新 HEAD 的完整 SHA 记录（含 `git rev-parse HEAD` + `git log -1 --format=fuller`）。
  2. 全分支列表快照（`git branch -a` + `git tag --list` 输出保存为文本附件，不在本 change 内提交，交主线程保管）。
  3. GitHub 原仓改名前：确认原仓 Settings 可改名回退（记录原名 `HD-QKD-Polar-pipeline`），或先由 Owner 建临时备份 fork（是否建备份由主线程决定，但“无记录不推送”不可豁免）。
- 无备份不推送原则：没有上述三项记录，主线程不得授权任何 push/改名/默认分支切换；执行者见缺即停（见 tasks.md 各任务阻塞即停）。
- 回滚动作（仅当已按 T0–T5 留痕后仍出错）：改名回退 / 默认分支切回 / 删除误推的精选 tag
  （`git push <remote> :refs/tags/<tag>` 需主线程单点授权）；禁止用 force-push 整支回滚代替逐项修复。

## 6. 安全禁令（全局有效，T0–T7 全程）

1. 禁用 `git push --all`、`git push --mirror`、`git push --tags`（全量形式）——任何场景、任何理由均不得使用。
2. 禁止改任何 git 配置（`git config` 写操作）超出 tasks.md 点名的只读核验；remote URL 变更只由主线程在 T1–T3 授权窗口内执行。
3. 禁止历史重写（rebase -i / filter-branch / filter-repo / BFG / push -f）——确需则按 T6 另起 change。
4. 禁止碰 `D:\Code\HD-QKD_Polar_Release` 工作树（本 planner Turn 及 Comparison 侧任务默认不得进入该目录；Release 侧操作另由主线程在 Release checkout 内授权）。
5. 禁止在未满足前置门时进入下一任务（前置门见 tasks.md）。
6. 禁clean/reset/stash clear/drop（298+31 untracked、staged2、stash1+2，一条即丢）；禁 `git clean` / `git reset --hard` / `git stash clear|drop`，任何清理/丢弃类操作一律禁止，确需清理另起 change 由主线程单点裁决。

## Impact Scope

- 仅约束远端/分支/tag/设置；不影响任何代码文件与实验输出。

## 7. B1 豁免名单（扩展冻结，主线程声明为准）

- 豁免性质：以下 4 项为 legacy 豁免（早于 20260906 声明），仅作 T2/T3 前置门（保护）“显式豁免声明”口径下的白名单引用，不改变 §4 设置清单与 §6 安全禁令，不新增推送授权。
- 豁免清单（追加冻结，共 4）：
  1. `codex/feat/polar-diagnostics-occupancy` 1b7055c（2026-04-15 unprotected）
  2. `feat/consolidate-cascade-single-kernel` df01f068（2026-08-30 unprotected）
  3. `project-restructure-20260427` 7d9a77f（2026-07-25 unprotected）
  4. `main` 6a58adb（2026-08-21 protected）
- 引用口径：push2未推4×false引用（推 2、未推 4、`×false` 引用口径）；上述 4 项均为 legacy，早于 20260906 声明，不视为 T2/T3 保护前置门 FAIL 事由。

## 8. H3 终态（冻结，PR#1 MERGED 为唯一有效描述）

- PR#1 描述口径：本 change 内 PR#1 的 OPEN/draft 描述全改为 MERGED；不存在有效的 OPEN/draft 描述，唯一有效描述为 MERGED。
- PR#1 终态：MERGED be6293893dbc47fc0b5e03147db8dd97c7e48ffe，mergedAt 2026-09-04T18:38:33Z，parents[ab58fe0,9b5793a]。
- 远端终态计数：Comparison heads 2+tag1；Release heads 9+tag2。
- 双 PRIVATE/main 绑定表（目标态冻结）：

| 远端仓库（目标） | 可见性 | 默认分支 | heads/tag 终态 |
|---|---|---|---|
| `Placebo303/HD-QKD-Polar-Release` | PRIVATE | `polar-mainline` | heads 9+tag2 |
| `Placebo303/HD-QKD-Polar-Comparison` | PRIVATE | `main` | heads 2+tag1 |

The counts in the preceding H3 table are the frozen planning target and are
not the post-execution state. `formal-ir-mainline` was explicitly transferred
to Comparison to preserve its only remote recovery ref before its Release ref
was deleted. The observed post-execution state is recorded below.

## Execution evidence (2026-09-05)

| Item | Observed result |
|---|---|
| Release metadata | PRIVATE; default `polar-mainline` |
| Comparison metadata | PRIVATE; default `main`; description set to the formal-IR/LDPC research-mainline description |
| Release heads | `codex/feat/polar-diagnostics-occupancy@1b7055c7f8f13e8cc50cc4adf6d4d89394c193c`, `codex/security-workbench-master-roadmap@546beb8d476db04d3301c6403e7f878873f46872`, `feat/consolidate-cascade-single-kernel@df01f0689ce08b33517c7d5dfc09db6c3171b060`, `main@6a58adbda0b20f8899f250f9471cd4f3fb915373`, `polar-mainline@be6293893dbc47fc0b5e03147db8dd97c7e48ffe`, `project-restructure-20260427@7d9a77f944fa9fccaa7afdd5fda333be018a2cd3`, `sync/polar-mainline-20260906@9b5793a35568149e476f8985a20d08108c861abb` |
| Comparison heads | `formal-ir-mainline@d7acfd28df80c5a1d5e22b4e77a3fa578105c25a`, `formal-ir-v72p1-addendum-clean@a393f83960c8434495fd0b43fb831dc7cf0442ce`, `main@ed0adfca7af1537f7808fbf5bdde83113479d235` |
| Release tags | `checkpoint-aggressive-line-20260827`, `polar-v1.0-aggressive-adaptive` |
| Comparison tags | `polar-v1.0-aggressive-adaptive` |
| Default protection | Both defaults report `allow_force_pushes.enabled=false` and `allow_deletions.enabled=false`; Release has PR review protection with 0 required approvals, Comparison has PR review protection with 1 required approval. |
| Legacy remotes | Fetch URL retained; push URL is `no_push://legacy-origin-disabled` in both checkouts. |

The Release security branch had a later local-only `4c79117` commit when the
post-check was read; the remote remains intentionally bound to the reviewed
and pushed `546beb8` until that new commit is separately reviewed. The
ambiguous `feat/consolidate-cascade-single-kernel` branch was not deleted.
