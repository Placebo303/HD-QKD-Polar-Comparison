# H0.3 — 外源隔离（exogenous-source isolation）

- **任务包**：H0.3，IDs `H03-1..4`
- **轨道**：docs / 工程卫生，**无 track gate**（AGENTS §1.2 应用矩阵：文档与实现性卫生项）
- **授权边界**：仅编辑 `.gitignore` + 新建本文件；**不授权**解码、DE、真实数据、commit、push、qualification
- **分支 / HEAD**：`formal-ir-v72p1-addendum-clean` @ `051e3687`
- **上游计划**：`docs/EXECUTION_PLAN_20260922.md` 轨 H 行 **H0.3**，风险行 **E6**（外源 `binary-ldpc-v5-*` 混入 commit → 姊妹线 crosstalk 重演，缓解 = H0.3 + H0.1 scoped manifest）

---

## 1. 四根排除清单（4-root exclusion list）

`.gitignore` 追加的四条根级排除（幂等；已存在即不重复追加）：

| # | 根路径（仓库相对） | H0.3 重测时状态 | 处置 |
|---|---|---|---|
| 1 | `/.codebuddy/` | untracked（`??`） | gitignore 排除，不 add、不 move、不 delete |
| 2 | `/.workbuddy/memory/2026-09-21.md` | untracked（`??`） | gitignore 排除，按**单文件**精确匹配（见 §1.1） |
| 3 | `/openspec/changes/binary-ldpc-v5-audit-remediation-plan/` | untracked（`??`） | gitignore 排除，不 move、不 delete |
| 4 | `/openspec/changes/binary-ldpc-v5-transfer-to-qrl/` | untracked（`??`） | gitignore 排除，不 move、不 delete |

重测（H03-1）命令输出摘要：

```text
$ git status --porcelain
?? .codebuddy/
?? .workbuddy/memory/2026-09-21.md
?? openspec/changes/binary-ldpc-v5-audit-remediation-plan/
?? openspec/changes/binary-ldpc-v5-transfer-to-qrl/

$ ls openspec/changes | grep binary-ldpc-v5
binary-ldpc-v5-audit-remediation-plan
binary-ldpc-v5-incremental-redundancy          <- tracked，历史遗留（§2）
binary-ldpc-v5-transfer-to-qrl
```

`cat .gitignore`（H03-1）确认四根均**不在**原 `.gitignore` 中 → 追加为非重复操作；H03-2 后复跑 grep 每条仅出现一次。

### 1.1 排除语义的两点说明

- `.workbuddy/` 目录下**已有 tracked 文件**（如 `.workbuddy/memory/2026-09-02.md`、`2026-09-09.md`、`.workbuddy/tasks/*`）。因此只排除**具体那一份** untracked 的 `2026-09-21.md`，不写 `/.workbuddy/` 整根，以免掩盖既有 tracked 内容的变更可见性。
- gitignore 对 tracked 文件无效力；上述四条只作用于当前 untracked 的外源内容，属"防止误 `git add`"的机械护栏，不构成对任何 tracked 文件的移动或删除。

---

## 2. 历史遗留 tracked 说明（不属本次隔离范围）

| 路径 | tracked 状态 | 处置 |
|---|---|---|
| `openspec/changes/binary-ldpc-v5-incremental-redundancy/` | **tracked**（18 文件：`proposal.md`、`tasks.md`、`phase1..4-*contract.md` 等） | **不动**。既不加 gitignore（对 tracked 无效），也不 move / delete / untrack |

该目录是历史遗留的已提交内容，**不属于** H0.3 的四根 untracked 反列。对其任何改动都需要独立授权与独立 review，本任务包明确排除。

---

## 3. 本线 commit 范围文档化（scope of the formal-IR line）

本线（`formal-ir-v72p1-addendum-clean`）允许进入 commit 的范围：

- 允许：`src/`、`experiments/`、`tools/`、`results/`（只读证据）、`comparison_bench/`、`docs/`、`openspec/`（**仅本线** change）、`AGENT_PROJECT_MEMORY.md`、`AGENTS.md`、`README.md`、根配置文件。
- 禁止混入：§1 的四根；以及任何姊妹 Polar 线 / 外源 `binary-ldpc-v5-audit-remediation-plan`、`binary-ldpc-v5-transfer-to-qrl` 内容。
- §2 的 tracked 遗留目录按现状保留，不作为本线"新内容"来源。

**本任务包（H0.3）产生的 dirty 文件，完整清单：**

```text
M  .gitignore                 <- 追加四根排除（+ 注释块）
?? docs/H0_3_ISOLATION.md     <- 本文件（新建）
```

除此之外不应出现任何 dirty / untracked 变化；`src/`、`experiments/`、`tools/` 的 diff 必须为空（见 §4）。
本文件**不**代为 commit / push —— commit 需 H0.1 式显式授权。

---

## 4. H0.1 scoped manifest 引用

H0.3 的姊妹门是 **H0.1 scoped manifest**（`docs/EXECUTION_PLAN_20260922.md` 行 H0.1 与风险行 E6）：

- H0.1 已执行的 scoped 提交为 **`051e3687`**（"hygiene: H0.1 commit X1 scoped tree + F1 fix + G0=B log"）。
- 该 commit 的 scoped 文件树（即 H0.1 manifest 的实际内容，15 files / +2855 −1）：

  ```text
  AGENT_PROJECT_MEMORY.md
  comparison_bench/src/comparison_bench/cli/x1_arm_runner.py
  comparison_bench/src/comparison_bench/cli/x1_bundle_build.py
  comparison_bench/tests/test_x1_arm_runner.py
  comparison_bench/tests/test_x1_bundle_build.py
  docs/EXECUTION_PLAN_20260922.md
  docs/V80_BASELINE_20260921.md
  docs/decision-log.md
  docs/research_cycles/V80-NBLDPC-JAN21/X1_BATCH_END_REVIEW.md
  docs/research_cycles/V80-NBLDPC-JAN21/X1_EXPLORATION_LOG.md
  docs/research_cycles/V80-NBLDPC-JAN21/X1_INDEPENDENT_ACCEPTANCE.md
  docs/research_cycles/V80-NBLDPC-JAN21/X1_SUCCESSOR_ENTRY_PACKET.md
  docs/research_cycles/V80-NBLDPC-JAN21/X1_SUCCESSOR_ENTRY_PREEXEC.md
  docs/research_cycles/V80-NBLDPC-JAN21/X1_SUCCESSOR_ENTRY_PREREG_AND_AUTH.md
  docs/research_cycles/V80-NBLDPC-JAN21/X1_SUCCESSOR_ENTRY_PROMPT.md
  ```

- 验收条件（H0.1 行原文）：工作区对本线文件 clean；**`binary-ldpc-v5-*` 不在 diff 内**。
  H0.1 的实测：上述 15 文件中**无**任何 `binary-ldpc-v5-*` 路径 → 该验收条件满足；
  §1 四根在 `051e3687` 时全部 untracked、未入 diff。
- **复核命令**（供后续 review 直接重跑）：

  ```bash
  git show --stat --oneline 051e3687 | grep -c binary-ldpc-v5   # 期望 0
  git diff --name-only 051e3687^ 051e3687 | grep binary-ldpc-v5 # 期望无输出
  ```

- 计划文件本身（`docs/EXECUTION_PLAN_20260922.md`）为 H0.1/H0.3 的权威上游；本文件不修改它。

---

## 5. H0.3 自检结果（H03-4）

```text
$ git status --porcelain
 M .gitignore
?? docs/H0_3_ISOLATION.md
(四根经 gitignore 后不再显示为 untracked)

$ git diff -- src/ experiments/ tools/
(空)

$ git diff -- .gitignore
(仅追加 H0.3 注释块 + 4 行根排除)

$ git check-ignore -v <四根各一路径>        # 四条均命中 .gitignore:45-48
$ git check-ignore -v <incremental-redundancy/…> <.workbuddy 已tracked两文件>
                                            # exit=1，均未被忽略（正确）
$ git status --porcelain -- src/ experiments/ tools/ results/ \
      comparison_bench/outputs_comparison/ workspace/
                                            # 无输出
```

**并发观察（非本任务包产物，未触碰）**：自 H03-1 重测（20:39 前）至 H03-4 自检（20:41）
期间，仓库出现并行会话的改动 —— `M docs/EXECUTION_PLAN_20260922.md`（+2/−2，
H0.1 行 SHA 句与 P5-gate 表述）、`?? docs/NOW.md`、`?? docs/H0_4_INTERPRETER.md`。
三者均**不在** H0.3 允许清单内，由 H0.4/H0.5 或主线程持有；本任务包**既未创建也未修改**，
按 scope 规则原样保留，不在本文件的 dirty 清单内。

**结论**：本任务包 dirty 集合 = `.gitignore` + `docs/H0_3_ISOLATION.md`，符合冻结包允许范围；
另有上述并行会话产物（见"并发观察"），不属本任务包；未执行 commit/push，未触碰 `src/ experiments/ tools/ results/ comparison_bench/outputs_comparison/ workspace/`，未 move/delete 任何 tracked 文件，未修改 `docs/EXECUTION_PLAN_20260922.md`、`docs/NOW.md`、`README.md`、`AGENTS.md`、decision-log/memory。
