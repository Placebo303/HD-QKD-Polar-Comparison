# Tasks: repo-remote-decoupling

- Change: `repo-remote-decoupling`
- Execution state: `PARTIAL_COMPLETE`; remote split and named branch cleanup
  were executed on 2026-09-05. T4 tag selection and T7 archive were not
  executed.
- 执行约束：planner 只定任务，不执行；每任务由主线程显式授权后执行；任何前置门 FAIL 即停，不进入下一任务。
- 全局禁令：禁用 `push --all/--mirror/--tags（全量）`；禁止历史重写；禁clean/reset/stash clear/drop（298+31 untracked、staged2、stash1+2，一条即丢）；禁止碰 Release 工作树（除 T2 明确在 Release checkout 内由主线程授权执行外，
  Comparison 侧任务不得进入 `D:\Code\HD-QKD_Polar_Release`）。

## Goal

按 T0→T7 顺序完成远端解耦，每步可验收、可回滚。

## Non-Goals

- T0–T7 之外不加任务；历史重写、代码改动、数据迁移一律不在本 change 内做。
- 不执行任何decoder/benchmark长跑/run_01，T0-T7之外不加执行任务（Comparison HEAD a393f839 正处 R2 授权态，防误触发）。

---

### T0 只读核验与基线留痕（只读，无写操作）

- 前置门：本 change 三文件已存在；双 checkout `git status` 可读；GitHub 当前远端 URL/默认分支已知。
- 动作（只读）：记录双 checkout `HEAD`、`git branch -a`、`git tag --list`、
  `git remote -v`、`git config --get-regexp 'remote\..*'`（检查无 `mirror=true`）；
  确认专属分支 SHA（`codex/security-workbench-master-roadmap@6f40e54`、
  `formal-ir-v72p1-addendum-clean`）与默认分支指向。
- 动作（只读，R4 快照）：默认分支快照（gh repo view --json defaultBranchRef或截图，双仓各一份）与可见性快照（private 证明截图/记录，双仓各一份），记入 manifest（含 head_full_sha 与 `git status --porcelain` 计数）。
- 验收：基线快照文本交主线程保管；发现任一远端已混入对方专属分支 → 阻塞即停，报主线程。
- 阻塞即停：任一命令返回非预期错误（贴 exact error），或快照缺失，停止，不进入 T1。
- 冻结句：T1完成前禁止一切push（T0→T1 之间任何 push 一律禁止，违者即停待裁决）。

### T1 GitHub 建仓与改名准备（授权窗口，design §1）

- 前置门：T0 快照完整；主线程书面确认目标名 `HD-QKD-Polar-Release` / `HD-QKD-Polar-Comparison` 与 D1=A（原仓复用 + 新仓新建、双 private）。
- 动作：新建空 private 仓 `HD-QKD-Polar-Comparison`；原仓改名HD-QKD-Polar-Release（推荐，保留redirect）（二选一已点名：改名优先，URL 复用仅为备选，需主线程书面改判）；记录改名前原名以备回滚（design §5）。
- 动作（legacy-origin 更名审计链，必做）：`git remote rename origin legacy-origin` → `git remote add origin <自家新URL>` → `git remote -v` 复核（`origin` 仅指向自家新 URL，`legacy-origin` 指向原 URL）→ `git config --get-regexp 'remote\..*'` 查无 `mirror=true`/多余 pushurl → `git ls-remote <新origin>` 验空（空仓预期无 ref）并存原文 + exit code；`legacy-origin` 审计残留必须保留，禁止删除/覆盖。
- 动作（改名后验证）：redirect验证+remote -v复核+旧URL grep清单（旧 URL 可跳转新仓；`git remote -v` 指向新仓 URL；`HD-QKD-Polar-pipeline` 残留引用逐项列出，无遗漏才继续）。
- 验收：双仓均为 private；URL 与 design §1 布局表一致。
- 阻塞即停：建仓/改名任一步失败、无备份记录、或可见性非 private → 即停，需主线程单点决策。

### T2 Release 侧收敛（在 Release checkout 内执行，默认分支 `polar-mainline`）

- 前置门：T1 双仓就绪；T0 回滚点有效；当前 checkout 经核对确为 Release（`remote -v` 指向 Release URL）。
- 前置门三件套：(a)git rev-parse HEAD==manifest head_full_sha；(b)git ls-remote <新origin> <待推ref>必须不存在否则停待裁决；(c)git status --porcelain计数与manifest一致否则重快照。
- 前置门（保护）：默认分支保护已在首次 push 前开启，或在本前置门中显式豁免声明（无开启且无豁免不得 push）。
- 首步断言：Release=D:\Code\HD-QKD_Polar_Release（`git rev-parse --show-toplevel` 必须为此路径，否则即停）。
- 动作：确认默认分支为 `polar-mainline`；切换顺序：T2 先将 Release 默认分支切为 `polar-mainline` 并验证通过后，才进入 T3；两次切换不得并行；确认专属分支
  `codex/security-workbench-master-roadmap@6f40e54` 存在且仅属 Release；
  确认 Comparison 研究分支/`formal-ir-*` 不存在于 Release 远端；按主线程点名逐个推送/保护分支（禁止 `--all`/`--mirror`）。
- 动作（推送粒度）：分支推送一律用精确模板git push <remote> <local>:refs/heads/<branch>（与 T4 tag 粒度对齐），禁push :通配符删除；每次push前后fetch+branch -vv核对（每次 push 前后 `fetch` + `branch -vv` 核对）。
- 验收：Release 远端分支列表 = 白名单（`polar-mainline` + 点名保留分支），无研究分支混入。
- 阻塞即停：远端出现对方专属分支、或误推研究内容、或任何 push 报错 → 即停，需主线程决策；禁止 force-push 修复。

### T3 Comparison 侧收敛（在 Comparison checkout 内执行，默认分支 `main`）

- 前置门：T1 双仓就绪；T0 回滚点有效；当前 checkout 经核对确为 Comparison
 （`remote -v` 指向 Comparison URL，即 `D:\Code\HD-QKD_Polar_Comparison`）。
- 前置门三件套：(a)git rev-parse HEAD==manifest head_full_sha；(b)git ls-remote <新origin> <待推ref>必须不存在否则停待裁决；(c)git status --porcelain计数与manifest一致否则重快照。
- 前置门（保护）：默认分支保护已在首次 push 前开启，或在本前置门中显式豁免声明（无开启且无豁免不得 push）。
- 首步断言：Comparison=D:\Code\HD-QKD_Polar_Comparison（`git rev-parse --show-toplevel` 必须为此路径，否则即停）。
- 动作：确认默认分支为 `main`；切换顺序：承接 T2，后确认 Comparison 默认分支为 `main`（T2→T3 顺序，两次切换不得并行）；确认专属分支 `formal-ir-v72p1-addendum-clean` 存在且仅属 Comparison；
  确认 `polar-mainline`/`codex/*` 不存在于 Comparison 远端；按主线程点名逐个推送/保护分支（禁止 `--all`/`--mirror`）。
- 动作（空仓首推专线，仅 Comparison 空仓）：`gh repo view --json defaultBranchRef` 确认 `defaultBranchRef` 为空即空仓 → 先单推 `main`（精确模板）→ `gh repo edit --default-branch main` 设默认 `main` → 开保护（或沿用前置门书面豁免）→ 再按白名单逐个推其余分支；非空仓走常规收敛流程，不得套用本专线。
- 动作（推送粒度）：分支推送一律用精确模板git push <remote> <local>:refs/heads/<branch>（与 T4 tag 粒度对齐），禁push :通配符删除；每次push前后fetch+branch -vv核对（每次 push 前后 `fetch` + `branch -vv` 核对）。
- 验收：Comparison 远端分支列表 = 白名单（`main` + 点名保留研究分支），无 Polar 专属分支混入。
- 阻塞即停：远端出现对方专属分支、或 `main` 被 sweep 污染、或任何 push 报错 → 即停，需主线程决策。

### T4 Tag 精选推送（B 方案，逐个显式推送）

- 前置门：T2/T3 分支收敛完成且分支列表已冻结；主线程书面点名精选 tag 清单（逐个列出归属远端）。
- 前置门三件套：(a)git rev-parse HEAD==manifest head_full_sha；(b)git ls-remote <新origin> <待推ref>必须不存在否则停待裁决；(c)git status --porcelain计数与manifest一致否则重快照。
- 动作：对清单中每个 tag 执行 `git push <remote> refs/tags/<tag>:refs/tags/<tag>`（一次一个）；
  推送前后核对本地/远端 tag 列表数量一致；研究 tag 不进 Release，Polar 里程碑 tag 不进 Comparison。
- 验收：远端 tag 集合 == 点名清单；`git push --tags` 全程未使用。
- 阻塞即停：清单外 tag 被推送、数量不一致、或任一 tag push 报错 → 即停，需主线程单点决策；删除误推 tag 需另行单点授权。

### T5 GitHub 设置锁定（design §4 清单逐项打勾）

- 前置门：T2–T4 完成；双远端分支/tag 已冻结。
- 动作：落实 private、默认分支、分支保护（禁 force-push/deletion）、权限最小化、secrets 不互拷；
  复核双 checkout `remote -v` 与 `remote.*.mirror` 无残留 mirror 配置。
- 验收：§4 清单全部勾选并记录（截图/文本）；§4.1 不迁移验收：原仓 Issue/PR/Wiki/Projects/Releases/Actions/Secrets 均不迁移不互拷（Secrets 不复制按需重建、Actions 不继承），Comparison 按需新建且有逐项记录；双 checkout `git status` 干净（除本 change 文件外）。
- 阻塞即停：任一设置项不符合 → 即停，需主线程决策；不得以后补设置名义继续推送。

### T6 历史重写声明（本 change 内不做，另起 change）

- 前置门：T0–T5 任一步完成或阻塞均可进入声明（本任务为文档性）。
- 声明：如需清理已发生的 2026-08-12..22 crosstalk 历史、或做 filter-repo/BFG、或删除远端历史分支，
  必须另起新的 OpenSpec change（另行 proposal/design/tasks + 主线程授权），不得在本 change 内执行；
  本 change 交付时历史保持原样，只保证未来不再串扰。
- 验收：本声明写入 decision-log（如主线程要求）或至少保留在本 tasks.md；无任何重写命令被执行。
- 阻塞即停：如有人提出在本 change 内顺手重写 → 拒绝并即停，需主线程另起 change 决策。

### T7 Archive（归档条件，含 memory triage）

- 前置门：T0–T6 全部达到各自验收；design §4 清单全勾；无未解决的阻塞；`git status` 证明除本 change 三文件外无其他文件改动，或已逐项记录。
- 动作：执行 `/opsx-archive repo-remote-decoupling` 前由 memory agent 做 memory triage
 （是否在 `AGENT_PROJECT_MEMORY.md` 追加远端解耦记录由 triage 决定，本 Turn 不写）；
  归档时确认分支归属矩阵与回滚点记录已交主线程保管。
- 验收（全部满足才可 archive）：
  1. T0–T5 证据齐全（快照、分支/tag 白名单、设置清单）。
  2. T6 另起-change 声明有效，无历史重写发生。
  3. memory triage 已执行。
  4. 本 change 仅含三文件，无其他文件改动声明成立（`git status` 口径：除本 change 三文件外无未提交改动，或已逐项记录）。
- 阻塞即停：任一归档条件不满足 → 不 archive，保持 change 开放并报主线程。

## 附录 B1 豁免名单（扩展冻结，主线程声明为准）

- 豁免性质：以下 4 项为 legacy 豁免（早于 20260906 声明），仅作 T2/T3 前置门（保护）“显式豁免声明”口径下的白名单引用，不改变 T0–T7 验收口径，不新增推送授权。
- 豁免清单（追加冻结，共 4）：
  1. `codex/feat/polar-diagnostics-occupancy` 1b7055c（2026-04-15 unprotected）
  2. `feat/consolidate-cascade-single-kernel` df01f068（2026-08-30 unprotected）
  3. `project-restructure-20260427` 7d9a77f（2026-07-25 unprotected）
  4. `main` 6a58adb（2026-08-21 protected）
- 引用口径：push2未推4×false引用（推 2、未推 4、`×false` 引用口径）；上述 4 项均为 legacy，早于 20260906 声明，不视为 T2/T3 保护前置门 FAIL 事由。

## 附录 H3 终态（冻结，PR#1 MERGED 为唯一有效描述）

- PR#1 描述口径：本 change 内 PR#1 的 OPEN/draft 描述全改为 MERGED；不存在有效的 OPEN/draft 描述，唯一有效描述为 MERGED。
- PR#1 终态：MERGED be6293893dbc47fc0b5e03147db8dd97c7e48ffe，mergedAt 2026-09-04T18:38:33Z，parents[ab58fe0,9b5793a]。
- 远端终态计数：Comparison heads 2+tag1；Release heads 9+tag2。
- 双 PRIVATE/main 绑定表（目标态冻结）：

| 远端仓库（目标） | 可见性 | 默认分支 | heads/tag 终态 |
|---|---|---|---|
| `Placebo303/HD-QKD-Polar-Release` | PRIVATE | `polar-mainline` | heads 9+tag2 |
| `Placebo303/HD-QKD-Polar-Comparison` | PRIVATE | `main` | heads 2+tag1 |

The H3 table above is a frozen pre-execution target. It is not a claim about
the current remote state: `formal-ir-mainline` was transferred to Comparison
because it had no corresponding recoverable ref on the new Comparison remote.

## Execution evidence (2026-09-05)

| Task | Status | Evidence / remaining boundary |
|---|---|---|
| T0 | COMPLETED | Baseline snapshot saved outside the repository; exact SHA, heads, tags, metadata, protection, and dirty-status outputs were captured before writes. |
| T1 | OBSERVED_COMPLETE | The two private repositories and separated origins already existed before this operator task. No repository was recreated or made public. |
| T2 | PARTIAL_COMPLETE | Release default changed to `polar-mainline`; reviewed security branch pushed at `546beb8`; named `formal-ir-mainline` and `formal-ir-v72p1-addendum-clean` refs deleted after recovery verification. The later local-only `4c79117` was not pushed. Ambiguous `feat/consolidate-cascade-single-kernel` retained. |
| T3 | COMPLETED_FOR_NAMED_REFS | Comparison `main` remained default; `formal-ir-mainline` was transferred at `d7acfd28`; `formal-ir-v72p1-addendum-clean` was retained from base `a393f839` and then received this evidence-only commit; current named branch upstreams point to Comparison `origin`. |
| T4 | NOT_EXECUTED | No tag was pushed; existing remote tags were preserved. A tag whitelist still requires main-thread selection. |
| T5 | COMPLETED_FOR_TARGETED_SETTINGS | Defaults are private and correctly named; default branch protection reports force-push and deletion disabled; Comparison description was added. Collaborator/secrets/Actions migration was not performed or inferred. |
| T6 | COMPLETED | No history rewrite, force push, mirror push, `--all`, cleanup, or destructive stash/reset command was used. |
| T7 | BLOCKED / NOT_ELIGIBLE | Dirty Comparison worktree, uncommitted evidence files, pending local `4c79117`, no tag selection, and no memory-triage handoff remain. Do not archive. |

The active Release security branch currently tracks Release `origin` but is
one local commit ahead because of the separately created `4c79117`; this is a
review/push decision for the main thread, not an automatic follow-up here.
