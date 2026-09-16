# Paste-ready prompt — D5-GUARD-REWORK-REVIEW-R1 independent review

Copy everything between the two `=====` lines into a FRESH session opened in
`D:/Code/HD-QKD_Polar_Comparison`. Do not reuse the session that wrote the
rework.

=====

你是本次的**独立只读评审**。你没有写这次守卫返工，也没参与之前任何一次 D5 任务包的
执行；不要采信任何转述结论（**包括任务包里引给你的那些数字**，其中有一条正是让你去
核的事实分歧），一切从源码和你自己的实测重新推导。

任务包全文在：
`D:/Code/HD-QKD_Polar_Comparison/.workbuddy/tasks/D5_GUARD_REWORK_REVIEW_R1_PACKET.md`

先完整读完，再按 §2 → §8 执行。

被评审对象：commit `860ebbff`（两个测试文件，+146/−49）。

**跑 pytest 时 basetemp 必须放 `workspace/` 下**——放到仓库外会让 D4 那批 audit 测试
假失败，那是调用方式的产物，不是回归。

## 要裁什么

六个守卫原先断言"正式输出根不存在"，一次**合法的、已授权的** P0 运行创建了 P0 根，
于是全红。`860ebbff` 把缺席断言换成了快照不变性。

这不只是测试卫生问题：同一套"陈旧缺席守卫"模型正是
`UNAUTHORIZED_G1_TEST_EXECUTION_INCIDENT_20260907.md` 那次事故的一环——失效的缺席
预期和一处裸 `authorized=True` 调用凑在一起，测试套把生产 decoder 开进了正式输出根。

你要判断：**新的守卫模型是否成立、是否真的比原来更强、以及有没有为了让测试变绿而
削弱任何东西。**

## 必须自己做的几项

1. **语义有没有漏洞**：读两个文件里的 `_formal_roots` / `_snapshot_formal_roots` /
   `_assert_formal_roots_unchanged`。缺席→缺席过、现存→相同过、**创建即失败**、
   删除或任何增删/改大小/改 mtime 即失败——这四条是否都真的成立？特别想清楚：
   会不会出现"测试创建了根却仍然通过"的情形（快照取得太晚、某个分支跳过比较、
   异常路径绕过末尾断言、helper 被调用但返回值被丢弃）？七个根是否都覆盖、路径是否
   都对？`None` 表示"不存在"是否与"空目录"明确区分？
2. **深度盲区**：实现者自曝 `_snapshot_dir` 只看顶层文件。评估正式根下的**嵌套写入**
   会怎样，这个缺口是可接受的遗留限制，还是必须在 G1/G2 产出之前补上。
3. **有没有被削弱**：把 `860ebbff` 与父提交逐一对照，确认六个测试里**只有那行缺席
   断言变了**，其余全部存活——`test_M20` 的可达性断言、`test_P0G1G2_f` 的无文件访问
   断言、`test_P0G1G2_g` 的四文件/不可覆盖/冻结字面路径断言、`test_R1_B2` 的授权与
   预算断言。同时确认生产 `.py` 零变更、SAFE A/B/C 与既有 AST 守卫未被削弱。
4. **创建捕获要你自己复现**：实现者声称已在正式根之外的临时目录证明 helper 能抓到
   "创建"。**不许采信，也不许复用它的脚本。** 自己在自己的 scratch 目录里构造演示，
   **绝不许拿真实正式根做**，并报告你怎么做的、看到了什么。若你无法让 helper 在创建
   时失败，这是阻塞发现。
5. **`test_T1_22`**：判据已从 `git status` porcelain 改为 `git diff --numstat`。确认
   它在真实跟踪内容变更时仍会红（演示时不许留下任何残留修改，做不到就标
   `NOT_VERIFIABLE` 并说明），并判断 staged/unstaged 是否都覆盖、二进制文件
   （`-`/`-`）是否处理。
   **一个要你核的事实分歧**：实现者报告称改前 porcelain 计数是 `STATUS=63`；评审
   发起时的独立测量是 **1887** 个修改路径、`numstat` 内容变更 **0**。你自己测出真实
   数字，报告这个分歧，并判断它只是报告笔误，还是影响返工本身的正确性。
6. **`test_T1_23`**：读它，判断它**实际**能不能挡住"重新引入缺席断言"，包括可能漏掉
   的写法（换比较运算符、路径走中间变量、字面路径不在它列表里、`os.path.exists`、
   `Path.is_dir` 等）。写出它的真实覆盖面，而不是它想覆盖的面。

## 硬约束

授权 false。不许跑 decoder、不许跑 P0/G1/G2（除必须 exit 3 的未授权拒绝检查）、
不许跑 prepare 脚本、不许读 CAL/VAL/parquet 行。**一旦 G2 正式根出现，立刻 STOP 并
作为严重发现上报。** `workspace/` 下除你自建并事后删除的 basetemp 与 scratch 目录外
一律只读，六个正式根是证据。不许改任何 `.py`、既有 `.md`、OpenSpec、
`cycle_state.yaml`。不许 `git add/commit/push/reset/stash/checkout/clean/rebase/
revert/add --renormalize` 或任何会写入跟踪文件的操作。**发现问题只报告，不修复。**

## 产出

**只允许新建 1 个文件**
`docs/research_cycles/V72P2D5-GF32-RATE-MOTHER/GUARD_REWORK_REVIEW_R1.md`，
内容按任务包 §7。结论只能二选一：`GUARD_REWORK_REVIEW_PASS`（并列出必须带进 G1 包的
限制）或 `GUARD_REWORK_REVIEW_FAIL`（点名阻塞发现 + 重审前必须做的那组修改）。

明确不主张：无 FER、无泄漏、无密钥率、无资格、无方法裁决，也不主张 G1 已就绪。

最后在消息里汇报：结论、检查表简表、你自己的创建捕获演示（一两句）、深度盲区判断、
`test_T1_23` 覆盖面判断、`STATUS=63` 分歧、pytest 原文行，以及——仅当仍成立时——

「P0 结果仅为记录，未接受；G1 未授权；next_gate 仍为 P0_PACKET_REVIEW。」

=====
