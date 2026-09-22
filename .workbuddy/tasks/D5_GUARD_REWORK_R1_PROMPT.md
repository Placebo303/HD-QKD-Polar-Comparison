# Paste-ready prompt — D5-GUARD-REWORK-R1 (tests only, no execution)

Copy everything between the two `=====` lines into a fresh session opened in
`D:/Code/HD-QKD_Polar_Comparison`.

=====

本次任务**只改测试代码**，不动任何生产代码，不跑 P0/G1/G2，不跑 decoder。

任务包全文在：
`D:/Code/HD-QKD_Polar_Comparison/.workbuddy/tasks/D5_GUARD_REWORK_R1_TASK_PACKET.md`

先完整读完，再按 T1 → T6 执行。

## 要修什么

`b4696273` 上有 7 个测试失败。**跑测试时 basetemp 必须放在 `workspace/` 下**——
放到仓库外会让 D4 那批 audit 测试假失败（这点我踩过，别重蹈）。

其中 6 个断言"P0 正式根不存在"，而 2026-09-07 一次**合法的、已授权的** P0 运行
创建了 `workspace/v72p2d5_p0_cost/20260906_r1/`，于是它们全红：

- `test_M24_formal_roots_absent`、`test_P12_formal_roots_absent`（model_f_input 文件）
- `test_R1_B2_all_exec_false_formal_absent_and_budgets`、
  `test_P0G1G2_f_no_holdout_or_file_access`、
  `test_P0G1G2_g_four_file_no_overwrite`、
  `test_M20_d5_authorized_fake_load_reaches_runner`（rate_mother 文件）

第 7 个 `test_T1_22_openspec_history_zero_mod` 是另一回事，见 T3。

## 为什么这不是"把红的改绿"

这正是 `UNAUTHORIZED_G1_TEST_EXECUTION_INCIDENT_20260907.md` 里那次未授权 G1 执行
的同一类缺陷：**守卫假定正式根永远不存在，合法产物一落地就悄悄失去意义。** 上次的
后果不只是测试变红——失效的缺席预期和一处裸 `authorized=True` 调用凑到一起，测试
套把生产 decoder 一路开进了正式输出根。这次隔离（SAFE A/B/C）拦住了执行，但
**守卫模型本身没修**，G1、G2 一产出合法结果就会再次失效。

## 怎么修

这些守卫真正需要的不变量是"**本测试没有碰过任何正式根**"，而不是"不存在任何正式
根"。缺席只是早期恰好成立的替身。

两个测试文件里已经有对的原语 `_snapshot_dir`（Model-F 和 G1 根就是这么守的）。
把它推广成共享 helper（两个文件各写一份，**不要跨文件 import**），语义必须是：

- 开始不存在、结束仍不存在 → 通过
- 开始存在、结束逐字节相同（名字/大小/mtime）→ 通过
- **被本测试创建 → 失败**
- 被删除，或有文件增删、大小或 mtime 变化 → 失败

覆盖 P0、G1、G2、G0、G0-recovery、Model-F、structure 全部正式根。

**绝对不许用来"让测试变绿"的做法**：删断言、缩小循环、加 `skip`/`xfail`、把断言写
成恒真。这些都算任务失败而不是完成。真觉得某个守卫无法既绿又有意义，就 STOP 并说明
是哪一个、为什么。

另外**不许动那六个测试里其余的断言**：`test_M20` 的可达性断言、`test_P0G1G2_f` 的
无文件访问断言、`test_P0G1G2_g` 的四文件与不可覆盖断言、`test_R1_B2` 的授权与预算
断言，全部原样保留。你换掉的只是那一行缺席断言。`test_P0G1G2_g` 里对三个正式根
**字面路径字符串**的断言属于冻结常量检查，也原样不动。

## T3：`test_T1_22`

它断言跟踪树干净，现在失败是因为工作区有约 1887 个文件的**纯行尾差异、内容零变更**
（`core.autocrlf=true`、无 `.gitattributes`，`299416ae` 自身不含这些）。复审已判为
化妆品问题，并明确排除了仓库侧规范化作为前置。

把它的判据改成**真实内容差异**（例如基于 `git diff --numstat`，增删行数都为 0 就不
算修改）。**它原本的作用必须保住**：跟踪文件**内容**一变它还得红。不许删、不许 skip、
不许改到没用。

## T4：加一个防复发守卫

新增一个测试，扫描这两个测试文件的源码，若发现任何针对 `P0_FORMAL_ROOT`、
`G1_FORMAL_ROOT`、`G2_FORMAL_ROOT`、`G0_FORMAL_ROOT`、`G0_RECOVERY_FORMAL_ROOT`、
`MODEL_F_FORMAL_ROOT` 或其字面路径的**不存在断言**，就失败（风格参照已有的 AST 静态
守卫）。失败信息里要写清该改用什么。这是防止后续任务包把同一类问题再塞回来的那道闸。

## T5 验证

- 两个测试文件 `py_compile`。
- 三文件全量跑，basetemp 放 `workspace/` 下，**目标 0 failed**，贴原文行；仍有失败
  必须点名解释，不许藏。
- 确认 SAFE A/B/C 与 AST 静态守卫仍通过且未被削弱。
- **要证明新 helper 真的能抓到"创建"**：在正式根之外的临时目录里演示它在被守护目录
  被创建时会失败。**不许拿真实正式根做这个演示。** 报告你是怎么证明的。
- 生产代码 `git diff --numstat` 必须为空——两个测试文件之外不许有任何 `.py` 变化。
- 六个正式根前后 stat 全部未变、G2 仍不存在；跑完删掉你自己建的 basetemp 目录。

## 其它硬约束

不许改 `cycle_state.yaml`、OpenSpec、任何既有 `.md`；不许读 CAL/VAL/parquet 行；
不许让 `workspace/v72p2d5_g2/20260906_r1` 出现；`workspace/` 下既有产物一律只读；
不许 `git push`、`add -A`、`add .`、`commit -a`、`reset`、`stash`、`checkout`、
`clean`、`rebase`、`amend`、`add --renormalize`。只提交那两个测试文件，提交前用
`git diff --cached --name-only` 核对，message 用任务包 T6 原文。

最后按任务包 §8 汇报，然后停下——下一步是独立复审，不是 G1。

=====
