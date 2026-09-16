# Paste-ready prompt — D5-P0-EXECUTE-R2 (REAL EXECUTION, use only after the fix lands and is reviewed)

Do not paste this until BOTH hold:
1. `D5_P0_LOADER_FIX_R1` has landed on the branch, and
2. it has passed an independent review.

The prompt contains the authorization sentence the executor will act on;
sending it IS the authorization act.

=====

我现在明确授权执行 P0（第二次授权，与 2026-09-07 那次已消耗的授权无关）：
**授权对冻结的 p0-cost 命令进行且仅进行一次调用，授权由"尝试"消耗而非由
"成功"消耗；不许重试、不许重跑、不许改任何参数，不许碰 G1 和 G2。**

任务包全文在：
`D:/Code/HD-QKD_Polar_Comparison/.workbuddy/tasks/D5_P0_EXECUTE_R2_TASK_PACKET.md`
（它整体取代 R1，**不要用 R1**）

先完整读完，再按 GATE ZERO → STEP 8 顺序执行。上面那句授权就是任务包 §0.1 要求
你持有的显式授权，逐字抄进报告和 STEP 4 的授权记录。

**GATE ZERO 先查**：Model-F 消费侧路径修复（`D5_P0_LOADER_FIX_R1`）是否已经落到
本分支，且是否已通过独立复审。两者缺一就 STOP。**不许"先跑一次看看现在行不行"**
——那正好会再废掉一次授权，这是 R1 的教训。

**R2 相对 R1 新增的核心是 STEP 2 可达性前置，绝对不许跳过或简化：**

在翻任何授权位**之前**，直接调用 `run_p0_cost_synthetic`（不走 CLI，所以不需要
授权），同时满足三个条件：`authorized=True`、显式 `out_dir` 指向正式根之外的全新
tmp 目录、以及一个**首次调用即抛出唯一哨兵异常的 probe decoder**。期望结果是
`REACH_OK REACHED_FIRST_DECODER_CALL probe_calls 1` 且 tmp 目录为空。

- 拿到 `REACH_FAIL` → 授权路径仍然够不到 decoder。**STOP，不许翻任何位，
  原样贴出异常和 traceback。** 此时一次授权都没被消耗，这就是这一步存在的全部
  意义。
- 拿到 `REACH_UNEXPECTED_COMPLETION` → probe 从未被调用，说明结构有问题，
  同样 STOP。

这一步会真读一次已接受的 Model-F 产物——**这是有意为之**，它正是整条链上从没被
任何测试覆盖过的那一步（测试要么注入表要么 monkeypatch 根）。它是操作员前置检查，
不是测试；必须只读，必须用 tmp 输出根，跑完要确认 P0/G2 正式根仍不存在、Model-F
根仍是 2 个文件且大小 mtime 未变。

其余要点：

1. STEP 1 的 E1–E6 新鲜证据不能省（OQ-P0-4，旧 session 的证据不算数），E4 任何
   测试失败就 STOP。
2. STEP 3 watchdog 演练期望 `exit=124`，拿不到工作正常的守卫就不许跑。
3. **只跑一次。** 无论 exit 0 / 124 / 3 / 其它都直接进 STEP 6，不许重试、不许换根、
   不许改参数。
4. 跑完**立刻**把 `p0_cost_execution_authorized` 翻回 `false`，先于任何分析和写作。
5. 失败产物原地保留，`workspace/` 下一律不许删/移/改名/覆盖/规范化/算 hash。
6. STEP 4 要写的 `P0_EXECUTION_PACKET_ADDENDUM_A1.md` 是**附录，不是修改**——
   冻结的 `P0_EXECUTION_PACKET.md` 必须保持逐字节不变。
7. 不许解读结果。P0 只量成本。不许说 FER、泄漏、密钥率、不许说"方法可行"、
   不许授权或提议 G1/G2。
8. 不许改任何 `.py`；**包括 STEP 2 探针失败的情况——你只报告，不修**。
9. 不许 `git push`、`add -A`、`add .`、`commit -a`、`reset`、`stash`、
   `checkout --`、`clean`、`rebase`、`commit --amend`。两次提交按路径白名单逐条
   `git add`，提交前用 `git diff --cached --name-only` 核对。
10. 不许读 CAL/VAL/原始 parquet 行。

任何门禁不过就 STOP，报步骤号和原始输出，不要自行修复、不要绕过。

最后按 STEP 8 逐项汇报，其中第 3 项**必须原样贴出 STEP 2 可达性结果**。结尾写：

**P0 已执行一次，授权已消耗。结果只是记录，不是接受。未作任何结论。接受需要
独立 Pre-RESULT 复审；G1 仍未授权。**

=====
