# Paste-ready prompt — D5-P0-EXECUTE-R3 (REAL EXECUTION)

Sending this IS the authorization act. Paste only when you have decided to
authorize P0.

Prerequisites, both already met as of `299416ae`:
- the Model-F consumer path fix has landed;
- `LOADER_FIX_REVIEW_R1` returned `LOADER_FIX_REVIEW_PASS`.

Open a fresh session in `D:/Code/HD-QKD_Polar_Comparison`.

=====

我现在明确授权执行 P0（第二次授权，与 2026-09-07 那次已消耗的授权无关）：
**授权对冻结的 p0-cost 命令进行且仅进行一次调用，授权由"尝试"消耗而非由"成功"
消耗；不许重试、不许重跑、不许改任何参数，不许碰 G1 和 G2。**

要读两个文件，**修订件优先**：
- 修订件：`D:/Code/HD-QKD_Polar_Comparison/.workbuddy/tasks/D5_P0_EXECUTE_R3_AMENDMENT.md`
- 主包：`D:/Code/HD-QKD_Polar_Comparison/.workbuddy/tasks/D5_P0_EXECUTE_R2_TASK_PACKET.md`

先完整读完修订件，再读主包。主包除被修订件明确取代的两处外全部有效。**不要用
`D5_P0_EXECUTE_R1_TASK_PACKET.md`。**

上面那句授权就是主包 §0.1 要求你持有的显式授权，逐字抄进报告和授权记录。

GATE ZERO 两条前提已满足（修复已落地 `299416ae`、复审 PASS），你仍需自己确认一眼。

**修订件取代了两处，务必按新版执行：**

1. **STEP 2' 可达性探针**——原版有缺陷：用 `python -c` 从仓库根跑，`sys.path[0]`
   就是仓库根，那个压垮 R1 的包导入本来就会成功，探针根本不可能失败。复审那次更
   直接把仓库根插进了 `sys.path`。**都不算数。**
   新版要求把探针写成**仓库之外**的脚本文件再跑，工作目录仍是仓库根，这样
   `sys.path[0]` 是脚本目录、仓库根不在 `sys.path` 上。**不许插 `sys.path`，
   不许用 `python -c`。**
   五个条件全中才算过：`repo_root_on_sys_path= False`、
   `package_import_available= False ModuleNotFoundError`、
   `REACH_OK REACHED_FIRST_DECODER_CALL probe_calls 1`、`tmp_contents []`、
   `p0_root False g2_root False`。
   其中 `package_import_available` 若打印 `True`，说明**探针本身无效**——去修启动
   条件重跑，**不许改代码**，也不许就这么往下走。
   `REACH_FAIL` → STOP，不翻任何位，原样贴 traceback。此时零授权消耗，这就是这步
   存在的意义。修订件里写了作者当时拿到的结果，**你要自己复现，不许引用作者的**。

2. **E6' 清洁度门禁**——原版要求"干净跟踪树"，现在过不了也不该要求它过。仓库在
   17:22:29 被批量改了 mtime，`git status` 报约 1887 个 `M`，但按内容比对
   **零差异**，纯行尾表示问题，复审判为化妆品、不阻塞。新判据是
   `git diff --numstat` 统计出的 `files_with_content_change: 0`。那个 1887 只作
   信息记录，**不许去降低它**：`git checkout`、`git add --renormalize`、
   `git clean`、`git reset` 一律禁止。仓库侧行尾规范化是另一件事，不是 P0 前置。

其余全部按主包 R2 执行，重点重申：

- STEP 1 的 E1–E5 新鲜证据不能省（旧 session 的不算数），测试任何失败就 STOP
  （`test_T1_22_openspec_history_zero_mod` 因行尾问题常红，属已知且不阻塞，
  但**除它以外**的任何失败都是 STOP）。
- watchdog 演练期望 `exit=124`，拿不到就不许跑。
- **只跑一次**，无论 exit 0/124/3/其它都直接进 STEP 6，不许重试、不许换根、
  不许改参数。
- 跑完**立刻**把 `p0_cost_execution_authorized` 翻回 `false`，先于任何分析与写作。
- 失败产物原地保留，`workspace/` 下不许删/移/改名/覆盖/规范化/算 hash。
- 授权记录要按修订件 A.4 额外收录：STEP 2' 原文（含那两行条件）、E6' 的内容差异
  计数与信息性原始计数、以及"复审 PASS 但其探针带仓库根在 `sys.path` 上、对脚本
  启动不具结论性，已由 STEP 2' 取代"这一句。
- `P0_EXECUTION_PACKET_ADDENDUM_A1.md` 是**附录不是修改**，冻结件保持逐字节不变。
- 不许改任何 `.py`（**包括探针失败的情况——你只报告，不修**）；不许读
  CAL/VAL/parquet 行；不许 `git push` 或 `add -A`/`add .`/`commit -a`/`amend`；
  两次提交按路径白名单逐条 `git add`，提交前 `git diff --cached --name-only` 核对。
- 不许解读结果。P0 只量成本，不许说 FER、泄漏、密钥率、不许说"方法可行"、
  不许授权或提议 G1/G2。

最后按主包 STEP 8 汇报，其中**必须原样贴出 STEP 2' 的全部输出**，并写明 E6' 结果。
结尾写：

**P0 已执行一次，授权已消耗。结果只是记录，不是接受。未作任何结论。接受需要
独立 Pre-RESULT 复审；G1 仍未授权。**

=====
