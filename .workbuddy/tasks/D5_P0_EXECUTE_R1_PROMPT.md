# Paste-ready prompt — D5-P0-EXECUTE-R1 (REAL EXECUTION, use only after authorizing)

Do not paste this until you have decided to authorize P0. The prompt contains
the authorization sentence the executor will quote and act on; sending it IS
the authorization act.

Open a fresh session in `D:/Code/HD-QKD_Polar_Comparison` and paste everything
between the two `=====` lines.

=====

我现在明确授权执行 P0：**授权对冻结的 p0-cost 命令进行且仅进行一次调用，
授权由"尝试"消耗而非由"成功"消耗；不许重试、不许重跑、不许改任何参数，
不许碰 G1 和 G2。**

任务包全文在：
`D:/Code/HD-QKD_Polar_Comparison/.workbuddy/tasks/D5_P0_EXECUTE_R1_TASK_PACKET.md`

先完整读完，再按 STEP 1 → STEP 7 顺序执行。上面那句授权就是任务包 §0 要求你
持有的显式授权，把它逐字抄进报告和 STEP 3 的授权记录里。

这是本轮第一个**真正跑 decoder** 的任务包，注意以下几条：

1. **STEP 1 的新鲜证据不能省。** Pre-EXECUTE 评审裁定（OQ-P0-4）隔离证据会
   过期，必须在翻转授权位之前、在你自己这个 session 里重新跑一遍 E1-E6。
   引用别的 session 的结果不算数。E4 任何一个测试失败就 STOP。
2. **STEP 2 的 watchdog 演练不能省**（OQ-P0-2），期望 `exit=124`。拿不到
   工作正常的守卫就不许跑 P0。
3. **只跑一次。** 无论 exit 0 / 124 / 3 / 其它，都直接进 STEP 5，不许重试、
   不许换根、不许改参数。授权被"尝试"消耗（OQ-P0-5）。
4. **跑完立刻把 `p0_cost_execution_authorized` 翻回 `false`**，在做任何分析、
   写任何文档之前先翻回去。
5. **失败产物原地保留。** 无论是部分输出还是崩溃残留，`workspace/` 下一律不许
   删除、移动、改名、覆盖、规范化、算 hash。
6. **不许解读结果。** P0 只量成本。不许说 FER、泄漏、密钥率、不许说"方法可行"、
   不许授权或提议 G1/G2、不许推广。你只负责如实记录数字。
7. 除 `p0_cost_execution_authorized` 的两次翻转外，不许改 `cycle_state.yaml`
   任何其它值，`next_gate` 保持 `P0_PACKET_REVIEW`。
8. 不许改任何 `.py`。跑出来暴露了代码缺陷就记录并停止，不要顺手修。
9. 不许 `git push`、`git add -A`、`git add .`、`git commit -a`、`reset`、
   `stash`、`checkout --`、`clean`、`rebase`、`commit --amend`。两次提交都按
   任务包给的路径白名单逐条 `git add`，提交前用 `git diff --cached --name-only`
   核对。
10. 不许读 CAL/VAL/原始 parquet 行；运行本身只通过代码自己的路径读已接受的
    Model-F 产物。

任何门禁不过就 STOP，报步骤号和原始输出，不要自行修复、不要绕过。

最后按 STEP 7 逐项汇报，包括你引用的授权原话、E1-E6、watchdog 演练码、运行
命令与 exit code、wall、stdout/stderr、输出根清单、全部成本标量、1440s 上限
比对与是否 `RESOURCE_OVERRUN`、峰值 RSS、两个 commit SHA、true/false 清单，
以及最后这一句：

**P0 已执行一次，授权已消耗。结果只是记录，不是接受。未作任何结论。接受需要
独立 Pre-RESULT 复审；G1 仍未授权。**

不要提议 G1，不要解读数字，不要判断方法是否可行。

=====
