# Paste-ready prompt — D5-DISPO-R1 resume after amendments A2 + A3

Copy everything between the two `=====` lines into the executing session.

=====

裁决已下：**放行。** 你两次 STOP 都是对的，两次都是任务包作者的门禁写错。

作者已把 STEP 6 / STEP 7 全部重审一遍，又找出 5 处同类缺陷（其中 2 处会让你必然
再次假 STOP），已在修订件 A3 中修好。

按顺序读这三个文件，再执行：
- `D:/Code/HD-QKD_Polar_Comparison/.workbuddy/tasks/D5_DISPO_R1_AMENDMENT_A3.md`（最新，优先级最高）
- `D:/Code/HD-QKD_Polar_Comparison/.workbuddy/tasks/D5_DISPO_R1_AMENDMENT_A2.md`
- `D:/Code/HD-QKD_Polar_Comparison/.workbuddy/tasks/D5_DISPO_R1_TASK_PACKET.md`（原包，A1 同目录）

原任务包与 A1/A2 除被 A3 明确取代的部分外全部继续有效，包括第 0 节全部 11 条
硬禁令。

已冻结的裁决（不要再质疑、不要再调查、不要重跑）：

1. **G03 = PASS**（A2.1，作者已用你 STEP 1 报告逐条比对）。不要重跑，不要再找
   STEP 1 字面值。
2. **G01/G02/G04/G05'/G06' 已通过或按 A2.4 不必重跑。** STEP 1-4 不要重做、不要
   重新编辑那三个 delta。
3. **commit 3 会暂存 20 个文件，这是正确的，不是越界**（A3.2 有逐条清单：你产出
   3 个 + 既有已修改 6 个 + 既有未跟踪 cycle 文档 11 个）。不要排除、不要拆分、
   不要 unstage。
4. **G07 判据已改**：白名单里的**目录**覆盖其下全部文件。用 A3.1 的 G07' 脚本
   判定，`OUT_OF_SCOPE []` + `G07_OK` 即通过。作者实测 STAGED_COUNT 期望
   commit1=7、commit2=7、commit3=20；数目不同本身不算失败，以 `OUT_OF_SCOPE`
   为准，但要报数。
5. **commit 3 的 message 已替换**，用 A3.3 的新版全文，不要用原包那版。
   commit 1 / commit 2 的 `git add` 与 message 原样不变。
6. **下列输出不是失败，不要因此 STOP**：`LF will be replaced by CRLF` 警告、
   `PytestConfigWarning: Unknown config option: cache_dir`、
   `workspace/v72p2d5_dispo_r1_*` 这个 pytest basetemp 目录存在（它不在任何白
   名单里，保持不提交即可）。POSIX 命令用等价 PowerShell 形式也可以，汇报里说
   一句。

执行顺序：

- 跑 A2.3 的 **G06'**（自锚定到任务包文件 mtime），期望
  `NEWER_THAN_PACKET []` + `G06_OK`；
- 通过后直接进 STEP 6，三次提交，每次 `git add` 之后、`git commit` 之前插入
  A3.1 的 **G07'**（把该次 `git add` 的同一批路径原样传给脚本当参数）；
- `G07_FAIL` 就 STOP，不提交、**不要 unstage、不要 clean**——带着已暂存的 index
  停住就是正确状态，直接报给我。

仍然禁止：`git push`、`git add -A`、`git add .`、`git commit -a`、`git reset`、
`git stash`、`git checkout --`、`git clean`、`git rebase`、`git commit --amend`。
仍然禁止：运行 decoder、运行 `--phase p0-cost|g1|g2`、运行
`v72p2d5_prepare_model_f_input.py`、读 CAL/VAL/parquet、改任何 `.py`、改任何
`*_execution_authorized`、写 `RESULT_SUMMARY`/`OPERATOR_RETURN`/`run_01`。

完成后按 STEP 7 汇报，其中第 1、2 项按 A3.5 的新写法（引用 A2.1 的 G03 裁决，
不要复现 STEP 1 表），第 3、4、5 项不变。另补一句：G05 由 A1 取代、G06 由 A2
取代、G07 与 commit-3 message 由 A3 取代，G05'/G06'/G07' 均通过。最后仍要原样
写出：

「PR16 仅以记录方式处置；Model-F Pre-RESULT 复审尚未进行；P0 未授权。」

不要提出下一步实验建议。不要自行推进到 P0。

=====
